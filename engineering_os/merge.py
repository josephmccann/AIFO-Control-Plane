"""Pure merge-authorization decisions; no merge API is invoked."""

from dataclasses import dataclass
from typing import Mapping, Sequence

from .approval import validate_approval
from .schema import validate_document


@dataclass(frozen=True)
class MergeDecision:
    allowed: bool
    code: str
    deployment_authorized: bool = False
    cutover_authorized: bool = False


def authorize_merge(
    *,
    state: str,
    mission_id: str,
    repository: str,
    pull_request: int,
    head_sha: str,
    merge_method: str,
    required_checks: Sequence[str],
    status_checks: Mapping[str, str],
    adversarial_review_complete: bool,
    unresolved_threads: int,
    tier_valid: bool,
    evidence: Mapping,
    approval: Mapping,
    founder_identities: Sequence[str],
    now: str,
    latest_commit_at: str,
    evidence_verifier: object,
    consumption_store: str,
    auto_merge_requested: bool,
    auto_merge_enabled: bool,
    submitter_kind: str = "agent",
) -> MergeDecision:
    if submitter_kind not in ("human", "agent"):
        return MergeDecision(False, "MERGE_SUBMITTER_INVALID")
    if state != "Merge Authorized":
        return MergeDecision(False, "MERGE_STATE_DENIED")
    if (
        not isinstance(required_checks, (list, tuple))
        or not required_checks
        or not isinstance(status_checks, Mapping)
        or any(status_checks.get(name) != "success" for name in required_checks)
    ):
        return MergeDecision(False, "MERGE_CHECKS_INCOMPLETE")
    if adversarial_review_complete is not True:
        return MergeDecision(False, "MERGE_REVIEW_INCOMPLETE")
    if (
        isinstance(unresolved_threads, bool)
        or not isinstance(unresolved_threads, int)
        or unresolved_threads != 0
    ):
        return MergeDecision(False, "MERGE_THREADS_UNRESOLVED")
    if tier_valid is not True:
        return MergeDecision(False, "MERGE_TIER_INVALID")
    if (
        not isinstance(evidence, Mapping)
        or validate_document("evidence", dict(evidence))
        or evidence.get("mission_id") != mission_id
        or evidence.get("repository") != repository
        or evidence.get("pull_request") != pull_request
        or evidence.get("head_sha") != head_sha
    ):
        return MergeDecision(False, "MERGE_EVIDENCE_INVALID")
    if merge_method not in ("merge", "squash", "rebase"):
        return MergeDecision(False, "MERGE_METHOD_INVALID")
    if auto_merge_requested and auto_merge_enabled is not True:
        return MergeDecision(False, "AUTO_MERGE_DISABLED")
    approval_decision = validate_approval(
        approval,
        founder_identities=founder_identities,
        mission_id=mission_id,
        action="merge",
        repository=repository,
        pull_request=pull_request,
        head_sha=head_sha,
        environment="github",
        merge_method=merge_method,
        now=now,
        latest_commit_at=latest_commit_at,
        evidence_verifier=evidence_verifier,
        consumption_store=consumption_store,
    )
    if not approval_decision.allowed:
        return MergeDecision(False, "MERGE_APPROVAL_INVALID")
    if auto_merge_requested:
        return MergeDecision(True, "AUTO_MERGE_AUTHORIZED")
    return MergeDecision(True, "MANUAL_MERGE_AUTHORIZED")
