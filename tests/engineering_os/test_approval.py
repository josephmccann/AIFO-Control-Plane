import tempfile
import unittest
from pathlib import Path

from engineering_os.approval import validate_approval
from tests.engineering_os.fake_github import (
    SealedFakeGitHubTransport,
    transported_record,
)


class ApprovalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = str(Path(self.temp.name) / "consumption.sqlite")

    def tearDown(self):
        self.temp.cleanup()

    def record(self, **overrides):
        payload = {
            "schema_version": "1.0.0",
            "record_id": "approval-record-1",
            "approval_id": "approval-1",
            "status": "approved",
            "mission_id": "mission-7",
            "action": "merge",
            "repository": "acme/widgets",
            "pull_request": 42,
            "head_sha": "2" * 40,
            "environment": "github",
            "merge_method": "squash",
            "issuer": "founder",
            "approved_at": "2026-07-15T12:00:00Z",
            "expires_at": "2026-07-15T14:00:00Z",
            "deployment_authorized": False,
            "cutover_authorized": False,
            "nonce": "approval-nonce-1",
            "single_use": True,
        }
        payload.update(overrides)
        record, evidence = transported_record(
            "founder_approval",
            payload,
            actor=payload["issuer"],
            created_at=payload["approved_at"],
            head_sha=payload["head_sha"],
        )
        return record, SealedFakeGitHubTransport(evidence)

    def decide(self, record, transport, **overrides):
        values = {
            "founder_identities": ["founder"],
            "mission_id": "mission-7",
            "action": "merge",
            "repository": "acme/widgets",
            "pull_request": 42,
            "head_sha": "2" * 40,
            "environment": "github",
            "merge_method": "squash",
            "now": "2026-07-15T13:00:00Z",
            "latest_commit_at": "2026-07-15T11:59:00Z",
            "evidence_verifier": transport,
            "consumption_store": self.store,
        }
        values.update(overrides)
        return validate_approval(record, **values)

    def test_exact_authenticated_approval_is_single_use(self):
        record, transport = self.record()
        decision = self.decide(record, transport)
        self.assertTrue(decision.allowed)
        self.assertFalse(decision.deployment_authorized)
        self.assertFalse(decision.cutover_authorized)
        self.assertEqual(self.decide(record, transport).code, "APPROVAL_REPLAYED")

    def test_stale_wrong_binding_or_post_approval_commit_is_denied(self):
        cases = (
            ({"pull_request": 99}, {}, "APPROVAL_PR_MISMATCH"),
            ({"head_sha": "3" * 40}, {}, "APPROVAL_HEAD_MISMATCH"),
            ({"environment": "production"}, {}, "APPROVAL_ENVIRONMENT_MISMATCH"),
            ({"merge_method": "merge"}, {}, "APPROVAL_MERGE_METHOD_MISMATCH"),
            ({"expires_at": "2026-07-15T13:00:00Z"}, {}, "APPROVAL_EXPIRED"),
            ({}, {"latest_commit_at": "2026-07-15T12:00:01Z"}, "APPROVAL_STALE_HEAD"),
        )
        for index, (record_updates, decision_updates, code) in enumerate(cases):
            record, transport = self.record(
                record_id=f"record-{index}", approval_id=f"approval-{index}",
                nonce=f"nonce-{index}", **record_updates,
            )
            self.assertEqual(self.decide(record, transport, **decision_updates).code, code)

    def test_merge_approval_does_not_imply_deploy_or_cutover(self):
        record, transport = self.record(
            deployment_authorized=True,
            cutover_authorized=True,
        )
        self.assertEqual(
            self.decide(record, transport).code,
            "APPROVAL_ACTION_SCOPE_INVALID",
        )

    def test_forged_unknown_or_non_founder_record_fails_closed(self):
        record, transport = self.record()
        record["environment"] = "forged"
        self.assertEqual(
            self.decide(record, transport).code,
            "APPROVAL_ENVIRONMENT_MISMATCH",
        )
        record, transport = self.record(issuer="outsider")
        self.assertEqual(self.decide(record, transport).code, "APPROVAL_ISSUER_DENIED")
        record, transport = self.record()
        record["unknown"] = True
        self.assertEqual(self.decide(record, transport).code, "APPROVAL_SCHEMA_INVALID")


if __name__ == "__main__":
    unittest.main()
