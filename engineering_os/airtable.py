"""Deterministic, one-way Airtable reporting projection and gated adapter."""

from dataclasses import dataclass
import json
import re
import time
from typing import Any, Mapping, Sequence, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import quote
import urllib.request

from .approval import validate_approval
from .canonical import canonical_json, content_sha256
from .schema import validate_document


_TIMESTAMP = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z"
)
_SHA = re.compile(r"[0-9a-f]{40}")
_BASE_ID = re.compile(r"app[A-Za-z0-9]{14,}")
_TABLE_ID = re.compile(r"tbl[A-Za-z0-9]{14,}")
_BATCH_SIZE = 10
_MAX_ATTEMPTS = 3
_MAX_RESPONSE_BYTES = 1_000_000


@dataclass(frozen=True)
class AirtableSyncResult:
    allowed: bool
    code: str
    records: Tuple[dict, ...] = ()
    attempted_batches: int = 0
    completed_batches: int = 0


def project_airtable_record(
    mission: Mapping[str, Any],
    projection: Mapping[str, Any],
    *,
    head_sha: str,
    projected_at: str,
) -> dict:
    """Project only the closed reporting fields; mission prose never crosses."""

    if (
        not isinstance(mission, Mapping)
        or validate_document("mission", dict(mission))
        or not isinstance(projection, Mapping)
        or validate_document("mission-state", dict(projection))
        or projection.get("mission_id") != mission.get("mission_id")
        or not isinstance(head_sha, str)
        or _SHA.fullmatch(head_sha) is None
        or not isinstance(projected_at, str)
        or _TIMESTAMP.fullmatch(projected_at) is None
    ):
        raise ValueError("Airtable projection input is invalid")
    record = {
        "schema_version": "1.0.0",
        "source": "github",
        "direction": "github_to_airtable",
        "upsert_key": "%s#%s" % (
            mission["repository"],
            mission["mission_id"],
        ),
        "mission_id": mission["mission_id"],
        "repository": mission["repository"],
        "state": projection["state"],
        "risk_tier": mission["risk_tier"],
        "head_sha": head_sha,
        "projected_at": projected_at,
    }
    if validate_document("airtable-record", record):
        raise ValueError("Airtable projection output is invalid")
    return record


def _closed_records(records: Sequence[Mapping[str, Any]]) -> Tuple[dict, ...]:
    if not isinstance(records, (list, tuple)) or not records:
        raise ValueError("Airtable records are absent")
    values = []
    keys = set()
    for record in records:
        if (
            not isinstance(record, Mapping)
            or validate_document("airtable-record", dict(record))
            or record.get("upsert_key") in keys
        ):
            raise ValueError("Airtable record is invalid")
        keys.add(record["upsert_key"])
        values.append(dict(record))
    return tuple(sorted(values, key=lambda item: item["upsert_key"]))


def _target_environment(
    base_id: str,
    table_id: str,
    records: Sequence[Mapping[str, Any]],
) -> str:
    return "airtable:%s:%s:%s" % (
        base_id,
        table_id,
        content_sha256(list(records)),
    )


def _retryable(error: Exception) -> bool:
    if isinstance(error, HTTPError):
        return error.code in (408, 409, 425, 429) or error.code >= 500
    return isinstance(error, (URLError, TimeoutError, OSError))


def _send_batch(
    batch: Sequence[Mapping[str, Any]],
    *,
    base_id: str,
    table_id: str,
    credential: str,
) -> bool:
    url = "https://api.airtable.com/v0/%s/%s" % (
        quote(base_id, safe=""),
        quote(table_id, safe=""),
    )
    body = canonical_json({
        "performUpsert": {"fieldsToMergeOn": ["upsert_key"]},
        "records": [{"fields": dict(record)} for record in batch],
    }).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": "Bearer %s" % credential,
            "Content-Type": "application/json",
        },
        method="PATCH",
    )
    for attempt in range(_MAX_ATTEMPTS):
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                if getattr(response, "status", None) != 200:
                    return False
                content = response.read(_MAX_RESPONSE_BYTES + 1)
                if len(content) > _MAX_RESPONSE_BYTES:
                    return False
                payload = json.loads(content.decode("utf-8"))
            return (
                isinstance(payload, dict)
                and isinstance(payload.get("records"), list)
                and len(payload["records"]) == len(batch)
            )
        except Exception as error:
            if not _retryable(error) or attempt + 1 >= _MAX_ATTEMPTS:
                return False
            try:
                time.sleep(float(2 ** attempt))
            except Exception:
                return False
    return False


def sync_airtable(
    *,
    direction: str,
    mode: str,
    records: Sequence[Mapping[str, Any]],
    policy: Mapping[str, Any] = None,
    approval: Mapping[str, Any] = None,
    authorization_mission_id: str = "",
    authorization_head_sha: str = "",
    pull_request: int = 0,
    now: str = "",
    latest_commit_at: str = "",
    base_id: str = "",
    table_id: str = "",
    credential: str = "",
    credential_source: str = "",
    evidence_verifier: Any = None,
    consumption_store: str = "",
) -> AirtableSyncResult:
    """Return a dry-run projection or perform an exactly gated live upsert."""

    if direction != "github_to_airtable":
        return AirtableSyncResult(False, "AIRTABLE_DIRECTION_DENIED")
    if mode not in ("dry-run", "live"):
        return AirtableSyncResult(False, "AIRTABLE_MODE_INVALID")
    try:
        projected = _closed_records(records)
    except (KeyError, TypeError, ValueError):
        return AirtableSyncResult(False, "AIRTABLE_RECORDS_INVALID")
    if mode == "dry-run":
        return AirtableSyncResult(True, "AIRTABLE_DRY_RUN", projected)

    if (
        not isinstance(policy, Mapping)
        or validate_document("repository-policy", dict(policy))
        or policy.get("airtable_live_enabled") is not True
        or any(record["repository"] != policy.get("repository") for record in projected)
    ):
        return AirtableSyncResult(False, "AIRTABLE_LIVE_POLICY_DISABLED", projected)
    if (
        not isinstance(base_id, str)
        or _BASE_ID.fullmatch(base_id) is None
        or not isinstance(table_id, str)
        or _TABLE_ID.fullmatch(table_id) is None
    ):
        return AirtableSyncResult(False, "AIRTABLE_LIVE_TARGET_INVALID", projected)
    if (
        not isinstance(credential, str)
        or not credential
        or "\n" in credential
        or "\r" in credential
        or credential_source != "environment"
    ):
        return AirtableSyncResult(
            False, "AIRTABLE_LIVE_CREDENTIAL_REQUIRED", projected
        )
    if (
        not isinstance(authorization_mission_id, str)
        or not authorization_mission_id
        or not isinstance(authorization_head_sha, str)
        or _SHA.fullmatch(authorization_head_sha) is None
        or not isinstance(approval, Mapping)
        or approval.get("deployment_authorized") is not False
        or approval.get("cutover_authorized") is not False
    ):
        return AirtableSyncResult(False, "AIRTABLE_LIVE_APPROVAL_INVALID", projected)
    approval_decision = validate_approval(
        approval,
        founder_identities=policy["founder_identities"],
        mission_id=authorization_mission_id,
        action="airtable_write",
        repository=policy["repository"],
        pull_request=pull_request,
        head_sha=authorization_head_sha,
        environment=_target_environment(base_id, table_id, projected),
        merge_method="merge",
        now=now,
        latest_commit_at=latest_commit_at,
        evidence_verifier=evidence_verifier,
        consumption_store=consumption_store,
    )
    if not approval_decision.allowed:
        return AirtableSyncResult(False, "AIRTABLE_LIVE_APPROVAL_INVALID", projected)
    batches = [
        projected[index:index + _BATCH_SIZE]
        for index in range(0, len(projected), _BATCH_SIZE)
    ]
    completed = 0
    for index, batch in enumerate(batches):
        if not _send_batch(
            batch,
            base_id=base_id,
            table_id=table_id,
            credential=credential,
        ):
            code = "AIRTABLE_PARTIAL_FAILURE" if completed else "AIRTABLE_API_FAILURE"
            return AirtableSyncResult(
                False, code, projected, index + 1, completed
            )
        completed += 1
    return AirtableSyncResult(
        True, "AIRTABLE_LIVE_SYNCED", projected, len(batches), completed
    )
