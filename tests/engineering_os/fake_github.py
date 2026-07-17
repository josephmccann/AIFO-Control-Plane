import copy
import hashlib

from engineering_os.canonical import content_sha256
from engineering_os.records import record_comment_body


class SealedFakeGitHubTransport:
    transport_provenance = "sealed-fake-github-api:v1"

    def __init__(self, evidence=None, *, error=None):
        self._evidence = copy.deepcopy(evidence)
        self._error = error
        self.requests = []

    def retrieve_comment(self, repository, subject_kind, subject_number, comment_id):
        self.requests.append((repository, subject_kind, subject_number, comment_id))
        if self._error is not None:
            raise self._error
        if isinstance(self._evidence, list):
            for item in self._evidence:
                if (
                    item.get("repository"), item.get("subject_kind"),
                    item.get("subject_number"), item.get("comment_id"),
                ) == (repository, subject_kind, subject_number, comment_id):
                    return copy.deepcopy(item)
            return None
        return copy.deepcopy(self._evidence)


def transported_record(
    record_kind, payload, *, repository="acme/widgets",
    subject_kind="pull_request", subject_number=42, comment_id=9001,
    actor="founder", created_at="2026-07-15T00:00:00Z",
    head_sha="2222222222222222222222222222222222222222",
):
    body = record_comment_body(record_kind, payload)
    subject_path = "pull" if subject_kind == "pull_request" else "issues"
    evidence = {
        "repository": repository,
        "subject_kind": subject_kind,
        "subject_number": subject_number,
        "comment_id": comment_id,
        "url": (
            f"https://github.com/{repository}/{subject_path}/{subject_number}"
            f"#issuecomment-{comment_id}"
        ),
        "actor": actor,
        "created_at": created_at,
        "updated_at": created_at,
        "body": body,
        "head_sha": head_sha,
        "transport_provenance": SealedFakeGitHubTransport.transport_provenance,
    }
    source = {
        "provider": "github",
        "record_kind": record_kind,
        "payload_sha256": content_sha256(payload),
        "repository": repository,
        "subject_kind": subject_kind,
        "subject_number": subject_number,
        "comment_id": comment_id,
        "url": evidence["url"],
        "actor": actor,
        "created_at": created_at,
        "content_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "head_sha": head_sha,
        "transport_provenance": evidence["transport_provenance"],
    }
    value = copy.deepcopy(payload)
    value["source"] = source
    return value, evidence
