"""Exact authenticated founder approval validation."""

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Any, Mapping, Sequence

from .canonical import content_sha256
from .consumption import ConsumptionBinding, consume_once
from .records import verify_record_evidence
from .schema import validate_document


_TIMESTAMP = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z"
)


def _time(value: Any) -> datetime:
    if not isinstance(value, str) or _TIMESTAMP.fullmatch(value) is None:
        raise ValueError("timestamp must be strict UTC RFC3339")
    return datetime.fromisoformat(value[:-1] + "+00:00").astimezone(timezone.utc)


@dataclass(frozen=True)
class ApprovalDecision:
    allowed: bool
    code: str
    approval_id: str = ""
    deployment_authorized: bool = False
    cutover_authorized: bool = False


def _deny(code: str, approval: Mapping[str, Any] = None) -> ApprovalDecision:
    approval_id = (
        approval.get("approval_id", "") if isinstance(approval, Mapping) else ""
    )
    return ApprovalDecision(False, code, approval_id)


def validate_approval(
    approval: Mapping[str, Any],
    *,
    founder_identities: Sequence[str],
    mission_id: str,
    action: str,
    repository: str,
    pull_request: int,
    head_sha: str,
    environment: str,
    merge_method: str,
    now: str,
    latest_commit_at: str,
    evidence_verifier: Any,
    consumption_store: str,
) -> ApprovalDecision:
    """Validate and atomically consume an approval bound to one exact action."""

    if not isinstance(approval, Mapping) or validate_document(
        "approval", dict(approval)
    ):
        return _deny("APPROVAL_SCHEMA_INVALID", approval)
    if (
        not isinstance(founder_identities, (list, tuple))
        or any(not isinstance(item, str) or not item for item in founder_identities)
        or not isinstance(mission_id, str) or not mission_id
        or action not in (
            "merge", "deploy", "cutover", "cloud_mutation", "spend", "exception",
        )
        or not isinstance(repository, str)
        or re.fullmatch(r"[^/]+/[^/]+", repository) is None
        or not isinstance(pull_request, int)
        or isinstance(pull_request, bool)
        or pull_request < 1
        or not isinstance(head_sha, str)
        or re.fullmatch(r"[0-9a-f]{40}", head_sha) is None
        or not isinstance(environment, str) or not environment
        or merge_method not in ("merge", "squash", "rebase")
        or not isinstance(consumption_store, str)
    ):
        return _deny("APPROVAL_INPUT_INVALID", approval)
    try:
        current = _time(now)
        approved_at = _time(approval["approved_at"])
        expires_at = _time(approval["expires_at"])
        latest_commit = _time(latest_commit_at)
    except (TypeError, ValueError):
        return _deny("APPROVAL_TIME_INVALID", approval)
    checks = (
        (approval.get("status") != "approved", "APPROVAL_INACTIVE"),
        (approval.get("mission_id") != mission_id, "APPROVAL_MISSION_MISMATCH"),
        (approval.get("action") != action, "APPROVAL_ACTION_MISMATCH"),
        (approval.get("repository") != repository, "APPROVAL_REPOSITORY_MISMATCH"),
        (approval.get("pull_request") != pull_request, "APPROVAL_PR_MISMATCH"),
        (approval.get("head_sha") != head_sha, "APPROVAL_HEAD_MISMATCH"),
        (
            approval.get("environment") != environment,
            "APPROVAL_ENVIRONMENT_MISMATCH",
        ),
        (
            approval.get("merge_method") != merge_method,
            "APPROVAL_MERGE_METHOD_MISMATCH",
        ),
        (
            approval.get("issuer") not in set(founder_identities),
            "APPROVAL_ISSUER_DENIED",
        ),
        (approved_at >= expires_at, "APPROVAL_TIME_INVALID"),
        (current < approved_at, "APPROVAL_NOT_STARTED"),
        (current >= expires_at, "APPROVAL_EXPIRED"),
        (latest_commit > approved_at, "APPROVAL_STALE_HEAD"),
        (
            action == "merge" and (
                approval.get("deployment_authorized") is not False
                or approval.get("cutover_authorized") is not False
            ),
            "APPROVAL_ACTION_SCOPE_INVALID",
        ),
        (
            not verify_record_evidence(
                approval, "founder_approval", evidence_verifier,
                repository=repository, actor=approval.get("issuer"), head_sha=head_sha,
            ),
            "APPROVAL_SOURCE_UNAUTHENTICATED",
        ),
    )
    failed = next((code for condition, code in checks if condition), None)
    if failed:
        return _deny(failed, approval)
    payload = dict(approval)
    del payload["source"]
    if not consume_once(consumption_store, [ConsumptionBinding(
        "founder_approval",
        approval["record_id"],
        approval["nonce"],
        content_sha256(payload),
    )]):
        return _deny("APPROVAL_REPLAYED", approval)
    return ApprovalDecision(
        True,
        "APPROVAL_ALLOWED",
        approval["approval_id"],
        approval["deployment_authorized"],
        approval["cutover_authorized"],
    )
