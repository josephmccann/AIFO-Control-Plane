"""Frozen-artifact declaration and exact one-shot exception enforcement."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from typing import Any, Dict, Iterable, Mapping, Sequence

from .schema import validate_document
from .scope import PathInputError, normalize_paths, path_matches


_EXCEPTION_FIELDS = frozenset((
    "exception_id", "declaration_id", "repository", "mission_id", "pull_request",
    "head_sha", "paths", "action", "issuer", "issuer_role", "starts_at",
    "expires_at", "status", "pinned_commit", "sealed_manifest_sha256",
    "protected_version", "release_condition", "one_shot",
))


@dataclass(frozen=True)
class FrozenDecision:
    allowed: bool
    code: str
    declaration_id: str = ""
    exception_id: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


def _time(value: str) -> datetime:
    if not isinstance(value, str) or re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z", value
    ) is None:
        raise ValueError("timestamp must be strict UTC RFC3339")
    return datetime.fromisoformat(value[:-1] + "+00:00").astimezone(timezone.utc)


def _decision(
    allowed: bool, code: str, declaration: Mapping[str, Any] = None,
    exception: Mapping[str, Any] = None,
) -> FrozenDecision:
    return FrozenDecision(
        allowed, code,
        declaration.get("declaration_id", "") if isinstance(declaration, Mapping) else "",
        exception.get("exception_id", "") if isinstance(exception, Mapping) else "",
    )


def _declaration_valid(declaration: Mapping[str, Any], repository: str) -> bool:
    try:
        if validate_document("frozen-path", dict(declaration)):
            return False
        paths = normalize_paths(declaration.get("paths", []), allow_glob=True)
        expiry = declaration.get("expires_at")
        if expiry is not None:
            _time(expiry)
        return bool(paths) and all((
            isinstance(declaration.get("declaration_id"), str) and bool(declaration.get("declaration_id")),
            declaration.get("repository") == repository,
            declaration.get("exception_authority") == "founder",
            isinstance(declaration.get("release_condition"), str) and bool(declaration.get("release_condition")),
            isinstance(declaration.get("one_shot"), bool),
        ))
    except (PathInputError, TypeError, ValueError):
        return False


def _observation_code(declaration: Mapping[str, Any], observations: Mapping[str, Any]) -> str:
    observed = observations.get(declaration.get("declaration_id"), {})
    if not isinstance(observed, Mapping):
        return "FROZEN_OBSERVATION_INVALID"
    comparisons = (
        ("pinned_commit", "FROZEN_PIN_MISMATCH"),
        ("sealed_manifest_sha256", "FROZEN_MANIFEST_MISMATCH"),
        ("protected_version", "FROZEN_VERSION_MISMATCH"),
    )
    for field, code in comparisons:
        expected = declaration.get(field)
        if expected is not None and observed.get(field) != expected:
            return code
    return ""


def validate_frozen_changes(
    mission: Mapping[str, Any], changed_files: Sequence[str],
    declarations: Sequence[Mapping[str, Any]], exceptions: Sequence[Mapping[str, Any]], *,
    repository: str, pull_request: int, head_sha: str, now: str, action: str = "write",
    observations: Mapping[str, Any] = None,
    satisfied_release_conditions: Iterable[str] = (),
    consumed_exception_ids: Iterable[str] = (),
) -> FrozenDecision:
    """Deny frozen writes unless every affected declaration has an exact exception."""

    try:
        changed = normalize_paths(changed_files)
        current = _time(now)
    except (PathInputError, TypeError, ValueError):
        return _decision(False, "FROZEN_INPUT_INVALID")
    if not isinstance(declarations, list) or not isinstance(exceptions, list):
        return _decision(False, "FROZEN_INPUT_INVALID")
    observations = observations if isinstance(observations, Mapping) else {}
    release_conditions = set(satisfied_release_conditions)
    consumed = set(consumed_exception_ids)

    affected = []
    for declaration in declarations:
        if not isinstance(declaration, Mapping) or not _declaration_valid(declaration, repository):
            return _decision(False, "FROZEN_DECLARATION_INVALID", declaration)
        patterns = normalize_paths(declaration.get("paths", []), allow_glob=True)
        expiry = declaration.get("expires_at")
        if expiry is not None and current >= _time(expiry):
            continue
        touched = tuple(path for path in changed if any(path_matches(path, pattern) for pattern in patterns))
        if touched:
            affected.append((declaration, touched))
    if not affected:
        return _decision(True, "FROZEN_PATHS_UNTOUCHED")

    for declaration, touched in affected:
        observation_failure = _observation_code(declaration, observations)
        if observation_failure:
            return _decision(False, observation_failure, declaration)
        matching_declaration = [
            item for item in exceptions
            if isinstance(item, Mapping) and item.get("declaration_id") == declaration.get("declaration_id")
        ]
        if not matching_declaration:
            return _decision(False, "FROZEN_WRITE_DENIED", declaration)
        last = _decision(False, "FROZEN_WRITE_DENIED", declaration)
        for exception in matching_declaration:
            if not _EXCEPTION_FIELDS.issubset(exception):
                last = _decision(False, "FROZEN_EXCEPTION_INVALID", declaration, exception)
                continue
            try:
                paths = normalize_paths(exception.get("paths", []))
                starts = _time(exception.get("starts_at"))
                expires = _time(exception.get("expires_at"))
                if (
                    starts >= expires
                    or not isinstance(exception.get("exception_id"), str)
                    or not exception.get("exception_id")
                    or not isinstance(exception.get("issuer"), str)
                    or not exception.get("issuer")
                    or not isinstance(exception.get("pull_request"), int)
                    or isinstance(exception.get("pull_request"), bool)
                    or re.fullmatch(r"[0-9a-f]{40}", str(exception.get("head_sha", ""))) is None
                ):
                    raise ValueError("empty exception interval")
            except (PathInputError, TypeError, ValueError):
                last = _decision(False, "FROZEN_EXCEPTION_INVALID", declaration, exception)
                continue
            checks = (
                (exception.get("repository") != repository, "FROZEN_EXCEPTION_REPOSITORY_MISMATCH"),
                (exception.get("mission_id") != mission.get("mission_id"), "FROZEN_EXCEPTION_MISSION_MISMATCH"),
                (exception.get("pull_request") != pull_request, "FROZEN_EXCEPTION_PR_MISMATCH"),
                (exception.get("head_sha") != head_sha, "FROZEN_EXCEPTION_HEAD_MISMATCH"),
                (set(paths) != set(touched) or len(paths) != len(touched), "FROZEN_EXCEPTION_PATH_MISMATCH"),
                (exception.get("action") != action, "FROZEN_EXCEPTION_ACTION_MISMATCH"),
                (exception.get("issuer_role") != declaration.get("exception_authority"), "FROZEN_EXCEPTION_ISSUER_DENIED"),
                (exception.get("status") != "active", "FROZEN_EXCEPTION_INACTIVE"),
                (current < starts, "FROZEN_EXCEPTION_NOT_STARTED"),
                (current >= expires, "FROZEN_EXCEPTION_EXPIRED"),
                (exception.get("pinned_commit") != declaration.get("pinned_commit"), "FROZEN_PIN_MISMATCH"),
                (exception.get("sealed_manifest_sha256") != declaration.get("sealed_manifest_sha256"), "FROZEN_MANIFEST_MISMATCH"),
                (exception.get("protected_version") != declaration.get("protected_version"), "FROZEN_VERSION_MISMATCH"),
                (exception.get("release_condition") != declaration.get("release_condition"), "FROZEN_RELEASE_CONDITION_MISMATCH"),
                (declaration.get("release_condition") not in release_conditions, "FROZEN_RELEASE_CONDITION_UNMET"),
                (exception.get("one_shot") is not declaration.get("one_shot"), "FROZEN_EXCEPTION_ONE_SHOT_MISMATCH"),
                (exception.get("exception_id") in consumed, "FROZEN_EXCEPTION_CONSUMED"),
            )
            failed = next((code for condition, code in checks if condition), None)
            if failed:
                last = _decision(False, failed, declaration, exception)
                continue
            last = _decision(True, "FROZEN_EXCEPTION_ALLOWED", declaration, exception)
            break
        if not last.allowed:
            return last
    return _decision(True, "FROZEN_EXCEPTION_ALLOWED", affected[-1][0])
