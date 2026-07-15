"""Deny-by-default mission state projection and transition authorization."""

from dataclasses import dataclass, field, replace
from typing import Any, Dict, Iterable, Mapping, Tuple

from .errors import Violation


@dataclass(frozen=True)
class Decision:
    allowed: bool
    code: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MissionProjection:
    state: str = "Proposed"
    remediation_cycles: int = 0
    history: Tuple[str, ...] = ()
    violations: Tuple[Violation, ...] = ()


TRANSITIONS = {
    "mission.ready": ({"Proposed", "Parked"}, "Ready", {"producer", "founder"}),
    "mission.recovered": ({"Parked"}, "Ready", {"founder"}),
    "mission.claimed": ({"Ready"}, "Claimed", {"producer"}),
    "mission.started": ({"Claimed"}, "In Progress", {"producer"}),
    "review.requested": ({"In Progress"}, "Adversarial Review", {"producer"}),
    "finding.valid": ({"Adversarial Review"}, "In Progress", {"adversary"}),
    "review.passed": ({"Adversarial Review"}, "Founder Approval", {"adversary"}),
    "approval.granted": ({"Founder Approval"}, "Merge Authorized", {"founder"}),
    "mission.merged": ({"Merge Authorized"}, "Merged", {"founder"}),
    "verification.passed": ({"Merged"}, "Verified", {"adversary", "founder"}),
    "mission.closed": ({"Verified"}, "Closed", {"founder"}),
    "mission.parked": (
        {"Proposed", "Ready", "Claimed", "In Progress", "Adversarial Review", "Founder Approval"},
        "Parked",
        {"producer", "adversary", "founder"},
    ),
    "mission.cancelled": (
        {"Proposed", "Ready", "Claimed", "In Progress", "Adversarial Review", "Founder Approval"},
        "Cancelled",
        {"founder"},
    ),
    "incident.opened": ({"Merged", "Verified", "Closed"}, "Incident", {"producer", "adversary", "founder"}),
    "incident.verified": ({"Incident"}, "Verified", {"adversary", "founder"}),
    "incident.closed": ({"Incident"}, "Closed", {"founder"}),
}


def authorize_transition(projection: MissionProjection, event: Mapping[str, Any], policy: Mapping[str, Any]) -> Decision:
    """Authorize a single event without mutating projection or external state."""

    event_type = event.get("type")
    rule = TRANSITIONS.get(event_type)
    if rule is None:
        return Decision(False, "STATE_EVENT_UNKNOWN", {"event_type": event_type, "state": projection.state})
    sources, target, default_roles = rule
    if projection.state not in sources:
        return Decision(False, "STATE_TRANSITION_DENIED", {
            "event_type": event_type,
            "from_state": projection.state,
            "allowed_from": sorted(sources),
        })
    configured = policy.get("transition_roles", {}) if isinstance(policy, Mapping) else {}
    roles = set(configured.get(event_type, default_roles)) if isinstance(configured, Mapping) else set(default_roles)
    role = event.get("actor_role")
    if role not in roles:
        return Decision(False, "STATE_ROLE_DENIED", {
            "event_type": event_type,
            "actor_role": role,
            "allowed_roles": sorted(roles),
        })
    return Decision(True, "STATE_TRANSITION_ALLOWED", {
        "event_type": event_type,
        "from_state": projection.state,
        "to_state": target,
    })


def project_state(events: Iterable[Mapping[str, Any]], policy: Mapping[str, Any] = None) -> MissionProjection:
    """Fold authenticated events into a projection, preserving denied input diagnostics."""

    effective_policy = policy or {}
    projection = MissionProjection()
    for event in events:
        decision = authorize_transition(projection, event, effective_policy)
        if not decision.allowed:
            violation = Violation(decision.code, "mission event was denied", "$.events", decision.details)
            projection = replace(projection, violations=projection.violations + (violation,))
            continue
        cycles = projection.remediation_cycles + (1 if event.get("type") == "finding.valid" else 0)
        projection = replace(
            projection,
            state=decision.details["to_state"],
            remediation_cycles=cycles,
            history=projection.history + (str(event.get("type")),),
        )
    return projection
