"""Mission issue parsing and Definition of Ready validation."""

import json
from pathlib import Path
from typing import Any, Dict, List

from . import EOS_VERSION
from .canonical import content_sha256
from .errors import EngineeringOSError, Violation
from .schema import validate_document


MISSION_BEGIN = "<!-- EOS:MISSION:BEGIN -->"
MISSION_END = "<!-- EOS:MISSION:END -->"
CONSTITUTION = Path(__file__).resolve().parents[1] / "docs" / "engineering-os" / "ENGINEERING_CONSTITUTION.md"


class MissionParseError(EngineeringOSError):
    """The issue body does not contain exactly one valid mission declaration."""


def parse_issue_body(body: str) -> Dict[str, Any]:
    """Extract exactly one JSON object from the canonical mission markers."""

    if body.count(MISSION_BEGIN) != 1 or body.count(MISSION_END) != 1:
        raise MissionParseError("issue body must contain exactly one EOS mission block")
    begin = body.index(MISSION_BEGIN) + len(MISSION_BEGIN)
    end = body.index(MISSION_END, begin)
    if end <= begin:
        raise MissionParseError("EOS mission markers are out of order")
    try:
        value = json.loads(body[begin:end].strip())
    except json.JSONDecodeError as error:
        raise MissionParseError("EOS mission block is not valid JSON: %s" % error) from error
    if not isinstance(value, dict):
        raise MissionParseError("EOS mission declaration must be a JSON object")
    return value


def _not_ready(field: str, reason: str) -> Violation:
    return Violation(
        code="MISSION_NOT_READY",
        message="mission does not satisfy the Definition of Ready",
        path="$.%s" % field,
        details={"field": field, "reason": reason},
    )


def validate_ready(mission: Dict[str, Any]) -> List[Violation]:
    """Validate the mission contract and independently testable readiness gates."""

    violations = list(validate_document("mission", mission))
    eos = mission.get("eos") if isinstance(mission, dict) else None
    if isinstance(eos, dict):
        if eos.get("version") != EOS_VERSION:
            violations.append(Violation(
                code="MISSION_EOS_VERSION_MISMATCH",
                message="mission does not pin the active EOS version",
                path="$.eos.version",
                details={"expected": EOS_VERSION, "actual": eos.get("version")},
            ))
        expected_hash = content_sha256(CONSTITUTION.read_bytes()) if CONSTITUTION.is_file() else None
        if expected_hash is None or eos.get("constitution_sha256") != expected_hash:
            violations.append(Violation(
                code="MISSION_EOS_HASH_MISMATCH",
                message="mission does not pin the exact Engineering Constitution bytes",
                path="$.eos.constitution_sha256",
                details={"expected": expected_hash, "actual": eos.get("constitution_sha256")},
            ))

    non_empty_lists = ("acceptance_criteria", "allowed_paths", "validation_commands")
    for field in non_empty_lists:
        if not isinstance(mission.get(field), list) or not mission.get(field):
            violations.append(_not_ready(field, "at least one independently reviewable item is required"))

    rollback = mission.get("rollback")
    if not isinstance(rollback, dict) or not str(rollback.get("plan", "")).strip():
        violations.append(_not_ready("rollback", "a non-empty rollback or recovery plan is required"))

    budgets = mission.get("budgets")
    if not isinstance(budgets, dict) or any(not isinstance(value, (int, float)) or value <= 0 for value in budgets.values()):
        violations.append(_not_ready("budgets", "all model, time, remediation, concurrency, and CI caps must be positive"))

    assignments = mission.get("assignments")
    producer = assignments.get("producer", {}) if isinstance(assignments, dict) else {}
    adversary = assignments.get("adversary", {}) if isinstance(assignments, dict) else {}
    if not producer.get("identity") or not adversary.get("identity") or producer.get("identity") == adversary.get("identity"):
        violations.append(_not_ready("assignments", "producer and adversary must be named and distinct"))
    return violations
