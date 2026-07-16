"""Trusted GitHub and Git adapter for the test-integrity kernel."""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence, Tuple

from .commands import authenticate_event_history
from .mission import parse_issue_body
from .schema import validate_document
from .test_integrity import (
    _file_digests, analyze_test_integrity, authenticate_integrity_context,
)


_SHA40 = re.compile(r"[0-9a-f]{40}")
_MISSION_MARKER = re.compile(r"<!-- AIFO-EOS-MISSION-ISSUE: ([1-9][0-9]*) -->")


def _git(root: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout


def _tree_manifest(root: Path, commit_sha: str, max_file_bytes: int) -> Dict[str, Dict[str, str]]:
    if _git(root, "status", "--porcelain=v1", "-z", "--untracked-files=all"):
        raise ValueError("TEST_CHECKOUT_DIRTY")
    raw = _git(root, "ls-tree", "-rz", commit_sha)
    if raw and not raw.endswith(b"\0"):
        raise ValueError("TEST_GIT_TREE_INCOMPLETE")
    manifest = {}
    for record in (item for item in raw.split(b"\0") if item):
        try:
            metadata, raw_path = record.split(b"\t", 1)
            mode, object_type, object_sha = metadata.decode("ascii").split(" ")
            name = raw_path.decode("utf-8")
        except (UnicodeDecodeError, ValueError):
            raise ValueError("TEST_GIT_PATH_INVALID")
        if object_type != "blob" or mode == "120000" or _SHA40.fullmatch(object_sha) is None:
            raise ValueError("TEST_GIT_OBJECT_UNSUPPORTED")
        path = root / name
        if not path.is_file() or path.is_symlink():
            raise ValueError("TEST_CHECKOUT_INCOMPLETE")
        evidence = _file_digests(path, max_file_bytes)
        if evidence["git_blob_sha"] != object_sha:
            raise ValueError("TEST_CHECKOUT_MISMATCH")
        manifest[name] = evidence
    disk = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(root).parts
    }
    if disk != set(manifest):
        raise ValueError("TEST_CHECKOUT_DIRTY")
    return manifest


def derive_git_manifests(
    base_root: Any, head_root: Any, base_sha: str, head_sha: str,
    max_file_bytes: int,
) -> Tuple[Dict[str, Dict[str, str]], Dict[str, Dict[str, str]]]:
    """Verify exact clean commits, direction, ancestry, and blob bytes."""

    base, head = Path(base_root).resolve(strict=True), Path(head_root).resolve(strict=True)
    if base == head or _SHA40.fullmatch(base_sha or "") is None or _SHA40.fullmatch(head_sha or "") is None:
        raise ValueError("TEST_REVISION_EVIDENCE_INVALID")
    if _git(base, "rev-parse", "--verify", "HEAD^{commit}").decode("ascii").strip() != base_sha:
        raise ValueError("TEST_REVISION_BASE_MISMATCH")
    if _git(head, "rev-parse", "--verify", "HEAD^{commit}").decode("ascii").strip() != head_sha:
        raise ValueError("TEST_REVISION_HEAD_MISMATCH")
    _git(head, "fetch", "--quiet", "--no-tags", str(base), base_sha)
    ancestor = subprocess.run(
        ["git", "-C", str(head), "merge-base", "--is-ancestor", base_sha, head_sha],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if ancestor.returncode != 0:
        raise ValueError("TEST_REVISION_UNRELATED")
    return (
        _tree_manifest(base, base_sha, max_file_bytes),
        _tree_manifest(head, head_sha, max_file_bytes),
    )


def _gh(*args: str) -> Any:
    process = subprocess.run(
        ["gh", "api", *args], check=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, env=os.environ,
    )
    return json.loads(process.stdout.decode("utf-8"))


def _flatten_pages(value: Any) -> list:
    if not isinstance(value, list):
        raise ValueError("TEST_GITHUB_EVIDENCE_INVALID")
    flattened = []
    for page in value:
        if not isinstance(page, list):
            raise ValueError("TEST_GITHUB_EVIDENCE_INVALID")
        flattened.extend(page)
    return flattened


def _github_mission(
    repository: str, pull_request: int, base_sha: str, head_sha: str,
    policy: Mapping[str, Any], changed_files: Sequence[str],
) -> Dict[str, Any]:
    pr = _gh("repos/%s/pulls/%d" % (repository, pull_request))
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
    issue = _gh("repos/%s/issues/%d" % (repository, issue_number))
    if not isinstance(issue, Mapping) or issue.get("number") != issue_number:
        raise ValueError("TEST_MISSION_ISSUE_INVALID")
    mission = parse_issue_body(issue.get("body", ""))
    comments = _flatten_pages(_gh(
        "--paginate", "--slurp",
        "repos/%s/issues/%d/comments?per_page=100" % (repository, issue_number),
    ))
    run_pages = _gh(
        "--paginate", "--slurp", "repos/%s/actions/runs?per_page=100" % repository,
    )
    actions_runs = []
    if not isinstance(run_pages, list):
        raise ValueError("TEST_GITHUB_EVIDENCE_INVALID")
    for page in run_pages:
        if not isinstance(page, Mapping) or not isinstance(page.get("workflow_runs"), list):
            raise ValueError("TEST_GITHUB_EVIDENCE_INVALID")
        actions_runs.extend(page["workflow_runs"])
    return authenticate_integrity_context(
        mission, comments, policy, changed_files, repository=repository,
        mission_issue=issue_number, pull_request=pull_request,
        base_sha=base_sha, head_sha=head_sha, actions_runs=actions_runs,
    )


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
        policy = json.loads(Path(args.base_policy).read_text(encoding="utf-8"))
        violations = validate_document("repository-policy", policy)
        if violations or policy.get("repository") != args.repository:
            raise ValueError("TEST_BASE_POLICY_INVALID")
        max_file_bytes = 16 * 1024 * 1024
        base_manifest, head_manifest = derive_git_manifests(
            args.base_root, args.head_root, args.base_sha, args.head_sha, max_file_bytes,
        )
        changed = sorted({
            path for path in set(base_manifest) | set(head_manifest)
            if base_manifest.get(path) != head_manifest.get(path)
        })
        mission = _github_mission(
            args.repository, args.pull_request, args.base_sha, args.head_sha,
            policy, changed,
        )
        evaluated = args.evaluated_at or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        analysis_policy = {
            "schema_version": "1.0.0", "repository": args.repository,
            "base_sha": args.base_sha, "head_sha": args.head_sha,
            "evaluated_at": evaluated, "base_manifest": base_manifest,
            "head_manifest": head_manifest,
            "founder_identities": policy["founder_identities"], "mission": mission,
            "configuration": {
                "test_globs": [
                    "tests/**/test_*.py", "tests/**/*.test.js", "tests/**/*.spec.js",
                    "tests/**/*.test.ts", "tests/**/*.spec.ts",
                ],
                "fixture_globs": ["tests/**/fixtures/**", "test/**/fixtures/**"],
                "validation_workflow_globs": [".github/workflows/**"],
                "test_config_globs": [
                    "pyproject.toml", "pytest.ini", "setup.cfg", "tox.ini", "package.json",
                    "*vitest*.js", "*vitest*.ts", "*jest*.js", "*jest*.ts",
                ],
                "coverage_paths": ["coverage.json", "coverage-summary.json", ".eos/coverage.json"],
                "material_coverage_decline": 1.0,
                "assertion_patterns": [r"\bassert\b", r"\bexpect\s*\(", r"\.assert[A-Z]\w*\s*\("],
                "skip_patterns": [r"\bskip(?:If|Unless|Test)?\b", r"\.(?:skip|todo|disabled)\b", r"\bdisabled\b"],
                "max_file_bytes": max_file_bytes, "coverage_max_age_seconds": 86400,
            },
        }
        report = analyze_test_integrity(args.base_root, args.head_root, analysis_policy)
        output.write_text(json.dumps(report.to_dict(), sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        return 0 if report.allowed else 1
    except (Exception, MemoryError, UnicodeError) as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
