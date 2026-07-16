"""Exact, expiring mission authority validation with read-only default."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from typing import Any, Dict, Mapping, Sequence, Tuple

from .schema import validate_document
from .scope import PathInputError, normalize_paths


_ACTIONS = frozenset((
    "read", "write", "merge", "deploy", "cloud_mutation", "secrets",
    "customer_data", "spend", "cutover",
))


@dataclass(frozen=True)
class AuthorityDecision:
    allowed: bool
    code: str
    authority_id: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


def _time(value: str) -> datetime:
    if not isinstance(value, str) or re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z", value
    ) is None:
        raise ValueError("timestamp must be strict UTC RFC3339")
    return datetime.fromisoformat(value[:-1] + "+00:00").astimezone(timezone.utc)


def _deny(code: str, record: Mapping[str, Any] = None) -> AuthorityDecision:
    authority_id = record.get("authority_id", "") if isinstance(record, Mapping) else ""
    return AuthorityDecision(False, code, authority_id)


def validate_authority(
    mission: Mapping[str, Any], policy: Mapping[str, Any], changed_files: Sequence[str],
    authority_records: Sequence[Mapping[str, Any]], *, action: str,
    pull_request: int, head_sha: str, now: str, subject: str,
) -> AuthorityDecision:
    """Require one exact authority record for every action other than read."""

    if action == "read" and not authority_records:
        return AuthorityDecision(True, "AUTHORITY_READ_ONLY_DEFAULT")
    if not authority_records:
        return _deny("AUTHORITY_REQUIRED")
    try:
        changed = normalize_paths(changed_files)
        current = _time(now)
    except (PathInputError, TypeError, ValueError):
        return _deny("AUTHORITY_INPUT_INVALID")
    if (
        action not in _ACTIONS or not isinstance(pull_request, int)
        or isinstance(pull_request, bool) or pull_request < 1
        or not isinstance(head_sha, str) or re.fullmatch(r"[0-9a-f]{40}", head_sha) is None
        or not isinstance(subject, str) or not subject
    ):
        return _deny("AUTHORITY_INPUT_INVALID")
    if policy.get("repository") != mission.get("repository"):
        return _deny("AUTHORITY_POLICY_REPOSITORY_MISMATCH")
    mission_capabilities = mission.get("capabilities")
    if (
        not isinstance(mission_capabilities, list)
        or action not in mission_capabilities
    ):
        return _deny("AUTHORITY_MISSION_CAPABILITY_DENIED")
    enabling_flag = {
        "deploy": "deployment_enabled",
        "cloud_mutation": "deployment_enabled",
        "cutover": "deployment_enabled",
    }.get(action)
    if enabling_flag is not None and policy.get(enabling_flag) is not True:
        return _deny("AUTHORITY_POLICY_CAPABILITY_DISABLED")

    founder_values = policy.get("founder_identities", []) if isinstance(policy, Mapping) else []
    founders = set(founder_values) if isinstance(founder_values, list) and all(
        isinstance(value, str) and value for value in founder_values
    ) else set()
    last_denial = _deny("AUTHORITY_REQUIRED")
    for record in authority_records:
        if not isinstance(record, Mapping):
            last_denial = _deny("AUTHORITY_RECORD_INVALID")
            continue
        if validate_document("authority", dict(record)):
            last_denial = _deny("AUTHORITY_RECORD_INVALID", record)
            continue
        try:
            paths = normalize_paths(record.get("paths", []))
            starts = _time(record.get("starts_at"))
            expires = _time(record.get("expires_at"))
            capabilities = record.get("capabilities")
            if (
                not isinstance(capabilities, list)
                or set(capabilities) != {action}
                or len(capabilities) != 1
            ):
                last_denial = _deny("AUTHORITY_ACTION_MISMATCH", record)
                continue
            if starts >= expires:
                raise ValueError("authority interval is empty")
        except (PathInputError, TypeError, ValueError):
            last_denial = _deny("AUTHORITY_RECORD_INVALID", record)
            continue
        checks = (
            (record.get("repository") != mission.get("repository"), "AUTHORITY_REPOSITORY_MISMATCH"),
            (record.get("mission_id") != mission.get("mission_id"), "AUTHORITY_MISSION_MISMATCH"),
            (record.get("pull_request") != pull_request, "AUTHORITY_PR_MISMATCH"),
            (record.get("head_sha") != head_sha, "AUTHORITY_HEAD_MISMATCH"),
            (record.get("subject") != subject, "AUTHORITY_SUBJECT_MISMATCH"),
            (set(paths) != set(changed) or len(paths) != len(changed), "AUTHORITY_PATH_MISMATCH"),
            (record.get("issuer") not in founders, "AUTHORITY_ISSUER_DENIED"),
            (record.get("status") != "active", "AUTHORITY_INACTIVE"),
            (current < starts, "AUTHORITY_NOT_STARTED"),
            (current >= expires, "AUTHORITY_EXPIRED"),
        )
        failed = next((code for condition, code in checks if condition), None)
        if failed:
            last_denial = _deny(failed, record)
            continue
        return AuthorityDecision(True, "AUTHORITY_ALLOWED", record.get("authority_id", ""))
    return last_denial
