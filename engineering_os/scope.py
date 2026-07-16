"""POSIX path scope and semantic mission conflict enforcement."""

from datetime import datetime, timezone
import re
from typing import Any, Iterable, List, Mapping, Sequence, Tuple

from .errors import Violation
from .records import VerifiedRecordEnvelope, verify_record_envelope
from .schema import validate_document


_GLOB_CHARS = frozenset("*?[")
_BLOCKING_STATES = frozenset((
    "Claimed", "In Progress", "Adversarial Review", "Founder Approval",
    "Merge Authorized", "Incident",
))
_MISSION_STATES = frozenset((
    "Proposed", "Ready", "Claimed", "In Progress", "Adversarial Review",
    "Founder Approval", "Merge Authorized", "Merged", "Verified", "Closed",
    "Parked", "Incident", "Cancelled",
))
_COORDINATION_FIELDS = frozenset((
    "record_id", "repository", "status", "issuer", "mission_ids",
    "pull_request", "head_sha", "starts_at", "expires_at", "nonce",
    "source", "scopes",
))


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
    """Apply segment-aware git-style glob matching everywhere in the package."""

    return re.fullmatch(_glob_regex(pattern), path) is not None


def _glob_regex(pattern: str) -> str:
    translated = []
    index = 0
    while index < len(pattern):
        char = pattern[index]
        if char == "*":
            if index + 1 < len(pattern) and pattern[index + 1] == "*":
                index += 2
                if index < len(pattern) and pattern[index] == "/":
                    translated.append("(?:[^/]+/)*")
                    index += 1
                else:
                    translated.append(".*")
                continue
            translated.append("[^/]*")
        elif char == "?":
            translated.append("[^/]")
        elif char == "[":
            end = pattern.find("]", index + 1)
            if end < 0 or "/" in pattern[index + 1:end]:
                raise PathInputError("invalid glob character class")
            body = pattern[index + 1:end]
            if not body:
                raise PathInputError("empty glob character class")
            if body[0] == "!":
                body = "^" + body[1:]
            translated.append("[" + body.replace("\\", "\\\\") + "]")
            index = end
        else:
            translated.append(re.escape(char))
        index += 1
    result = "".join(translated)
    try:
        re.compile(result)
    except re.error as error:
        raise PathInputError("invalid glob expression") from error
    return result


def _policy_patterns(policy: Mapping[str, Any]) -> Tuple[Tuple[str, ...], Tuple[Mapping[str, Any], ...]]:
    if not isinstance(policy, Mapping):
        raise PathInputError("policy must be an object")
    tier_two = normalize_paths(policy.get("tier_2_paths", []), allow_glob=True)
    for pattern in tier_two:
        _glob_regex(pattern)
    domains = policy.get("semantic_domains", [])
    if not isinstance(domains, list):
        raise PathInputError("semantic domains must be an array")
    normalized_domains = []
    for domain in domains:
        if not isinstance(domain, Mapping):
            raise PathInputError("semantic domains must be objects")
        patterns = normalize_paths(domain.get("paths", []), allow_glob=True)
        for pattern in patterns:
            _glob_regex(pattern)
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
        if _paths_overlap(paths, domain["paths"])
    }


def validate_scope(
    mission: Mapping[str, Any], policy: Mapping[str, Any], changed_files: Sequence[str]
) -> List[Violation]:
    """Validate changed files against mission scope and base-policy tier boundaries."""

    if not isinstance(mission, Mapping) or validate_document("mission", dict(mission)):
        return [Violation("SCOPE_MISSION_INVALID", "mission schema is invalid", "$.mission")]
    if not isinstance(policy, Mapping) or validate_document("repository-policy", dict(policy)):
        return [Violation("SCOPE_POLICY_INVALID", "base policy schema is invalid", "$.policy")]
    try:
        changed = normalize_paths(changed_files)
        allowed = normalize_paths(mission.get("allowed_paths", []), allow_glob=True)
        prohibited = normalize_paths(mission.get("prohibited_paths", []), allow_glob=True)
        for pattern in allowed + prohibited:
            _glob_regex(pattern)
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


def _segment_tokens(pattern: str) -> Tuple[Tuple[str, str], ...]:
    tokens = []
    index = 0
    while index < len(pattern):
        char = pattern[index]
        if char == "*":
            tokens.append(("star", ""))
        elif char == "?":
            tokens.append(("any", ""))
        elif char == "[":
            end = pattern.find("]", index + 1)
            if end < 0:
                raise PathInputError("invalid glob character class")
            expression = pattern[index:end + 1]
            try:
                re.compile(expression)
            except re.error as error:
                raise PathInputError("invalid glob character class") from error
            tokens.append(("class", expression))
            index = end
        else:
            tokens.append(("literal", char))
        index += 1
    return tuple(tokens)


def _token_intersects(left: Tuple[str, str], right: Tuple[str, str], alphabet: set) -> bool:
    if left[0] in ("star", "any") or right[0] in ("star", "any"):
        return True
    if left[0] == "literal" and right[0] == "literal":
        return left[1] == right[1]
    if left[0] == "literal":
        return re.fullmatch(right[1], left[1]) is not None
    if right[0] == "literal":
        return re.fullmatch(left[1], right[1]) is not None
    return any(
        re.fullmatch(left[1], char) is not None
        and re.fullmatch(right[1], char) is not None
        for char in alphabet
    )


def _segments_overlap(left: str, right: str) -> bool:
    left_tokens, right_tokens = _segment_tokens(left), _segment_tokens(right)
    alphabet = {
        *(chr(value) for value in range(1, 128) if chr(value) not in "/\\"),
        *(char for char in left + right if char not in "*?[]!-/\\"),
        "\u0100",
    }
    pending = [(0, 0)]
    visited = set()
    while pending:
        left_index, right_index = pending.pop()
        if (left_index, right_index) in visited:
            continue
        visited.add((left_index, right_index))
        if left_index == len(left_tokens) and right_index == len(right_tokens):
            return True
        if left_index < len(left_tokens) and left_tokens[left_index][0] == "star":
            pending.append((left_index + 1, right_index))
        if right_index < len(right_tokens) and right_tokens[right_index][0] == "star":
            pending.append((left_index, right_index + 1))
        if left_index >= len(left_tokens) or right_index >= len(right_tokens):
            continue
        left_token, right_token = left_tokens[left_index], right_tokens[right_index]
        if not _token_intersects(left_token, right_token, alphabet):
            continue
        pending.append((
            left_index if left_token[0] == "star" else left_index + 1,
            right_index if right_token[0] == "star" else right_index + 1,
        ))
    return False


def _patterns_overlap(left: str, right: str) -> bool:
    left_segments, right_segments = left.split("/"), right.split("/")
    pending = [(0, 0)]
    visited = set()
    while pending:
        left_index, right_index = pending.pop()
        if (left_index, right_index) in visited:
            continue
        visited.add((left_index, right_index))
        if left_index == len(left_segments) and right_index == len(right_segments):
            return True
        left_recursive = left_index < len(left_segments) and left_segments[left_index] == "**"
        right_recursive = right_index < len(right_segments) and right_segments[right_index] == "**"
        if left_recursive:
            pending.append((left_index + 1, right_index))
        if right_recursive:
            pending.append((left_index, right_index + 1))
        if left_index >= len(left_segments) or right_index >= len(right_segments):
            continue
        if left_recursive or right_recursive or _segments_overlap(
            left_segments[left_index], right_segments[right_index],
        ):
            pending.append((
                left_index if left_recursive else left_index + 1,
                right_index if right_recursive else right_index + 1,
            ))
    return False


def _paths_overlap(left: Sequence[str], right: Sequence[str]) -> bool:
    return any(_patterns_overlap(first, second) for first in left for second in right)


def _time(value: str) -> datetime:
    if not isinstance(value, str) or re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z", value
    ) is None:
        raise ValueError("invalid timestamp")
    return datetime.fromisoformat(value[:-1] + "+00:00").astimezone(timezone.utc)


def _coordinated(
    mission_id: str, current_paths: Sequence[str], other_id: str, other_paths: Sequence[str],
    records: Iterable[Mapping[str, Any]], policy: Mapping[str, Any], *,
    repository: str, pull_request: int, head_sha: str, now: str,
    verified_envelopes: Sequence[VerifiedRecordEnvelope],
) -> bool:
    expected_ids = {mission_id, other_id}
    try:
        current = _time(now)
    except (TypeError, ValueError):
        return False
    founders = policy.get("founder_identities", [])
    if not isinstance(founders, list):
        return False
    for record in records:
        if not isinstance(record, Mapping) or set(record) != _COORDINATION_FIELDS:
            continue
        ids = record.get("mission_ids")
        scopes = record.get("scopes")
        try:
            starts, expires = _time(record.get("starts_at")), _time(record.get("expires_at"))
            valid_ids = (
                isinstance(ids, list) and len(ids) == 2
                and all(isinstance(value, str) for value in ids)
                and set(ids) == expected_ids
            )
            if not valid_ids or not isinstance(scopes, Mapping):
                continue
            left = normalize_paths(scopes.get(mission_id, []), allow_glob=True)
            right = normalize_paths(scopes.get(other_id, []), allow_glob=True)
            for pattern in left + right:
                _glob_regex(pattern)
        except (PathInputError, TypeError, ValueError):
            continue
        issuer = record.get("issuer")
        if (
            record.get("status") == "active"
            and isinstance(record.get("record_id"), str) and record.get("record_id")
            and isinstance(record.get("nonce"), str) and record.get("nonce")
            and record.get("repository") == repository == policy.get("repository")
            and record.get("pull_request") == pull_request
            and record.get("head_sha") == head_sha
            and issuer in founders
            and starts <= current < expires
            and verify_record_envelope(
                record, "coordination", verified_envelopes,
                repository=repository, actor=issuer,
            )
            and set(left) == set(current_paths) and len(left) == len(current_paths)
            and set(right) == set(other_paths) and len(right) == len(other_paths)
        ):
            return True
    return False


def detect_mission_conflicts(
    mission: Mapping[str, Any], policy: Mapping[str, Any], changed_files: Sequence[str],
    active_missions: Sequence[Mapping[str, Any]], *,
    coordination_records: Iterable[Mapping[str, Any]] = (),
    repository: str = "", pull_request: int = 0, head_sha: str = "", now: str = "",
    verified_envelopes: Sequence[VerifiedRecordEnvelope] = (),
) -> List[Violation]:
    """Deny active path or semantic overlap absent an exact founder coordination record."""

    if not isinstance(mission, Mapping) or validate_document("mission", dict(mission)):
        return [Violation("MISSION_CONFLICT_INPUT_INVALID", "mission schema is invalid")]
    if not isinstance(policy, Mapping) or validate_document("repository-policy", dict(policy)):
        return [Violation("MISSION_CONFLICT_INPUT_INVALID", "base policy schema is invalid")]
    try:
        current_paths = normalize_paths(changed_files)
        _, domains = _policy_patterns(policy)
        mission_id = mission["mission_id"]
        if not isinstance(mission_id, str) or not mission_id or not isinstance(active_missions, list):
            raise PathInputError("invalid mission conflict input")
    except (KeyError, PathInputError, TypeError):
        return [Violation("MISSION_CONFLICT_INPUT_INVALID", "mission conflict input is invalid")]

    normalized_active = []
    seen_ids = set()
    for other in active_missions:
        if not isinstance(other, Mapping):
            return [Violation("MISSION_CONFLICT_INPUT_INVALID", "active mission must be an object")]
        other_id = other.get("mission_id")
        state = other.get("state")
        if (
            not isinstance(other_id, str) or not other_id or other_id in seen_ids
            or state not in _MISSION_STATES
        ):
            return [Violation("MISSION_CONFLICT_INPUT_INVALID", "active mission identity or state is invalid")]
        seen_ids.add(other_id)
        if state not in _BLOCKING_STATES:
            continue
        try:
            other_paths = normalize_paths(other.get("paths", []), allow_glob=True)
            for pattern in other_paths:
                _glob_regex(pattern)
        except PathInputError:
            return [Violation("MISSION_CONFLICT_INPUT_INVALID", "active mission paths are invalid")]
        if not other_paths:
            return [Violation("MISSION_CONFLICT_INPUT_INVALID", "active mission paths are empty")]
        normalized_active.append((other, other_id, state, other_paths))

    current_groups = _domain_groups(current_paths, domains)
    violations = []
    for other, other_id, state, other_paths in normalized_active:
        if other_id == mission_id:
            continue
        other_groups = _domain_groups(other_paths, domains)
        path_conflict = _paths_overlap(current_paths, other_paths)
        semantic_conflict = bool(current_groups & other_groups)
        if not (path_conflict or semantic_conflict):
            continue
        if _coordinated(
            mission_id, current_paths, other_id, other_paths, coordination_records, policy,
            repository=repository, pull_request=pull_request, head_sha=head_sha,
            now=now, verified_envelopes=verified_envelopes,
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
