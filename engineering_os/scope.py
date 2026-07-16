"""POSIX path scope and semantic mission conflict enforcement."""

from fnmatch import fnmatchcase
from typing import Any, Iterable, List, Mapping, Sequence, Tuple

from .errors import Violation


_GLOB_CHARS = frozenset("*?[")
_INACTIVE_STATES = frozenset(("Parked", "Cancelled", "Closed", "Released"))


class PathInputError(ValueError):
    """A path or glob is not a normalized repository-relative POSIX value."""


def normalize_path(value: str, *, allow_glob: bool = False) -> str:
    """Return a repository-relative POSIX path and reject ambiguous escape forms."""

    if not isinstance(value, str) or not value or "\x00" in value or "\\" in value:
        raise PathInputError("path must be a non-empty POSIX string")
    if value.startswith("/"):
        raise PathInputError("absolute paths are not allowed")
    if not allow_glob and any(char in value for char in _GLOB_CHARS):
        raise PathInputError("changed paths must not contain glob metacharacters")
    parts = []
    for part in value.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            raise PathInputError("path traversal is not allowed")
        parts.append(part)
    if not parts:
        raise PathInputError("path must identify a repository entry")
    return "/".join(parts)


def normalize_paths(values: Sequence[str], *, allow_glob: bool = False) -> Tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        raise PathInputError("paths must be an array")
    return tuple(normalize_path(value, allow_glob=allow_glob) for value in values)


def path_matches(path: str, pattern: str) -> bool:
    """Apply one matching rule everywhere in the enforcement package."""

    return fnmatchcase(path, pattern)


def _policy_patterns(policy: Mapping[str, Any]) -> Tuple[Tuple[str, ...], Tuple[Mapping[str, Any], ...]]:
    if not isinstance(policy, Mapping):
        raise PathInputError("policy must be an object")
    tier_two = normalize_paths(policy.get("tier_2_paths", []), allow_glob=True)
    domains = policy.get("semantic_domains", [])
    if not isinstance(domains, list):
        raise PathInputError("semantic domains must be an array")
    normalized_domains = []
    for domain in domains:
        if not isinstance(domain, Mapping):
            raise PathInputError("semantic domains must be objects")
        patterns = normalize_paths(domain.get("paths", []), allow_glob=True)
        if not patterns:
            raise PathInputError("semantic domain paths must not be empty")
        if not isinstance(domain.get("conflict_group"), str) or not domain.get("conflict_group"):
            raise PathInputError("semantic domains require conflict groups")
        normalized = dict(domain)
        normalized["paths"] = patterns
        normalized_domains.append(normalized)
    return tier_two, tuple(normalized_domains)


def _domain_groups(paths: Sequence[str], domains: Sequence[Mapping[str, Any]]) -> set:
    return {
        domain["conflict_group"]
        for domain in domains
        if any(path_matches(path, pattern) for path in paths for pattern in domain["paths"])
    }


def validate_scope(
    mission: Mapping[str, Any], policy: Mapping[str, Any], changed_files: Sequence[str]
) -> List[Violation]:
    """Validate changed files against mission scope and base-policy tier boundaries."""

    try:
        changed = normalize_paths(changed_files)
        allowed = normalize_paths(mission.get("allowed_paths", []), allow_glob=True)
        prohibited = normalize_paths(mission.get("prohibited_paths", []), allow_glob=True)
    except (AttributeError, PathInputError, TypeError):
        return [Violation("SCOPE_PATH_INVALID", "mission or changed path is invalid", "$.paths")]
    try:
        tier_two, _ = _policy_patterns(policy)
    except (PathInputError, TypeError):
        return [Violation("SCOPE_POLICY_INVALID", "base policy path rules are invalid", "$.policy")]

    violations = []
    for path in changed:
        if not any(path_matches(path, pattern) for pattern in allowed):
            violations.append(Violation(
                "SCOPE_PATH_NOT_ALLOWED", "changed path is outside mission scope",
                "$.changed_files", {"path": path},
            ))
        if any(path_matches(path, pattern) for pattern in prohibited):
            violations.append(Violation(
                "SCOPE_PATH_PROHIBITED", "changed path is explicitly prohibited",
                "$.changed_files", {"path": path},
            ))
        if mission.get("risk_tier") != "Tier 2" and any(
            path_matches(path, pattern) for pattern in tier_two
        ):
            violations.append(Violation(
                "SCOPE_TIER_2_PATH", "a Tier 2 policy path requires a Tier 2 mission",
                "$.changed_files", {"path": path},
            ))
    return violations


def _literal_prefix(pattern: str) -> str:
    wildcard = min((pattern.find(char) for char in _GLOB_CHARS if char in pattern), default=len(pattern))
    return pattern[:wildcard].rstrip("/")


def _paths_overlap(left: Sequence[str], right: Sequence[str]) -> bool:
    for first in left:
        for second in right:
            if first == second or path_matches(first, second) or path_matches(second, first):
                return True
            first_prefix = _literal_prefix(first)
            second_prefix = _literal_prefix(second)
            if first_prefix and second_prefix and (
                first_prefix == second_prefix
                or first_prefix.startswith(second_prefix + "/")
                or second_prefix.startswith(first_prefix + "/")
            ):
                return True
            if not first_prefix or not second_prefix:
                return True
    return False


def _coordinated(
    mission_id: str, current_paths: Sequence[str], other_id: str, other_paths: Sequence[str],
    records: Iterable[Mapping[str, Any]],
) -> bool:
    expected_ids = {mission_id, other_id}
    for record in records:
        if not isinstance(record, Mapping):
            continue
        ids = record.get("mission_ids")
        scopes = record.get("scopes")
        if (
            record.get("status") == "active"
            and record.get("issuer_role") == "founder"
            and isinstance(ids, list)
            and set(ids) == expected_ids
            and len(ids) == 2
            and isinstance(scopes, Mapping)
        ):
            try:
                left = normalize_paths(scopes.get(mission_id, []), allow_glob=True)
                right = normalize_paths(scopes.get(other_id, []), allow_glob=True)
            except PathInputError:
                continue
            if set(left) == set(current_paths) and set(right) == set(other_paths):
                return True
    return False


def detect_mission_conflicts(
    mission: Mapping[str, Any], policy: Mapping[str, Any], changed_files: Sequence[str],
    active_missions: Sequence[Mapping[str, Any]], *,
    coordination_records: Iterable[Mapping[str, Any]] = (),
) -> List[Violation]:
    """Deny active path or semantic overlap absent an exact founder coordination record."""

    try:
        current_paths = normalize_paths(changed_files)
        _, domains = _policy_patterns(policy)
        mission_id = mission["mission_id"]
        if not isinstance(mission_id, str) or not mission_id or not isinstance(active_missions, list):
            raise PathInputError("invalid mission conflict input")
    except (KeyError, PathInputError, TypeError):
        return [Violation("MISSION_CONFLICT_INPUT_INVALID", "mission conflict input is invalid")]

    current_groups = _domain_groups(current_paths, domains)
    violations = []
    for other in active_missions:
        if not isinstance(other, Mapping) or other.get("state") in _INACTIVE_STATES:
            continue
        other_id = other.get("mission_id")
        if not isinstance(other_id, str) or not other_id or other_id == mission_id:
            continue
        try:
            other_paths = normalize_paths(other.get("paths", []), allow_glob=True)
        except PathInputError:
            violations.append(Violation(
                "MISSION_CONFLICT_INPUT_INVALID", "active mission paths are invalid",
                "$.active_missions", {"mission_id": other_id},
            ))
            continue
        other_groups_value = other.get("conflict_groups")
        if isinstance(other_groups_value, list) and all(
            isinstance(group, str) and group for group in other_groups_value
        ):
            other_groups = set(other_groups_value)
        else:
            other_groups = _domain_groups(other_paths, domains)
        path_conflict = _paths_overlap(current_paths, other_paths)
        semantic_conflict = bool(current_groups & other_groups)
        if not (path_conflict or semantic_conflict):
            continue
        if _coordinated(
            mission_id, current_paths, other_id, other_paths, coordination_records
        ):
            continue
        if path_conflict:
            violations.append(Violation(
                "MISSION_PATH_CONFLICT", "changed paths overlap an active mission",
                "$.active_missions", {"mission_id": other_id},
            ))
        if semantic_conflict:
            violations.append(Violation(
                "MISSION_SEMANTIC_CONFLICT", "semantic ownership conflicts with an active mission",
                "$.active_missions", {"mission_id": other_id, "conflict_groups": sorted(current_groups & other_groups)},
            ))
    return violations
