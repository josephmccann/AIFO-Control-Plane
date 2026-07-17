"""Adversarial finding normalization and separation-of-duties checks."""

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Sequence, Tuple

from .schema import validate_document


_DISPOSITIONS = ("valid", "invalid", "duplicate", "founder_decision")


@dataclass(frozen=True)
class FindingDecision:
    allowed: bool
    code: str
    findings: Tuple[Dict[str, Any], ...] = ()
    counts: Dict[str, int] = field(default_factory=dict)


def normalize_findings(
    findings: Sequence[Mapping[str, Any]],
    *,
    mission_id: str,
    producer_identity: str,
    producer_model_family: str,
    adversary_identity: str,
    adversary_model_family: str,
    require_distinct_model_family: bool,
) -> FindingDecision:
    """Validate findings without imposing acceptance, rejection, or severity quotas."""

    identities = (
        mission_id, producer_identity, producer_model_family,
        adversary_identity, adversary_model_family,
    )
    if (
        not isinstance(findings, (list, tuple))
        or any(not isinstance(value, str) or not value for value in identities)
        or type(require_distinct_model_family) is not bool
    ):
        return FindingDecision(False, "FINDING_INPUT_INVALID")
    if producer_identity.casefold() == adversary_identity.casefold():
        return FindingDecision(False, "FINDING_IDENTITY_CONFLICT")
    if (
        require_distinct_model_family
        and producer_model_family.casefold() == adversary_model_family.casefold()
    ):
        return FindingDecision(False, "FINDING_MODEL_FAMILY_CONFLICT")
    normalized = []
    identifiers = set()
    counts = {name: 0 for name in _DISPOSITIONS}
    for finding in findings:
        if not isinstance(finding, Mapping) or validate_document(
            "finding", dict(finding)
        ):
            return FindingDecision(False, "FINDING_SCHEMA_INVALID")
        finding_id = finding.get("finding_id")
        if finding_id in identifiers:
            return FindingDecision(False, "FINDING_DUPLICATE_ID")
        identifiers.add(finding_id)
        if finding.get("mission_id") != mission_id:
            return FindingDecision(False, "FINDING_MISSION_MISMATCH")
        if finding.get("reviewer").casefold() != adversary_identity.casefold():
            return FindingDecision(False, "FINDING_REVIEWER_MISMATCH")
        value = dict(finding)
        normalized.append(value)
        counts[value["disposition"]] += 1
    return FindingDecision(
        True, "FINDINGS_NORMALIZED", tuple(normalized), counts,
    )
