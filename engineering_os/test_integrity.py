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

from .canonical import canonical_json
from .scope import PathInputError, path_matches


_SHA40 = re.compile(r"[0-9a-f]{40}")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_TIME = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z")
_POLICY_FIELDS = frozenset((
    "schema_version", "repository", "base_sha", "head_sha", "evaluated_at",
    "base_manifest", "head_manifest", "founder_identities",
    "reviewer_identities", "configuration",
))
_CONFIG_FIELDS = frozenset((
    "test_globs", "fixture_globs", "validation_workflow_globs",
    "test_config_globs", "coverage_paths", "material_coverage_decline",
    "assertion_patterns", "skip_patterns",
))
_OVERRIDE_FIELDS = frozenset((
    "schema_version", "override_id", "mission_id", "repository",
    "pull_request", "base_sha", "head_sha", "risk_tier",
    "report_sha256", "finding_codes", "reason", "behavior_removed",
    "producer_identity", "adversary_identity", "issued_at", "expires_at",
    "nonce", "single_use", "consumed_at",
))
_REVIEW_FIELDS = frozenset((
    "schema_version", "status", "override_id", "mission_id", "repository",
    "pull_request", "head_sha", "report_sha256", "reviewer_identity",
    "reviewer_role", "reviewed_at", "nonce",
))
_APPROVAL_FIELDS = frozenset((
    "schema_version", "status", "action", "override_id", "mission_id",
    "repository", "pull_request", "head_sha", "report_sha256", "issuer",
    "approved_at", "expires_at", "nonce",
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
    findings: Tuple[IntegrityFinding, ...]
    deltas: Dict[str, Any]
    founder_identities: Tuple[str, ...] = field(repr=False)
    reviewer_identities: Tuple[str, ...] = field(repr=False)

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


@dataclass(frozen=True)
class _FileStats:
    signatures: Tuple[str, ...] = ()
    assertions: int = 0
    skips: int = 0
    sourcing_assertions: int = 0
    property_assertions: int = 0


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


def _validate_manifest(value: Any) -> Dict[str, str]:
    if not isinstance(value, Mapping):
        raise ValueError("manifest is not an object")
    result = {}
    for path, digest in value.items():
        if (
            not isinstance(path, str) or not path or path.startswith("/")
            or "\\" in path or ".." in path.split("/")
            or not isinstance(digest, str) or _SHA256.fullmatch(digest) is None
        ):
            raise ValueError("manifest entry is invalid")
        result[path] = digest
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
    reviewers = _strings(policy.get("reviewer_identities"))
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
    }
    threshold = parsed_config["material_coverage_decline"]
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or threshold < 0:
        raise ValueError("coverage threshold is invalid")
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
        "reviewer_identities": reviewers,
        "configuration": parsed_config,
    }


def _scan(root: Path) -> Dict[str, str]:
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
            result[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
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
    signatures = []
    assertions = skips = sourcing = properties = 0
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or not node.name.startswith("test"):
            continue
        signatures.append(node.name)
        lowered_name = node.name.lower()
        for decorator in node.decorator_list:
            rendered = ast.dump(decorator).lower()
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
                rendered = ast.dump(child).lower() + " " + lowered_name
                if any(term in rendered for term in ("source", "citation", "provenance")):
                    sourcing += 1
                if any(term in rendered for term in ("property", "invariant")):
                    properties += 1
        if not any(isinstance(child, (ast.Assert, ast.Call)) for child in ast.walk(node)):
            # Empty/return-only tests are not skips, but assertion decline below
            # still exposes their lost checks.
            pass
    return _FileStats(tuple(sorted(signatures)), assertions, skips, sourcing, properties)


def _javascript_stats(text: str) -> _FileStats:
    matches = list(re.finditer(
        r"\b(test|it)(?:\.(skip|todo|disabled))?\s*\(\s*(['\"])(.*?)\3", text,
    ))
    names = tuple(sorted(match.group(4) for match in matches))
    skips = sum(1 for match in matches if match.group(2))
    assertions = len(re.findall(r"\b(?:expect|assert)\s*\(", text))
    lowered = text.lower()
    sourcing = assertions if any(term in lowered for term in ("source", "citation", "provenance")) else 0
    properties = assertions if any(term in lowered for term in ("property", "invariant")) else 0
    return _FileStats(names, assertions, skips, sourcing, properties)


def _test_stats(
    root: Path, paths: Iterable[str], findings: list, config: Mapping[str, Any],
) -> Dict[str, _FileStats]:
    result = {}
    for relative in sorted(paths):
        try:
            text = _source(root / relative)
            semantic = _python_stats(text) if relative.endswith(".py") else _javascript_stats(text)
            assertions = sum(len(re.findall(pattern, text)) for pattern in config["assertion_patterns"])
            skips = sum(len(re.findall(pattern, text)) for pattern in config["skip_patterns"])
            result[relative] = _FileStats(
                semantic.signatures, assertions, skips,
                semantic.sourcing_assertions, semantic.property_assertions,
            )
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
        return sum(1 for line in text.splitlines() if re.match(r"^-\s+", line))
    return len([line for line in text.splitlines() if line.strip()])


def _coverage(path: Path) -> float:
    value = json.loads(_source(path))
    candidates = (
        (("totals", "percent_covered"),),
        (("totals", "percent_covered_display"),),
        (("total", "lines", "pct"),),
    )
    for wrapped in candidates:
        current = value
        try:
            for key in wrapped[0]:
                current = current[key]
            number = float(current)
        except (KeyError, TypeError, ValueError):
            continue
        if 0 <= number <= 100:
            return number
    raise ValueError("coverage percentage is absent or invalid")


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
    return IntegrityReport(
        "1.0.0",
        mapping.get("repository", "") if isinstance(mapping.get("repository", ""), str) else "",
        mapping.get("base_sha", "") if isinstance(mapping.get("base_sha", ""), str) else "",
        mapping.get("head_sha", "") if isinstance(mapping.get("head_sha", ""), str) else "",
        mapping.get("evaluated_at", "") if isinstance(mapping.get("evaluated_at", ""), str) else "",
        (IntegrityFinding(code, message),), {}, (), (),
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
        actual_base, actual_head = _scan(base), _scan(head)
    except (OSError, TypeError, ValueError):
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
    for path in deleted:
        old = base_stats.get(path)
        if old is None:
            continue
        exact = [candidate for candidate, stats in head_stats.items() if stats == old]
        if len(exact) == 1:
            continue
        if len(exact) > 1:
            findings.append(IntegrityFinding(
                "TEST_RENAME_AMBIGUOUS", "Deleted test has multiple indistinguishable destinations.",
                path, {"candidates": sorted(exact)},
            ))
            continue
        partial = [
            candidate for candidate, stats in head_stats.items()
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
            if _weakened(_source(base / path), _source(head / path)):
                findings.append(IntegrityFinding(
                    "VALIDATION_WORKFLOW_WEAKENED", "A validation workflow was weakened.", path,
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
            if _weakened(_source(base / path), _source(head / path)):
                findings.append(IntegrityFinding(
                    "TEST_CONFIGURATION_WEAKENED", "Test configuration was weakened.", path,
                ))
        except UnicodeDecodeError:
            findings.append(IntegrityFinding("TEST_FILE_UNREADABLE", "Configuration is not valid UTF-8.", path))

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
                before = _coverage(base / present_base[0])
                after = _coverage(head / present_head[0])
                coverage_delta = round(after - before, 6)
                if coverage_delta < -float(config["material_coverage_decline"]):
                    findings.append(IntegrityFinding(
                        "TEST_COVERAGE_DECLINE", "Material coverage decline was detected.",
                        present_head[0], {"base_percent": before, "head_percent": after},
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
        checked["evaluated_at"], ordered, deltas,
        checked["founder_identities"], checked["reviewer_identities"],
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
    review: Optional[Mapping[str, Any]], approval: Optional[Mapping[str, Any]],
) -> IntegrityDecision:
    """Validate a single-use, exact override without hiding the raw report."""

    if not isinstance(report, IntegrityReport):
        return IntegrityDecision(False, "TEST_OVERRIDE_REPORT_INVALID")
    details = {
        "findings": [asdict(item) for item in report.findings],
        "deltas": dict(report.deltas),
    }
    if report.allowed:
        return IntegrityDecision(True, "TEST_INTEGRITY_CLEAN", details)
    if not _closed(override, _OVERRIDE_FIELDS):
        return _deny(report, "TEST_OVERRIDE_INVALID")
    try:
        finding_codes = _strings(override.get("finding_codes"))
        issued = _timestamp(override.get("issued_at"))
        expires = _timestamp(override.get("expires_at"))
        evaluated = _timestamp(report.evaluated_at)
        structurally_valid = (
            override.get("schema_version") == "1.0.0"
            and all(isinstance(override.get(field), str) and override.get(field) for field in (
                "override_id", "mission_id", "repository", "reason", "behavior_removed",
                "producer_identity", "adversary_identity", "nonce",
            ))
            and isinstance(override.get("pull_request"), int)
            and not isinstance(override.get("pull_request"), bool)
            and override["pull_request"] > 0
            and override.get("risk_tier") in ("Tier 0", "Tier 1", "Tier 2")
            and isinstance(override.get("report_sha256"), str)
            and _SHA256.fullmatch(override["report_sha256"]) is not None
            and override.get("single_use") is True
            and (override.get("consumed_at") is None or isinstance(override.get("consumed_at"), str))
            and issued < expires
            and override.get("producer_identity") != override.get("adversary_identity")
        )
        if not structurally_valid:
            raise ValueError("override structure")
    except (TypeError, ValueError):
        return _deny(report, "TEST_OVERRIDE_INVALID")
    checks = (
        (override["repository"] != report.repository, "TEST_OVERRIDE_REPOSITORY_MISMATCH"),
        (override["base_sha"] != report.base_sha, "TEST_OVERRIDE_BASE_MISMATCH"),
        (override["head_sha"] != report.head_sha, "TEST_OVERRIDE_HEAD_MISMATCH"),
        (override["report_sha256"] != report.report_sha256, "TEST_OVERRIDE_REPORT_MISMATCH"),
        (set(finding_codes) != {item.code for item in report.findings}, "TEST_OVERRIDE_FINDINGS_MISMATCH"),
        (evaluated < issued, "TEST_OVERRIDE_NOT_STARTED"),
        (evaluated >= expires, "TEST_OVERRIDE_EXPIRED"),
        (override.get("consumed_at") is not None, "TEST_OVERRIDE_REPLAYED"),
    )
    denied = next((code for failed, code in checks if failed), None)
    if denied:
        return _deny(report, denied)

    if review is None:
        return _deny(report, "TEST_OVERRIDE_REVIEW_REQUIRED")
    if not _closed(review, _REVIEW_FIELDS):
        return _deny(report, "TEST_OVERRIDE_REVIEW_INVALID")
    try:
        reviewed = _timestamp(review.get("reviewed_at"))
    except (TypeError, ValueError):
        return _deny(report, "TEST_OVERRIDE_REVIEW_INVALID")
    review_bindings = (
        ("override_id", "override_id"), ("mission_id", "mission_id"),
        ("repository", "repository"), ("pull_request", "pull_request"),
        ("head_sha", "head_sha"), ("report_sha256", "report_sha256"),
    )
    if any(review.get(left) != override.get(right) for left, right in review_bindings):
        return _deny(report, "TEST_OVERRIDE_REVIEW_MISMATCH")
    if review.get("status") != "approved" or review.get("reviewer_role") != "adversary":
        return _deny(report, "TEST_OVERRIDE_REVIEW_DENIED")
    if (
        review.get("reviewer_identity") != override.get("adversary_identity")
        or review.get("reviewer_identity") not in report.reviewer_identities
        or review.get("reviewer_identity") == override.get("producer_identity")
    ):
        return _deny(report, "TEST_OVERRIDE_REVIEWER_DENIED")
    if not isinstance(review.get("nonce"), str) or not review["nonce"] or reviewed < issued or reviewed >= expires:
        return _deny(report, "TEST_OVERRIDE_REVIEW_INVALID")

    if override["risk_tier"] == "Tier 2":
        if approval is None:
            return _deny(report, "TEST_OVERRIDE_FOUNDER_APPROVAL_REQUIRED")
        if not _closed(approval, _APPROVAL_FIELDS):
            return _deny(report, "TEST_OVERRIDE_APPROVAL_INVALID")
        try:
            approved = _timestamp(approval.get("approved_at"))
            approval_expires = _timestamp(approval.get("expires_at"))
        except (TypeError, ValueError):
            return _deny(report, "TEST_OVERRIDE_APPROVAL_INVALID")
        approval_bindings = (
            ("override_id", "override_id"), ("mission_id", "mission_id"),
            ("repository", "repository"), ("pull_request", "pull_request"),
            ("head_sha", "head_sha"), ("report_sha256", "report_sha256"),
        )
        if any(approval.get(left) != override.get(right) for left, right in approval_bindings):
            return _deny(report, "TEST_OVERRIDE_APPROVAL_MISMATCH")
        if (
            approval.get("status") != "approved"
            or approval.get("action") != "test-removal-override"
        ):
            return _deny(report, "TEST_OVERRIDE_APPROVAL_DENIED")
        if approval.get("issuer") not in report.founder_identities:
            return _deny(report, "TEST_OVERRIDE_FOUNDER_DENIED")
        if (
            not isinstance(approval.get("nonce"), str) or not approval["nonce"]
            or approved < reviewed or evaluated >= approval_expires
            or len({override["nonce"], review["nonce"], approval["nonce"]}) != 3
        ):
            return _deny(report, "TEST_OVERRIDE_APPROVAL_INVALID")
    elif approval is not None:
        return _deny(report, "TEST_OVERRIDE_APPROVAL_UNEXPECTED")

    return IntegrityDecision(True, "TEST_INTEGRITY_OVERRIDE_ALLOWED", details)
