"""Canonical GitHub record envelopes for scoped Engineering OS authority."""

from dataclasses import dataclass
import json
import re
from typing import Any, Dict, Mapping, Sequence, Tuple

from .canonical import canonical_json, content_sha256


_KINDS = frozenset((
    "authority", "coordination", "frozen_exception", "frozen_release",
    "frozen_reservation",
))
_ENVELOPE_FIELDS = frozenset((
    "provider", "record_kind", "payload_sha256", "repository",
    "issue_number", "comment_id", "url", "actor", "created_at",
))
_TIMESTAMP = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z"
)
_ENVELOPE_PROOF = object()


class RecordEnvelopeError(ValueError):
    """GitHub comment evidence is not an exact canonical record envelope."""


@dataclass(frozen=True, init=False)
class VerifiedRecordEnvelope:
    """Envelope derived by an adapter from authenticated GitHub API evidence."""

    record_kind: str
    payload_sha256: str
    repository: str
    issue_number: int
    comment_id: int
    url: str
    actor: str
    created_at: str

    def __init__(
        self, record_kind: str, payload_sha256: str, repository: str,
        issue_number: int, comment_id: int, url: str, actor: str,
        created_at: str, *, _proof: object = None,
    ) -> None:
        if _proof is not _ENVELOPE_PROOF:
            raise RecordEnvelopeError(
                "verified envelopes are created only from GitHub API evidence"
            )
        for name, value in (
            ("record_kind", record_kind), ("payload_sha256", payload_sha256),
            ("repository", repository), ("issue_number", issue_number),
            ("comment_id", comment_id), ("url", url), ("actor", actor),
            ("created_at", created_at),
        ):
            object.__setattr__(self, name, value)

    def source(self) -> Dict[str, Any]:
        return {
            "provider": "github",
            "record_kind": self.record_kind,
            "payload_sha256": self.payload_sha256,
            "repository": self.repository,
            "issue_number": self.issue_number,
            "comment_id": self.comment_id,
            "url": self.url,
            "actor": self.actor,
            "created_at": self.created_at,
        }


def _strict_object(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    value: Dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise RecordEnvelopeError("duplicate JSON key")
        value[key] = item
    return value


def record_comment_body(record_kind: str, payload: Mapping[str, Any]) -> str:
    """Return the only accepted canonical GitHub comment representation."""

    if record_kind not in _KINDS or not isinstance(payload, Mapping):
        raise RecordEnvelopeError("record kind or payload is invalid")
    if "source" in payload:
        raise RecordEnvelopeError("record payload must not contain its envelope")
    try:
        return canonical_json({"record_kind": record_kind, "payload": dict(payload)})
    except (TypeError, ValueError) as error:
        raise RecordEnvelopeError("record payload is not canonical JSON") from error


def authenticate_github_record_comment(
    comment: Mapping[str, Any], repository: str,
) -> Tuple[Dict[str, Any], VerifiedRecordEnvelope]:
    """Derive a verified record and envelope from authenticated GitHub API JSON.

    Transport authentication belongs to the GitHub adapter. This function
    closes and binds the API response fields and exact canonical comment body.
    """

    if not isinstance(comment, Mapping) or not isinstance(repository, str):
        raise RecordEnvelopeError("GitHub comment evidence is invalid")
    try:
        comment_id = comment["id"]
        url = comment["html_url"]
        issue_url = comment["issue_url"]
        actor = comment["user"]["login"]
        created_at = comment["created_at"]
        body = comment["body"]
    except (KeyError, TypeError):
        raise RecordEnvelopeError("GitHub comment evidence is incomplete")
    repository_pattern = re.escape(repository)
    issue_match = re.fullmatch(
        r"https://api\.github\.com/repos/" + repository_pattern + r"/issues/([1-9]\d*)",
        issue_url if isinstance(issue_url, str) else "",
    )
    if (
        not isinstance(comment_id, int) or isinstance(comment_id, bool) or comment_id < 1
        or issue_match is None
        or not isinstance(actor, str) or not actor
        or not isinstance(created_at, str) or _TIMESTAMP.fullmatch(created_at) is None
        or not isinstance(body, str)
    ):
        raise RecordEnvelopeError("GitHub comment metadata is invalid")
    issue_number = int(issue_match.group(1))
    expected_url = "https://github.com/%s/issues/%d#issuecomment-%d" % (
        repository, issue_number, comment_id,
    )
    if url != expected_url:
        raise RecordEnvelopeError("GitHub comment URL is not exact")
    try:
        document = json.loads(
            body, object_pairs_hook=_strict_object,
            parse_constant=lambda value: (_ for _ in ()).throw(
                RecordEnvelopeError("non-finite JSON number")
            ),
        )
    except (json.JSONDecodeError, TypeError, ValueError) as error:
        raise RecordEnvelopeError("GitHub record body is invalid JSON") from error
    if (
        not isinstance(document, Mapping)
        or set(document) != {"record_kind", "payload"}
        or document.get("record_kind") not in _KINDS
        or not isinstance(document.get("payload"), Mapping)
        or body != record_comment_body(document["record_kind"], document["payload"])
    ):
        raise RecordEnvelopeError("GitHub record body is not canonical")
    payload = dict(document["payload"])
    envelope = VerifiedRecordEnvelope(
        document["record_kind"], content_sha256(payload), repository,
        issue_number, comment_id, url, actor, created_at, _proof=_ENVELOPE_PROOF,
    )
    record = dict(payload)
    record["source"] = envelope.source()
    return record, envelope


def verify_record_envelope(
    record: Mapping[str, Any], record_kind: str,
    verified_envelopes: Sequence[VerifiedRecordEnvelope], *,
    repository: str, actor: str,
) -> bool:
    """Verify an exact payload against adapter-derived GitHub envelopes."""

    if (
        not isinstance(record, Mapping) or record_kind not in _KINDS
        or not isinstance(verified_envelopes, (list, tuple))
        or any(not isinstance(item, VerifiedRecordEnvelope) for item in verified_envelopes)
        or not isinstance(repository, str) or not isinstance(actor, str)
    ):
        return False
    source = record.get("source")
    if not isinstance(source, Mapping) or set(source) != _ENVELOPE_FIELDS:
        return False
    issue_number = source.get("issue_number")
    comment_id = source.get("comment_id")
    if (
        not isinstance(issue_number, int) or isinstance(issue_number, bool) or issue_number < 1
        or not isinstance(comment_id, int) or isinstance(comment_id, bool) or comment_id < 1
        or not isinstance(source.get("payload_sha256"), str)
        or re.fullmatch(r"[0-9a-f]{64}", source.get("payload_sha256")) is None
        or not isinstance(source.get("repository"), str)
        or not isinstance(source.get("actor"), str) or not source.get("actor")
        or not isinstance(source.get("created_at"), str)
        or _TIMESTAMP.fullmatch(source.get("created_at")) is None
        or source.get("url") != "https://github.com/%s/issues/%d#issuecomment-%d" % (
            source.get("repository"), issue_number, comment_id,
        )
    ):
        return False
    payload = dict(record)
    del payload["source"]
    try:
        digest = content_sha256(payload)
    except (TypeError, ValueError):
        return False
    expected = VerifiedRecordEnvelope(
        record_kind, digest, repository, issue_number,
        comment_id, source.get("url"), actor,
        source.get("created_at"), _proof=_ENVELOPE_PROOF,
    )
    return (
        source.get("provider") == "github"
        and source.get("record_kind") == record_kind
        and source.get("payload_sha256") == digest
        and source.get("repository") == repository
        and source.get("actor") == actor
        and source == expected.source()
        and any(item == expected for item in verified_envelopes)
    )
