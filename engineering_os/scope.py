"""POSIX path scope and semantic mission conflict enforcement."""

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Any, Iterable, List, Mapping, Sequence, Tuple

from .errors import Violation
from .records import verify_record_evidence
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


_UNIVERSE_INTERVALS = ((1, 46), (48, 91), (93, 0x10FFFF))


def _merge_intervals(intervals: Sequence[Tuple[int, int]]) -> Tuple[Tuple[int, int], ...]:
    merged = []
    for start, end in sorted(intervals):
        if start > end:
            raise PathInputError("glob character range is reversed")
        if merged and start <= merged[-1][1] + 1:
            merged[-1] = (merged[-1][0], max(end, merged[-1][1]))
        else:
            merged.append((start, end))
    return tuple(merged)


def _subtract_intervals(
    universe: Sequence[Tuple[int, int]], excluded: Sequence[Tuple[int, int]],
) -> Tuple[Tuple[int, int], ...]:
    remaining = []
    for lower, upper in universe:
        cursor = lower
        for start, end in excluded:
            if end < cursor or start > upper:
                continue
            if start > cursor:
                remaining.append((cursor, min(start - 1, upper)))
            cursor = max(cursor, end + 1)
            if cursor > upper:
                break
        if cursor <= upper:
            remaining.append((cursor, upper))
    return tuple(remaining)


@dataclass(frozen=True)
class _CharacterSet:
    intervals: Tuple[Tuple[int, int], ...]

    def contains(self, character: str) -> bool:
        codepoint = ord(character)
        return any(start <= codepoint <= end for start, end in self.intervals)

    def intersects(self, other: "_CharacterSet") -> bool:
        left = right = 0
        while left < len(self.intervals) and right < len(other.intervals):
            first, second = self.intervals[left], other.intervals[right]
            if max(first[0], second[0]) <= min(first[1], second[1]):
                return True
            if first[1] < second[1]:
                left += 1
            else:
                right += 1
        return False


_ANY_CHARACTER = _CharacterSet(_UNIVERSE_INTERVALS)


@dataclass(frozen=True)
class _SegmentToken:
    star: bool
    characters: _CharacterSet = _ANY_CHARACTER


@dataclass(frozen=True)
class _SegmentPattern:
    tokens: Tuple[_SegmentToken, ...]

    def matches(self, value: str) -> bool:
        states = self._epsilon_closure({0})
        for character in value:
            next_states = set()
            for index in states:
                if index >= len(self.tokens):
                    continue
                token = self.tokens[index]
                if token.star:
                    next_states.add(index)
                elif token.characters.contains(character):
                    next_states.add(index + 1)
            states = self._epsilon_closure(next_states)
        return len(self.tokens) in self._epsilon_closure(states)

    def intersects(self, other: "_SegmentPattern") -> bool:
        pending = [(0, 0)]
        visited = set()
        while pending:
            left, right = pending.pop()
            if (left, right) in visited:
                continue
            visited.add((left, right))
            if left == len(self.tokens) and right == len(other.tokens):
                return True
            if left < len(self.tokens) and self.tokens[left].star:
                pending.append((left + 1, right))
            if right < len(other.tokens) and other.tokens[right].star:
                pending.append((left, right + 1))
            if left >= len(self.tokens) or right >= len(other.tokens):
                continue
            first, second = self.tokens[left], other.tokens[right]
            if first.characters.intersects(second.characters):
                pending.append((
                    left if first.star else left + 1,
                    right if second.star else right + 1,
                ))
        return False

    def _epsilon_closure(self, states: set) -> set:
        closure = set(states)
        pending = list(states)
        while pending:
            index = pending.pop()
            if index < len(self.tokens) and self.tokens[index].star and index + 1 not in closure:
                closure.add(index + 1)
                pending.append(index + 1)
        return closure


@dataclass(frozen=True)
class ParsedGlob:
    normalized: str
    segments: Tuple[Any, ...]

    def matches(self, path: str) -> bool:
        concrete = normalize_path(path).split("/")
        states = self._recursive_closure({0})
        for segment in concrete:
            next_states = set()
            for index in states:
                if index >= len(self.segments):
                    continue
                pattern = self.segments[index]
                if pattern is None:
                    next_states.add(index)
                elif pattern.matches(segment):
                    next_states.add(index + 1)
            states = self._recursive_closure(next_states)
        return len(self.segments) in self._recursive_closure(states)

    def intersects(self, other: "ParsedGlob") -> bool:
        pending = [(0, 0)]
        visited = set()
        while pending:
            left, right = pending.pop()
            if (left, right) in visited:
                continue
            visited.add((left, right))
            if left == len(self.segments) and right == len(other.segments):
                return True
            left_recursive = left < len(self.segments) and self.segments[left] is None
            right_recursive = right < len(other.segments) and other.segments[right] is None
            if left_recursive:
                pending.append((left + 1, right))
            if right_recursive:
                pending.append((left, right + 1))
            if left >= len(self.segments) or right >= len(other.segments):
                continue
            if (
                left_recursive or right_recursive
                or self.segments[left].intersects(other.segments[right])
            ):
                pending.append((
                    left if left_recursive else left + 1,
                    right if right_recursive else right + 1,
                ))
        return False

    def _recursive_closure(self, states: set) -> set:
        closure = set(states)
        pending = list(states)
        while pending:
            index = pending.pop()
            if index < len(self.segments) and self.segments[index] is None and index + 1 not in closure:
                closure.add(index + 1)
                pending.append(index + 1)
        return closure


def _parse_character_class(segment: str, index: int) -> Tuple[_SegmentToken, int]:
    end = segment.find("]", index + 1)
    if end < 0:
        raise PathInputError("unterminated glob character class")
    body = segment[index + 1:end]
    negated = body.startswith("!")
    if negated:
        body = body[1:]
    if not body or body.startswith("^"):
        raise PathInputError("empty or unsupported glob character class")
    intervals = []
    cursor = 0
    while cursor < len(body):
        character = body[cursor]
        if character in "[]/\\\x00" or character == "-":
            raise PathInputError("unsupported glob character class member")
        start = end_codepoint = ord(character)
        if cursor + 1 < len(body) and body[cursor + 1] == "-":
            if cursor + 2 >= len(body):
                raise PathInputError("unterminated glob character range")
            range_end = body[cursor + 2]
            if range_end in "[]/\\\x00-" or ord(range_end) < start:
                raise PathInputError("invalid glob character range")
            end_codepoint = ord(range_end)
            if any(start <= excluded <= end_codepoint for excluded in (0, 47, 92)):
                raise PathInputError("glob range includes an invalid path character")
            cursor += 2
        intervals.append((start, end_codepoint))
        cursor += 1
    normalized = _merge_intervals(intervals)
    if negated:
        normalized = _subtract_intervals(_UNIVERSE_INTERVALS, normalized)
    if not normalized:
        raise PathInputError("glob character class matches no valid character")
    return _SegmentToken(False, _CharacterSet(normalized)), end + 1


def _parse_segment(segment: str) -> _SegmentPattern:
    tokens = []
    index = 0
    while index < len(segment):
        character = segment[index]
        if character == "*":
            tokens.append(_SegmentToken(True))
            index += 1
        elif character == "?":
            tokens.append(_SegmentToken(False, _ANY_CHARACTER))
            index += 1
        elif character == "[":
            token, index = _parse_character_class(segment, index)
            tokens.append(token)
        else:
            tokens.append(_SegmentToken(False, _CharacterSet(((ord(character), ord(character)),))))
            index += 1
    return _SegmentPattern(tuple(tokens))


def parse_glob(pattern: str) -> ParsedGlob:
    """Parse the one supported glob grammar used for matching and intersection."""

    normalized = normalize_path(pattern, allow_glob=True)
    parsed = []
    for segment in normalized.split("/"):
        if segment == "**":
            parsed.append(None)
            continue
        if "**" in segment:
            raise PathInputError("recursive wildcard must occupy a complete path segment")
        parsed.append(_parse_segment(segment))
    return ParsedGlob(normalized, tuple(parsed))


def path_matches(path: str, pattern: str) -> bool:
    """Match using the same parsed glob automaton used for intersection."""

    return parse_glob(pattern).matches(path)


def patterns_overlap(left: str, right: str) -> bool:
    """Conservatively determine intersection using the shared parsed grammar."""

    return parse_glob(left).intersects(parse_glob(right))


def _policy_patterns(policy: Mapping[str, Any]) -> Tuple[Tuple[str, ...], Tuple[Mapping[str, Any], ...]]:
    if not isinstance(policy, Mapping):
        raise PathInputError("policy must be an object")
    tier_two = normalize_paths(policy.get("tier_2_paths", []), allow_glob=True)
    for pattern in tier_two:
        parse_glob(pattern)
    domains = policy.get("semantic_domains", [])
    if not isinstance(domains, list):
        raise PathInputError("semantic domains must be an array")
    normalized_domains = []
    for domain in domains:
        if not isinstance(domain, Mapping):
            raise PathInputError("semantic domains must be objects")
        patterns = normalize_paths(domain.get("paths", []), allow_glob=True)
        for pattern in patterns:
            parse_glob(pattern)
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
            parse_glob(pattern)
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


def _patterns_overlap(left: str, right: str) -> bool:
    return patterns_overlap(left, right)


def _paths_overlap(left: Sequence[str], right: Sequence[str]) -> bool:
    return any(patterns_overlap(first, second) for first in left for second in right)


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
    evidence_verifier: Any,
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
                parse_glob(pattern)
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
            and verify_record_evidence(
                record, "coordination", evidence_verifier,
                repository=repository, actor=issuer, head_sha=head_sha,
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
    evidence_verifier: Any = None,
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
                parse_glob(pattern)
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
            now=now, evidence_verifier=evidence_verifier,
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
