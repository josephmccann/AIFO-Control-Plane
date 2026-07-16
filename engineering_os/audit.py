"""Canonical audit-event normalization and hash-chain validation."""

from dataclasses import dataclass
import re
from typing import Any, Dict, Mapping, Optional, Sequence

from .canonical import content_sha256
from .schema import validate_document


_TIMESTAMP = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z"
)
_PROPOSAL_FIELDS = frozenset((
    "schema_version", "mission_id", "type", "details", "actor", "actor_role",
    "occurred_at", "source_url",
))
_SOURCE_FIELDS = frozenset((
    "actor", "actor_role", "occurred_at", "source_url",
))


@dataclass(frozen=True)
class AuditDecision:
    allowed: bool
    code: str
    head_hash: Optional[str] = None


def normalize_audit_event(
    proposal: Mapping[str, Any],
    authenticated_source: Mapping[str, Any],
    *,
    sequence: int,
    previous_event_hash: Optional[str],
) -> Dict[str, Any]:
    """Bind a proposal to adapter-owned actor, role, time, and source metadata."""

    if (
        not isinstance(proposal, Mapping)
        or set(proposal) - _PROPOSAL_FIELDS
        or set(proposal) < {"schema_version", "mission_id", "type", "details"}
        or proposal.get("schema_version") != "1.0.0"
        or not isinstance(proposal.get("mission_id"), str)
        or not proposal.get("mission_id")
        or not isinstance(proposal.get("type"), str)
        or not proposal.get("type")
        or not isinstance(proposal.get("details"), dict)
        or not isinstance(authenticated_source, Mapping)
        or set(authenticated_source) != _SOURCE_FIELDS
        or not isinstance(sequence, int)
        or isinstance(sequence, bool)
        or sequence < 1
        or (
            previous_event_hash is not None
            and (
                not isinstance(previous_event_hash, str)
                or re.fullmatch(r"[0-9a-f]{64}", previous_event_hash) is None
            )
        )
    ):
        raise ValueError("audit proposal or chain binding is invalid")
    actor = authenticated_source.get("actor")
    actor_role = authenticated_source.get("actor_role")
    occurred_at = authenticated_source.get("occurred_at")
    source_url = authenticated_source.get("source_url")
    if (
        not isinstance(actor, str) or not actor
        or actor_role not in ("producer", "adversary", "founder", "system")
        or not isinstance(occurred_at, str)
        or _TIMESTAMP.fullmatch(occurred_at) is None
        or not isinstance(source_url, str)
        or not source_url.startswith("https://github.com/")
    ):
        raise ValueError("authenticated audit source is invalid")
    event = {
        "schema_version": "1.0.0",
        "mission_id": proposal["mission_id"],
        "sequence": sequence,
        "type": proposal["type"],
        "actor": actor,
        "actor_role": actor_role,
        "occurred_at": occurred_at,
        "source_url": source_url,
        "previous_event_hash": previous_event_hash,
        "event_hash": "0" * 64,
        "details": dict(proposal["details"]),
    }
    event["event_hash"] = content_sha256(event)
    if validate_document("audit-event", event):
        raise ValueError("normalized audit event is invalid")
    return event


def validate_audit_chain(events: Sequence[Mapping[str, Any]]) -> AuditDecision:
    """Validate exact ordering, mission identity, and complete hash linkage."""

    if not isinstance(events, (list, tuple)):
        return AuditDecision(False, "AUDIT_CHAIN_INVALID")
    previous = None
    mission_id = None
    for index, event in enumerate(events, start=1):
        if not isinstance(event, Mapping) or validate_document(
            "audit-event", dict(event)
        ):
            return AuditDecision(False, "AUDIT_SCHEMA_INVALID")
        if event.get("sequence") != index:
            return AuditDecision(False, "AUDIT_SEQUENCE_INVALID")
        if mission_id is None:
            mission_id = event.get("mission_id")
        elif event.get("mission_id") != mission_id:
            return AuditDecision(False, "AUDIT_MISSION_MISMATCH")
        if event.get("previous_event_hash") != previous:
            return AuditDecision(False, "AUDIT_PREVIOUS_HASH_INVALID")
        if event.get("event_hash") != content_sha256(event):
            return AuditDecision(False, "AUDIT_EVENT_HASH_INVALID")
        previous = event["event_hash"]
    return AuditDecision(True, "AUDIT_CHAIN_VALID", previous)
