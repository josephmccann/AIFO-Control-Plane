"""Canonical records bound to independently retrieved GitHub transport evidence."""

import hashlib
import json
import re
from typing import Any, Dict, Mapping, Sequence, Tuple

from .canonical import canonical_json, content_sha256


_KINDS = frozenset((
    "authority", "coordination", "frozen_exception", "frozen_release",
    "frozen_reservation",
))
_SOURCE_FIELDS = frozenset((
    "provider", "record_kind", "payload_sha256", "repository",
    "subject_kind", "subject_number", "comment_id", "url", "actor",
    "created_at", "content_sha256", "head_sha", "transport_provenance",
))
_EVIDENCE_FIELDS = frozenset((
    "repository", "subject_kind", "subject_number", "comment_id", "url",
    "actor", "created_at", "updated_at", "body", "head_sha",
    "transport_provenance",
))
_TIMESTAMP = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z"
)
_SHA256 = re.compile(r"[0-9a-f]{64}")
_GIT_SHA = re.compile(r"[0-9a-f]{40}")


class RecordEvidenceError(ValueError):
    """A canonical record or independently retrieved source is invalid."""


def _strict_object(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    value: Dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise RecordEvidenceError("duplicate JSON key")
        value[key] = item
    return value


def record_comment_body(record_kind: str, payload: Mapping[str, Any]) -> str:
    """Return the only canonical GitHub comment body accepted by the kernel."""

    if record_kind not in _KINDS or not isinstance(payload, Mapping):
        raise RecordEvidenceError("record kind or payload is invalid")
    if "source" in payload:
        raise RecordEvidenceError("record payload must not contain source claims")
    try:
        return canonical_json({"record_kind": record_kind, "payload": dict(payload)})
    except (TypeError, ValueError) as error:
        raise RecordEvidenceError("record payload is not canonical JSON") from error


def _exact_url(
    repository: str, subject_kind: str, subject_number: int, comment_id: int,
) -> str:
    route = "pull" if subject_kind == "pull_request" else "issues"
    return "https://github.com/%s/%s/%d#issuecomment-%d" % (
        repository, route, subject_number, comment_id,
    )


def _source_locator(source: Any) -> Tuple[str, str, int, int]:
    if not isinstance(source, Mapping) or set(source) != _SOURCE_FIELDS:
        raise RecordEvidenceError("record source claims are not closed")
    repository = source.get("repository")
    subject_kind = source.get("subject_kind")
    subject_number = source.get("subject_number")
    comment_id = source.get("comment_id")
    if (
        source.get("provider") != "github"
        or not isinstance(repository, str) or re.fullmatch(r"[^/]+/[^/]+", repository) is None
        or subject_kind not in ("issue", "pull_request")
        or not isinstance(subject_number, int) or isinstance(subject_number, bool) or subject_number < 1
        or not isinstance(comment_id, int) or isinstance(comment_id, bool) or comment_id < 1
        or source.get("url") != _exact_url(
            repository, subject_kind, subject_number, comment_id,
        )
        or not isinstance(source.get("actor"), str) or not source.get("actor")
        or not isinstance(source.get("created_at"), str)
        or _TIMESTAMP.fullmatch(source.get("created_at")) is None
        or not isinstance(source.get("payload_sha256"), str)
        or _SHA256.fullmatch(source.get("payload_sha256")) is None
        or not isinstance(source.get("content_sha256"), str)
        or _SHA256.fullmatch(source.get("content_sha256")) is None
        or not isinstance(source.get("head_sha"), str)
        or _GIT_SHA.fullmatch(source.get("head_sha")) is None
        or not isinstance(source.get("transport_provenance"), str)
        or not source.get("transport_provenance")
    ):
        raise RecordEvidenceError("record source claims are invalid")
    return repository, subject_kind, subject_number, comment_id


def verify_record_evidence(
    record: Mapping[str, Any], record_kind: str, evidence_verifier: Any, *,
    repository: str, actor: str, head_sha: str,
) -> bool:
    """Retrieve GitHub evidence and bind it to an exact canonical record.

    The verifier is the adapter-owned trust boundary. The kernel passes only an
    exact locator and accepts no caller-supplied evidence mapping or constructor
    identity as authentication.
    """

    if (
        not isinstance(record, Mapping) or record_kind not in _KINDS
        or not isinstance(repository, str) or not isinstance(actor, str)
        or not isinstance(head_sha, str) or _GIT_SHA.fullmatch(head_sha) is None
        or isinstance(evidence_verifier, Mapping)
    ):
        return False
    retrieve = getattr(evidence_verifier, "retrieve_comment", None)
    provenance = getattr(evidence_verifier, "transport_provenance", None)
    if not callable(retrieve) or not isinstance(provenance, str) or not provenance:
        return False
    try:
        source = record.get("source")
        locator = _source_locator(source)
        if locator[0] != repository:
            return False
        evidence = retrieve(*locator)
    except Exception:
        return False
    if not isinstance(evidence, Mapping) or set(evidence) != _EVIDENCE_FIELDS:
        return False
    evidence_repository = evidence.get("repository")
    subject_kind = evidence.get("subject_kind")
    subject_number = evidence.get("subject_number")
    comment_id = evidence.get("comment_id")
    body = evidence.get("body")
    if (
        evidence_repository != repository
        or subject_kind != locator[1]
        or subject_number != locator[2] or isinstance(subject_number, bool)
        or comment_id != locator[3] or isinstance(comment_id, bool)
        or evidence.get("url") != _exact_url(
            repository, subject_kind, subject_number, comment_id,
        )
        or evidence.get("actor") != actor
        or not isinstance(evidence.get("created_at"), str)
        or _TIMESTAMP.fullmatch(evidence.get("created_at")) is None
        or evidence.get("updated_at") != evidence.get("created_at")
        or evidence.get("head_sha") != head_sha
        or evidence.get("transport_provenance") != provenance
        or not isinstance(body, str)
    ):
        return False
    try:
        document = json.loads(
            body, object_pairs_hook=_strict_object,
            parse_constant=lambda value: (_ for _ in ()).throw(
                RecordEvidenceError("non-finite JSON number")
            ),
        )
    except (json.JSONDecodeError, TypeError, ValueError):
        return False
    if (
        not isinstance(document, Mapping)
        or set(document) != {"record_kind", "payload"}
        or document.get("record_kind") != record_kind
        or not isinstance(document.get("payload"), Mapping)
    ):
        return False
    payload = dict(record)
    payload.pop("source", None)
    try:
        canonical_body = record_comment_body(record_kind, document["payload"])
        payload_digest = content_sha256(payload)
        evidence_payload_digest = content_sha256(document["payload"])
        body_digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    except (TypeError, ValueError):
        return False
    expected_source = {
        "provider": "github",
        "record_kind": record_kind,
        "payload_sha256": payload_digest,
        "repository": repository,
        "subject_kind": subject_kind,
        "subject_number": subject_number,
        "comment_id": comment_id,
        "url": evidence.get("url"),
        "actor": actor,
        "created_at": evidence.get("created_at"),
        "content_sha256": body_digest,
        "head_sha": head_sha,
        "transport_provenance": provenance,
    }
    return (
        body == canonical_body
        and payload_digest == evidence_payload_digest
        and dict(source) == expected_source
    )
