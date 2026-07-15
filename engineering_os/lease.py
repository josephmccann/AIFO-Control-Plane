"""Pure mission lease decisions over an authenticated event history."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


@dataclass(frozen=True)
class LeaseDecision:
    allowed: bool
    code: str
    event: Optional[Dict[str, Any]] = None
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
    expires_at: datetime
    expires_at_text: str
    paths: Tuple[str, ...]


def _timestamp(value: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("timestamp must be a non-empty UTC RFC3339 string")
    text = value.strip()
    parsed = datetime.fromisoformat(text[:-1] + "+00:00" if text.endswith("Z") else text)
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError("timestamp must identify UTC explicitly")
    return parsed.astimezone(timezone.utc)


def _rfc3339(value: str) -> str:
    return _timestamp(value).isoformat(timespec="seconds").replace("+00:00", "Z")


def _event_lease(event: Mapping[str, Any]) -> Optional[_Lease]:
    details = event.get("details")
    if not isinstance(details, Mapping):
        return None
    try:
        mission_id = event["mission_id"]
        owner = details["lease_owner"]
        nonce = details["lease_nonce"]
        expiry_text = _rfc3339(details["lease_expires_at"])
        paths = details.get("paths", [])
        if not all(isinstance(value, str) and value for value in (mission_id, owner, nonce)):
            return None
        if not isinstance(paths, list) or any(not isinstance(path, str) or not path for path in paths):
            return None
        return _Lease(
            mission_id, owner, nonce, _timestamp(expiry_text), expiry_text, tuple(paths)
        )
    except (KeyError, TypeError, ValueError):
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
                    mission_id, lease.owner, lease.nonce, new_expiry,
                    new_expiry_text, lease.paths,
                )
        elif event_type == "lease.released" and mission_id in active:
            lease = active[mission_id]
            details = event.get("details", {})
            normal_release = (
                event.get("actor") == lease.owner
                and details.get("lease_owner") == lease.owner
                and details.get("lease_nonce") == lease.nonce
            )
            try:
                occurred_at = _timestamp(event["occurred_at"])
            except (KeyError, TypeError, ValueError):
                continue
            recovery_release = (
                details.get("recovery") is True
                and event.get("actor_role") == "system"
                and details.get("lease_owner") == lease.owner
                and details.get("lease_nonce") == lease.nonce
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
    paths: Sequence[str],
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
    if not isinstance(paths, (list, tuple)) or not paths or any(not isinstance(path, str) or not path for path in paths):
        return _deny("LEASE_PATHS_INVALID")

    history = list(events)
    active = _active_leases(history)
    current = active.get(mission_id)
    if current is not None:
        if current.nonce == nonce:
            return _deny("LEASE_NONCE_REUSED", mission_id=mission_id, nonce=nonce)
        code = "LEASE_ALREADY_CLAIMED" if _timestamp(now_text) < current.expires_at else "LEASE_RECOVERY_REQUIRED"
        return _deny(code, mission_id=mission_id, lease_owner=current.owner)
    if any(
        event.get("details", {}).get("lease_nonce") == nonce
        for event in history if isinstance(event, Mapping) and isinstance(event.get("details"), Mapping)
    ):
        return _deny("LEASE_NONCE_REUSED", nonce=nonce)
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
            "lease_owner": owner.strip(), "lease_nonce": nonce.strip(),
            "lease_expires_at": expiry_text, "paths": list(paths),
        },
    }
    return LeaseDecision(True, "LEASE_CLAIM_ALLOWED", event=event)


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
    if nonce != lease.nonce:
        return _deny("LEASE_NONCE_MISMATCH")
    if _timestamp(now_text) >= lease.expires_at:
        return _deny("LEASE_EXPIRED", expires_at=lease.expires_at_text)
    if _timestamp(expiry_text) <= lease.expires_at:
        return _deny("LEASE_EXTENSION_INVALID", current_expires_at=lease.expires_at_text)
    event = {
        "mission_id": mission_id, "type": "lease.heartbeat", "actor": owner,
        "actor_role": "producer", "occurred_at": now_text,
        "details": {
            "lease_owner": owner, "lease_nonce": nonce,
            "lease_expires_at": expiry_text,
        },
    }
    return LeaseDecision(True, "LEASE_HEARTBEAT_ALLOWED", event=event)


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
    if nonce != lease.nonce:
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
    event = {
        "mission_id": mission_id, "type": "lease.released", "actor": owner,
        "actor_role": actor_role, "occurred_at": now_text,
        "details": {
            "lease_owner": lease.owner, "lease_nonce": lease.nonce,
            "recovery": recovery, "recommended_action": "Parked" if recovery else "Ready",
        },
    }
    return LeaseDecision(True, "LEASE_RELEASE_ALLOWED", event=event)


def find_orphans(events: Iterable[Mapping[str, Any]], *, now: str) -> List[OrphanedLease]:
    """Return expired active leases; discovery never releases or parks a mission."""

    try:
        observed_at = _timestamp(now)
    except (TypeError, ValueError):
        return []
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
