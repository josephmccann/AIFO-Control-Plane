"""Incident linkage and rollback/recovery validation."""

from dataclasses import dataclass
from typing import Mapping

from .schema import validate_document


_ROLLBACKS = frozenset((
    "clean_revert", "forward_fix", "point_in_time_restore",
    "data_migration_recovery", "irreversible",
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
    recovery_authorized: bool,
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
    if recovery_authorized is not True:
        return IncidentDecision(False, "INCIDENT_RECOVERY_AUTHORITY_REQUIRED")
    if (
        not incident.get("kill_switch")
        or not incident.get("recovery_actions")
        or not incident.get("verification")
    ):
        return IncidentDecision(False, "INCIDENT_RECOVERY_INCOMPLETE")
    return IncidentDecision(True, "INCIDENT_VALID")
