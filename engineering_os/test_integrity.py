"""Deterministic, delta-based test-integrity enforcement.

The kernel compares two complete immutable source trees. It never applies an
absolute test-count floor: only evidence deltas between the authenticated base
and head revisions can produce findings.
"""

import ast
import hashlib
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple

from .canonical import canonical_json, content_sha256
from .consumption import ConsumptionBinding, consume_once
from .records import verify_record_evidence
from .commands import authenticate_event_history
from .mission import validate_ready
from .risk import compute_tier
from .scope import PathInputError, path_matches


_SHA40 = re.compile(r"[0-9a-f]{40}")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_TIME = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z")
_POLICY_FIELDS = frozenset((
    "schema_version", "repository", "base_sha", "head_sha", "evaluated_at",
    "base_manifest", "head_manifest", "founder_identities", "mission",
    "configuration",
))
_CONFIG_FIELDS = frozenset((
    "test_globs", "fixture_globs", "validation_workflow_globs",
    "test_config_globs", "coverage_paths", "material_coverage_decline",
    "assertion_patterns", "skip_patterns",
    "max_file_bytes", "coverage_max_age_seconds",
))
_MISSION_FIELDS = frozenset((
    "mission_id", "mission_issue", "pull_request", "mission_sha256",
    "mission_event_hash", "declared_tier", "computed_tier", "effective_tier",
    "producer_identity", "producer_model_family", "adversary_identity",
    "adversary_model_family",
))
_OVERRIDE_FIELDS = frozenset((
    "schema_version", "record_id", "override_id", "mission_id", "mission_issue",
    "repository", "pull_request", "base_sha", "head_sha", "mission_sha256",
    "mission_event_hash", "risk_tier",
    "report_sha256", "finding_codes", "reason", "behavior_removed",
    "producer_identity", "adversary_identity", "issued_at", "expires_at",
    "nonce", "single_use", "source",
))
_REVIEW_FIELDS = frozenset((
    "schema_version", "record_id", "review_id", "status", "override_id",
    "override_sha256", "mission_id", "mission_issue", "repository",
    "pull_request", "head_sha", "report_sha256", "reviewer_identity",
    "reviewer_role", "reviewed_at", "nonce", "single_use", "source",
))
_APPROVAL_FIELDS = frozenset((
    "schema_version", "record_id", "approval_id", "status", "action",
    "override_id", "override_sha256", "review_id", "review_sha256",
    "mission_id", "mission_issue", "repository", "pull_request", "head_sha",
    "report_sha256", "issuer", "approved_at", "expires_at", "nonce",
    "single_use", "source",
))


@dataclass(frozen=True)
class IntegrityFinding:
    code: str
    message: str
    path: str = "$"
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IntegrityReport:
    schema_version: str
    repository: str
    base_sha: str
    head_sha: str
    evaluated_at: str
    mission_id: str
    mission_issue: int
    pull_request: int
    mission_sha256: str
    mission_event_hash: str
    declared_tier: str
    computed_tier: str
    effective_tier: str
    producer_identity: str
    producer_model_family: str
    adversary_identity: str
    adversary_model_family: str
    base_manifest_sha256: str
    head_manifest_sha256: str
    findings: Tuple[IntegrityFinding, ...]
    deltas: Dict[str, Any]
    founder_identities: Tuple[str, ...] = field(repr=False)

    @property
    def allowed(self) -> bool:
        return not self.findings

    def _content(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "repository": self.repository,
            "base_sha": self.base_sha,
            "head_sha": self.head_sha,
            "evaluated_at": self.evaluated_at,
            "mission_id": self.mission_id,
            "mission_issue": self.mission_issue,
            "pull_request": self.pull_request,
            "mission_sha256": self.mission_sha256,
            "mission_event_hash": self.mission_event_hash,
            "declared_tier": self.declared_tier,
            "computed_tier": self.computed_tier,
            "effective_tier": self.effective_tier,
            "producer_identity": self.producer_identity,
            "producer_model_family": self.producer_model_family,
            "adversary_identity": self.adversary_identity,
            "adversary_model_family": self.adversary_model_family,
            "base_manifest_sha256": self.base_manifest_sha256,
            "head_manifest_sha256": self.head_manifest_sha256,
            "allowed": self.allowed,
            "findings": [asdict(item) for item in self.findings],
            "deltas": self.deltas,
        }

    @property
    def report_sha256(self) -> str:
        return hashlib.sha256(canonical_json(self._content()).encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        value = self._content()
        value["report_sha256"] = self.report_sha256
        return value


@dataclass(frozen=True)
class IntegrityDecision:
    allowed: bool
    code: str
    details: Dict[str, Any] = field(default_factory=dict)


def authenticate_integrity_context(
    mission: Mapping[str, Any], comments: Sequence[Mapping[str, Any]],
    policy: Mapping[str, Any], changed_files: Sequence[str], *, repository: str,
    mission_issue: int, pull_request: int, base_sha: str, head_sha: str,
    actions_runs: Sequence[Mapping[str, Any]] = (),
) -> Dict[str, Any]:
    """Derive immutable report truth from an authenticated mission history."""

    if validate_ready(dict(mission)):
        raise ValueError("TEST_MISSION_NOT_READY")
    history = authenticate_event_history(
        comments, mission, policy, repository=repository, actions_runs=actions_runs,
    )
    if not history.allowed or history.projection.violations:
        raise ValueError("TEST_MISSION_HISTORY_INVALID")
    ready_events = [item for item in history.events if item.get("type") == "mission.ready"]
    if not ready_events:
        raise ValueError("TEST_MISSION_READY_EVENT_REQUIRED")
    risk = compute_tier(mission, policy, changed_files)
    if not risk.allowed:
        raise ValueError("TEST_MISSION_RISK_INVALID")
    assignments = mission["assignments"]
    if (
        mission.get("repository") != repository
        or not isinstance(mission_issue, int) or isinstance(mission_issue, bool) or mission_issue < 1
        or not isinstance(pull_request, int) or isinstance(pull_request, bool) or pull_request < 1
        or _SHA40.fullmatch(base_sha or "") is None or _SHA40.fullmatch(head_sha or "") is None
    ):
        raise ValueError("TEST_MISSION_BINDING_INVALID")
    event_hash = history.events[-1].get("event_hash")
    if not isinstance(event_hash, str) or _SHA256.fullmatch(event_hash) is None:
        raise ValueError("TEST_MISSION_EVENT_HASH_INVALID")
    return {
        "mission_id": mission["mission_id"], "mission_issue": mission_issue,
        "pull_request": pull_request, "mission_sha256": content_sha256(mission),
        "mission_event_hash": event_hash, "declared_tier": risk.declared_tier,
        "computed_tier": risk.computed_tier, "effective_tier": risk.effective_tier,
        "producer_identity": assignments["producer"]["identity"],
        "producer_model_family": assignments["producer"]["model_family"],
        "adversary_identity": assignments["adversary"]["identity"],
        "adversary_model_family": assignments["adversary"]["model_family"],
    }


@dataclass(frozen=True)
class _CaseStats:
    identity: str
    body_hash: str
    assertions: int
    skips: int
    sourcing_assertions: int
    property_assertions: int


@dataclass(frozen=True)
class _FileStats:
    cases: Tuple[_CaseStats, ...] = ()

    @property
    def signatures(self):
        return tuple(item.identity for item in self.cases)

    @property
    def assertions(self):
        return sum(item.assertions for item in self.cases)

    @property
    def skips(self):
        return sum(item.skips for item in self.cases)

    @property
    def sourcing_assertions(self):
        return sum(item.sourcing_assertions for item in self.cases)

    @property
    def property_assertions(self):
        return sum(item.property_assertions for item in self.cases)


def _timestamp(value: Any) -> datetime:
    if not isinstance(value, str) or _TIME.fullmatch(value) is None:
        raise ValueError("invalid timestamp")
    return datetime.fromisoformat(value[:-1] + "+00:00").astimezone(timezone.utc)


def _strings(value: Any, *, nonempty: bool = True) -> Tuple[str, ...]:
    if not isinstance(value, list) or (nonempty and not value):
        raise ValueError("expected non-empty string array")
    if any(not isinstance(item, str) or not item for item in value):
        raise ValueError("expected string array")
    if len(value) != len(set(value)):
        raise ValueError("duplicate string")
    return tuple(value)


def _validate_manifest(value: Any) -> Dict[str, Dict[str, str]]:
    if not isinstance(value, Mapping):
        raise ValueError("manifest is not an object")
    result = {}
    for path, evidence in value.items():
        if (
            not isinstance(path, str) or not path or path.startswith("/")
            or "\\" in path or ".." in path.split("/")
            or not isinstance(evidence, Mapping)
            or set(evidence) != {"sha256", "git_blob_sha"}
            or not isinstance(evidence.get("sha256"), str)
            or _SHA256.fullmatch(evidence["sha256"]) is None
            or not isinstance(evidence.get("git_blob_sha"), str)
            or _SHA40.fullmatch(evidence["git_blob_sha"]) is None
        ):
            raise ValueError("manifest entry is invalid")
        result[path] = dict(evidence)
    return result


def _validate_policy(policy: Any) -> Dict[str, Any]:
    if not isinstance(policy, Mapping) or set(policy) != _POLICY_FIELDS:
        raise ValueError("policy fields are not closed")
    if (
        policy.get("schema_version") != "1.0.0"
        or not isinstance(policy.get("repository"), str)
        or re.fullmatch(r"[^/]+/[^/]+", policy["repository"]) is None
        or not isinstance(policy.get("base_sha"), str)
        or _SHA40.fullmatch(policy["base_sha"]) is None
        or not isinstance(policy.get("head_sha"), str)
        or _SHA40.fullmatch(policy["head_sha"]) is None
        or policy["base_sha"] == policy["head_sha"]
    ):
        raise ValueError("revision policy is invalid")
    _timestamp(policy.get("evaluated_at"))
    founders = _strings(policy.get("founder_identities"))
    mission = policy.get("mission")
    if not isinstance(mission, Mapping) or set(mission) != _MISSION_FIELDS:
        raise ValueError("mission truth is invalid")
    if (
        any(not isinstance(mission.get(field), str) or not mission.get(field) for field in (
            "mission_id", "producer_identity", "producer_model_family",
            "adversary_identity", "adversary_model_family",
        ))
        or not isinstance(mission.get("mission_issue"), int)
        or isinstance(mission.get("mission_issue"), bool) or mission["mission_issue"] < 1
        or not isinstance(mission.get("pull_request"), int)
        or isinstance(mission.get("pull_request"), bool) or mission["pull_request"] < 1
        or any(_SHA256.fullmatch(str(mission.get(field, ""))) is None for field in (
            "mission_sha256", "mission_event_hash",
        ))
        or any(mission.get(field) not in ("Tier 0", "Tier 1", "Tier 2") for field in (
            "declared_tier", "computed_tier", "effective_tier",
        ))
        or mission["producer_identity"] == mission["adversary_identity"]
    ):
        raise ValueError("mission truth is malformed")
    config = policy.get("configuration")
    if not isinstance(config, Mapping) or set(config) != _CONFIG_FIELDS:
        raise ValueError("configuration fields are not closed")
    parsed_config = {
        "test_globs": _strings(config.get("test_globs")),
        "fixture_globs": _strings(config.get("fixture_globs")),
        "validation_workflow_globs": _strings(config.get("validation_workflow_globs")),
        "test_config_globs": _strings(config.get("test_config_globs")),
        "coverage_paths": _strings(config.get("coverage_paths")),
        "assertion_patterns": _strings(config.get("assertion_patterns")),
        "skip_patterns": _strings(config.get("skip_patterns")),
        "material_coverage_decline": config.get("material_coverage_decline"),
        "max_file_bytes": config.get("max_file_bytes"),
        "coverage_max_age_seconds": config.get("coverage_max_age_seconds"),
    }
    threshold = parsed_config["material_coverage_decline"]
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or threshold < 0:
        raise ValueError("coverage threshold is invalid")
    if any(
        isinstance(parsed_config[field], bool)
        or not isinstance(parsed_config[field], int)
        or parsed_config[field] < 1
        for field in ("max_file_bytes", "coverage_max_age_seconds")
    ):
        raise ValueError("resource configuration is invalid")
    # Parse every glob before it can influence a decision. Unsupported syntax
    # fails closed through the shared matcher.
    for name in (
        "test_globs", "fixture_globs", "validation_workflow_globs", "test_config_globs",
    ):
        for pattern in parsed_config[name]:
            path_matches("__eos_probe__/file.py", pattern)
    for pattern in parsed_config["assertion_patterns"] + parsed_config["skip_patterns"]:
        re.compile(pattern)
    return {
        **dict(policy),
        "base_manifest": _validate_manifest(policy.get("base_manifest")),
        "head_manifest": _validate_manifest(policy.get("head_manifest")),
        "founder_identities": founders,
        "mission": dict(mission),
        "configuration": parsed_config,
    }


def _file_digests(path: Path, max_file_bytes: int) -> Dict[str, str]:
    size = path.stat().st_size
    if size > max_file_bytes:
        raise OverflowError("TEST_RESOURCE_LIMIT")
    sha256 = hashlib.sha256()
    blob = hashlib.sha1()
    blob.update(b"blob " + str(size).encode("ascii") + b"\0")
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(min(1024 * 1024, max_file_bytes + 1))
            if not chunk:
                break
            sha256.update(chunk)
            blob.update(chunk)
    return {"sha256": sha256.hexdigest(), "git_blob_sha": blob.hexdigest()}


def _scan(root: Path, max_file_bytes: int) -> Dict[str, Dict[str, str]]:
    if not root.is_dir() or root.is_symlink():
        raise ValueError("checkout root is unavailable")
    result = {}
    for path in sorted(root.rglob("*")):
        relative_parts = path.relative_to(root).parts
        if relative_parts and relative_parts[0] == ".git":
            continue
        if path.is_symlink():
            raise ValueError("checkout contains a symlink")
        if path.is_file():
            relative = path.relative_to(root).as_posix()
            result[relative] = _file_digests(path, max_file_bytes)
    return result


def _matches(path: str, patterns: Sequence[str]) -> bool:
    return any(path_matches(path, pattern) for pattern in patterns)


def _source(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


def _python_stats(text: str) -> _FileStats:
    tree = ast.parse(text)
    aliases = {"skip", "skipIf", "skipUnless"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for name in node.names:
                if name.name in ("skip", "skipIf", "skipUnless"):
                    aliases.add(name.asname or name.name)
    cases = []

    def visit(nodes, prefix=""):
        for node in nodes:
            if isinstance(node, ast.ClassDef):
                visit(node.body, prefix + node.name + ".")
                continue
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or not node.name.startswith("test"):
                continue
            assertions = skips = sourcing = properties = 0
            semantic_checks = []
            identity = prefix + node.name
            lowered_name = identity.lower()
            for decorator in node.decorator_list:
                rendered = ast.dump(decorator, include_attributes=False).lower()
                root_name = decorator.func.id if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name) else ""
                if root_name in aliases or "skip" in rendered or "disabled" in rendered:
                    skips += 1
            for child in ast.walk(node):
                is_assertion = isinstance(child, ast.Assert)
                if isinstance(child, ast.Call):
                    function = child.func
                    called = ""
                    if isinstance(function, ast.Attribute):
                        called = function.attr
                    elif isinstance(function, ast.Name):
                        called = function.id
                    is_assertion = called.startswith("assert") or called in ("expect", "fail")
                    if called in ("skipTest", "xfail"):
                        skips += 1
                if is_assertion:
                    assertions += 1
                    rendered = ast.dump(child, include_attributes=False).lower() + " " + lowered_name
                    semantic_checks.append(rendered)
                    if any(term in rendered for term in ("source", "citation", "provenance")):
                        sourcing += 1
                    if any(term in rendered for term in ("property", "invariant")):
                        properties += 1
            normalized_body = canonical_json(sorted(semantic_checks))
            body_hash = hashlib.sha256(normalized_body.encode("utf-8")).hexdigest()
            cases.append(_CaseStats(
                identity, body_hash, assertions, skips, sourcing, properties,
            ))
    visit(tree.body)
    return _FileStats(tuple(sorted(cases, key=lambda item: item.identity)))


def _javascript_stats(text: str) -> _FileStats:
    sanitized = list(text)
    stack = []
    index = 0
    while index < len(text):
        char = text[index]
        if char in ("'", '"', "`"):
            quote = char
            index += 1
            while index < len(text):
                if text[index] == "\\":
                    sanitized[index] = " "
                    index += 2
                    continue
                if text[index] == quote:
                    break
                if quote != "`" and text[index] in "\r\n":
                    raise SyntaxError("unterminated JavaScript string")
                sanitized[index] = " "
                index += 1
            if index >= len(text):
                raise SyntaxError("unterminated JavaScript string")
        elif text.startswith("//", index):
            end = text.find("\n", index)
            end = len(text) if end < 0 else end
            for cursor in range(index, end):
                sanitized[cursor] = " "
            index = end
            continue
        elif text.startswith("/*", index):
            end = text.find("*/", index + 2)
            if end < 0:
                raise SyntaxError("unterminated JavaScript comment")
            for cursor in range(index, end + 2):
                sanitized[cursor] = " "
            index = end + 2
            continue
        elif char in "({[":
            stack.append(char)
        elif char in ")}]":
            pairs = {")": "(", "}": "{", "]": "["}
            if not stack or stack.pop() != pairs[char]:
                raise SyntaxError("unbalanced JavaScript")
        index += 1
    if stack:
        raise SyntaxError("truncated JavaScript")
    clean = "".join(sanitized)
    aliases = {
        match.group(1) for match in re.finditer(
            r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:test|it)\.(?:skip|todo|disabled)\b",
            clean,
        )
    }
    matches = list(re.finditer(
        r"\b(test|it)(?:\.(skip|todo|disabled))?\s*\(\s*(['\"])(.*?)\3", text,
    ))
    cases = []
    for match in matches:
        start = match.start()
        opening = clean.find("(", start)
        depth = 0
        end = None
        for cursor in range(opening, len(clean)):
            if clean[cursor] == "(":
                depth += 1
            elif clean[cursor] == ")":
                depth -= 1
                if depth == 0:
                    end = cursor + 1
                    break
        if end is None:
            raise SyntaxError("truncated JavaScript test")
        body = clean[start:end]
        assertions = len(re.findall(r"\b(?:expect|assert)\s*\(", body))
        lowered = body.lower() + " " + match.group(4).lower()
        cases.append(_CaseStats(
            match.group(4), hashlib.sha256(re.sub(r"\s+", "", body).encode("utf-8")).hexdigest(),
            assertions, 1 if match.group(2) else 0,
            assertions if any(term in lowered for term in ("source", "citation", "provenance")) else 0,
            assertions if any(term in lowered for term in ("property", "invariant")) else 0,
        ))
    for alias in aliases:
        if re.search(r"\b%s\s*\(" % re.escape(alias), clean):
            cases.append(_CaseStats(alias, content_sha256(alias), 0, 1, 0, 0))
    return _FileStats(tuple(sorted(cases, key=lambda item: item.identity)))


def _test_stats(
    root: Path, paths: Iterable[str], findings: list, config: Mapping[str, Any],
) -> Dict[str, _FileStats]:
    result = {}
    for relative in sorted(paths):
        try:
            text = _source(root / relative)
            result[relative] = _python_stats(text) if relative.endswith(".py") else _javascript_stats(text)
        except UnicodeDecodeError:
            findings.append(IntegrityFinding(
                "TEST_FILE_UNREADABLE", "Test file is not valid UTF-8.", relative,
            ))
        except SyntaxError:
            findings.append(IntegrityFinding(
                "TEST_FILE_UNPARSABLE", "Test file cannot be parsed deterministically.", relative,
            ))
    return result


def _fixture_cases(path: Path) -> int:
    text = _source(path)
    suffix = path.suffix.lower()
    if suffix == ".json":
        value = json.loads(text)
        if isinstance(value, list):
            return len(value)
        if isinstance(value, Mapping):
            return len(value)
        raise ValueError("JSON fixture root is not a collection")
    if suffix == ".csv":
        lines = [line for line in text.splitlines() if line.strip()]
        return max(0, len(lines) - 1)
    # YAML is intentionally dependency-free: count top-level sequence cases.
    if suffix in (".yaml", ".yml"):
        return sum(1 for line in text.splitlines() if re.match(r"^\s*-\s+", line))
    return len([line for line in text.splitlines() if line.strip()])


def _coverage(
    path: Path, *, repository: str, commit_sha: str,
    source_manifest_sha256: str, evaluated_at: str, max_age_seconds: int,
) -> float:
    value = json.loads(_source(path))
    if not isinstance(value, Mapping) or set(value) != {
        "schema_version", "repository", "commit_sha", "source_manifest_sha256",
        "generated_at", "coverage",
    }:
        raise ValueError("coverage envelope is not closed")
    coverage = value.get("coverage")
    if not isinstance(coverage, Mapping) or set(coverage) != {"lines_percent"}:
        raise ValueError("coverage payload is not closed")
    number = coverage.get("lines_percent")
    if isinstance(number, bool) or not isinstance(number, (int, float)) or not 0 <= number <= 100:
        raise ValueError("coverage percentage is invalid")
    if (
        value.get("schema_version") != "1.0.0"
        or value.get("repository") != repository
        or value.get("commit_sha") != commit_sha
        or value.get("source_manifest_sha256") != source_manifest_sha256
    ):
        raise LookupError("coverage is not bound to the revision")
    generated = _timestamp(value.get("generated_at"))
    evaluated = _timestamp(evaluated_at)
    age = (evaluated - generated).total_seconds()
    if age < 0 or age > max_age_seconds:
        raise TimeoutError("coverage evidence is stale")
    return float(number)


def _weakened(base: str, head: str) -> bool:
    markers = (
        "|| true", "continue-on-error: true", "--passwithnotests",
        "passwithnotests", "testpathignorepatterns", "exclude:", "if: false",
    )
    lower_base, lower_head = base.lower(), head.lower()
    if any(marker not in lower_base and marker in lower_head for marker in markers):
        return True
    base_floor = re.search(r"--cov-fail-under(?:=|\s+)(\d+(?:\.\d+)?)", lower_base)
    head_floor = re.search(r"--cov-fail-under(?:=|\s+)(\d+(?:\.\d+)?)", lower_head)
    return bool(base_floor and (not head_floor or float(head_floor.group(1)) < float(base_floor.group(1))))


def _invalid_report(policy: Any, code: str, message: str) -> IntegrityReport:
    mapping = policy if isinstance(policy, Mapping) else {}
    mission = mapping.get("mission", {}) if isinstance(mapping.get("mission", {}), Mapping) else {}
    return IntegrityReport(
        "1.0.0",
        mapping.get("repository", "") if isinstance(mapping.get("repository", ""), str) else "",
        mapping.get("base_sha", "") if isinstance(mapping.get("base_sha", ""), str) else "",
        mapping.get("head_sha", "") if isinstance(mapping.get("head_sha", ""), str) else "",
        mapping.get("evaluated_at", "") if isinstance(mapping.get("evaluated_at", ""), str) else "",
        mission.get("mission_id", ""), mission.get("mission_issue", 0),
        mission.get("pull_request", 0), mission.get("mission_sha256", ""),
        mission.get("mission_event_hash", ""), mission.get("declared_tier", "Tier 2"),
        mission.get("computed_tier", "Tier 2"), mission.get("effective_tier", "Tier 2"),
        mission.get("producer_identity", ""), mission.get("producer_model_family", ""),
        mission.get("adversary_identity", ""), mission.get("adversary_model_family", ""),
        "", "", (IntegrityFinding(code, message),), {}, (),
    )


def analyze_test_integrity(
    base_root: Any, head_root: Any, policy: Mapping[str, Any],
) -> IntegrityReport:
    """Compare complete immutable base/head trees and return raw deltas."""

    if (
        isinstance(policy, Mapping)
        and isinstance(policy.get("base_sha"), str)
        and policy.get("base_sha") == policy.get("head_sha")
    ):
        return _invalid_report(
            policy, "TEST_REVISION_EVIDENCE_INVALID",
            "Base and head revision evidence must identify distinct commits.",
        )
    try:
        checked = _validate_policy(policy)
    except (PathInputError, TypeError, ValueError, re.error):
        return _invalid_report(policy, "TEST_INTEGRITY_POLICY_INVALID", "Test-integrity policy is invalid.")
    try:
        base = Path(base_root).resolve(strict=True)
        head = Path(head_root).resolve(strict=True)
        if base == head:
            raise ValueError("base and head roots must differ")
        cap = checked["configuration"]["max_file_bytes"]
        actual_base, actual_head = _scan(base, cap), _scan(head, cap)
    except (OverflowError, MemoryError):
        return _invalid_report(checked, "TEST_RESOURCE_LIMIT", "Checkout exceeds deterministic resource limits.")
    except (OSError, TypeError, ValueError, UnicodeError):
        return _invalid_report(checked, "TEST_CHECKOUT_UNAVAILABLE", "A checkout cannot be read safely.")

    expected_base, expected_head = checked["base_manifest"], checked["head_manifest"]
    if set(actual_base) != set(expected_base) or set(actual_head) != set(expected_head):
        return _invalid_report(checked, "TEST_CHECKOUT_INCOMPLETE", "Checkout manifest is incomplete.")
    if actual_base != expected_base or actual_head != expected_head:
        return _invalid_report(checked, "TEST_CHECKOUT_MISMATCH", "Checkout bytes do not match immutable evidence.")

    config = checked["configuration"]
    findings = []
    base_tests = {path for path in actual_base if _matches(path, config["test_globs"])}
    head_tests = {path for path in actual_head if _matches(path, config["test_globs"])}
    base_stats = _test_stats(base, base_tests, findings, config)
    head_stats = _test_stats(head, head_tests, findings, config)

    deleted = sorted(base_tests - head_tests)
    added = set(head_tests - base_tests)
    for path in deleted:
        old = base_stats.get(path)
        if old is None:
            continue
        exact = [candidate for candidate in added if head_stats.get(candidate) == old]
        if len(exact) == 1:
            continue
        if len(exact) > 1:
            findings.append(IntegrityFinding(
                "TEST_RENAME_AMBIGUOUS", "Deleted test has multiple indistinguishable destinations.",
                path, {"candidates": sorted(exact)},
            ))
            continue
        partial = [
            candidate for candidate in added for stats in (head_stats.get(candidate),)
            if stats is not None
            if set(old.signatures) & set(stats.signatures)
        ]
        if partial:
            findings.append(IntegrityFinding(
                "TEST_RENAME_COVERAGE_REDUCED", "Renamed test preserves only part of prior coverage.",
                path, {"candidates": sorted(partial)},
            ))
        else:
            findings.append(IntegrityFinding(
                "TEST_FILE_DELETED", "A test file was deleted without an equivalent destination.", path,
            ))

    base_signatures = Counter(
        signature for stats in base_stats.values() for signature in stats.signatures
    )
    head_signatures = Counter(
        signature for stats in head_stats.values() for signature in stats.signatures
    )
    removed_counts = base_signatures - head_signatures
    removed_signatures = sorted(removed_counts.elements())
    if removed_signatures:
        findings.append(IntegrityFinding(
            "TEST_CASE_REMOVED", "One or more test cases were removed.",
            details={"signatures": removed_signatures},
        ))

    for path in sorted(base_tests & head_tests):
        before_cases = {item.identity: item for item in base_stats.get(path, _FileStats()).cases}
        after_cases = {item.identity: item for item in head_stats.get(path, _FileStats()).cases}
        for identity in sorted(set(before_cases) & set(after_cases)):
            before, after = before_cases[identity], after_cases[identity]
            if after.assertions < before.assertions:
                findings.append(IntegrityFinding(
                    "TEST_CASE_ASSERTION_DECLINE", "Assertions declined within a test case.",
                    path, {"case": identity, "base": before.assertions, "head": after.assertions},
                ))
            if after.skips > before.skips:
                findings.append(IntegrityFinding(
                    "TEST_CASE_SKIP_ADDED", "A test case became skipped or disabled.",
                    path, {"case": identity},
                ))
            if after.sourcing_assertions < before.sourcing_assertions:
                findings.append(IntegrityFinding(
                    "TEST_CASE_SOURCING_ASSERTION_REMOVED", "Sourcing assertions declined within a test case.",
                    path, {"case": identity},
                ))
            if after.property_assertions < before.property_assertions:
                findings.append(IntegrityFinding(
                    "TEST_CASE_PROPERTY_ASSERTION_REMOVED", "Property assertions declined within a test case.",
                    path, {"case": identity},
                ))

    totals = lambda values, field: sum(getattr(item, field) for item in values.values())
    base_assertions = totals(base_stats, "assertions")
    head_assertions = totals(head_stats, "assertions")
    base_skips = totals(base_stats, "skips")
    head_skips = totals(head_stats, "skips")
    base_sourcing = totals(base_stats, "sourcing_assertions")
    head_sourcing = totals(head_stats, "sourcing_assertions")
    base_properties = totals(base_stats, "property_assertions")
    head_properties = totals(head_stats, "property_assertions")
    if head_skips > base_skips:
        findings.append(IntegrityFinding("TEST_SKIP_ADDED", "New skipped or disabled tests were detected."))
    if head_assertions < base_assertions:
        findings.append(IntegrityFinding("TEST_ASSERTION_DECLINE", "Assertion count declined."))
    if head_sourcing < base_sourcing:
        findings.append(IntegrityFinding(
            "TEST_SOURCING_ASSERTION_REMOVED", "Sourcing/provenance assertions declined.",
        ))
    if head_properties < base_properties:
        findings.append(IntegrityFinding(
            "TEST_PROPERTY_ASSERTION_REMOVED", "Property/invariant assertions declined.",
        ))

    base_workflows = {path for path in actual_base if _matches(path, config["validation_workflow_globs"])}
    head_workflows = {path for path in actual_head if _matches(path, config["validation_workflow_globs"])}
    for path in sorted(base_workflows - head_workflows):
        findings.append(IntegrityFinding(
            "VALIDATION_WORKFLOW_DELETED", "A validation workflow was deleted.", path,
        ))
    for path in sorted(base_workflows & head_workflows):
        try:
            before_text, after_text = _source(base / path), _source(head / path)
            if _weakened(before_text, after_text):
                findings.append(IntegrityFinding(
                    "VALIDATION_WORKFLOW_WEAKENED", "A validation workflow was weakened.", path,
                ))
            elif before_text != after_text:
                findings.append(IntegrityFinding(
                    "VALIDATION_WORKFLOW_CHANGE_AMBIGUOUS",
                    "A validation workflow changed in a way that cannot be proven equivalent.", path,
                ))
        except UnicodeDecodeError:
            findings.append(IntegrityFinding("TEST_FILE_UNREADABLE", "Workflow is not valid UTF-8.", path))

    base_configs = {path for path in actual_base if _matches(path, config["test_config_globs"])}
    head_configs = {path for path in actual_head if _matches(path, config["test_config_globs"])}
    for path in sorted(base_configs - head_configs):
        findings.append(IntegrityFinding(
            "TEST_CONFIGURATION_WEAKENED", "A test configuration file was deleted.", path,
        ))
    for path in sorted(base_configs & head_configs):
        try:
            before_text, after_text = _source(base / path), _source(head / path)
            weakened = _weakened(before_text, after_text)
            if path == "package.json":
                before_package, after_package = json.loads(before_text), json.loads(after_text)
                before_command = before_package.get("scripts", {}).get("test") if isinstance(before_package, Mapping) else None
                after_command = after_package.get("scripts", {}).get("test") if isinstance(after_package, Mapping) else None
                weakened = (
                    not isinstance(before_command, str) or not before_command
                    or not isinstance(after_command, str) or not after_command
                    or before_command != after_command
                )
            if weakened:
                findings.append(IntegrityFinding(
                    "TEST_CONFIGURATION_WEAKENED", "Test configuration was weakened.", path,
                ))
            elif before_text != after_text:
                findings.append(IntegrityFinding(
                    "TEST_CONFIGURATION_CHANGE_AMBIGUOUS",
                    "Test configuration changed in a way that cannot be proven equivalent.", path,
                ))
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, AttributeError):
            findings.append(IntegrityFinding("TEST_CONFIGURATION_INVALID", "Configuration cannot be compared safely.", path))

    base_fixtures = {path for path in actual_base if _matches(path, config["fixture_globs"])}
    head_fixtures = {path for path in actual_head if _matches(path, config["fixture_globs"])}
    base_fixture_cases = head_fixture_cases = 0
    for path in sorted(base_fixtures | head_fixtures):
        try:
            before = _fixture_cases(base / path) if path in base_fixtures else 0
            after = _fixture_cases(head / path) if path in head_fixtures else 0
            base_fixture_cases += before
            head_fixture_cases += after
            if after < before:
                findings.append(IntegrityFinding(
                    "TEST_FIXTURE_CASE_DECLINE", "Fixture substitution reduced behavioral cases.",
                    path, {"base_cases": before, "head_cases": after},
                ))
            elif (
                before == after and path in base_fixtures and path in head_fixtures
                and checked["base_manifest"].get(path) != checked["head_manifest"].get(path)
            ):
                findings.append(IntegrityFinding(
                    "TEST_FIXTURE_SUBSTITUTION_AMBIGUOUS",
                    "Changed fixture cases cannot be proven behaviorally equivalent.", path,
                    {"base_cases": before, "head_cases": after},
                ))
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
            findings.append(IntegrityFinding(
                "TEST_FIXTURE_EVIDENCE_INVALID", "Fixture cases cannot be compared deterministically.", path,
            ))

    coverage_delta = None
    present_base = [path for path in config["coverage_paths"] if path in actual_base]
    present_head = [path for path in config["coverage_paths"] if path in actual_head]
    if present_base or present_head:
        if len(present_base) != 1 or len(present_head) != 1 or present_base[0] != present_head[0]:
            findings.append(IntegrityFinding(
                "TEST_COVERAGE_EVIDENCE_MISSING", "Coverage evidence is not present at the same unique path.",
            ))
        else:
            try:
                source_base = content_sha256({
                    path: evidence for path, evidence in checked["base_manifest"].items()
                    if path not in config["coverage_paths"]
                })
                source_head = content_sha256({
                    path: evidence for path, evidence in checked["head_manifest"].items()
                    if path not in config["coverage_paths"]
                })
                before = _coverage(
                    base / present_base[0], repository=checked["repository"],
                    commit_sha=checked["base_sha"], source_manifest_sha256=source_base,
                    evaluated_at=checked["evaluated_at"],
                    max_age_seconds=config["coverage_max_age_seconds"],
                )
                after = _coverage(
                    head / present_head[0], repository=checked["repository"],
                    commit_sha=checked["head_sha"], source_manifest_sha256=source_head,
                    evaluated_at=checked["evaluated_at"],
                    max_age_seconds=config["coverage_max_age_seconds"],
                )
                coverage_delta = round(after - before, 6)
                if coverage_delta < -float(config["material_coverage_decline"]):
                    findings.append(IntegrityFinding(
                        "TEST_COVERAGE_DECLINE", "Material coverage decline was detected.",
                        present_head[0], {"base_percent": before, "head_percent": after},
                    ))
            except TimeoutError:
                findings.append(IntegrityFinding(
                    "TEST_COVERAGE_EVIDENCE_STALE", "Coverage evidence is stale or future-dated.",
                ))
            except LookupError:
                findings.append(IntegrityFinding(
                    "TEST_COVERAGE_EVIDENCE_UNBOUND", "Coverage evidence is not bound to source revision bytes.",
                ))
            except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
                findings.append(IntegrityFinding(
                    "TEST_COVERAGE_EVIDENCE_INVALID", "Coverage evidence is malformed.",
                ))

    deltas = {
        "test_files": len(head_tests) - len(base_tests),
        "test_cases": sum(head_signatures.values()) - sum(base_signatures.values()),
        "assertions": head_assertions - base_assertions,
        "skips": head_skips - base_skips,
        "sourcing_assertions": head_sourcing - base_sourcing,
        "property_assertions": head_properties - base_properties,
        "fixture_cases": head_fixture_cases - base_fixture_cases,
        "coverage_percent": coverage_delta,
    }
    ordered = tuple(sorted(findings, key=lambda item: (item.code, item.path, canonical_json(item.details))))
    return IntegrityReport(
        "1.0.0", checked["repository"], checked["base_sha"], checked["head_sha"],
        checked["evaluated_at"],
        checked["mission"]["mission_id"], checked["mission"]["mission_issue"],
        checked["mission"]["pull_request"], checked["mission"]["mission_sha256"],
        checked["mission"]["mission_event_hash"], checked["mission"]["declared_tier"],
        checked["mission"]["computed_tier"], checked["mission"]["effective_tier"],
        checked["mission"]["producer_identity"], checked["mission"]["producer_model_family"],
        checked["mission"]["adversary_identity"], checked["mission"]["adversary_model_family"],
        content_sha256(checked["base_manifest"]), content_sha256(checked["head_manifest"]),
        ordered, deltas, checked["founder_identities"],
    )


def _closed(value: Any, fields: frozenset) -> bool:
    return isinstance(value, Mapping) and set(value) == fields


def _deny(report: IntegrityReport, code: str) -> IntegrityDecision:
    return IntegrityDecision(False, code, {
        "findings": [asdict(item) for item in report.findings],
        "deltas": dict(report.deltas),
    })


def validate_test_override(
    report: IntegrityReport, override: Mapping[str, Any],
    review: Optional[Mapping[str, Any]], approval: Optional[Mapping[str, Any]], *,
    now: str = "", evidence_verifier: Any = None, consumption_store: str = "",
) -> IntegrityDecision:
    """Authenticate and atomically consume exact test-removal authority."""

    if not isinstance(report, IntegrityReport):
        return IntegrityDecision(False, "TEST_OVERRIDE_REPORT_INVALID")
    details = {
        "findings": [asdict(item) for item in report.findings],
        "deltas": dict(report.deltas),
    }
    if report.allowed:
        return IntegrityDecision(True, "TEST_INTEGRITY_CLEAN", details)
    if not _closed(override, _OVERRIDE_FIELDS) or not _closed(review, _REVIEW_FIELDS):
        return _deny(report, "TEST_OVERRIDE_INVALID")
    try:
        finding_codes = _strings(override.get("finding_codes"))
        issued = _timestamp(override.get("issued_at"))
        expires = _timestamp(override.get("expires_at"))
        reviewed = _timestamp(review.get("reviewed_at"))
        current = _timestamp(now)
    except (TypeError, ValueError):
        return _deny(report, "TEST_OVERRIDE_INVALID")
    required_strings = (
        "record_id", "override_id", "mission_id", "repository", "base_sha",
        "head_sha", "mission_sha256", "mission_event_hash", "risk_tier",
        "report_sha256", "reason", "behavior_removed", "producer_identity",
        "adversary_identity", "issued_at", "expires_at", "nonce",
    )
    if (
        override.get("schema_version") != "1.0.0"
        or any(not isinstance(override.get(field), str) or not override[field] for field in required_strings)
        or not isinstance(override.get("mission_issue"), int) or isinstance(override.get("mission_issue"), bool)
        or not isinstance(override.get("pull_request"), int) or isinstance(override.get("pull_request"), bool)
        or override.get("single_use") is not True
        or issued < _timestamp(report.evaluated_at) or issued >= expires
        or reviewed < issued or reviewed >= expires or current < reviewed or current >= expires
    ):
        return _deny(report, "TEST_OVERRIDE_INVALID")
    report_checks = (
        (override["repository"] != report.repository, "TEST_OVERRIDE_REPOSITORY_MISMATCH"),
        (override["mission_id"] != report.mission_id, "TEST_OVERRIDE_MISSION_MISMATCH"),
        (override["mission_issue"] != report.mission_issue, "TEST_OVERRIDE_MISSION_MISMATCH"),
        (override["pull_request"] != report.pull_request, "TEST_OVERRIDE_PR_MISMATCH"),
        (override["base_sha"] != report.base_sha, "TEST_OVERRIDE_BASE_MISMATCH"),
        (override["head_sha"] != report.head_sha, "TEST_OVERRIDE_HEAD_MISMATCH"),
        (override["mission_sha256"] != report.mission_sha256, "TEST_OVERRIDE_MISSION_MISMATCH"),
        (override["mission_event_hash"] != report.mission_event_hash, "TEST_OVERRIDE_MISSION_MISMATCH"),
        (override["risk_tier"] != report.effective_tier, "TEST_OVERRIDE_TIER_MISMATCH"),
        (override["report_sha256"] != report.report_sha256, "TEST_OVERRIDE_REPORT_MISMATCH"),
        (set(finding_codes) != {item.code for item in report.findings}, "TEST_OVERRIDE_FINDINGS_MISMATCH"),
        (override["producer_identity"] != report.producer_identity, "TEST_OVERRIDE_PRODUCER_MISMATCH"),
        (override["adversary_identity"] != report.adversary_identity, "TEST_OVERRIDE_ADVERSARY_MISMATCH"),
    )
    denied = next((code for failed, code in report_checks if failed), None)
    if denied:
        return _deny(report, denied)
    override_payload = dict(override)
    override_payload.pop("source")
    override_digest = content_sha256(override_payload)
    if (
        not verify_record_evidence(
            override, "test_override", evidence_verifier,
            repository=report.repository, actor=report.producer_identity, head_sha=report.head_sha,
        )
        or override.get("source", {}).get("subject_kind") != "pull_request"
        or override.get("source", {}).get("subject_number") != report.pull_request
        or override.get("source", {}).get("created_at") != override.get("issued_at")
    ):
        return _deny(report, "TEST_OVERRIDE_SOURCE_UNAUTHENTICATED")
    review_bindings = {
        "override_id": override["override_id"], "override_sha256": override_digest,
        "mission_id": report.mission_id, "mission_issue": report.mission_issue,
        "repository": report.repository, "pull_request": report.pull_request,
        "head_sha": report.head_sha, "report_sha256": report.report_sha256,
        "reviewer_identity": report.adversary_identity,
    }
    if any(review.get(field) != value for field, value in review_bindings.items()):
        return _deny(report, "TEST_OVERRIDE_REVIEW_MISMATCH")
    if (
        review.get("schema_version") != "1.0.0" or review.get("status") != "approved"
        or review.get("reviewer_role") != "adversary" or review.get("single_use") is not True
        or any(not isinstance(review.get(field), str) or not review[field] for field in (
            "record_id", "review_id", "nonce",
        ))
    ):
        return _deny(report, "TEST_OVERRIDE_REVIEW_DENIED")
    if (
        not verify_record_evidence(
            review, "test_override_review", evidence_verifier,
            repository=report.repository, actor=report.adversary_identity, head_sha=report.head_sha,
        )
        or review.get("source", {}).get("subject_kind") != "pull_request"
        or review.get("source", {}).get("subject_number") != report.pull_request
        or review.get("source", {}).get("created_at") != review.get("reviewed_at")
    ):
        return _deny(report, "TEST_OVERRIDE_REVIEW_SOURCE_UNAUTHENTICATED")
    review_payload = dict(review)
    review_payload.pop("source")
    review_digest = content_sha256(review_payload)
    records = [
        ConsumptionBinding("test_override", override["record_id"], override["nonce"], override_digest),
        ConsumptionBinding("test_override_review", review["record_id"], review["nonce"], review_digest),
    ]
    if report.effective_tier == "Tier 2":
        if approval is None:
            return _deny(report, "TEST_OVERRIDE_FOUNDER_APPROVAL_REQUIRED")
        if not _closed(approval, _APPROVAL_FIELDS):
            return _deny(report, "TEST_OVERRIDE_APPROVAL_INVALID")
        try:
            approved = _timestamp(approval.get("approved_at"))
            approval_expires = _timestamp(approval.get("expires_at"))
        except (TypeError, ValueError):
            return _deny(report, "TEST_OVERRIDE_APPROVAL_INVALID")
        approval_bindings = {
            "override_id": override["override_id"], "override_sha256": override_digest,
            "review_id": review["review_id"], "review_sha256": review_digest,
            "mission_id": report.mission_id, "mission_issue": report.mission_issue,
            "repository": report.repository, "pull_request": report.pull_request,
            "head_sha": report.head_sha, "report_sha256": report.report_sha256,
        }
        if any(approval.get(field) != value for field, value in approval_bindings.items()):
            return _deny(report, "TEST_OVERRIDE_APPROVAL_MISMATCH")
        if (
            approval.get("schema_version") != "1.0.0" or approval.get("status") != "approved"
            or approval.get("action") != "test-removal-override" or approval.get("single_use") is not True
            or any(not isinstance(approval.get(field), str) or not approval[field] for field in (
                "record_id", "approval_id", "nonce",
            ))
        ):
            return _deny(report, "TEST_OVERRIDE_APPROVAL_DENIED")
        if approval.get("issuer") not in report.founder_identities:
            return _deny(report, "TEST_OVERRIDE_FOUNDER_DENIED")
        if (
            approved < reviewed or current < approved or current >= approval_expires
            or approval_expires > expires
            or not verify_record_evidence(
                approval, "test_override_approval", evidence_verifier,
                repository=report.repository, actor=approval["issuer"], head_sha=report.head_sha,
            )
            or approval.get("source", {}).get("subject_kind") != "pull_request"
            or approval.get("source", {}).get("subject_number") != report.pull_request
            or approval.get("source", {}).get("created_at") != approval.get("approved_at")
        ):
            return _deny(report, "TEST_OVERRIDE_APPROVAL_INVALID")
        approval_payload = dict(approval)
        approval_payload.pop("source")
        records.append(ConsumptionBinding(
            "test_override_approval", approval["record_id"], approval["nonce"],
            content_sha256(approval_payload),
        ))
    elif approval is not None:
        return _deny(report, "TEST_OVERRIDE_APPROVAL_UNEXPECTED")
    ids = [item.record_id for item in records]
    nonces = [item.nonce for item in records]
    if len(ids) != len(set(ids)) or len(nonces) != len(set(nonces)):
        return _deny(report, "TEST_OVERRIDE_DUPLICATE")
    if not consume_once(consumption_store, records):
        return _deny(report, "TEST_OVERRIDE_REPLAYED")
    return IntegrityDecision(True, "TEST_INTEGRITY_OVERRIDE_ALLOWED", details)
