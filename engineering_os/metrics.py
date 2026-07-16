"""Deterministic aggregate Engineering OS metric projection."""

from datetime import datetime, timezone
import math
import re
from typing import Any, Mapping, Sequence

from .schema import validate_document


_TIMESTAMP = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z"
)
_KNOWN_EVENTS = frozenset((
    "mission.ready", "mission.closed", "finding.valid", "finding.invalid",
    "finding.duplicate", "finding.founder_decision", "mission.parked",
    "mission.orphaned", "override.applied", "rollback.completed",
    "incident.opened", "usage.recorded",
))


def _time(value: Any) -> datetime:
    if not isinstance(value, str) or _TIMESTAMP.fullmatch(value) is None:
        raise ValueError("timestamp must be strict UTC RFC3339")
    return datetime.fromisoformat(value[:-1] + "+00:00").astimezone(timezone.utc)


def _nonnegative(value: Any, *, integer: bool = False) -> bool:
    if isinstance(value, bool):
        return False
    if integer:
        return isinstance(value, int) and value >= 0
    return (
        isinstance(value, (int, float))
        and (not isinstance(value, float) or math.isfinite(value))
        and value >= 0
    )


def project_metrics(
    events: Sequence[Mapping[str, Any]],
    evidence_manifests: Sequence[Mapping[str, Any]],
    *,
    period_start: str,
    period_end: str,
) -> dict:
    """Project operational evidence; never derive quotas or people rankings."""

    start = _time(period_start)
    end = _time(period_end)
    if start >= end or not isinstance(events, (list, tuple)) or not isinstance(
        evidence_manifests, (list, tuple)
    ):
        raise ValueError("metric period or inputs are invalid")
    findings = {
        "valid": 0, "invalid": 0, "duplicate": 0, "founder_decision": 0,
    }
    lifecycle_starts = {}
    lifecycle_seconds = {}
    founder_minutes = 0.0
    model_cost = 0.0
    model_tokens = 0
    defects = 0
    false_positive_blocks = 0
    counts = {
        "parked": 0, "orphaned": 0, "overrides": 0,
        "rollbacks": 0, "incidents": 0,
    }
    for event in events:
        if (
            not isinstance(event, Mapping)
            or set(event) - {"mission_id", "type", "occurred_at", "details"}
            or event.get("type") not in _KNOWN_EVENTS
            or not isinstance(event.get("details"), Mapping)
        ):
            raise ValueError("metric event is invalid")
        occurred = _time(event.get("occurred_at"))
        if occurred < start or occurred >= end:
            continue
        mission_id = event.get("mission_id")
        if not isinstance(mission_id, str) or not mission_id:
            raise ValueError("metric event mission is invalid")
        event_type = event["type"]
        details = event["details"]
        if event_type == "mission.ready":
            if mission_id in lifecycle_starts:
                raise ValueError("duplicate mission lifecycle start")
            lifecycle_starts[mission_id] = occurred
        elif event_type == "mission.closed":
            if mission_id not in lifecycle_starts or mission_id in lifecycle_seconds:
                raise ValueError("mission lifecycle is incomplete")
            if occurred < lifecycle_starts[mission_id]:
                raise ValueError("mission lifecycle timestamps are reversed")
            lifecycle_seconds[mission_id] = int(
                (occurred - lifecycle_starts[mission_id]).total_seconds()
            )
        elif event_type.startswith("finding."):
            findings[event_type.split(".", 1)[1]] += 1
        elif event_type == "mission.parked":
            counts["parked"] += 1
        elif event_type == "mission.orphaned":
            counts["orphaned"] += 1
        elif event_type == "override.applied":
            counts["overrides"] += 1
        elif event_type == "rollback.completed":
            counts["rollbacks"] += 1
        elif event_type == "incident.opened":
            counts["incidents"] += 1
        allowed_details = {
            "founder_minutes", "model_cost_usd", "model_tokens",
            "defects", "false_positive_blocks",
        }
        if set(details) - allowed_details:
            raise ValueError("metric event details are not closed")
        values = {
            "founder_minutes": (details.get("founder_minutes", 0), False),
            "model_cost_usd": (details.get("model_cost_usd", 0), False),
            "model_tokens": (details.get("model_tokens", 0), True),
            "defects": (details.get("defects", 0), True),
            "false_positive_blocks": (
                details.get("false_positive_blocks", 0), True,
            ),
        }
        if any(not _nonnegative(value, integer=integer) for value, integer in values.values()):
            raise ValueError("metric value is invalid")
        founder_minutes += values["founder_minutes"][0]
        model_cost += values["model_cost_usd"][0]
        model_tokens += values["model_tokens"][0]
        defects += values["defects"][0]
        false_positive_blocks += values["false_positive_blocks"][0]
    throughput_missions = set()
    for manifest in evidence_manifests:
        if (
            not isinstance(manifest, Mapping)
            or set(manifest) != {"mission_id", "generated_at"}
            or not isinstance(manifest.get("mission_id"), str)
            or not manifest.get("mission_id")
        ):
            raise ValueError("metric evidence manifest is invalid")
        generated = _time(manifest.get("generated_at"))
        if start <= generated < end:
            throughput_missions.add(manifest["mission_id"])
    metrics = {
        "schema_version": "1.0.0",
        "period_start": period_start,
        "period_end": period_end,
        "founder_minutes": founder_minutes,
        "lifecycle_seconds": dict(sorted(lifecycle_seconds.items())),
        "model_cost_usd": model_cost,
        "model_tokens": model_tokens,
        "findings": findings,
        "remediation_cycles": findings["valid"],
        "defects": defects,
        "parked": counts["parked"],
        "orphaned": counts["orphaned"],
        "false_positive_blocks": false_positive_blocks,
        "overrides": counts["overrides"],
        "rollbacks": counts["rollbacks"],
        "incidents": counts["incidents"],
        "throughput": len(throughput_missions),
    }
    if validate_document("metrics", metrics):
        raise ValueError("generated metrics are invalid")
    return metrics
