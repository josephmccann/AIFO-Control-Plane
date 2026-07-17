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
    "mission.ready": ({"Proposed"}, "Ready", {"producer", "founder"}),
    "mission.recovered": ({"Parked"}, "Ready", {"founder"}),
    "mission.claimed": ({"Ready"}, "Claimed", {"producer"}),
    "lease.heartbeat": (
        {"Claimed", "In Progress", "Adversarial Review", "Founder Approval"},
        "__PRESERVE__",
        {"producer"},
    ),
    "mission.orphaned": (
        {"Claimed", "In Progress", "Adversarial Review", "Founder Approval"},
        "Parked",
        {"system"},
    ),
    "mission.released": (
        {"Claimed", "In Progress", "Adversarial Review", "Founder Approval", "Parked"},
        "Ready",
        {"producer", "system"},
    ),
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
    if not isinstance(policy, Mapping):
        return Decision(False, "STATE_POLICY_INVALID", {"reason": "policy must be an object"})
    configured = policy.get("transition_roles", {})
    if not isinstance(configured, Mapping):
        return Decision(False, "STATE_POLICY_INVALID", {"reason": "transition_roles must be an object"})
    normalized_roles = {}
    for configured_event, configured_value in configured.items():
        configured_rule = TRANSITIONS.get(configured_event)
        if configured_rule is None:
            return Decision(False, "STATE_POLICY_INVALID", {
                "reason": "transition_roles contains an unknown event",
                "event_type": configured_event,
            })
        if not isinstance(configured_value, list) or any(not isinstance(item, str) for item in configured_value):
            return Decision(False, "STATE_POLICY_INVALID", {
                "reason": "transition roles must be an array of role strings",
                "event_type": configured_event,
            })
        role_set = set(configured_value)
        configured_defaults = configured_rule[2]
        if len(role_set) != len(configured_value) or not role_set.issubset(configured_defaults):
            return Decision(False, "STATE_POLICY_INVALID", {
                "reason": "transition roles may only tighten default authority",
                "event_type": configured_event,
                "default_roles": sorted(configured_defaults),
            })
        normalized_roles[configured_event] = role_set
    roles = normalized_roles.get(event_type, set(default_roles))
    role = event.get("actor_role")
    if event_type == "mission.released" and (
        (role == "system" and projection.state != "Parked")
        or (role == "producer" and projection.state == "Parked")
    ):
        return Decision(False, "STATE_ROLE_DENIED", {
            "event_type": event_type,
            "actor_role": role,
            "state": projection.state,
        })
    if role not in roles:
        return Decision(False, "STATE_ROLE_DENIED", {
            "event_type": event_type,
            "actor_role": role,
            "allowed_roles": sorted(roles),
        })
    return Decision(True, "STATE_TRANSITION_ALLOWED", {
        "event_type": event_type,
        "from_state": projection.state,
        "to_state": projection.state if target == "__PRESERVE__" else target,
    })


def project_state(events: Iterable[Mapping[str, Any]], policy: Mapping[str, Any] = None) -> MissionProjection:
    """Fold authenticated events into a projection, preserving denied input diagnostics."""

    effective_policy = {} if policy is None else policy
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
