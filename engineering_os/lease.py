"""Pure mission lease decisions over an authenticated event history."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import PurePosixPath
import re
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .errors import EngineeringOSError


class LeaseInputError(EngineeringOSError):
    """Fail-closed lease input error with a stable machine code."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class LeaseDecision:
    allowed: bool
    code: str
    event: Optional[Dict[str, Any]] = None
    events: Tuple[Dict[str, Any], ...] = ()
    preserve_state: bool = True
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OrphanedLease:
    mission_id: str
    owner: str
    nonce: str
    expires_at: str
    paths: Tuple[str, ...]
    preserve_state: bool = True
    recommended_action: str = "Parked"


@dataclass(frozen=True)
class _Lease:
    mission_id: str
    owner: str
    nonce: str
    lease_start: datetime
    lease_start_text: str
    expires_at: datetime
    expires_at_text: str
    wall_clock_cap_minutes: int
    paths: Tuple[str, ...]


def _timestamp(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("timestamp must be a non-empty UTC RFC3339 string")
    text = value.strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z", text) is None:
        raise ValueError("timestamp must be strict UTC RFC3339 with a Z suffix")
    return datetime.fromisoformat(text[:-1] + "+00:00").astimezone(timezone.utc)


def _rfc3339(value: str) -> str:
    _timestamp(value)
    return value.strip()


def _event_lease(event: Mapping[str, Any]) -> Optional[_Lease]:
    details = event.get("details")
    if not isinstance(details, Mapping):
        return None
    try:
        mission_id = event["mission_id"]
        owner = details["lease_owner"]
        nonce = details["lease_nonce"].strip()
        lease_start_text = _rfc3339(details["lease_start"])
        expiry_text = _rfc3339(details["lease_expires_at"])
        wall_clock_cap_minutes = details["wall_clock_cap_minutes"]
        paths = details.get("paths", [])
        if not all(isinstance(value, str) and value for value in (mission_id, owner, nonce)):
            return None
        if (
            not isinstance(wall_clock_cap_minutes, int)
            or isinstance(wall_clock_cap_minutes, bool)
            or wall_clock_cap_minutes <= 0
        ):
            return None
        lease_start = _timestamp(lease_start_text)
        expiry = _timestamp(expiry_text)
        if expiry <= lease_start or expiry > lease_start + timedelta(minutes=wall_clock_cap_minutes):
            return None
        if not isinstance(paths, list) or any(not isinstance(path, str) or not path for path in paths):
            return None
        return _Lease(
            mission_id, owner, nonce, lease_start, lease_start_text,
            expiry, expiry_text, wall_clock_cap_minutes, tuple(paths)
        )
    except (AttributeError, KeyError, TypeError, ValueError):
        return None


def _active_leases(events: Iterable[Mapping[str, Any]]) -> Dict[str, _Lease]:
    """Replay only internally valid lease events; first concurrent claim wins."""

    active: Dict[str, _Lease] = {}
    for event in events:
        if not isinstance(event, Mapping):
            continue
        event_type = event.get("type")
        mission_id = event.get("mission_id")
        if not isinstance(mission_id, str):
            continue
        if event_type == "mission.claimed":
            lease = _event_lease(event)
            if lease is not None and event.get("actor_role") == "producer" and mission_id not in active:
                active[mission_id] = lease
        elif event_type == "lease.heartbeat" and mission_id in active:
            lease = active[mission_id]
            details = event.get("details", {})
            try:
                occurred_at = _timestamp(event["occurred_at"])
                new_expiry_text = _rfc3339(details["lease_expires_at"])
                new_expiry = _timestamp(new_expiry_text)
            except (KeyError, TypeError, ValueError):
                continue
            if (
                details.get("lease_owner") == lease.owner
                and details.get("lease_nonce") == lease.nonce
                and event.get("actor") == lease.owner
                and occurred_at < lease.expires_at
                and new_expiry > occurred_at
                and new_expiry > lease.expires_at
            ):
                active[mission_id] = _Lease(
                    mission_id, lease.owner, lease.nonce,
                    lease.lease_start, lease.lease_start_text,
                    new_expiry, new_expiry_text,
                    lease.wall_clock_cap_minutes, lease.paths,
                )
        elif event_type == "mission.released" and mission_id in active:
            lease = active[mission_id]
            details = event.get("details", {})
            normal_release = (
                event.get("actor") == lease.owner
                and details.get("lease_owner") == lease.owner
                and str(details.get("lease_nonce", "")).strip() == lease.nonce
            )
            try:
                occurred_at = _timestamp(event["occurred_at"])
            except (KeyError, TypeError, ValueError):
                continue
            recovery_release = (
                details.get("recovery") is True
                and event.get("actor_role") == "system"
                and details.get("lease_owner") == lease.owner
                and str(details.get("lease_nonce", "")).strip() == lease.nonce
                and occurred_at >= lease.expires_at
            )
            if normal_release or recovery_release:
                del active[mission_id]
    return active


def _paths_conflict(left: Sequence[str], right: Sequence[str]) -> bool:
    def literal_prefix(pattern: str) -> str:
        wildcard = min((pattern.find(char) for char in "*[?" if char in pattern), default=len(pattern))
        return pattern[:wildcard].rstrip("/")

    for first in left:
        for second in right:
            if first == second:
                return True
            first_literal = not any(char in first for char in "*[?")
            second_literal = not any(char in second for char in "*[?")
            if first_literal and PurePosixPath(first).match(second):
                return True
            if second_literal and PurePosixPath(second).match(first):
                return True
            first_prefix = literal_prefix(first)
            second_prefix = literal_prefix(second)
            if not first_literal and not second_literal and (not first_prefix or not second_prefix):
                return True
            if first_prefix and second_prefix and (
                first_prefix == second_prefix
                or first_prefix.startswith(second_prefix + "/")
                or second_prefix.startswith(first_prefix + "/")
            ):
                return True
    return False


def _deny(code: str, **details: Any) -> LeaseDecision:
    return LeaseDecision(False, code, details=details)


def claim_mission(
    events: Iterable[Mapping[str, Any]], *, mission_id: str, owner: str,
    actor_role: str, now: str, expires_at: str, nonce: str,
    paths: Sequence[str], wall_clock_minutes: int,
) -> LeaseDecision:
    """Propose one producer claim without mutating history or mission state."""

    try:
        now_text = _rfc3339(now)
        expiry_text = _rfc3339(expires_at)
        if _timestamp(expiry_text) <= _timestamp(now_text):
            return _deny("LEASE_EXPIRY_INVALID", expires_at=expiry_text, now=now_text)
    except (TypeError, ValueError):
        return _deny("LEASE_TIMESTAMP_INVALID")
    if actor_role != "producer":
        return _deny("LEASE_ROLE_DENIED", actor_role=actor_role)
    if not all(isinstance(value, str) and value.strip() for value in (mission_id, owner, nonce)):
        return _deny("LEASE_INPUT_INVALID")
    if not isinstance(wall_clock_minutes, int) or isinstance(wall_clock_minutes, bool) or wall_clock_minutes <= 0:
        return _deny("LEASE_WALL_CLOCK_CAP_INVALID")
    if _timestamp(expiry_text) > _timestamp(now_text) + timedelta(minutes=wall_clock_minutes):
        return _deny("LEASE_WALL_CLOCK_CAP_EXCEEDED")
    if not isinstance(paths, (list, tuple)) or not paths or any(not isinstance(path, str) or not path for path in paths):
        return _deny("LEASE_PATHS_INVALID")

    history = list(events)
    normalized_nonce = nonce.strip()
    active = _active_leases(history)
    current = active.get(mission_id)
    if current is not None:
        if current.nonce == normalized_nonce:
            return _deny("LEASE_NONCE_REUSED", mission_id=mission_id, nonce=normalized_nonce)
        code = "LEASE_ALREADY_CLAIMED" if _timestamp(now_text) < current.expires_at else "LEASE_RECOVERY_REQUIRED"
        return _deny(code, mission_id=mission_id, lease_owner=current.owner)
    if any(
        str(event.get("details", {}).get("lease_nonce", "")).strip() == normalized_nonce
        for event in history if isinstance(event, Mapping) and isinstance(event.get("details"), Mapping)
    ):
        return _deny("LEASE_NONCE_REUSED", nonce=normalized_nonce)
    for other in active.values():
        if other.mission_id != mission_id and _paths_conflict(paths, other.paths):
            return _deny(
                "LEASE_PATH_CONFLICT", conflicting_mission_id=other.mission_id,
                conflicting_paths=list(other.paths),
            )
    event = {
        "mission_id": mission_id,
        "type": "mission.claimed",
        "actor": owner.strip(),
        "actor_role": "producer",
        "occurred_at": now_text,
        "details": {
            "lease_owner": owner.strip(), "lease_nonce": normalized_nonce,
            "lease_start": now_text, "lease_expires_at": expiry_text,
            "wall_clock_cap_minutes": wall_clock_minutes, "paths": list(paths),
        },
    }
    return LeaseDecision(True, "LEASE_CLAIM_ALLOWED", event=event, events=(event,))


def heartbeat_lease(
    events: Iterable[Mapping[str, Any]], *, mission_id: str, owner: str,
    now: str, expires_at: str, nonce: str,
) -> LeaseDecision:
    """Propose a lease extension after exact owner, nonce, and expiry checks."""

    try:
        now_text = _rfc3339(now)
        expiry_text = _rfc3339(expires_at)
    except (TypeError, ValueError):
        return _deny("LEASE_TIMESTAMP_INVALID")
    lease = _active_leases(events).get(mission_id)
    if lease is None:
        return _deny("LEASE_NOT_FOUND", mission_id=mission_id)
    if owner != lease.owner:
        return _deny("LEASE_OWNER_MISMATCH", expected=lease.owner, actual=owner)
    if not isinstance(nonce, str) or nonce.strip() != lease.nonce:
        return _deny("LEASE_NONCE_MISMATCH")
    if _timestamp(now_text) >= lease.expires_at:
        return _deny("LEASE_EXPIRED", expires_at=lease.expires_at_text)
    if _timestamp(expiry_text) <= lease.expires_at:
        return _deny("LEASE_EXTENSION_INVALID", current_expires_at=lease.expires_at_text)
    if _timestamp(expiry_text) > lease.lease_start + timedelta(minutes=lease.wall_clock_cap_minutes):
        return _deny("LEASE_WALL_CLOCK_CAP_EXCEEDED", lease_start=lease.lease_start_text)
    event = {
        "mission_id": mission_id, "type": "lease.heartbeat", "actor": owner,
        "actor_role": "producer", "occurred_at": now_text,
        "details": {
            "lease_owner": owner, "lease_nonce": nonce.strip(),
            "lease_start": lease.lease_start_text,
            "lease_expires_at": expiry_text,
            "wall_clock_cap_minutes": lease.wall_clock_cap_minutes,
        },
    }
    return LeaseDecision(True, "LEASE_HEARTBEAT_ALLOWED", event=event, events=(event,))


def release_mission(
    events: Iterable[Mapping[str, Any]], *, mission_id: str, owner: str,
    now: str, nonce: str, recovery: bool = False,
) -> LeaseDecision:
    """Propose owner release, or system recovery of an explicitly expired lease."""

    try:
        now_text = _rfc3339(now)
    except (TypeError, ValueError):
        return _deny("LEASE_TIMESTAMP_INVALID")
    lease = _active_leases(events).get(mission_id)
    if lease is None:
        return _deny("LEASE_NOT_FOUND", mission_id=mission_id)
    if not isinstance(nonce, str) or nonce.strip() != lease.nonce:
        return _deny("LEASE_NONCE_MISMATCH")
    if recovery:
        if owner != "system":
            return _deny("LEASE_RECOVERY_ROLE_DENIED")
        if _timestamp(now_text) < lease.expires_at:
            return _deny("LEASE_NOT_EXPIRED", expires_at=lease.expires_at_text)
        actor_role = "system"
    else:
        if owner != lease.owner:
            return _deny("LEASE_OWNER_MISMATCH", expected=lease.owner, actual=owner)
        actor_role = "producer"
    released = {
        "mission_id": mission_id, "type": "mission.released", "actor": owner,
        "actor_role": actor_role, "occurred_at": now_text,
        "details": {
            "lease_owner": lease.owner, "lease_nonce": lease.nonce,
            "recovery": recovery, "recommended_action": "Parked" if recovery else "Ready",
        },
    }
    if recovery:
        recovery_details = {
            "lease_owner": lease.owner, "lease_nonce": lease.nonce,
            "lease_start": lease.lease_start_text,
            "lease_expires_at": lease.expires_at_text,
            "recovery": True, "recommended_action": "Parked",
        }
        orphaned = {
            "mission_id": mission_id, "type": "mission.orphaned", "actor": owner,
            "actor_role": "system", "occurred_at": now_text,
            "details": dict(recovery_details),
        }
        released["details"] = dict(recovery_details)
        return LeaseDecision(
            True, "LEASE_RELEASE_ALLOWED", event=released,
            events=(orphaned, released),
        )
    return LeaseDecision(True, "LEASE_RELEASE_ALLOWED", event=released, events=(released,))


def find_orphans(events: Iterable[Mapping[str, Any]], *, now: str) -> List[OrphanedLease]:
    """Return expired active leases; discovery never releases or parks a mission."""

    try:
        observed_at = _timestamp(now)
    except (TypeError, ValueError) as error:
        raise LeaseInputError(
            "LEASE_TIMESTAMP_INVALID",
            "orphan observation time must be strict UTC RFC3339",
        ) from error
    return sorted(
        (
            OrphanedLease(
                lease.mission_id, lease.owner, lease.nonce,
                lease.expires_at_text, lease.paths,
            )
            for lease in _active_leases(events).values()
            if observed_at >= lease.expires_at
        ),
        key=lambda orphan: orphan.mission_id,
    )
