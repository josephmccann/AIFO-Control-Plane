"""Machine-derived evidence manifest generation."""

from dataclasses import dataclass
import re
from typing import Any, Mapping, Sequence

from .audit import validate_audit_chain
from .canonical import content_sha256
from .schema import validate_document


_TIMESTAMP = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z"
)


@dataclass(frozen=True)
class ArtifactInput:
    name: str
    content: bytes
    source: str


def generate_evidence(
    *,
    mission: Mapping[str, Any],
    policy: Mapping[str, Any],
    audit_events: Sequence[Mapping[str, Any]],
    repository: str,
    pull_request: int,
    base_sha: str,
    head_sha: str,
    generated_at: str,
    status_checks: Sequence[Mapping[str, Any]],
    artifacts: Sequence[ArtifactInput],
    cleanup_state: str,
    deployment_state: str,
) -> dict:
    """Build a closed manifest from validated adapter outputs only."""

    if (
        not isinstance(mission, Mapping)
        or validate_document("mission", dict(mission))
        or not isinstance(policy, Mapping)
        or validate_document("repository-policy", dict(policy))
        or mission.get("repository") != repository
        or policy.get("repository") != repository
        or not isinstance(pull_request, int)
        or isinstance(pull_request, bool)
        or pull_request < 1
        or re.fullmatch(r"[0-9a-f]{40}", base_sha or "") is None
        or re.fullmatch(r"[0-9a-f]{40}", head_sha or "") is None
        or not isinstance(generated_at, str)
        or _TIMESTAMP.fullmatch(generated_at) is None
        or cleanup_state not in ("not_required", "pending", "complete", "failed")
        or deployment_state not in (
            "not_authorized", "not_deployed", "deployed", "rolled_back",
        )
        or deployment_state in ("deployed", "rolled_back")
        and policy.get("deployment_enabled") is not True
    ):
        raise ValueError("evidence identity or policy is invalid")
    audit = validate_audit_chain(audit_events)
    if (
        not audit.allowed
        or not audit.head_hash
        or not audit_events
        or audit_events[0].get("mission_id") != mission.get("mission_id")
    ):
        raise ValueError("audit evidence is invalid")
    required_checks = policy.get("required_status_checks")
    if (
        not isinstance(status_checks, (list, tuple))
        or not isinstance(required_checks, list)
        or any(
            not isinstance(item, Mapping)
            or set(item) != {"name", "conclusion"}
            or not isinstance(item.get("name"), str)
            or item.get("conclusion") not in ("success", "neutral", "skipped")
            for item in status_checks
        )
    ):
        raise ValueError("status-check evidence is invalid")
    checks_by_name = {item["name"]: item["conclusion"] for item in status_checks}
    if (
        len(checks_by_name) != len(status_checks)
        or any(checks_by_name.get(name) != "success" for name in required_checks)
    ):
        raise ValueError("required status checks did not pass")
    if not isinstance(artifacts, (list, tuple)) or not artifacts:
        raise ValueError("artifact evidence is absent")
    artifact_values = []
    artifact_names = set()
    for artifact in artifacts:
        if (
            type(artifact) is not ArtifactInput
            or not isinstance(artifact.name, str)
            or not artifact.name
            or artifact.name in artifact_names
            or not isinstance(artifact.content, bytes)
            or not isinstance(artifact.source, str)
            or not artifact.source
        ):
            raise ValueError("artifact evidence is invalid")
        artifact_names.add(artifact.name)
        artifact_values.append({
            "name": artifact.name,
            "sha256": content_sha256(artifact.content),
            "size_bytes": len(artifact.content),
            "source": artifact.source,
        })
    manifest = {
        "schema_version": "1.0.0",
        "mission_id": mission["mission_id"],
        "repository": repository,
        "pull_request": pull_request,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "generated_at": generated_at,
        "policy_hash": content_sha256(dict(policy)),
        "mission_hash": content_sha256(dict(mission)),
        "audit_head_hash": audit.head_hash,
        "status_checks": [
            {"name": item["name"], "conclusion": item["conclusion"]}
            for item in status_checks
        ],
        "artifacts": artifact_values,
        "cleanup_state": cleanup_state,
        "deployment_state": deployment_state,
    }
    if validate_document("evidence", manifest):
        raise ValueError("generated evidence manifest is invalid")
    return manifest
