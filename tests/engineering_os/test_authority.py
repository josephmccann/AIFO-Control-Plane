import copy
from concurrent.futures import ThreadPoolExecutor
import json
import tempfile
import unittest
from pathlib import Path

from engineering_os.authority import validate_authority
from engineering_os.records import (
    authenticate_github_record_comment, RecordEnvelopeError, record_comment_body,
    VerifiedRecordEnvelope, verify_record_envelope,
)
from tests.engineering_os.test_risk import mission, policy


ROOT = Path(__file__).resolve().parents[2]
AUTHORITY = ROOT / "tests" / "engineering_os" / "fixtures" / "authority-records"
HEAD = "2222222222222222222222222222222222222222"


def record():
    return json.loads((AUTHORITY / "valid/write.json").read_text(encoding="utf-8"))


def authority_envelope():
    candidate = record()
    source = candidate.pop("source")
    comment = {
        "id": source["comment_id"],
        "html_url": source["url"],
        "issue_url": "https://api.github.com/repos/acme/widgets/issues/%d" % source["issue_number"],
        "user": {"login": source["actor"]},
        "created_at": source["created_at"],
        "body": record_comment_body("authority", candidate),
    }
    authenticated, envelope = authenticate_github_record_comment(comment, "acme/widgets")
    if authenticated != record():
        raise AssertionError("authority fixture is not its canonical GitHub record")
    return envelope


def decide(records, **updates):
    consumption_store = updates.pop("consumption_store", None)
    if consumption_store is None:
        with tempfile.TemporaryDirectory() as directory:
            return decide(
                records, consumption_store=str(Path(directory) / "consumed.sqlite3"),
                **updates,
            )
    changed_files = updates.pop("changed_files", ["src/reporting/render.py"])
    context = {
        "action": "write",
        "pull_request": 42,
        "head_sha": HEAD,
        "now": "2026-07-15T12:00:00Z",
        "subject": "producer-a",
        "verified_envelopes": [authority_envelope()],
        "consumption_store": consumption_store,
    }
    context.update(updates)
    return validate_authority(
        mission("Tier 1"), policy(), changed_files, records, **context
    )


class AuthorityTests(unittest.TestCase):
    def test_payload_mutation_cannot_reuse_an_old_authenticated_source(self):
        candidate = record()
        candidate["paths"] = ["src/reporting/other.py"]
        decision = validate_authority(
            mission("Tier 1"), policy(), ["src/reporting/other.py"], [candidate],
            action="write", pull_request=42, head_sha=HEAD,
            now="2026-07-15T12:00:00Z", subject="producer-a",
            verified_envelopes=[authority_envelope()],
            consumption_store=str(Path(tempfile.gettempdir()) / "unused-authority.sqlite3"),
        )
        self.assertEqual(decision.code, "AUTHORITY_SOURCE_UNAUTHENTICATED")

    def test_envelope_metadata_uses_exact_json_types(self):
        payload = record()
        payload.pop("source")
        candidate, envelope = authenticate_github_record_comment({
            "id": 9001,
            "html_url": "https://github.com/acme/widgets/issues/1#issuecomment-9001",
            "issue_url": "https://api.github.com/repos/acme/widgets/issues/1",
            "user": {"login": "founder"},
            "created_at": "2026-07-15T00:00:00Z",
            "body": record_comment_body("authority", payload),
        }, "acme/widgets")
        candidate["source"]["issue_number"] = True
        self.assertFalse(verify_record_envelope(
            candidate, "authority", [envelope],
            repository="acme/widgets", actor="founder",
        ))

    def test_callers_cannot_mint_verified_envelopes(self):
        with self.assertRaises(RecordEnvelopeError):
            VerifiedRecordEnvelope(
                "authority", "a" * 64, "acme/widgets", 1, 2,
                "https://github.com/acme/widgets/issues/1#issuecomment-2",
                "founder", "2026-07-15T00:00:00Z",
            )

    def test_authority_is_consumed_once_sequentially(self):
        with tempfile.TemporaryDirectory() as directory:
            store = str(Path(directory) / "consumed.sqlite3")
            first = decide([record()], consumption_store=store)
            second = decide([record()], consumption_store=store)
        self.assertEqual((first.allowed, second.code), (True, "AUTHORITY_REPLAYED"))

    def test_authority_is_consumed_once_concurrently(self):
        with tempfile.TemporaryDirectory() as directory:
            store = str(Path(directory) / "consumed.sqlite3")
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(
                    lambda _: decide([record()], consumption_store=store), range(2),
                ))
        self.assertEqual(sum(result.allowed for result in results), 1)
        self.assertEqual(sum(result.code == "AUTHORITY_REPLAYED" for result in results), 1)

    def test_default_authority_is_read_only(self):
        read = decide([], action="read")
        write = decide([])
        self.assertEqual((read.allowed, read.code), (True, "AUTHORITY_READ_ONLY_DEFAULT"))
        self.assertEqual((write.allowed, write.code), (False, "AUTHORITY_REQUIRED"))

    def test_authority_requires_authenticated_source_and_rejects_replay(self):
        candidate = record()
        self.assertEqual(decide([candidate], verified_envelopes=[]).code, "AUTHORITY_SOURCE_UNAUTHENTICATED")
        with tempfile.TemporaryDirectory() as directory:
            store = str(Path(directory) / "consumed.sqlite3")
            self.assertTrue(decide([candidate], consumption_store=store).allowed)
            self.assertEqual(decide([candidate], consumption_store=store).code, "AUTHORITY_REPLAYED")

        duplicate = copy.deepcopy(candidate)
        duplicate["authority_id"] = "authority-write-2"
        self.assertEqual(decide([candidate, duplicate]).code, "AUTHORITY_RECORD_DUPLICATE")

    def test_exact_active_record_authorizes_only_its_bound_action(self):
        self.assertEqual((decide([record()]).allowed, decide([record()]).code), (True, "AUTHORITY_ALLOWED"))
        for field, value, code in (
            ("mission_id", "mission-other", "AUTHORITY_MISSION_MISMATCH"),
            ("pull_request", 43, "AUTHORITY_PR_MISMATCH"),
            ("head_sha", "3" * 40, "AUTHORITY_HEAD_MISMATCH"),
            ("subject", "producer-b", "AUTHORITY_SUBJECT_MISMATCH"),
            ("capabilities", ["merge"], "AUTHORITY_ACTION_MISMATCH"),
        ):
            with self.subTest(field=field):
                candidate = record()
                candidate[field] = value
                self.assertEqual(decide([candidate]).code, code)

    def test_expired_wrong_repository_and_wrong_path_are_denied(self):
        expired = record()
        expired["expires_at"] = "2026-07-15T12:00:00Z"
        wrong_repo = record()
        wrong_repo["repository"] = "acme/other"
        wrong_path = record()
        wrong_path["paths"] = ["src/reporting/other.py"]
        self.assertEqual(decide([expired]).code, "AUTHORITY_EXPIRED")
        self.assertEqual(decide([wrong_repo]).code, "AUTHORITY_REPOSITORY_MISMATCH")
        self.assertEqual(decide([wrong_path]).code, "AUTHORITY_PATH_MISMATCH")

        wrong_base = policy()
        wrong_base["repository"] = "acme/other"
        base_denied = validate_authority(
            mission("Tier 1"), wrong_base, ["src/reporting/render.py"], [record()],
            action="write", pull_request=42, head_sha=HEAD,
            now="2026-07-15T12:00:00Z", subject="producer-a",
            verified_envelopes=[authority_envelope()],
            consumption_store=str(Path(tempfile.gettempdir()) / "wrong-base.sqlite3"),
        )
        self.assertEqual(base_denied.code, "AUTHORITY_POLICY_REPOSITORY_MISMATCH")

    def test_future_revoked_consumed_or_non_founder_authority_is_denied(self):
        cases = []
        future = record(); future["starts_at"] = "2026-07-15T12:00:01Z"; cases.append((future, "AUTHORITY_NOT_STARTED"))
        revoked = record(); revoked["status"] = "revoked"; cases.append((revoked, "AUTHORITY_INACTIVE"))
        consumed = record(); consumed["status"] = "consumed"; cases.append((consumed, "AUTHORITY_INACTIVE"))
        outsider = record(); outsider["issuer"] = "outsider"; cases.append((outsider, "AUTHORITY_ISSUER_DENIED"))
        for candidate, code in cases:
            with self.subTest(code=code):
                self.assertEqual(decide([candidate]).code, code)

        no_founders = policy()
        no_founders["founder_identities"] = []
        denied = validate_authority(
            mission("Tier 1"), no_founders, ["src/reporting/render.py"], [record()],
            action="write", pull_request=42, head_sha=HEAD,
            now="2026-07-15T12:00:00Z", subject="producer-a",
            verified_envelopes=[authority_envelope()],
            consumption_store=str(Path(tempfile.gettempdir()) / "no-founders.sqlite3"),
        )
        self.assertEqual(denied.code, "AUTHORITY_POLICY_INVALID")

    def test_malformed_timestamps_and_paths_fail_closed(self):
        malformed = record(); malformed["expires_at"] = "tomorrow"
        traversal = record(); traversal["paths"] = ["../escape"]
        incomplete = record(); incomplete.pop("authority_id")
        self.assertEqual(decide([malformed]).code, "AUTHORITY_RECORD_INVALID")
        self.assertEqual(decide([traversal]).code, "AUTHORITY_RECORD_INVALID")
        self.assertEqual(decide([incomplete]).code, "AUTHORITY_RECORD_INVALID")

    def test_authority_cannot_expand_mission_or_disabled_base_policy_capabilities(self):
        deploy = record()
        deploy["capabilities"] = ["deploy"]
        undeclared = decide([deploy], action="deploy")
        self.assertEqual(undeclared.code, "AUTHORITY_MISSION_CAPABILITY_DENIED")

        declared_mission = mission("Tier 2")
        declared_mission["capabilities"].append("deploy")
        base_policy = policy()
        base_policy["deployment_enabled"] = False
        disabled = validate_authority(
            declared_mission, base_policy, ["src/reporting/render.py"], [deploy],
            action="deploy", pull_request=42, head_sha=HEAD,
            now="2026-07-15T12:00:00Z", subject="producer-a",
            verified_envelopes=[authority_envelope()],
            consumption_store=str(Path(tempfile.gettempdir()) / "disabled.sqlite3"),
        )
        self.assertEqual(disabled.code, "AUTHORITY_POLICY_CAPABILITY_DISABLED")

    def test_malformed_collections_and_boolean_pr_fail_stably(self):
        self.assertEqual(validate_authority(
            mission("Tier 1"), policy(), ["src/reporting/render.py"], None,
            action="write", pull_request=42, head_sha=HEAD, now="2026-07-15T12:00:00Z",
            subject="producer-a", verified_envelopes=[], consumption_store="",
        ).code, "AUTHORITY_INPUT_INVALID")
        self.assertEqual(validate_authority(
            mission("Tier 1"), policy(), ["src/reporting/render.py"], [record()],
            action="write", pull_request=True, head_sha=HEAD, now="2026-07-15T12:00:00Z",
            subject="producer-a", verified_envelopes=[authority_envelope()],
            consumption_store="",
        ).code, "AUTHORITY_INPUT_INVALID")

    def test_credential_model_names_real_gap_and_github_app_migration(self):
        text = (ROOT / "docs/engineering-os/CREDENTIAL_MODEL.md").read_text(encoding="utf-8")
        compact = " ".join(text.split())
        self.assertIn("cannot path-scope the Git credential", compact)
        self.assertIn("GitHub App", compact)
        self.assertIn("expiring installation token", compact)
        self.assertIn("does not claim that it enforces path-scoped Git credentials", compact)

    def test_authority_document_names_envelope_and_operational_store_boundaries(self):
        text = (ROOT / "docs/engineering-os/AUTHORITY_MODEL.md").read_text(encoding="utf-8")
        self.assertIn("canonical payload SHA-256", text)
        self.assertIn("SQLite", text)
        self.assertIn("raw mappings", text)
        self.assertIn("no operational adapter", text)


if __name__ == "__main__":
    unittest.main()
