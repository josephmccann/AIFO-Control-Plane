"""Trusted GitHub and Git adapter for the test-integrity kernel."""

import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from .commands import authenticate_event_history
from .mission import parse_issue_body
from .schema import validate_document
from .test_integrity import (
    CoverageAttestation, ResourceBudget, _file_digests, analyze_test_integrity,
    authenticate_integrity_context,
)
from .canonical import content_sha256


_SHA40 = re.compile(r"[0-9a-f]{40}")
_MISSION_MARKER = re.compile(r"<!-- AIFO-EOS-MISSION-ISSUE: ([1-9][0-9]*) -->")
_INITIAL_READY_REPOSITORY = "josephmccann/AI.FO-Demo"
_INITIAL_READY_BASE_SHA = "438a68bf0b4f49ae15a04a69ad72c14cc43de0cb"
_INITIAL_READY_MISSION_SHA256 = "9a9c6b751c45732d108d0f833f6096df1558c9d546761fc03a922489dfa0240a"
_DEFAULT_LIMITS = {
    "max_files": 10000, "max_total_bytes": 256 * 1024 * 1024,
    "max_path_bytes": 1024, "max_git_record_bytes": 4096,
    "max_github_pages": 20, "max_github_items": 2000,
    "max_github_response_bytes": 8 * 1024 * 1024,
    "max_coverage_bytes": 1024 * 1024,
}


def _initial_ready_attestation(
    pr: Mapping[str, Any], issue: Mapping[str, Any], mission_sha256: str,
    comments: Sequence[Mapping[str, Any]], policy: Mapping[str, Any], *,
    repository: str, pull_request: int, base_sha: str, head_sha: str,
) -> Optional[str]:
    """Bind the one authorized pre-activation mission to GitHub evidence."""

    if not (
        repository == _INITIAL_READY_REPOSITORY
        and pull_request == 202
        and base_sha == _INITIAL_READY_BASE_SHA
        and _SHA40.fullmatch(head_sha or "") is not None
        and mission_sha256 == _INITIAL_READY_MISSION_SHA256
        and comments == []
        and pr.get("number") == pull_request
        and pr.get("state") == "open"
        and pr.get("user", {}).get("login") == "josephmccann"
        and pr.get("head", {}).get("ref") == "codex/eos-package-8"
        and pr.get("head", {}).get("sha") == head_sha
        and pr.get("head", {}).get("repo", {}).get("full_name") == repository
        and issue.get("number") == 201
        and issue.get("state") == "open"
        and issue.get("user", {}).get("login") == "josephmccann"
        and policy.get("repository") == repository
        and "josephmccann" in policy.get("founder_identities", [])
    ):
        return None
    return content_sha256({
        "schema_version": "1.0.0",
        "type": "initial-ready-attestation",
        "repository": repository,
        "pull_request": pull_request,
        "mission_issue": 201,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "mission_sha256": mission_sha256,
        "founder": "josephmccann",
    })


def _bounded_file_bytes(
    path: Path, resource_budget: ResourceBudget, *, phase: str,
) -> bytes:
    payload = bytearray()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(65536)
            if not chunk:
                break
            resource_budget.consume_bytes(len(chunk), phase=phase)
            payload.extend(chunk)
    return bytes(payload)


def _command_bytes(
    command: Sequence[str], max_bytes: int, *, env=None,
    resource_budget: ResourceBudget = None, phase: str = "command",
) -> bytes:
    process = subprocess.Popen(
        list(command), stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env,
    )
    output = bytearray()
    try:
        while True:
            chunk = process.stdout.read(min(65536, max_bytes + 1))
            if not chunk:
                break
            output.extend(chunk)
            if len(output) > max_bytes:
                process.kill()
                raise OverflowError("TEST_RESOURCE_LIMIT")
        if process.wait() != 0:
            raise subprocess.CalledProcessError(process.returncode, command)
        result = bytes(output)
        if resource_budget is not None:
            resource_budget.consume_bytes(len(result), phase=phase)
        return result
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        if process.stdout is not None:
            process.stdout.close()


def _git(
    root: Path, *args: str, max_bytes: int = 65536,
    resource_budget: ResourceBudget = None,
) -> bytes:
    return _command_bytes(
        ["git", "-C", str(root), *args], max_bytes,
        resource_budget=resource_budget, phase="git-command",
    )


def _git_zero_records(
    root: Path, args: Sequence[str], *, max_record_bytes: int, max_total_bytes: int,
    resource_budget: ResourceBudget = None,
):
    process = subprocess.Popen(
        ["git", "-C", str(root), *args], stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    pending = bytearray()
    total = 0
    try:
        while True:
            chunk = process.stdout.read(65536)
            if not chunk:
                break
            total += len(chunk)
            if total > max_total_bytes:
                raise OverflowError("TEST_RESOURCE_LIMIT")
            pending.extend(chunk)
            while b"\0" in pending:
                record, _, remainder = pending.partition(b"\0")
                pending = bytearray(remainder)
                if len(record) > max_record_bytes:
                    raise OverflowError("TEST_RESOURCE_LIMIT")
                if record:
                    if resource_budget is not None:
                        resource_budget.consume_git_record(len(record))
                    yield bytes(record)
            if len(pending) > max_record_bytes:
                raise OverflowError("TEST_RESOURCE_LIMIT")
        if pending:
            raise ValueError("TEST_GIT_TREE_INCOMPLETE")
        if process.wait() != 0:
            raise subprocess.CalledProcessError(process.returncode, args)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        if process.stdout is not None:
            process.stdout.close()


def _tree_manifest(
    root: Path, commit_sha: str, max_file_bytes: int, limits: Mapping[str, int],
    usage: Dict[str, int], resource_budget: ResourceBudget = None,
) -> Dict[str, Dict[str, str]]:
    if _git(
        root, "status", "--porcelain=v1", "-z", "--untracked-files=all",
        max_bytes=limits["max_total_bytes"], resource_budget=resource_budget,
    ):
        raise ValueError("TEST_CHECKOUT_DIRTY")
    manifest = {}
    for record in _git_zero_records(
        root, ["ls-tree", "-rz", commit_sha],
        max_record_bytes=limits["max_git_record_bytes"],
        max_total_bytes=limits["max_total_bytes"],
        resource_budget=resource_budget,
    ):
        try:
            metadata, raw_path = record.split(b"\t", 1)
            mode, object_type, object_sha = metadata.decode("ascii").split(" ")
            name = raw_path.decode("utf-8")
        except (UnicodeDecodeError, ValueError):
            raise ValueError("TEST_GIT_PATH_INVALID")
        if len(name.encode("utf-8")) > limits["max_path_bytes"]:
            raise OverflowError("TEST_RESOURCE_LIMIT")
        usage["files"] += 1
        if usage["files"] > limits["max_files"]:
            raise OverflowError("TEST_RESOURCE_LIMIT")
        if resource_budget is not None:
            resource_budget.consume_file(name, phase="git-tree")
        if object_type != "blob" or mode == "120000" or _SHA40.fullmatch(object_sha) is None:
            raise ValueError("TEST_GIT_OBJECT_UNSUPPORTED")
        path = root / name
        if not path.is_file() or path.is_symlink():
            raise ValueError("TEST_CHECKOUT_INCOMPLETE")
        usage["bytes"] += path.stat().st_size
        if usage["bytes"] > limits["max_total_bytes"]:
            raise OverflowError("TEST_RESOURCE_LIMIT")
        evidence = _file_digests(
            path, max_file_bytes, resource_budget, phase="git-blob-verification",
        )
        if evidence["git_blob_sha"] != object_sha:
            raise ValueError("TEST_CHECKOUT_MISMATCH")
        manifest[name] = evidence
    disk = set()
    pending = [root]
    reconciled_entries = 0
    while pending:
        directory = pending.pop()
        with os.scandir(str(directory)) as entries:
            for entry in entries:
                path = Path(entry.path)
                relative = path.relative_to(root)
                if relative.parts and relative.parts[0] == ".git":
                    continue
                reconciled_entries += 1
                if reconciled_entries > limits["max_files"]:
                    raise OverflowError("TEST_RESOURCE_LIMIT")
                name = relative.as_posix()
                if resource_budget is not None:
                    resource_budget.consume_entry(name, phase="filesystem-reconciliation")
                elif len(name.encode("utf-8")) > limits["max_path_bytes"]:
                    raise OverflowError("TEST_RESOURCE_LIMIT")
                if entry.is_symlink():
                    raise ValueError("TEST_CHECKOUT_DIRTY")
                if entry.is_dir(follow_symlinks=False):
                    pending.append(path)
                    continue
                if not entry.is_file(follow_symlinks=False):
                    raise ValueError("TEST_CHECKOUT_DIRTY")
                if len(disk) >= limits["max_files"]:
                    raise OverflowError("TEST_RESOURCE_LIMIT")
                disk.add(name)
    if disk != set(manifest):
        raise ValueError("TEST_CHECKOUT_DIRTY")
    return manifest


def derive_git_manifests(
    base_root: Any, head_root: Any, base_sha: str, head_sha: str,
    max_file_bytes: int, limits: Mapping[str, int] = None,
    *, resource_budget: ResourceBudget = None,
) -> Tuple[Dict[str, Dict[str, str]], Dict[str, Dict[str, str]]]:
    """Verify exact clean commits, direction, ancestry, and blob bytes."""

    bounded = {**_DEFAULT_LIMITS, **dict(limits or {})}
    budget = resource_budget or ResourceBudget(bounded)
    budget.require_limits(bounded)
    base, head = Path(base_root).resolve(strict=True), Path(head_root).resolve(strict=True)
    if base == head or _SHA40.fullmatch(base_sha or "") is None or _SHA40.fullmatch(head_sha or "") is None:
        raise ValueError("TEST_REVISION_EVIDENCE_INVALID")
    if _git(base, "rev-parse", "--verify", "HEAD^{commit}", max_bytes=64, resource_budget=budget).decode("ascii").strip() != base_sha:
        raise ValueError("TEST_REVISION_BASE_MISMATCH")
    if _git(head, "rev-parse", "--verify", "HEAD^{commit}", max_bytes=64, resource_budget=budget).decode("ascii").strip() != head_sha:
        raise ValueError("TEST_REVISION_HEAD_MISMATCH")
    _git(
        head, "fetch", "--quiet", "--no-tags", str(base), base_sha,
        max_bytes=1024, resource_budget=budget,
    )
    ancestor = subprocess.run(
        ["git", "-C", str(head), "merge-base", "--is-ancestor", base_sha, head_sha],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if ancestor.returncode != 0:
        raise ValueError("TEST_REVISION_UNRELATED")
    usage = {"files": 0, "bytes": 0}
    return (
        _tree_manifest(base, base_sha, max_file_bytes, bounded, usage, budget),
        _tree_manifest(head, head_sha, max_file_bytes, bounded, usage, budget),
    )


def _gh(
    *args: str, max_response_bytes: int, usage: Dict[str, int] = None,
    resource_budget: ResourceBudget = None,
) -> Any:
    remaining = max_response_bytes
    if usage is not None:
        remaining -= usage.get("response_bytes", 0)
        if remaining < 1:
            raise ValueError("TEST_GITHUB_RESOURCE_LIMIT")
    raw = _command_bytes(
        ["gh", "api", *args], remaining, env=os.environ,
    )
    if usage is not None:
        usage["response_bytes"] = usage.get("response_bytes", 0) + len(raw)
    if resource_budget is not None:
        resource_budget.consume_github(response_bytes=len(raw))
    return json.loads(raw.decode("utf-8"))


def validate_github_pages(
    value: Any, max_pages: int, max_items: int, max_response_bytes: int,
) -> list:
    if not isinstance(value, list) or len(value) > max_pages:
        raise ValueError("TEST_GITHUB_RESOURCE_LIMIT")
    if len(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")) > max_response_bytes:
        raise ValueError("TEST_GITHUB_RESOURCE_LIMIT")
    flattened = []
    for page in value:
        if not isinstance(page, list):
            raise ValueError("TEST_GITHUB_EVIDENCE_INVALID")
        if len(flattened) + len(page) > max_items:
            raise ValueError("TEST_GITHUB_RESOURCE_LIMIT")
        flattened.extend(page)
    return flattened


def _github_mission(
    repository: str, pull_request: int, base_sha: str, head_sha: str,
    policy: Mapping[str, Any], changed_files: Sequence[str],
    resource_budget: ResourceBudget = None,
) -> Dict[str, Any]:
    limits = _DEFAULT_LIMITS
    response_cap = limits["max_github_response_bytes"]
    usage = {"response_bytes": 0, "pages": 0, "items": 0}
    pr = _gh(
        "repos/%s/pulls/%d" % (repository, pull_request),
        max_response_bytes=response_cap, usage=usage,
        resource_budget=resource_budget,
    )
    if (
        not isinstance(pr, Mapping) or pr.get("number") != pull_request
        or pr.get("base", {}).get("sha") != base_sha
        or pr.get("head", {}).get("sha") != head_sha
        or pr.get("base", {}).get("repo", {}).get("full_name") != repository
    ):
        raise ValueError("TEST_PULL_REQUEST_EVIDENCE_INVALID")
    markers = _MISSION_MARKER.findall(pr.get("body") if isinstance(pr.get("body"), str) else "")
    if len(markers) != 1:
        raise ValueError("TEST_MISSION_MARKER_INVALID")
    issue_number = int(markers[0])
    issue = _gh(
        "repos/%s/issues/%d" % (repository, issue_number),
        max_response_bytes=response_cap, usage=usage,
        resource_budget=resource_budget,
    )
    if not isinstance(issue, Mapping) or issue.get("number") != issue_number:
        raise ValueError("TEST_MISSION_ISSUE_INVALID")
    mission = parse_issue_body(issue.get("body", ""))
    comment_pages = _gh(
        "--paginate", "--slurp",
        "repos/%s/issues/%d/comments?per_page=100" % (repository, issue_number),
        max_response_bytes=response_cap, usage=usage,
        resource_budget=resource_budget,
    )
    comments = validate_github_pages(
        comment_pages, limits["max_github_pages"], limits["max_github_items"], response_cap,
    )
    usage["pages"] += len(comment_pages)
    usage["items"] += 2 + len(comments)
    if resource_budget is not None:
        resource_budget.consume_github(pages=len(comment_pages), items=2 + len(comments))
    run_pages = _gh(
        "--paginate", "--slurp", "repos/%s/actions/runs?per_page=100" % repository,
        max_response_bytes=response_cap, usage=usage,
        resource_budget=resource_budget,
    )
    actions_runs = []
    if not isinstance(run_pages, list):
        raise ValueError("TEST_GITHUB_EVIDENCE_INVALID")
    if len(run_pages) > limits["max_github_pages"]:
        raise ValueError("TEST_GITHUB_RESOURCE_LIMIT")
    usage["pages"] += len(run_pages)
    if usage["pages"] > limits["max_github_pages"]:
        raise ValueError("TEST_GITHUB_RESOURCE_LIMIT")
    for page in run_pages:
        if not isinstance(page, Mapping) or not isinstance(page.get("workflow_runs"), list):
            raise ValueError("TEST_GITHUB_EVIDENCE_INVALID")
        if usage["items"] + len(actions_runs) + len(page["workflow_runs"]) > limits["max_github_items"]:
            raise ValueError("TEST_GITHUB_RESOURCE_LIMIT")
        actions_runs.extend(page["workflow_runs"])
    if resource_budget is not None:
        resource_budget.consume_github(pages=len(run_pages), items=len(actions_runs))
    mission_sha256 = content_sha256(mission)
    initial_ready_attestation = _initial_ready_attestation(
        pr,
        issue,
        mission_sha256,
        comments,
        policy,
        repository=repository,
        pull_request=pull_request,
        base_sha=base_sha,
        head_sha=head_sha,
    )
    return authenticate_integrity_context(
        mission, comments, policy, changed_files, repository=repository,
        mission_issue=issue_number, pull_request=pull_request,
        base_sha=base_sha, head_sha=head_sha, actions_runs=actions_runs,
        initial_ready_attestation_sha256=initial_ready_attestation,
    )


def _coverage_attestation(
    repository: str, commit_sha: str, root: Path, manifest: Mapping[str, Any],
    coverage_path: str, coverage_paths: Sequence[str], limits: Mapping[str, int],
    resource_budget: ResourceBudget = None,
) -> CoverageAttestation:
    response_cap = limits["max_github_response_bytes"]
    usage = {"response_bytes": 0}
    runs = _gh(
        "repos/%s/actions/workflows/coverage.yml/runs?head_sha=%s&status=completed&per_page=100"
        % (repository, commit_sha), max_response_bytes=response_cap, usage=usage,
        resource_budget=resource_budget,
    )
    candidates = runs.get("workflow_runs") if isinstance(runs, Mapping) else None
    if not isinstance(candidates, list) or len(candidates) > limits["max_github_items"]:
        raise ValueError("TEST_COVERAGE_ATTESTATION_UNAVAILABLE")
    if resource_budget is not None:
        resource_budget.consume_github(pages=1, items=len(candidates))
    candidates = [
        item for item in candidates
        if isinstance(item, Mapping)
        and item.get("head_sha") == commit_sha
        and item.get("path") == ".github/workflows/coverage.yml"
        and item.get("conclusion") == "success"
        and isinstance(item.get("id"), int) and not isinstance(item.get("id"), bool)
    ]
    if len(candidates) != 1:
        raise ValueError("TEST_COVERAGE_ATTESTATION_UNAVAILABLE")
    run = candidates[0]
    workflow = _gh(
        "repos/%s/contents/.github/workflows/coverage.yml?ref=%s" % (repository, commit_sha),
        max_response_bytes=response_cap, usage=usage,
        resource_budget=resource_budget,
    )
    workflow_sha = workflow.get("sha") if isinstance(workflow, Mapping) else None
    if not isinstance(workflow_sha, str) or _SHA40.fullmatch(workflow_sha) is None:
        raise ValueError("TEST_COVERAGE_ATTESTATION_UNAVAILABLE")
    if resource_budget is not None:
        resource_budget.consume_github(pages=1, items=1)
    artifacts = _gh(
        "repos/%s/actions/runs/%d/artifacts?per_page=100" % (repository, run["id"]),
        max_response_bytes=response_cap, usage=usage,
        resource_budget=resource_budget,
    )
    candidates = artifacts.get("artifacts") if isinstance(artifacts, Mapping) else None
    expected_name = "eos-coverage-%s" % commit_sha
    if not isinstance(candidates, list) or len(candidates) > limits["max_github_items"]:
        raise ValueError("TEST_COVERAGE_ATTESTATION_UNAVAILABLE")
    if resource_budget is not None:
        resource_budget.consume_github(pages=1, items=len(candidates))
    candidates = [
        item for item in candidates
        if isinstance(item, Mapping) and item.get("name") == expected_name
        and item.get("expired") is False
    ]
    if len(candidates) != 1:
        raise ValueError("TEST_COVERAGE_ATTESTATION_UNAVAILABLE")
    artifact = candidates[0]
    raw_digest = artifact.get("digest")
    if not isinstance(raw_digest, str) or not raw_digest.startswith("sha256:"):
        raise ValueError("TEST_COVERAGE_ATTESTATION_UNAVAILABLE")
    artifact_digest = raw_digest.removeprefix("sha256:")
    if re.fullmatch(r"[0-9a-f]{64}", artifact_digest) is None:
        raise ValueError("TEST_COVERAGE_ATTESTATION_UNAVAILABLE")
    archive = _command_bytes(
        ["gh", "api", "repos/%s/actions/artifacts/%d/zip" % (repository, artifact.get("id"))],
        limits["max_coverage_bytes"], env=os.environ,
    )
    if resource_budget is not None:
        resource_budget.consume_coverage(len(archive))
    if hashlib.sha256(archive).hexdigest() != artifact_digest:
        raise ValueError("TEST_COVERAGE_ATTESTATION_UNAVAILABLE")
    try:
        with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
            names = bundle.namelist()
            if names != [coverage_path]:
                raise ValueError("TEST_COVERAGE_ATTESTATION_UNAVAILABLE")
            info = bundle.getinfo(coverage_path)
            if info.file_size > limits["max_coverage_bytes"]:
                raise OverflowError("TEST_RESOURCE_LIMIT")
            with bundle.open(info) as handle:
                coverage_bytes = handle.read(limits["max_coverage_bytes"] + 1)
    except (KeyError, OSError, zipfile.BadZipFile):
        raise ValueError("TEST_COVERAGE_ATTESTATION_UNAVAILABLE")
    if len(coverage_bytes) > limits["max_coverage_bytes"]:
        raise OverflowError("TEST_RESOURCE_LIMIT")
    if resource_budget is not None:
        resource_budget.consume_coverage(len(coverage_bytes))
    file_digest = hashlib.sha256(coverage_bytes).hexdigest()
    if file_digest != manifest[coverage_path]["sha256"]:
        raise ValueError("TEST_COVERAGE_ATTESTATION_UNAVAILABLE")
    document = json.loads(coverage_bytes.decode("utf-8"))
    generated_at = document.get("generated_at")
    transport_created_at = artifact.get("created_at")
    if not isinstance(generated_at, str) or not isinstance(transport_created_at, str):
        raise ValueError("TEST_COVERAGE_ATTESTATION_UNAVAILABLE")
    source_manifest = {
        path: evidence for path, evidence in manifest.items() if path not in coverage_paths
    }
    return CoverageAttestation(
        "1.0.0", repository, commit_sha, content_sha256(source_manifest), generated_at,
        transport_created_at,
        ".github/workflows/coverage.yml", workflow_sha, run["id"], artifact["id"],
        artifact_digest, coverage_path, file_digest, run["conclusion"],
        "github-actions-api:%s" % run.get("html_url", ""),
    )


def _coverage_attestations(
    repository: str, base_sha: str, head_sha: str, base_root: Path, head_root: Path,
    base_manifest: Mapping[str, Any], head_manifest: Mapping[str, Any],
    coverage_paths: Sequence[str], limits: Mapping[str, int],
    resource_budget: ResourceBudget = None,
):
    present_base = [path for path in coverage_paths if path in base_manifest]
    present_head = [path for path in coverage_paths if path in head_manifest]
    if not present_base and not present_head:
        return None
    if len(present_base) != 1 or len(present_head) != 1 or present_base[0] != present_head[0]:
        return None
    try:
        return {
            "base": _coverage_attestation(
                repository, base_sha, base_root, base_manifest, present_base[0],
                coverage_paths, limits,
                resource_budget,
            ),
            "head": _coverage_attestation(
                repository, head_sha, head_root, head_manifest, present_head[0],
                coverage_paths, limits,
                resource_budget,
            ),
        }
    except OverflowError:
        raise
    except (Exception, MemoryError, UnicodeError):
        return None


def _initial_report(args: Sequence[str]) -> Tuple[Path, Dict[str, Any]]:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--output", required=True)
    parsed, _ = parser.parse_known_args(args)
    output = Path(parsed.output)
    value = {
        "schema_version": "1.0.0", "repository": "", "base_sha": "",
        "head_sha": "", "allowed": False, "findings": [{
            "code": "TEST_INTEGRITY_NOT_COMPLETED",
            "message": "Test-integrity analysis did not complete.", "path": "$", "details": {},
        }], "deltas": {},
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return output, value


def main(argv: Sequence[str] = None) -> int:
    values = list(sys.argv[1:] if argv is None else argv)
    if "--help" in values or "-h" in values:
        print("usage: validate-test-integrity --base-root BASE --head-root HEAD --base-sha SHA --head-sha SHA --repository OWNER/REPO --base-policy PATH --pull-request NUMBER --output PATH")
        return 0
    try:
        output, _ = _initial_report(values)
    except BaseException:
        return 2
    parser = argparse.ArgumentParser(description="Generate authenticated EOS test-integrity evidence")
    parser.add_argument("--base-root", required=True)
    parser.add_argument("--head-root", required=True)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--base-policy", required=True)
    parser.add_argument("--pull-request", required=True, type=int)
    parser.add_argument("--evaluated-at")
    parser.add_argument("--output", required=True)
    try:
        args = parser.parse_args(values)
        if re.fullmatch(r"[^/]+/[^/]+", args.repository) is None:
            raise ValueError("TEST_REPOSITORY_INVALID")
        limits = dict(_DEFAULT_LIMITS)
        resource_budget = ResourceBudget(limits)
        policy = json.loads(_bounded_file_bytes(
            Path(args.base_policy), resource_budget, phase="policy-input",
        ).decode("utf-8"))
        violations = validate_document("repository-policy", policy)
        if violations or policy.get("repository") != args.repository:
            raise ValueError("TEST_BASE_POLICY_INVALID")
        max_file_bytes = 16 * 1024 * 1024
        base_manifest, head_manifest = derive_git_manifests(
            args.base_root, args.head_root, args.base_sha, args.head_sha, max_file_bytes,
            limits, resource_budget=resource_budget,
        )
        changed = sorted({
            path for path in set(base_manifest) | set(head_manifest)
            if base_manifest.get(path) != head_manifest.get(path)
        })
        mission = _github_mission(
            args.repository, args.pull_request, args.base_sha, args.head_sha,
            policy, changed, resource_budget,
        )
        evaluated = args.evaluated_at or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        configuration = {
            "test_globs": [
                "tests/**/test_*.py", "tests/**/*.test.js", "tests/**/*.spec.js",
                "tests/**/*.test.ts", "tests/**/*.spec.ts",
            ],
            "fixture_globs": ["tests/**/fixtures/**", "test/**/fixtures/**"],
            "validation_workflow_globs": [".github/workflows/**"],
            "test_config_globs": [
                "**/pyproject.toml", "**/pytest.ini", "**/setup.cfg", "**/tox.ini",
                "**/package.json", "**/jest.config.js", "**/jest.config.ts",
                "**/jest.config.mjs", "**/jest.config.cjs", "**/jest.config.json",
                "**/jest.config.yml", "**/jest.config.yaml", "**/vitest.config.js",
                "**/vitest.config.ts", "**/vitest.config.mjs", "**/vitest.config.cjs",
                "**/vitest.config.json", "**/vitest.config.yml", "**/vitest.config.yaml",
            ],
            "coverage_paths": ["coverage.json", "coverage-summary.json", ".eos/coverage.json"],
            "material_coverage_decline": 1.0,
            "assertion_patterns": [r"\bassert\b", r"\bexpect\s*\(", r"\.assert[A-Z]\w*\s*\("],
            "skip_patterns": [r"\bskip(?:If|Unless|Test)?\b", r"\.(?:skip|todo|disabled)\b", r"\bdisabled\b"],
            "max_file_bytes": max_file_bytes, "coverage_max_age_seconds": 86400,
            **limits,
        }
        attestations = _coverage_attestations(
            args.repository, args.base_sha, args.head_sha,
            Path(args.base_root), Path(args.head_root), base_manifest, head_manifest,
            configuration["coverage_paths"], limits,
            resource_budget,
        )
        analysis_policy = {
            "schema_version": "1.0.0", "repository": args.repository,
            "base_sha": args.base_sha, "head_sha": args.head_sha,
            "evaluated_at": evaluated, "base_manifest": base_manifest,
            "head_manifest": head_manifest,
            "coverage_attestations": attestations,
            "founder_identities": policy["founder_identities"], "mission": mission,
            "configuration": configuration,
        }
        report = analyze_test_integrity(
            args.base_root, args.head_root, analysis_policy,
            resource_budget=resource_budget,
        )
        report_bytes = (
            json.dumps(report.to_dict(), sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        resource_budget.consume_bytes(len(report_bytes), phase="report-output")
        output.write_bytes(report_bytes)
        return 0 if report.allowed else 1
    except (OverflowError, MemoryError) as error:
        value = {
            "schema_version": "1.0.0",
            "repository": getattr(locals().get("args"), "repository", ""),
            "base_sha": getattr(locals().get("args"), "base_sha", ""),
            "head_sha": getattr(locals().get("args"), "head_sha", ""),
            "allowed": False,
            "findings": [{
                "code": "TEST_RESOURCE_LIMIT",
                "message": "Integrity processing exceeded its shared deterministic resource budget.",
                "path": "$", "details": {},
            }],
            "deltas": {},
        }
        output.write_text(
            json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        print(str(error), file=sys.stderr)
        return 1
    except (Exception, UnicodeError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
