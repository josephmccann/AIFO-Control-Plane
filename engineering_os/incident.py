"""Incident linkage and rollback/recovery validation."""

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .authority import validate_authority
from .schema import validate_document


_ROLLBACKS = frozenset((
    "clean_revert", "forward_fix", "point_in_time_restore",
    "data_migration_recovery", "irreversible",
))
_RECOVERY_ACTIONS = frozenset((
    "write", "merge", "deploy", "cloud_mutation", "secrets",
    "customer_data", "spend", "cutover",
))


@dataclass(frozen=True)
class IncidentDecision:
    allowed: bool
    code: str


def validate_incident(
    incident: Mapping,
    *,
    origin_mission_id: str,
    repository: str,
    pull_request: int,
    rollback_class: str,
    mission: Mapping,
    policy: Mapping,
    changed_files: Sequence[str],
    authority_records: Sequence[Mapping],
    recovery_action: str,
    head_sha: str,
    now: str,
    subject: str,
    evidence_verifier: Any,
    consumption_store: str,
) -> IncidentDecision:
    if not isinstance(incident, Mapping) or validate_document(
        "incident", dict(incident)
    ):
        return IncidentDecision(False, "INCIDENT_SCHEMA_INVALID")
    if (
        incident.get("origin_mission_id") != origin_mission_id
        or incident.get("repository") != repository
        or incident.get("pull_request") != pull_request
    ):
        return IncidentDecision(False, "INCIDENT_ORIGIN_MISMATCH")
    if rollback_class not in _ROLLBACKS:
        return IncidentDecision(False, "INCIDENT_ROLLBACK_INVALID")
    if (
        not incident.get("kill_switch")
        or not incident.get("recovery_actions")
        or not incident.get("verification")
    ):
        return IncidentDecision(False, "INCIDENT_RECOVERY_INCOMPLETE")
    if (
        not isinstance(mission, Mapping)
        or mission.get("mission_id") != origin_mission_id
        or mission.get("repository") != repository
        or recovery_action not in _RECOVERY_ACTIONS
        or not isinstance(authority_records, (list, tuple))
        or not authority_records
    ):
        return IncidentDecision(False, "INCIDENT_RECOVERY_AUTHORITY_REQUIRED")
    authority = validate_authority(
        mission,
        policy,
        changed_files,
        authority_records,
        action=recovery_action,
        pull_request=pull_request,
        head_sha=head_sha,
        now=now,
        subject=subject,
        evidence_verifier=evidence_verifier,
        consumption_store=consumption_store,
    )
    if not authority.allowed:
        return IncidentDecision(False, "INCIDENT_RECOVERY_AUTHORITY_REQUIRED")
    return IncidentDecision(True, "INCIDENT_VALID")
