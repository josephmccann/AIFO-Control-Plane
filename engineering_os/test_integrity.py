"""Deterministic, delta-based test-integrity enforcement.

The kernel compares two complete immutable source trees. It never applies an
absolute test-count floor: only evidence deltas between the authenticated base
and head revisions can produce findings.
"""

import ast
import copy
import hashlib
import json
import keyword
import math
import os
import re
from collections import Counter
from dataclasses import asdict, dataclass, field, replace
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
    "coverage_attestations",
    "configuration",
))
_CONFIG_FIELDS = frozenset((
    "test_globs", "fixture_globs", "validation_workflow_globs",
    "test_config_globs", "coverage_paths", "material_coverage_decline",
    "assertion_patterns", "skip_patterns",
    "max_file_bytes", "coverage_max_age_seconds",
    "max_files", "max_total_bytes", "max_path_bytes", "max_git_record_bytes",
    "max_github_pages", "max_github_items", "max_github_response_bytes",
    "max_coverage_bytes",
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
class CoverageAttestation:
    schema_version: str
    repository: str
    commit_sha: str
    source_manifest_sha256: str
    generated_at: str
    transport_created_at: str
    workflow_path: str
    workflow_sha: str
    run_id: int
    artifact_id: int
    artifact_digest: str
    coverage_path: str
    coverage_file_sha256: str
    conclusion: str
    transport_provenance: str


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


class ResourceBudget:
    """One fail-closed aggregate budget shared by every integrity phase."""

    def __init__(self, limits: Mapping[str, Any]):
        self._limits = dict(limits)
        self._usage = {
            "files": 0, "bytes": 0, "github_pages": 0,
            "github_items": 0, "github_response_bytes": 0,
            "coverage_bytes": 0,
        }

    def require_limits(self, limits: Mapping[str, Any]) -> None:
        for name in (
            "max_files", "max_total_bytes", "max_path_bytes",
            "max_git_record_bytes", "max_github_pages", "max_github_items",
            "max_github_response_bytes", "max_coverage_bytes",
        ):
            if self._limits.get(name) != limits.get(name):
                raise ValueError("TEST_RESOURCE_BUDGET_MISMATCH")

    def consume_bytes(self, amount: int, *, phase: str) -> None:
        if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0 or not phase:
            raise ValueError("TEST_RESOURCE_USAGE_INVALID")
        self._usage["bytes"] += amount
        if self._usage["bytes"] > self._limits["max_total_bytes"]:
            raise OverflowError("TEST_RESOURCE_LIMIT")

    def consume_entry(self, path: str, *, phase: str) -> None:
        if not isinstance(path, str) or not path or not phase:
            raise ValueError("TEST_RESOURCE_USAGE_INVALID")
        if len(path.encode("utf-8")) > self._limits["max_path_bytes"]:
            raise OverflowError("TEST_RESOURCE_LIMIT")
        self._usage["files"] += 1
        if self._usage["files"] > self._limits["max_files"]:
            raise OverflowError("TEST_RESOURCE_LIMIT")

    def consume_file(self, path: str, *, phase: str) -> None:
        self.consume_entry(path, phase=phase)

    def consume_git_record(self, amount: int) -> None:
        if amount > self._limits["max_git_record_bytes"]:
            raise OverflowError("TEST_RESOURCE_LIMIT")
        self.consume_bytes(amount, phase="git")

    def consume_github(self, *, response_bytes: int = 0, pages: int = 0, items: int = 0) -> None:
        for name, amount in (
            ("github_response_bytes", response_bytes),
            ("github_pages", pages), ("github_items", items),
        ):
            if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:
                raise ValueError("TEST_RESOURCE_USAGE_INVALID")
            self._usage[name] += amount
        if (
            self._usage["github_response_bytes"] > self._limits["max_github_response_bytes"]
            or self._usage["github_pages"] > self._limits["max_github_pages"]
            or self._usage["github_items"] > self._limits["max_github_items"]
        ):
            raise OverflowError("TEST_RESOURCE_LIMIT")
        self.consume_bytes(response_bytes, phase="github")

    def consume_coverage(self, amount: int) -> None:
        if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:
            raise ValueError("TEST_RESOURCE_USAGE_INVALID")
        self._usage["coverage_bytes"] += amount
        if self._usage["coverage_bytes"] > self._limits["max_coverage_bytes"]:
            raise OverflowError("TEST_RESOURCE_LIMIT")
        self.consume_bytes(amount, phase="coverage")

    @property
    def usage(self) -> Dict[str, int]:
        return dict(self._usage)


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
    local_identity: str
    body_hash: str
    assertions: int
    skips: int
    sourcing_assertions: int
    property_assertions: int
    focused: bool = False


@dataclass(frozen=True)
class _FileStats:
    cases: Tuple[_CaseStats, ...] = ()
    focus_declarations: int = 0

    @property
    def signatures(self):
        return tuple(item.local_identity for item in self.cases)

    @property
    def assertions(self):
        return sum(item.assertions for item in self.cases)

    @property
    def skips(self):
        return sum(item.skips for item in self.cases)

    @property
    def focuses(self):
        return sum(1 for item in self.cases if item.focused)

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


def _validate_manifest(
    value: Any, *, max_files: int = 10000, max_path_bytes: int = 1024,
    budget: Optional[ResourceBudget] = None, phase: str = "policy",
) -> Dict[str, Dict[str, str]]:
    if not isinstance(value, Mapping):
        raise ValueError("manifest is not an object")
    result = {}
    for path, evidence in value.items():
        if len(result) >= max_files:
            raise OverflowError("TEST_RESOURCE_LIMIT")
        if isinstance(path, str) and len(path.encode("utf-8")) > max_path_bytes:
            raise OverflowError("TEST_RESOURCE_LIMIT")
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
        if budget is not None:
            budget.consume_file(path, phase=phase)
        result[path] = dict(evidence)
    return result


def _validate_policy(
    policy: Any, resource_budget: Optional[ResourceBudget] = None,
) -> Dict[str, Any]:
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
        "max_files": config.get("max_files"),
        "max_total_bytes": config.get("max_total_bytes"),
        "max_path_bytes": config.get("max_path_bytes"),
        "max_git_record_bytes": config.get("max_git_record_bytes"),
        "max_github_pages": config.get("max_github_pages"),
        "max_github_items": config.get("max_github_items"),
        "max_github_response_bytes": config.get("max_github_response_bytes"),
        "max_coverage_bytes": config.get("max_coverage_bytes"),
    }
    threshold = parsed_config["material_coverage_decline"]
    if isinstance(threshold, bool) or not isinstance(threshold, (int, float)) or threshold < 0:
        raise ValueError("coverage threshold is invalid")
    if any(
        isinstance(parsed_config[field], bool)
        or not isinstance(parsed_config[field], int)
        or parsed_config[field] < 1
        for field in (
            "max_file_bytes", "coverage_max_age_seconds", "max_files",
            "max_total_bytes", "max_path_bytes", "max_git_record_bytes",
            "max_github_pages", "max_github_items", "max_github_response_bytes",
            "max_coverage_bytes",
        )
    ):
        raise ValueError("resource configuration is invalid")
    budget = resource_budget or ResourceBudget(parsed_config)
    budget.require_limits(parsed_config)
    # Parse every glob before it can influence a decision. Unsupported syntax
    # fails closed through the shared matcher.
    for name in (
        "test_globs", "fixture_globs", "validation_workflow_globs", "test_config_globs",
    ):
        for pattern in parsed_config[name]:
            path_matches("__eos_probe__/file.py", pattern)
    for pattern in parsed_config["assertion_patterns"] + parsed_config["skip_patterns"]:
        re.compile(pattern)
    attestations = policy.get("coverage_attestations")
    if attestations is not None and (
        not isinstance(attestations, Mapping) or set(attestations) != {"base", "head"}
        or any(type(attestations.get(key)) is not CoverageAttestation for key in ("base", "head"))
    ):
        raise ValueError("coverage attestations are not sealed adapter results")
    return {
        **dict(policy),
        "base_manifest": _validate_manifest(
            policy.get("base_manifest"), max_files=parsed_config["max_files"],
            max_path_bytes=parsed_config["max_path_bytes"], budget=budget,
            phase="base-manifest",
        ),
        "head_manifest": _validate_manifest(
            policy.get("head_manifest"), max_files=parsed_config["max_files"],
            max_path_bytes=parsed_config["max_path_bytes"], budget=budget,
            phase="head-manifest",
        ),
        "founder_identities": founders,
        "mission": dict(mission),
        "coverage_attestations": attestations,
        "configuration": parsed_config,
        "_resource_budget": budget,
    }


def _file_digests(
    path: Path, max_file_bytes: int, budget: Optional[ResourceBudget] = None,
    *, phase: str = "discovery",
) -> Dict[str, str]:
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
            if budget is not None:
                budget.consume_bytes(len(chunk), phase=phase)
            sha256.update(chunk)
            blob.update(chunk)
    return {"sha256": sha256.hexdigest(), "git_blob_sha": blob.hexdigest()}


def _scan(
    root: Path, config: Mapping[str, Any], budget: ResourceBudget,
) -> Dict[str, Dict[str, str]]:
    if not root.is_dir() or root.is_symlink():
        raise ValueError("checkout root is unavailable")
    result = {}
    pending = [root]
    while pending:
        directory = pending.pop()
        with os.scandir(str(directory)) as entries:
            for entry in entries:
                path = Path(entry.path)
                relative = path.relative_to(root).as_posix()
                if relative == ".git" or relative.startswith(".git/"):
                    continue
                budget.consume_entry(relative, phase="checkout-traversal")
                if entry.is_symlink():
                    raise ValueError("checkout contains a symlink")
                if entry.is_dir(follow_symlinks=False):
                    pending.append(path)
                    continue
                if not entry.is_file(follow_symlinks=False):
                    raise ValueError("checkout contains an unsupported entry")
                result[relative] = _file_digests(
                    path, config["max_file_bytes"], budget, phase="checkout-digest",
                )
    return result


def _matches(path: str, patterns: Sequence[str]) -> bool:
    return any(path_matches(path, pattern) for pattern in patterns)


def _source(
    path: Path, budget: Optional[ResourceBudget] = None, *, phase: str = "parsing",
) -> str:
    payload = path.read_bytes()
    if budget is not None:
        budget.consume_bytes(len(payload), phase=phase)
    return payload.decode("utf-8")


class _DuplicateCaseError(ValueError):
    pass


def _descendant_binding_names(node: ast.AST) -> Tuple[str, ...]:
    """Return every syntactic name binding under any present or future AST node."""

    names = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, (ast.Store, ast.Del)):
            names.add(child.id)
        elif isinstance(child, ast.arg):
            names.add(child.arg)
        elif isinstance(child, ast.alias):
            names.add(child.asname or child.name.split(".")[0])
        elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(child.name)
        elif isinstance(child, ast.ExceptHandler) and child.name:
            names.add(child.name)
        elif isinstance(child, (ast.Global, ast.Nonlocal)):
            names.update(child.names)
        elif type(child).__name__.startswith("Match"):
            for field in ("name", "rest"):
                value = getattr(child, field, None)
                if isinstance(value, str) and value:
                    names.add(value)
    return tuple(sorted(names))


def _bounded_definition_literal(value: Optional[ast.AST]) -> bool:
    """Recognize inert, bounded literal ASTs without evaluating operators."""

    max_depth = 16
    max_items = 256
    max_bytes = 16_384
    max_number = 1_000_000_000
    items = 0
    payload_bytes = 0

    def visit(node: Optional[ast.AST], depth: int, *, hashable: bool = False) -> bool:
        nonlocal items, payload_bytes
        if node is None:
            return True
        items += 1
        if items > max_items or depth > max_depth:
            return False
        if isinstance(node, ast.Constant):
            constant = node.value
            if constant is None or isinstance(constant, bool):
                size = 1
            elif isinstance(constant, int):
                if abs(constant) > max_number:
                    return False
                size = len(str(constant))
            elif isinstance(constant, float):
                if not math.isfinite(constant) or abs(constant) > max_number:
                    return False
                size = len(repr(constant))
            elif isinstance(constant, str):
                size = len(constant.encode("utf-8"))
            elif isinstance(constant, bytes):
                size = len(constant)
            else:
                return False
            payload_bytes += size
            return payload_bytes <= max_bytes
        if isinstance(node, ast.UnaryOp):
            return (
                isinstance(node.op, (ast.UAdd, ast.USub))
                and isinstance(node.operand, ast.Constant)
                and isinstance(node.operand.value, (int, float))
                and not isinstance(node.operand.value, bool)
                and visit(node.operand, depth + 1, hashable=True)
            )
        if isinstance(node, ast.Tuple):
            return all(
                visit(item, depth + 1, hashable=hashable) for item in node.elts
            )
        if isinstance(node, ast.List):
            return not hashable and all(
                visit(item, depth + 1) for item in node.elts
            )
        if isinstance(node, ast.Set):
            return not hashable and all(
                visit(item, depth + 1, hashable=True) for item in node.elts
            )
        if isinstance(node, ast.Dict):
            if hashable or any(key is None for key in node.keys):
                return False
            return all(
                visit(key, depth + 1, hashable=True)
                and visit(item, depth + 1)
                for key, item in zip(node.keys, node.values)
            )
        return False

    return visit(value, 0)


def _has_dynamic_namespace_mutation(tree: ast.AST) -> bool:
    """Reject dynamic module/class namespace behavior without resolving aliases."""

    primitives = {
        "globals", "locals", "vars", "exec", "eval", "getattr", "setattr",
        "delattr", "__import__",
    }
    reflection_attributes = primitives | {
        "__builtins__", "__dict__", "__globals__", "__getattribute__",
        "f_globals", "f_locals", "modules",
    }

    def references_dynamic_primitive(statement: ast.stmt) -> bool:
        if isinstance(statement, (ast.Import, ast.ImportFrom)):
            for item in statement.names:
                components = item.name.split(".")
                if any(part in reflection_attributes for part in components):
                    return True
                if item.asname in reflection_attributes:
                    return True
        for node in ast.walk(statement):
            if isinstance(node, ast.Name) and node.id in reflection_attributes:
                return True
            if isinstance(node, ast.Attribute) and node.attr in reflection_attributes:
                return True
        return False

    def static_value(value: Optional[ast.AST]) -> bool:
        return _bounded_definition_literal(value)

    def simple_target(target: ast.AST) -> bool:
        return (
            isinstance(target, ast.Name)
            and target.id not in reflection_attributes
        )

    def explicit_test_flag(statement: ast.Assign) -> bool:
        return (
            len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Attribute)
            and statement.targets[0].attr == "__test__"
            and isinstance(statement.targets[0].value, ast.Name)
            and statement.targets[0].value.id.startswith("test")
            and isinstance(statement.value, ast.Constant)
            and statement.value.value is False
        )

    def direct_binding_names(statement: ast.stmt) -> set:
        if isinstance(statement, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            return {statement.name}
        if isinstance(statement, (ast.Import, ast.ImportFrom)):
            return {
                item.asname or item.name.split(".")[0] for item in statement.names
            }
        targets = []
        if isinstance(statement, ast.Assign):
            targets = statement.targets
        elif isinstance(statement, (ast.AnnAssign, ast.AugAssign)):
            targets = [statement.target]
        names = set()
        for target in targets:
            names.update(_descendant_binding_names(target))
        return names

    def safe_runtime_body(
        body: Sequence[ast.stmt], *, class_scope: bool = False,
        module_scope: bool = False,
    ) -> bool:
        framework_imports = set()
        for statement in body:
            if class_scope and direct_binding_names(statement) & {"pytest", "unittest"}:
                return False
            if isinstance(statement, (ast.Import, ast.ImportFrom)):
                if (
                    not module_scope
                    or not isinstance(statement, ast.Import)
                    or len(statement.names) != 1
                    or statement.names[0].name not in {"pytest", "unittest"}
                    or statement.names[0].asname is not None
                    or statement.names[0].name in framework_imports
                ):
                    return False
                framework_imports.add(statement.names[0].name)
            if references_dynamic_primitive(statement):
                return False
            if isinstance(statement, ast.ClassDef):
                if not safe_runtime_body(statement.body, class_scope=True):
                    return False
                continue
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if isinstance(statement, (ast.Import, ast.ImportFrom, ast.Pass)):
                continue
            if isinstance(statement, ast.Assign):
                if explicit_test_flag(statement):
                    continue
                if len(statement.targets) != 1 or not simple_target(statement.targets[0]):
                    return False
                simple_alias = (
                    not class_scope and len(statement.targets) == 1
                    and isinstance(statement.targets[0], ast.Name)
                    and isinstance(statement.value, ast.Name)
                )
                if not simple_alias and not static_value(statement.value):
                    return False
                continue
            if isinstance(statement, ast.AnnAssign):
                if not simple_target(statement.target) or not static_value(statement.value):
                    return False
                continue
            if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant):
                continue
            return False
        return True

    return not isinstance(tree, ast.Module) or not safe_runtime_body(
        tree.body, module_scope=True,
    )


class _SafeConstantFolder(ast.NodeTransformer):
    def visit_UnaryOp(self, node):
        node = self.generic_visit(node)
        if (
            isinstance(node.operand, ast.Constant)
            and isinstance(node.operand.value, (int, float))
            and not isinstance(node.operand.value, bool)
            and isinstance(node.op, (ast.UAdd, ast.USub))
        ):
            value = +node.operand.value if isinstance(node.op, ast.UAdd) else -node.operand.value
            if abs(value) <= 1_000_000_000:
                return ast.copy_location(ast.Constant(value=value), node)
        return node

    def visit_BinOp(self, node):
        node = self.generic_visit(node)
        if not isinstance(node.left, ast.Constant) or not isinstance(node.right, ast.Constant):
            return node
        left, right = node.left.value, node.right.value
        try:
            if isinstance(node.op, ast.Add) and type(left) is type(right) and isinstance(left, (str, int, float)):
                value = left + right
            elif (
                isinstance(node.op, (ast.Sub, ast.Mult))
                and isinstance(left, (int, float)) and not isinstance(left, bool)
                and isinstance(right, (int, float)) and not isinstance(right, bool)
            ):
                value = left - right if isinstance(node.op, ast.Sub) else left * right
            else:
                return node
        except (ArithmeticError, MemoryError, TypeError):
            return node
        if len(repr(value).encode("utf-8")) <= 128 and (
            not isinstance(value, (int, float)) or abs(value) <= 1_000_000_000
        ):
            return ast.copy_location(ast.Constant(value=value), node)
        return node


def _python_stats(
    text: str, module: str, *, allow_unittest_testcase: bool,
    allow_pytest_parametrize: bool,
) -> _FileStats:
    tree = ast.parse(text)
    if _has_dynamic_namespace_mutation(tree):
        raise SyntaxError("dynamic Python namespace mutation")
    for statement in tree.body:
        if not isinstance(statement, ast.Import):
            continue
        imported = statement.names[0].name
        if (
            (imported == "unittest" and not allow_unittest_testcase)
            or (imported == "pytest" and not allow_pytest_parametrize)
        ):
            raise SyntaxError("shadowed Python collection framework import")
    statement_positions = {id(statement): index for index, statement in enumerate(tree.body)}

    def validate_module_declarations() -> None:
        module_test_flag_seen = False
        resolvable_classes = set()
        bound_names = set()
        for statement in tree.body:
            if isinstance(statement, ast.ClassDef):
                resolvable_classes.add(statement.name)
                bound_names.add(statement.name)
                continue
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                bound_names.add(statement.name)
                continue
            if isinstance(statement, (ast.Import, ast.ImportFrom)):
                bound_names.update(
                    item.asname or item.name.split(".")[0]
                    for item in statement.names
                )
                continue
            if not isinstance(statement, (ast.Assign, ast.AnnAssign)):
                continue
            targets = (
                statement.targets if isinstance(statement, ast.Assign)
                else [statement.target]
            )
            if any(
                isinstance(target, ast.Name) and target.id == "__test__"
                for target in targets
            ):
                if (
                    module_test_flag_seen
                    or len(targets) != 1
                    or not isinstance(targets[0], ast.Name)
                    or not isinstance(statement.value, ast.Constant)
                    or not isinstance(statement.value.value, bool)
                ):
                    raise SyntaxError("invalid module Python collection flag")
                module_test_flag_seen = True
            if (
                len(targets) == 1
                and isinstance(targets[0], ast.Name)
                and isinstance(statement.value, ast.Name)
            ):
                target = targets[0].id
                source = statement.value.id
                if (
                    target in {"pytest", "unittest"}
                    or target in bound_names
                    or source not in resolvable_classes
                ):
                    raise SyntaxError("unresolved module Python class alias")
                resolvable_classes.add(target)
                bound_names.add(target)
            else:
                bound_names.update(
                    target.id for target in targets if isinstance(target, ast.Name)
                )

    validate_module_declarations()

    def exact_module_import_before(name: str, position: int) -> bool:
        bindings = []
        for statement in tree.body[:position]:
            if isinstance(statement, ast.Import):
                for item in statement.names:
                    bound = item.asname or item.name.split(".")[0]
                    if bound == name:
                        bindings.append(item.name == name and item.asname is None)
                continue
            if isinstance(statement, ast.ImportFrom):
                for item in statement.names:
                    if (item.asname or item.name) == name:
                        bindings.append(False)
                continue
            if isinstance(statement, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                if statement.name == name:
                    bindings.append(False)
                continue
            if name in _descendant_binding_names(statement):
                bindings.append(False)
        return bindings == [True]

    def exact_unittest_testcase(base: ast.AST, owner: ast.ClassDef) -> bool:
        return (
            allow_unittest_testcase
            and isinstance(base, ast.Attribute)
            and base.attr == "TestCase"
            and isinstance(base.value, ast.Name)
            and base.value.id == "unittest"
            and exact_module_import_before("unittest", statement_positions[id(owner)])
        )

    def static_definition_value(value: Optional[ast.AST]) -> bool:
        return _bounded_definition_literal(value)

    def safe_annotation(value: Optional[ast.AST]) -> bool:
        return value is None or (
            isinstance(value, ast.Constant)
            and (value.value is None or isinstance(value.value, str))
            and _bounded_definition_literal(value)
        )

    def dotted_name(value: ast.AST) -> Tuple[str, ...]:
        if isinstance(value, ast.Name):
            return (value.id,)
        if isinstance(value, ast.Attribute):
            parent = dotted_name(value.value)
            return parent + (value.attr,) if parent else ()
        return ()

    def parametrize_argnames(value: ast.AST) -> Optional[Tuple[str, ...]]:
        names = []
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            names = [item.strip() for item in value.value.split(",")]
        elif isinstance(value, (ast.List, ast.Tuple)):
            if not all(
                isinstance(item, ast.Constant) and isinstance(item.value, str)
                for item in value.elts
            ):
                return None
            names = [item.value for item in value.elts]
        if (
            not names
            or any(
                not name or name == "request"
                or not name.isidentifier() or keyword.iskeyword(name)
                for name in names
            )
            or len(names) != len(set(names))
            or not _bounded_definition_literal(value)
        ):
            return None
        return tuple(names)

    def safe_parametrize(
        decorator: ast.Call, position: int, function: Optional[Any],
        bound_receiver: Optional[str],
    ) -> bool:
        if (
            function is None
            or not allow_pytest_parametrize
            or not exact_module_import_before("pytest", position)
            or len(decorator.args) != 2
        ):
            return False
        names = parametrize_argnames(decorator.args[0])
        values = decorator.args[1]
        if (
            names is None or not isinstance(values, (ast.List, ast.Tuple))
            or not values.elts
        ):
            return False
        if not _bounded_definition_literal(values):
            return False
        if len(names) > 1 and any(
            not isinstance(item, (ast.List, ast.Tuple)) or len(item.elts) != len(names)
            for item in values.elts
        ):
            return False
        parameters = {
            item.arg for item in (
                list(function.args.args) + list(function.args.kwonlyargs)
            )
        }
        if bound_receiver is not None:
            parameters.discard(bound_receiver)
        positional = list(function.args.posonlyargs) + list(function.args.args)
        defaulted = {
            item.arg for item in positional[-len(function.args.defaults):]
        } if function.args.defaults else set()
        defaulted.update(
            item.arg for item, default in zip(
                function.args.kwonlyargs, function.args.kw_defaults,
            ) if default is not None
        )
        if not set(names) <= parameters or set(names) & defaulted:
            return False

        keyword_names = [item.arg for item in decorator.keywords]
        if (
            None in keyword_names
            or len(keyword_names) != len(set(keyword_names))
            or any(
                name not in {"ids", "indirect", "scope"}
                for name in keyword_names
            )
        ):
            return False
        keyword_values = {item.arg: item.value for item in decorator.keywords}
        indirect = keyword_values.get("indirect")
        ids = keyword_values.get("ids")
        scope = keyword_values.get("scope")

        if indirect is not None:
            if isinstance(indirect, ast.Constant) and isinstance(indirect.value, bool):
                pass
            elif isinstance(indirect, (ast.List, ast.Tuple)):
                selected = parametrize_argnames(indirect)
                if selected is None or not set(selected) <= set(names):
                    return False
            else:
                return False
        if ids is not None:
            if isinstance(ids, ast.Constant) and ids.value is None:
                pass
            elif isinstance(ids, (ast.List, ast.Tuple)):
                if (
                    len(ids.elts) != len(values.elts)
                    or not all(
                        isinstance(item, ast.Constant)
                        and (item.value is None or isinstance(item.value, str))
                        for item in ids.elts
                    )
                    or not _bounded_definition_literal(ids)
                ):
                    return False
            else:
                return False
        if scope is not None and not (
            isinstance(scope, ast.Constant)
            and scope.value in {"class", "function", "module", "package", "session"}
        ):
            return False
        return True

    def safe_collection_decorator(
        decorator: ast.AST, position: int, function: Optional[Any] = None,
        bound_receiver: Optional[str] = None,
    ) -> bool:
        if not isinstance(decorator, ast.Call):
            return False
        name = dotted_name(decorator.func)
        if name in {
            ("unittest", "skip"),
            ("unittest", "skipIf"),
            ("unittest", "skipUnless"),
        }:
            if (
                not allow_unittest_testcase
                or not exact_module_import_before("unittest", position)
                or decorator.keywords
            ):
                return False
            if name[-1] == "skip":
                return (
                    len(decorator.args) == 1
                    and isinstance(decorator.args[0], ast.Constant)
                    and isinstance(decorator.args[0].value, str)
                    and _bounded_definition_literal(decorator.args[0])
                )
            return (
                len(decorator.args) == 2
                and isinstance(decorator.args[0], ast.Constant)
                and isinstance(decorator.args[0].value, bool)
                and isinstance(decorator.args[1], ast.Constant)
                and isinstance(decorator.args[1].value, str)
                and _bounded_definition_literal(decorator.args[1])
            )
        if name == ("pytest", "mark", "parametrize"):
            return safe_parametrize(
                decorator, position, function, bound_receiver,
            )
        return False

    def safe_init_subclass_body(node: Any) -> bool:
        positional = list(node.args.posonlyargs) + list(node.args.args)
        if not positional:
            return False
        receiver = positional[0].arg
        for statement in node.body:
            if isinstance(statement, ast.Pass):
                continue
            if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant):
                continue
            if isinstance(statement, (ast.Assign, ast.AnnAssign)):
                targets = (
                    statement.targets if isinstance(statement, ast.Assign)
                    else [statement.target]
                )
                if (
                    len(targets) != 1
                    or not all(
                        isinstance(target, ast.Attribute)
                        and isinstance(target.value, ast.Name)
                        and target.value.id == receiver
                        and target.attr in {
                            "__test__", "__unittest_skip__", "__unittest_skip_why__",
                        }
                        for target in targets
                    )
                    or not all(
                        (
                            target.attr in {"__test__", "__unittest_skip__"}
                            and isinstance(statement.value, ast.Constant)
                            and isinstance(statement.value.value, bool)
                        ) or (
                            target.attr == "__unittest_skip_why__"
                            and isinstance(statement.value, ast.Constant)
                            and isinstance(statement.value.value, str)
                            and _bounded_definition_literal(statement.value)
                        )
                        for target in targets
                    )
                ):
                    return False
                continue
            return False
        return True

    def safe_function_definition(
        node: Any, position: int, *, bound_method: bool = False,
    ) -> bool:
        arguments = node.args
        annotated = (
            list(arguments.posonlyargs) + list(arguments.args)
            + list(arguments.kwonlyargs)
        )
        if arguments.vararg is not None:
            annotated.append(arguments.vararg)
        if arguments.kwarg is not None:
            annotated.append(arguments.kwarg)
        positional_receivers = list(arguments.posonlyargs) + list(arguments.args)
        if bound_method and not positional_receivers:
            return False
        bound_receiver = (
            positional_receivers[0].arg
            if bound_method and positional_receivers else None
        )
        parametrized = set()
        for decorator in node.decorator_list:
            if (
                isinstance(decorator, ast.Call)
                and dotted_name(decorator.func) == ("pytest", "mark", "parametrize")
            ):
                names = (
                    parametrize_argnames(decorator.args[0])
                    if decorator.args else None
                )
                if names is None or parametrized & set(names):
                    return False
                parametrized.update(names)
        return (
            not getattr(node, "type_params", [])
            and (
                node.name != "__init_subclass__"
                or safe_init_subclass_body(node)
            )
            and all(
                safe_collection_decorator(
                    item, position, node, bound_receiver,
                )
                for item in node.decorator_list
            )
            and all(static_definition_value(item) for item in arguments.defaults)
            and all(
                item is None or static_definition_value(item)
                for item in arguments.kw_defaults
            )
            and all(safe_annotation(item.annotation) for item in annotated)
            and safe_annotation(node.returns)
        )

    def validate_direct_class_flags(body: Sequence[ast.stmt]) -> None:
        fields = {"__test__", "__unittest_skip__", "__unittest_skip_why__"}
        seen = set()
        for statement in body:
            if not isinstance(statement, (ast.Assign, ast.AnnAssign)):
                continue
            targets = (
                statement.targets if isinstance(statement, ast.Assign)
                else [statement.target]
            )
            named = [
                target.id for target in targets
                if isinstance(target, ast.Name) and target.id in fields
            ]
            if not named:
                continue
            if len(targets) != 1 or len(named) != 1 or named[0] in seen:
                raise SyntaxError("ambiguous direct Python collection flag")
            seen.add(named[0])
            value = statement.value
            if named[0] in {"__test__", "__unittest_skip__"}:
                valid = (
                    isinstance(value, ast.Constant)
                    and isinstance(value.value, bool)
                )
            else:
                valid = (
                    isinstance(value, ast.Constant)
                    and isinstance(value.value, str)
                    and _bounded_definition_literal(value)
                )
            if not valid:
                raise SyntaxError("invalid direct Python collection flag")

    def validate_definitions(
        body: Sequence[ast.stmt], owner_position: Optional[int] = None,
        *, class_body: bool = False,
    ) -> None:
        for statement in body:
            position = (
                statement_positions[id(statement)]
                if id(statement) in statement_positions else owner_position
            )
            if isinstance(statement, ast.ClassDef):
                if (
                    position is None
                    or statement.keywords
                    or getattr(statement, "type_params", [])
                    or not all(
                        safe_collection_decorator(item, position)
                        for item in statement.decorator_list
                    )
                ):
                    raise SyntaxError("unproven Python class definition execution")
                validate_direct_class_flags(statement.body)
                validate_definitions(statement.body, position, class_body=True)
            elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if position is None or not safe_function_definition(
                    statement, position, bound_method=class_body,
                ):
                    raise SyntaxError("unproven Python function definition execution")
            elif isinstance(statement, ast.AnnAssign):
                if not safe_annotation(statement.annotation):
                    raise SyntaxError("unproven Python annotation execution")

    validate_definitions(tree.body)

    top_level_classes = {
        id(statement) for statement in tree.body if isinstance(statement, ast.ClassDef)
    }
    for candidate in ast.walk(tree):
        if not isinstance(candidate, ast.ClassDef):
            continue
        if id(candidate) not in top_level_classes:
            raise SyntaxError("nested Python test collection class")
        if any(not isinstance(base, (ast.Name, ast.Attribute)) for base in candidate.bases):
            raise SyntaxError("unsupported Python test base expression")
        if any(
            isinstance(base, ast.Attribute) and not exact_unittest_testcase(base, candidate)
            for base in candidate.bases
        ):
            raise SyntaxError("unsupported qualified Python test base class")
    aliases = {"skip", "skipIf", "skipUnless"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for name in node.names:
                if name.name in ("skip", "skipIf", "skipUnless"):
                    aliases.add(name.asname or name.name)
    cases = []

    def normalized(value: Any) -> str:
        folded = _SafeConstantFolder().visit(copy.deepcopy(value))
        return ast.dump(folded, include_attributes=False)

    def decorators_disable(decorators: Sequence[ast.expr]) -> bool:
        for decorator in decorators:
            rendered = ast.dump(decorator, include_attributes=False).lower()
            root_name = (
                decorator.func.id
                if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name)
                else ""
            )
            if root_name in aliases or "skip" in rendered or "disabled" in rendered:
                return True
        return False

    def false_assignment(statement: ast.stmt, name: str) -> bool:
        targets = []
        value = None
        if isinstance(statement, (ast.Assign, ast.AnnAssign)):
            targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
            value = statement.value
        return (
            isinstance(value, ast.Constant) and value.value is False
            and any(isinstance(target, ast.Name) and target.id == name for target in targets)
        )

    function_disabled = set()
    for statement in tree.body:
        if not isinstance(statement, (ast.Assign, ast.AnnAssign)):
            continue
        targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
        value = statement.value
        if not isinstance(value, ast.Constant) or value.value is not False:
            continue
        for target in targets:
            if (
                isinstance(target, ast.Attribute) and target.attr == "__test__"
                and isinstance(target.value, ast.Name) and target.value.id.startswith("test")
            ):
                function_disabled.add(target.value.id)

    module_metadata = tuple(
        normalized(statement) for statement in tree.body
        if not (
            isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
            and statement.name.startswith("test")
        ) and not isinstance(statement, ast.ClassDef)
    )
    module_disabled = any(false_assignment(statement, "__test__") for statement in tree.body)
    class_statements = [
        (index, statement) for index, statement in enumerate(tree.body)
        if isinstance(statement, ast.ClassDef)
    ]
    class_names = [statement.name for _, statement in class_statements]
    if len(class_names) != len(set(class_names)):
        raise SyntaxError("duplicate local test base class binding")
    local_classes = {statement.name: statement for _, statement in class_statements}
    class_binding_positions = {statement.name: index for index, statement in class_statements}

    binding_records: Dict[str, list] = {}

    def target_names(target: ast.AST) -> Tuple[str, ...]:
        if isinstance(target, ast.Name):
            return (target.id,)
        if isinstance(target, (ast.Tuple, ast.List)):
            return tuple(name for item in target.elts for name in target_names(item))
        if isinstance(target, ast.Starred):
            return target_names(target.value)
        return ()

    def referenced_names(value: Optional[ast.AST]) -> Tuple[str, ...]:
        if value is None:
            return ()
        return tuple(sorted({
            child.id for child in ast.walk(value)
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load)
        }))

    def record_binding(
        name: str, kind: str, position: int, sources: Tuple[str, ...] = (),
    ) -> None:
        binding_records.setdefault(name, []).append((kind, position, sources))

    def record_named_expressions(value: Optional[ast.AST], position: int) -> None:
        if value is None:
            return
        for child in ast.walk(value):
            if isinstance(child, ast.NamedExpr):
                for name in target_names(child.target):
                    record_binding(name, "unsupported", position, referenced_names(child.value))

    def collect_bindings(statement: ast.stmt, position: int, *, top_level: bool) -> None:
        if isinstance(statement, ast.ClassDef):
            record_binding(statement.name, "class" if top_level else "unsupported", position)
            return
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            record_binding(
                statement.name, "unsupported", position,
                referenced_names(ast.Module(body=statement.body, type_ignores=[])),
            )
            return
        if isinstance(statement, ast.Assign):
            sources = referenced_names(statement.value)
            simple = (
                top_level and len(statement.targets) == 1
                and isinstance(statement.targets[0], ast.Name)
                and isinstance(statement.value, ast.Name)
            )
            for target in statement.targets:
                for name in target_names(target):
                    record_binding(name, "alias" if simple else "unsupported", position, sources)
            record_named_expressions(statement.value, position)
            return
        if isinstance(statement, ast.AnnAssign):
            for name in target_names(statement.target):
                record_binding(name, "unsupported", position, referenced_names(statement.value))
            record_named_expressions(statement.value, position)
            return
        if isinstance(statement, ast.AugAssign):
            for name in target_names(statement.target):
                record_binding(name, "unsupported", position, referenced_names(statement.value))
            return
        if isinstance(statement, ast.Delete):
            for target in statement.targets:
                for name in target_names(target):
                    record_binding(name, "unsupported", position)
            return
        if isinstance(statement, (ast.Import, ast.ImportFrom)):
            for item in statement.names:
                bound = item.asname or item.name.split(".")[0]
                record_binding(bound, "unsupported", position)
            return
        if isinstance(statement, (ast.For, ast.AsyncFor)):
            sources = referenced_names(statement.iter)
            for name in target_names(statement.target):
                record_binding(name, "unsupported", position, sources)
            record_named_expressions(statement.iter, position)
            for child in statement.body + statement.orelse:
                collect_bindings(child, position, top_level=False)
            return
        if isinstance(statement, (ast.With, ast.AsyncWith)):
            for item in statement.items:
                record_named_expressions(item.context_expr, position)
                if item.optional_vars is not None:
                    for name in target_names(item.optional_vars):
                        record_binding(
                            name, "unsupported", position,
                            referenced_names(item.context_expr),
                        )
            for child in statement.body:
                collect_bindings(child, position, top_level=False)
            return
        if isinstance(statement, ast.If):
            record_named_expressions(statement.test, position)
            for child in statement.body + statement.orelse:
                collect_bindings(child, position, top_level=False)
            return
        if isinstance(statement, ast.While):
            record_named_expressions(statement.test, position)
            for child in statement.body + statement.orelse:
                collect_bindings(child, position, top_level=False)
            return
        if isinstance(statement, ast.Try):
            for child in statement.body + statement.orelse + statement.finalbody:
                collect_bindings(child, position, top_level=False)
            for handler in statement.handlers:
                if handler.name:
                    record_binding(handler.name, "unsupported", position)
                for child in handler.body:
                    collect_bindings(child, position, top_level=False)
            return
        record_named_expressions(statement, position)

    for statement_index, statement in enumerate(tree.body):
        collect_bindings(statement, statement_index, top_level=True)
        supported_alias = (
            isinstance(statement, ast.Assign)
            and len(statement.targets) == 1
            and isinstance(statement.targets[0], ast.Name)
            and isinstance(statement.value, ast.Name)
        )
        if isinstance(statement, ast.ClassDef) or supported_alias:
            continue
        sources = referenced_names(statement)
        for name in _descendant_binding_names(statement):
            record_binding(name, "unsupported", statement_index, sources)

    participating_names = set(local_classes)
    participating_names.update(
        base.id for _, node in class_statements for base in node.bases
        if isinstance(base, ast.Name)
    )
    changed = True
    while changed:
        changed = False
        for name, records in binding_records.items():
            related = {source for _, _, sources in records for source in sources}
            if name in participating_names or related & participating_names:
                before = len(participating_names)
                participating_names.add(name)
                participating_names.update(related)
                changed = changed or len(participating_names) != before
    for name in participating_names:
        records = binding_records.get(name, [])
        if not records:
            continue
        if len(records) != 1:
            raise SyntaxError("ambiguous local test base binding")
        kind, position, sources = records[0]
        if kind == "class":
            continue
        if kind != "alias" or len(sources) != 1:
            raise SyntaxError("unsupported local test base binding")
        source_records = binding_records.get(sources[0], [])
        if source_records and min(item[1] for item in source_records) >= position:
            raise SyntaxError("local test base alias used before binding")

    class_reference_names = {name: name for name in local_classes}
    class_reference_positions = dict(class_binding_positions)
    assignments_by_name: Dict[str, list] = {}
    assignment_positions: Dict[str, list] = {}
    for statement_index, statement in enumerate(tree.body):
        if not isinstance(statement, (ast.Assign, ast.AnnAssign)):
            continue
        targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
        for target in targets:
            if isinstance(target, ast.Name):
                assignments_by_name.setdefault(target.id, []).append(statement.value)
                assignment_positions.setdefault(target.id, []).append(statement_index)
                if target.id in local_classes:
                    raise SyntaxError("rebound local test base class")
    changed = True
    while changed:
        changed = False
        for name, values in assignments_by_name.items():
            if name in class_reference_names or len(values) != 1:
                continue
            value = values[0]
            if isinstance(value, ast.Name) and value.id in class_reference_names:
                position = assignment_positions[name][0]
                if class_reference_positions[value.id] >= position:
                    continue
                class_reference_names[name] = class_reference_names[value.id]
                class_reference_positions[name] = position
                changed = True
    class_cache: Dict[str, Tuple[str, bool]] = {}

    def own_class_metadata(node: ast.ClassDef) -> str:
        return normalized(ast.ClassDef(
            name=node.name, bases=copy.deepcopy(node.bases),
            keywords=copy.deepcopy(node.keywords),
            body=copy.deepcopy(node.body),
            decorator_list=copy.deepcopy(node.decorator_list),
            type_params=copy.deepcopy(getattr(node, "type_params", [])),
        ))

    def own_class_disabled(node: ast.ClassDef) -> bool:
        init_subclass_disables = any(
            isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef))
            and statement.name == "__init_subclass__"
            and any(
                isinstance(child, (ast.Assign, ast.AnnAssign))
                and isinstance(child.value, ast.Constant)
                and any(
                    isinstance(target, ast.Attribute)
                    and target.attr in {"__unittest_skip__", "__test__"}
                    and (
                        (target.attr == "__unittest_skip__" and child.value.value is True)
                        or (target.attr == "__test__" and child.value.value is False)
                    )
                    for target in (
                        child.targets if isinstance(child, ast.Assign) else [child.target]
                    )
                )
                for child in ast.walk(statement)
            )
            for statement in node.body
        )
        return (
            decorators_disable(node.decorator_list)
            or any(false_assignment(statement, "__test__") for statement in node.body)
            or any(
                isinstance(statement, (ast.Assign, ast.AnnAssign))
                and isinstance(statement.value, ast.Constant)
                and statement.value.value is True
                and any(
                    isinstance(target, ast.Name)
                    and target.id == "__unittest_skip__"
                    for target in (
                        statement.targets if isinstance(statement, ast.Assign)
                        else [statement.target]
                    )
                )
                for statement in node.body
            )
            or init_subclass_disables
            or any(
                "skip" in normalized(statement).lower()
                for statement in node.body
                if isinstance(statement, (ast.Assign, ast.AnnAssign))
                and any(
                    isinstance(target, ast.Name) and target.id == "pytestmark"
                    for target in (
                        statement.targets if isinstance(statement, ast.Assign)
                        else [statement.target]
                    )
                )
            )
        )

    def resolved_class_metadata(
        node: ast.ClassDef, trail: Tuple[str, ...] = (),
    ) -> Tuple[str, bool]:
        cacheable = local_classes.get(node.name) is node
        if cacheable and node.name in class_cache:
            return class_cache[node.name]
        if node.name in trail:
            raise SyntaxError("cyclic local test base class")
        if len(node.bases) > 1:
            raise SyntaxError("ambiguous Python test MRO")
        inherited_metadata = []
        inherited_disabled = False
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in class_reference_names:
                if class_reference_positions[base.id] >= class_binding_positions.get(node.name, len(tree.body)):
                    raise SyntaxError("local test base used before binding")
                resolved_name = class_reference_names[base.id]
                base_metadata, base_disabled = resolved_class_metadata(
                    local_classes[resolved_name], trail + (node.name,),
                )
                inherited_metadata.append((base.id, resolved_name, base_metadata))
                inherited_disabled = inherited_disabled or base_disabled
            elif isinstance(base, ast.Name) and base.id in assignments_by_name:
                raise SyntaxError("ambiguous local test base class")
            elif isinstance(base, ast.Name):
                raise SyntaxError("unresolved Python test base class")
        if len(inherited_metadata) > 1:
            raise SyntaxError("ambiguous multiple local Python test bases")
        result = (
            canonical_json({
                "class": own_class_metadata(node),
                "local_bases": inherited_metadata,
            }),
            own_class_disabled(node) or inherited_disabled,
        )
        if cacheable:
            class_cache[node.name] = result
        return result

    def local_base_name(node: ast.ClassDef) -> Optional[str]:
        local_bases = []
        for base in node.bases:
            if not isinstance(base, ast.Name) or base.id not in class_reference_names:
                continue
            if class_reference_positions[base.id] >= class_binding_positions[node.name]:
                raise SyntaxError("local test base used before binding")
            local_bases.append(class_reference_names[base.id])
        if len(local_bases) > 1:
            raise SyntaxError("ambiguous multiple local Python test bases")
        return local_bases[0] if local_bases else None

    method_cache: Dict[str, Dict[str, Tuple[Any, str]]] = {}

    def runtime_methods(
        node: ast.ClassDef, trail: Tuple[str, ...] = (),
    ) -> Dict[str, Tuple[Any, str]]:
        if node.name in method_cache:
            return dict(method_cache[node.name])
        if node.name in trail:
            raise SyntaxError("cyclic local test method inheritance")
        base_name = local_base_name(node)
        methods = (
            runtime_methods(local_classes[base_name], trail + (node.name,))
            if base_name is not None else {}
        )
        own_slots: Dict[str, Optional[Any]] = {}
        direct_test_definitions = set()
        relevant = set(methods)
        for statement in node.body:
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = statement.name
                if name.startswith("test"):
                    if name in direct_test_definitions:
                        raise _DuplicateCaseError("duplicate Python test runtime identity")
                    direct_test_definitions.add(name)
                    own_slots[name] = statement
                    relevant.add(name)
                continue
            if isinstance(statement, ast.ClassDef):
                if statement.name in relevant or statement.name.startswith("test"):
                    own_slots[statement.name] = None
                continue
            if isinstance(statement, ast.Assign):
                names = {
                    name for target in statement.targets for name in target_names(target)
                    if name in relevant or name.startswith("test")
                }
                if names:
                    if not _bounded_definition_literal(statement.value):
                        raise SyntaxError("unproven inherited Python test override")
                    for name in names:
                        own_slots[name] = None
                        relevant.add(name)
                continue
            if isinstance(statement, ast.AnnAssign):
                names = {
                    name for name in target_names(statement.target)
                    if name in relevant or name.startswith("test")
                }
                if names and statement.value is not None:
                    if not _bounded_definition_literal(statement.value):
                        raise SyntaxError("unproven inherited Python test override")
                    for name in names:
                        own_slots[name] = None
                        relevant.add(name)
                continue
            affected = set(_descendant_binding_names(statement)) & relevant
            if affected:
                raise SyntaxError("ambiguous inherited Python test override")
        for name, method in own_slots.items():
            if method is None:
                methods.pop(name, None)
            else:
                methods[name] = (method, node.name)
        method_cache[node.name] = dict(methods)
        return methods

    def append_case(
        node: Any, local_identity: str, context: Tuple[str, ...],
        inherited_skip: bool, declaring_class: Optional[str] = None,
    ) -> None:
        assertions = sourcing = properties = 0
        skips = 1 if (
            inherited_skip or module_disabled or node.name in function_disabled
        ) else 0
        semantic_checks = []
        identity = module + "::" + local_identity
        lowered_name = local_identity.lower()
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
        body = copy.deepcopy(node.body)
        if (
            body and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            body = body[1:]
        function_metadata = {
            "kind": "async" if isinstance(node, ast.AsyncFunctionDef) else "sync",
            "arguments": normalized(node.args),
            "decorators": [normalized(item) for item in node.decorator_list],
            "returns": normalized(node.returns) if node.returns is not None else None,
            "type_comment": node.type_comment,
            "module": module_metadata,
            "enclosing": context,
            "declaring_class": declaring_class,
        }
        normalized_body = normalized(ast.Module(body=body, type_ignores=[]))
        semantic = canonical_json({"metadata": function_metadata, "body": normalized_body})
        body_hash = hashlib.sha256(semantic.encode("utf-8")).hexdigest()
        cases.append(_CaseStats(
            identity, local_identity, body_hash, assertions, skips, sourcing, properties,
        ))

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            class_metadata, class_disabled = resolved_class_metadata(node)
            for name, (method, declaring_class) in runtime_methods(node).items():
                append_case(
                    method, node.name + "." + name, (class_metadata,),
                    class_disabled or module_disabled, declaring_class,
                )
        elif (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test")
        ):
            append_case(node, node.name, (), module_disabled)
    identities = [item.identity for item in cases]
    if len(identities) != len(set(identities)):
        raise _DuplicateCaseError("duplicate Python test runtime identity")
    return _FileStats(tuple(sorted(cases, key=lambda item: item.identity)))


@dataclass(frozen=True)
class _JSToken:
    kind: str
    value: str


def _javascript_tokens(text: str) -> Tuple[_JSToken, ...]:
    tokens = []
    index = 0
    while index < len(text):
        char = text[index]
        if char.isspace():
            index += 1
            continue
        if text.startswith("//", index):
            end = text.find("\n", index + 2)
            index = len(text) if end < 0 else end + 1
            continue
        if text.startswith("/*", index):
            end = text.find("*/", index + 2)
            if end < 0:
                raise SyntaxError("unterminated JavaScript comment")
            index = end + 2
            continue
        if char in ("'", '"', "`"):
            quote = char
            start = index
            index += 1
            while index < len(text):
                if text[index] == "\\":
                    index += 2
                    continue
                if text[index] == quote:
                    break
                if quote != "`" and text[index] in "\r\n":
                    raise SyntaxError("unterminated JavaScript string")
                index += 1
            if index >= len(text):
                raise SyntaxError("unterminated JavaScript string")
            index += 1
            tokens.append(_JSToken("string", text[start:index]))
            continue
        identifier = re.match(r"[A-Za-z_$][A-Za-z0-9_$]*", text[index:])
        if identifier:
            value = identifier.group(0)
            tokens.append(_JSToken("identifier", value))
            index += len(value)
            continue
        if text.startswith("=>", index):
            tokens.append(_JSToken("symbol", "=>"))
            index += 2
            continue
        tokens.append(_JSToken("symbol", char))
        index += 1
    stack = []
    pairs = {")": "(", "}": "{", "]": "["}
    for token in tokens:
        if token.value in "({[":
            stack.append(token.value)
        elif token.value in ")}]":
            if not stack or stack.pop() != pairs[token.value]:
                raise SyntaxError("unbalanced JavaScript")
    if stack:
        raise SyntaxError("truncated JavaScript")
    return tuple(tokens)


def _javascript_stats(text: str, module: str) -> _FileStats:
    tokens = _javascript_tokens(text)
    delimiter_pairs = {"(": ")", "{": "}", "[": "]"}

    def closing(opening: int) -> int:
        target = delimiter_pairs.get(tokens[opening].value)
        if target is None:
            raise SyntaxError("JavaScript delimiter expected")
        depth = 0
        for cursor in range(opening, len(tokens)):
            if tokens[cursor].value == tokens[opening].value:
                depth += 1
            elif tokens[cursor].value == target:
                depth -= 1
                if depth == 0:
                    return cursor
        raise SyntaxError("truncated JavaScript expression")

    cases = []
    test_names = {"test", "it"}
    suite_names = {"describe", "suite", "context"}
    modifiers = {"skip", "todo", "disabled", "only"}

    def string_value(token: _JSToken) -> str:
        if token.kind != "string":
            raise SyntaxError("static JavaScript member required")
        if token.value[0] == "`":
            value = token.value[1:-1]
            if "${" in value:
                raise SyntaxError("dynamic JavaScript member")
            return value
        try:
            value = ast.literal_eval(token.value)
        except (SyntaxError, ValueError):
            raise SyntaxError("invalid JavaScript member")
        if not isinstance(value, str):
            raise SyntaxError("invalid JavaScript member")
        return value

    def computed_member(opening: int) -> Tuple[str, int]:
        ending = closing(opening)
        cursor = opening + 1
        parts = []
        expect_string = True
        while cursor < ending:
            if expect_string:
                parts.append(string_value(tokens[cursor]))
            elif tokens[cursor].value != "+":
                raise SyntaxError("dynamic JavaScript member")
            expect_string = not expect_string
            cursor += 1
        if expect_string or not parts:
            raise SyntaxError("dynamic JavaScript member")
        return "".join(parts), ending + 1

    global_roots = {"globalThis", "window", "global", "self"}
    global_references = set(global_roots)

    def parenthesized_reference(start: int) -> Tuple[Optional[str], int]:
        cursor = start
        openings = 0
        while cursor < len(tokens) and tokens[cursor].value == "(":
            openings += 1
            cursor += 1
        if cursor >= len(tokens) or tokens[cursor].kind != "identifier":
            return None, start
        name = tokens[cursor].value
        cursor += 1
        for _ in range(openings):
            if cursor >= len(tokens) or tokens[cursor].value != ")":
                return None, start
            cursor += 1
        return name, cursor

    changed = True
    while changed:
        changed = False
        for index in range(len(tokens) - 3):
            if (
                tokens[index].value in ("const", "let", "var")
                and tokens[index + 1].kind == "identifier"
                and tokens[index + 2].value == "="
            ):
                referenced, _ = parenthesized_reference(index + 3)
                if (
                    referenced in global_references
                    and tokens[index + 1].value not in global_references
                ):
                    global_references.add(tokens[index + 1].value)
                    changed = True
    collection_names = test_names | suite_names
    for index, token in enumerate(tokens):
        if token.kind == "identifier" and token.value in global_references:
            cursor = index + 1
            while cursor < len(tokens) and tokens[cursor].value == ")":
                cursor += 1
            if cursor + 1 < len(tokens) and tokens[cursor].value == "?" and tokens[cursor + 1].value == ".":
                cursor += 2
            if cursor < len(tokens) and tokens[cursor].value == "[":
                member, _ = computed_member(cursor)
                if member in collection_names:
                    raise SyntaxError("computed global JavaScript collection reference")
        if token.value != "[" or index == 0 or tokens[index - 1].kind != "identifier":
            continue
        if tokens[index - 1].value in collection_names:
            continue
        try:
            member, _ = computed_member(index)
        except SyntaxError:
            continue
        if member in collection_names:
            raise SyntaxError("computed indirect JavaScript collection reference")

    aliases: Dict[str, Tuple[str, Optional[str]]] = {}
    alias_reference_positions = set()
    alias_declaration_positions = set()

    def reference(start: int, stop: int) -> Tuple[str, Optional[str], int]:
        if start >= stop or tokens[start].kind != "identifier":
            raise SyntaxError("indirect JavaScript collection reference")
        name = tokens[start].value
        if name in aliases:
            root, modifier = aliases[name]
        elif name in test_names | suite_names:
            root, modifier = name, None
        else:
            raise SyntaxError("indirect JavaScript collection reference")
        cursor = start + 1
        if cursor < stop and tokens[cursor].value == ".":
            if cursor + 1 >= stop or tokens[cursor + 1].kind != "identifier":
                raise SyntaxError("malformed JavaScript test modifier")
            if modifier is not None:
                raise SyntaxError("chained JavaScript test modifier")
            modifier = tokens[cursor + 1].value
            cursor += 2
        elif cursor < stop and tokens[cursor].value == "[":
            if modifier is not None:
                raise SyntaxError("chained JavaScript test modifier")
            modifier, cursor = computed_member(cursor)
        if modifier is not None and modifier not in modifiers:
            raise SyntaxError("unsupported JavaScript test modifier")
        return root, modifier, cursor

    index = 0
    while index < len(tokens) - 3:
        if tokens[index].value in ("const", "let", "var"):
            end = index + 1
            while end < len(tokens) and tokens[end].value not in (";", ","):
                end += 1
            simple_assignment = (
                index + 2 < end and tokens[index + 1].kind == "identifier"
                and tokens[index + 2].value == "="
            )
            known_reference = any(
                item.kind == "identifier"
                and (item.value in test_names | suite_names or item.value in aliases)
                for item in tokens[index + 1:end]
            )
            if known_reference:
                if not simple_assignment:
                    raise SyntaxError("indirect JavaScript collection reference")
                root, modifier, consumed = reference(index + 3, end)
                if consumed != end:
                    raise SyntaxError("indirect JavaScript collection reference")
                aliases[tokens[index + 1].value] = (root, modifier)
                alias_declaration_positions.add(index + 1)
                alias_reference_positions.add(index + 3)
            index = end + 1
            continue
        index += 1

    for index, token in enumerate(tokens):
        if token.kind != "identifier" or token.value not in test_names | suite_names:
            continue
        previous = tokens[index - 1].value if index else ""
        following = tokens[index + 1].value if index + 1 < len(tokens) else ""
        if previous == "." or (
            index not in alias_reference_positions and following not in ("(", ".", "[")
        ):
            raise SyntaxError("indirect JavaScript collection reference")

    def static_title(token: _JSToken) -> str:
        if token.kind != "string" or token.value[0] == "`":
            raise SyntaxError("static JavaScript test title required")
        return token.value[1:-1]

    def visit(
        start: int, stop: int, suites: Tuple[str, ...], inherited_skip: bool,
        inherited_focus: bool = False,
        suite_semantics: Tuple[Tuple[str, Optional[str]], ...] = (),
    ) -> None:
        nonlocal any_focus, focus_declarations
        index = start
        while index < stop:
            token = tokens[index]
            if token.kind != "identifier" or (index and tokens[index - 1].value == "."):
                index += 1
                continue
            name = token.value
            is_alias = name in aliases
            if name not in test_names | suite_names and not is_alias:
                index += 1
                continue
            root, modifier, cursor = reference(index, stop)
            if cursor >= stop or tokens[cursor].value != "(":
                if index not in alias_reference_positions | alias_declaration_positions:
                    raise SyntaxError("indirect JavaScript collection reference")
                index += 1
                continue
            call_end = closing(cursor)
            if call_end > stop or cursor + 1 >= call_end:
                raise SyntaxError("malformed JavaScript test declaration")
            case_title = static_title(tokens[cursor + 1])
            arrow = next((position for position in range(cursor + 2, call_end) if tokens[position].value == "=>"), None)
            if arrow is None:
                raise SyntaxError("ambiguous JavaScript test callback")
            body_open = arrow + 1
            if body_open >= call_end:
                raise SyntaxError("missing JavaScript test callback")
            body_close = call_end
            if tokens[body_open].value == "{":
                body_close = closing(body_open)
                if body_close >= call_end:
                    raise SyntaxError("JavaScript callback escapes declaration")
                body_start = body_open + 1
            else:
                body_start = body_open
            skipped = inherited_skip or modifier in ("skip", "todo", "disabled")
            focused = inherited_focus or modifier == "only"
            if modifier == "only":
                any_focus = True
                focus_declarations += 1
            if root in suite_names:
                if tokens[body_open].value != "{":
                    raise SyntaxError("suite callback must be a block")
                visit(
                    body_start, body_close, suites + (case_title,), skipped, focused,
                    suite_semantics + ((case_title, modifier),),
                )
            else:
                local_identity = " > ".join(suites + (case_title,))
                identity = module + "::" + local_identity
                body_tokens = tokens[body_start:body_close]
                assertions = sum(
                    1 for position, item in enumerate(body_tokens[:-1])
                    if item.kind == "identifier" and item.value in ("expect", "assert")
                    and body_tokens[position + 1].value == "("
                )
                normalized = canonical_json({
                    "suite_semantics": suite_semantics,
                    "case_modifier": modifier,
                    "body": [(item.kind, item.value) for item in body_tokens],
                })
                lowered = normalized.lower() + " " + local_identity.lower()
                cases.append(_CaseStats(
                    identity, local_identity,
                    hashlib.sha256(normalized.encode("utf-8")).hexdigest(), assertions,
                    1 if skipped else 0,
                    assertions if any(term in lowered for term in ("source", "citation", "provenance")) else 0,
                    assertions if any(term in lowered for term in ("property", "invariant")) else 0,
                    focused,
                ))
                case_focus[identity] = focused
            index = call_end + 1

    any_focus = False
    focus_declarations = 0
    case_focus = {}
    visit(0, len(tokens), (), False)
    if any_focus:
        cases = [
            item if case_focus.get(item.identity, False)
            else replace(item, skips=max(1, item.skips))
            for item in cases
        ]
    identities = [item.identity for item in cases]
    if len(identities) != len(set(identities)):
        raise _DuplicateCaseError("duplicate JavaScript test runtime identity")
    return _FileStats(
        tuple(sorted(cases, key=lambda item: item.identity)), focus_declarations,
    )


def _test_stats(
    root: Path, paths: Iterable[str], repository_paths: Iterable[str], findings: list,
    config: Mapping[str, Any], budget: Optional[ResourceBudget] = None,
) -> Dict[str, _FileStats]:
    unittest_shadowed = any(
        path == "unittest.py" or path.endswith("/unittest.py")
        or path == "unittest/__init__.py" or path.endswith("/unittest/__init__.py")
        for path in repository_paths
    )
    pytest_shadowed = any(
        path == "pytest.py" or path.endswith("/pytest.py")
        or path == "pytest/__init__.py" or path.endswith("/pytest/__init__.py")
        for path in repository_paths
    )
    result = {}
    for relative in sorted(paths):
        try:
            text = _source(root / relative, budget, phase="test-parsing")
            result[relative] = (
                _python_stats(
                    text, relative, allow_unittest_testcase=not unittest_shadowed,
                    allow_pytest_parametrize=not pytest_shadowed,
                ) if relative.endswith(".py")
                else _javascript_stats(text, relative)
            )
        except _DuplicateCaseError:
            findings.append(IntegrityFinding(
                "TEST_CASE_DUPLICATE", "A runtime test identity is declared more than once.", relative,
            ))
        except UnicodeDecodeError:
            findings.append(IntegrityFinding(
                "TEST_FILE_UNREADABLE", "Test file is not valid UTF-8.", relative,
            ))
        except SyntaxError:
            findings.append(IntegrityFinding(
                "TEST_FILE_UNPARSABLE", "Test file cannot be parsed deterministically.", relative,
            ))
    return result


def _fixture_cases(path: Path, budget: Optional[ResourceBudget] = None) -> int:
    text = _source(path, budget, phase="fixture-parsing")
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
    budget: Optional[ResourceBudget] = None,
) -> float:
    value = json.loads(_source(path, budget, phase="coverage-parsing"))
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


def _verify_coverage_attestation(
    attestation: Any, path: Path, *, repository: str, commit_sha: str,
    source_manifest_sha256: str, coverage_path: str,
    manifest: Mapping[str, Mapping[str, str]], evaluated_at: str,
    max_age_seconds: int, max_coverage_bytes: int,
    budget: Optional[ResourceBudget] = None,
) -> None:
    if attestation is None:
        raise PermissionError("coverage transport attestation is unavailable")
    if type(attestation) is not CoverageAttestation:
        raise ValueError("coverage transport attestation is not sealed")
    if path.stat().st_size > max_coverage_bytes:
        raise OverflowError("TEST_RESOURCE_LIMIT")
    if (
        attestation.schema_version != "1.0.0"
        or attestation.repository != repository
        or attestation.commit_sha != commit_sha
        or attestation.source_manifest_sha256 != source_manifest_sha256
        or attestation.coverage_path != coverage_path
        or attestation.coverage_file_sha256 != manifest[coverage_path]["sha256"]
        or attestation.workflow_path != ".github/workflows/coverage.yml"
        or _SHA40.fullmatch(attestation.workflow_sha or "") is None
        or not isinstance(attestation.run_id, int) or isinstance(attestation.run_id, bool)
        or attestation.run_id < 1
        or not isinstance(attestation.artifact_id, int) or isinstance(attestation.artifact_id, bool)
        or attestation.artifact_id < 1
        or _SHA256.fullmatch(attestation.artifact_digest or "") is None
        or attestation.conclusion != "success"
        or not isinstance(attestation.transport_provenance, str)
        or not attestation.transport_provenance
    ):
        raise LookupError("coverage transport attestation is not bound")
    document = json.loads(_source(path, budget, phase="coverage-verification"))
    if document.get("generated_at") != attestation.generated_at:
        raise LookupError("coverage generation timestamp is not bound")
    generated = _timestamp(attestation.generated_at)
    transported = _timestamp(attestation.transport_created_at)
    evaluated = _timestamp(evaluated_at)
    age = (evaluated - generated).total_seconds()
    if (
        age < 0 or age > max_age_seconds or generated > transported
        or (transported - generated).total_seconds() > max_age_seconds
        or transported > evaluated
    ):
        raise TimeoutError("coverage transport attestation is stale")


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


def _rename_projection(stats: Optional[_FileStats]) -> Tuple[Tuple[Any, ...], ...]:
    if stats is None:
        return ()
    return tuple(sorted(
        (
            item.local_identity, item.body_hash, item.assertions, item.skips,
            item.sourcing_assertions, item.property_assertions, item.focused,
        )
        for item in stats.cases
    ))


def _analyze_test_integrity(
    base_root: Any, head_root: Any, policy: Mapping[str, Any],
    resource_budget: Optional[ResourceBudget] = None,
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
        checked = _validate_policy(policy, resource_budget)
    except (OverflowError, MemoryError):
        return _invalid_report(policy, "TEST_RESOURCE_LIMIT", "Policy evidence exceeds deterministic resource limits.")
    except (PathInputError, TypeError, ValueError, re.error):
        return _invalid_report(policy, "TEST_INTEGRITY_POLICY_INVALID", "Test-integrity policy is invalid.")
    try:
        base = Path(base_root).resolve(strict=True)
        head = Path(head_root).resolve(strict=True)
        if base == head:
            raise ValueError("base and head roots must differ")
        budget = checked["_resource_budget"]
        actual_base = _scan(base, checked["configuration"], budget)
        actual_head = _scan(head, checked["configuration"], budget)
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
    base_stats = _test_stats(
        base, base_tests, actual_base, findings, config, budget,
    )
    head_stats = _test_stats(
        head, head_tests, actual_head, findings, config, budget,
    )

    deleted = sorted(base_tests - head_tests)
    added = set(head_tests - base_tests)
    for path in deleted:
        old = base_stats.get(path)
        if old is None:
            continue
        exact = [
            candidate for candidate in added
            if _rename_projection(head_stats.get(candidate)) == _rename_projection(old)
        ]
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
            if after.body_hash != before.body_hash:
                findings.append(IntegrityFinding(
                    "TEST_CASE_BEHAVIOR_CHANGE_AMBIGUOUS",
                    "Executable test behavior changed without proof that coverage was preserved.",
                    path, {"case": identity},
                ))
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
            if after.focused and not before.focused:
                findings.append(IntegrityFinding(
                    "TEST_CASE_FOCUS_ADDED",
                    "A test case became focused and may exclude peer tests.",
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
    base_focuses = totals(base_stats, "focuses")
    head_focuses = totals(head_stats, "focuses")
    base_focus_declarations = totals(base_stats, "focus_declarations")
    head_focus_declarations = totals(head_stats, "focus_declarations")
    base_sourcing = totals(base_stats, "sourcing_assertions")
    head_sourcing = totals(head_stats, "sourcing_assertions")
    base_properties = totals(base_stats, "property_assertions")
    head_properties = totals(head_stats, "property_assertions")
    if head_skips > base_skips:
        findings.append(IntegrityFinding("TEST_SKIP_ADDED", "New skipped or disabled tests were detected."))
    if (
        head_focuses > base_focuses
        or head_focus_declarations > base_focus_declarations
    ):
        findings.append(IntegrityFinding(
            "TEST_FOCUS_ADDED", "Focused tests or suites were introduced.",
        ))
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
            before_text = _source(base / path, budget, phase="workflow-comparison")
            after_text = _source(head / path, budget, phase="workflow-comparison")
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
            before_text = _source(base / path, budget, phase="configuration-comparison")
            after_text = _source(head / path, budget, phase="configuration-comparison")
            weakened = _weakened(before_text, after_text)
            if path == "package.json" or path.endswith("/package.json"):
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
            before = _fixture_cases(base / path, budget) if path in base_fixtures else 0
            after = _fixture_cases(head / path, budget) if path in head_fixtures else 0
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
                    budget=budget,
                )
                after = _coverage(
                    head / present_head[0], repository=checked["repository"],
                    commit_sha=checked["head_sha"], source_manifest_sha256=source_head,
                    evaluated_at=checked["evaluated_at"],
                    max_age_seconds=config["coverage_max_age_seconds"],
                    budget=budget,
                )
                attestations = checked["coverage_attestations"]
                if attestations is None:
                    raise PermissionError("coverage transport attestation is unavailable")
                _verify_coverage_attestation(
                    attestations["base"], base / present_base[0],
                    repository=checked["repository"], commit_sha=checked["base_sha"],
                    source_manifest_sha256=source_base, coverage_path=present_base[0],
                    manifest=checked["base_manifest"], evaluated_at=checked["evaluated_at"],
                    max_age_seconds=config["coverage_max_age_seconds"],
                    max_coverage_bytes=config["max_coverage_bytes"],
                    budget=budget,
                )
                _verify_coverage_attestation(
                    attestations["head"], head / present_head[0],
                    repository=checked["repository"], commit_sha=checked["head_sha"],
                    source_manifest_sha256=source_head, coverage_path=present_head[0],
                    manifest=checked["head_manifest"], evaluated_at=checked["evaluated_at"],
                    max_age_seconds=config["coverage_max_age_seconds"],
                    max_coverage_bytes=config["max_coverage_bytes"],
                    budget=budget,
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
            except PermissionError:
                findings.append(IntegrityFinding(
                    "TEST_COVERAGE_ATTESTATION_UNAVAILABLE",
                    "Authenticated GitHub coverage transport evidence is unavailable.",
                ))
            except OverflowError:
                findings.append(IntegrityFinding(
                    "TEST_RESOURCE_LIMIT", "Coverage evidence exceeds deterministic resource limits.",
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
        "focused_tests": head_focuses - base_focuses,
        "focus_declarations": head_focus_declarations - base_focus_declarations,
        "sourcing_assertions": head_sourcing - base_sourcing,
        "property_assertions": head_properties - base_properties,
        "fixture_cases": head_fixture_cases - base_fixture_cases,
        "coverage_percent": coverage_delta,
    }
    budget.consume_bytes(
        len(canonical_json({
            "findings": [asdict(item) for item in findings], "deltas": deltas,
        }).encode("utf-8")),
        phase="reporting",
    )
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


def analyze_test_integrity(
    base_root: Any, head_root: Any, policy: Mapping[str, Any], *,
    resource_budget: Optional[ResourceBudget] = None,
) -> IntegrityReport:
    """Run all phases against one aggregate fail-closed resource budget."""

    try:
        return _analyze_test_integrity(
            base_root, head_root, policy, resource_budget=resource_budget,
        )
    except (OverflowError, MemoryError):
        return _invalid_report(
            policy, "TEST_RESOURCE_LIMIT",
            "Integrity processing exceeded its shared deterministic resource budget.",
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
