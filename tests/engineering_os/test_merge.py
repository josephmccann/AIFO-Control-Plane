import unittest
from pathlib import Path
import tempfile

from engineering_os.merge import authorize_merge
from tests.engineering_os.fake_github import SealedFakeGitHubTransport, transported_record


ROOT = Path(__file__).resolve().parents[2]


class MergeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.store = str(Path(self.temp.name) / "approval.sqlite")

    def tearDown(self):
        self.temp.cleanup()

    def approval(self):
        payload = {
            "schema_version": "1.0.0", "record_id": "record-1",
            "approval_id": "approval-1", "status": "approved",
            "mission_id": "mission-7", "action": "merge",
            "repository": "acme/widgets", "pull_request": 42,
            "head_sha": "2" * 40, "environment": "github",
            "merge_method": "squash", "issuer": "founder",
            "approved_at": "2026-07-15T12:00:00Z",
            "expires_at": "2026-07-15T14:00:00Z",
            "deployment_authorized": False, "cutover_authorized": False,
            "nonce": "nonce-1", "single_use": True,
        }
        record, evidence = transported_record(
            "founder_approval", payload, actor="founder",
            created_at=payload["approved_at"], head_sha=payload["head_sha"],
        )
        return record, SealedFakeGitHubTransport(evidence)

    def context(self, **overrides):
        approval, transport = self.approval()
        value = {
            "state": "Merge Authorized",
            "mission_id": "mission-7",
            "repository": "acme/widgets",
            "pull_request": 42,
            "head_sha": "2" * 40,
            "merge_method": "squash",
            "required_checks": ["EOS", "Tests"],
            "status_checks": {"EOS": "success", "Tests": "success"},
            "adversarial_review_complete": True,
            "unresolved_threads": 0,
            "tier_valid": True,
            "evidence": {
                "schema_version": "1.0.0", "mission_id": "mission-7",
                "repository": "acme/widgets", "pull_request": 42,
                "base_sha": "1" * 40, "head_sha": "2" * 40,
                "generated_at": "2026-07-15T13:00:00Z",
                "policy_hash": "a" * 64, "mission_hash": "b" * 64,
                "audit_head_hash": "c" * 64,
                "status_checks": [{"name": "EOS", "conclusion": "success"}],
                "artifacts": [{"name": "report", "sha256": "d" * 64, "size_bytes": 1, "source": "ci"}],
                "cleanup_state": "complete", "deployment_state": "not_authorized",
            },
            "approval": approval,
            "founder_identities": ["founder"],
            "now": "2026-07-15T13:00:00Z",
            "latest_commit_at": "2026-07-15T11:59:00Z",
            "evidence_verifier": transport,
            "consumption_store": self.store,
            "auto_merge_requested": False,
            "auto_merge_enabled": False,
        }
        value.update(overrides)
        return value

    def test_exact_manual_merge_is_authorized_as_decision_only(self):
        decision = authorize_merge(**self.context())
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.code, "MANUAL_MERGE_AUTHORIZED")
        self.assertFalse(decision.deployment_authorized)
        self.assertFalse(decision.cutover_authorized)

    def test_every_merge_gate_fails_closed(self):
        cases = (
            ("state", "Founder Approval", "MERGE_STATE_DENIED"),
            ("required_checks", [], "MERGE_CHECKS_INCOMPLETE"),
            ("status_checks", {"EOS": "success"}, "MERGE_CHECKS_INCOMPLETE"),
            ("adversarial_review_complete", False, "MERGE_REVIEW_INCOMPLETE"),
            ("unresolved_threads", 1, "MERGE_THREADS_UNRESOLVED"),
            ("unresolved_threads", False, "MERGE_THREADS_UNRESOLVED"),
            ("tier_valid", False, "MERGE_TIER_INVALID"),
            ("approval", {}, "MERGE_APPROVAL_INVALID"),
            ("evidence", {}, "MERGE_EVIDENCE_INVALID"),
        )
        for field, value, code in cases:
            self.assertEqual(authorize_merge(**self.context(**{field: value})).code, code)

    def test_auto_merge_requires_explicit_policy_enablement(self):
        self.assertEqual(
            authorize_merge(**self.context(auto_merge_requested=True)).code,
            "AUTO_MERGE_DISABLED",
        )
        self.assertEqual(
            authorize_merge(**self.context(
                auto_merge_requested=True, auto_merge_enabled=True,
            )).code,
            "AUTO_MERGE_AUTHORIZED",
        )

    def test_merge_adapter_forms_templates_and_docs_are_non_mutating(self):
        workflow = (
            ROOT / ".github/workflows/reusable-merge-authorization.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("permissions: {}", workflow)
        self.assertNotIn("pull-requests: write", workflow)
        self.assertNotIn("gh pr merge", workflow)
        self.assertNotIn("auto-merge", workflow)
        self.assertIn(
            "run: kernel/scripts/engineering-os/validate-merge-authorization",
            workflow,
        )
        self.assertNotIn(
            "run: scripts/engineering-os/validate-merge-authorization",
            workflow,
        )
        self.assertTrue((
            ROOT / "scripts/engineering-os/validate-merge-authorization"
        ).is_file())
        for name in ("engineering-mission.yml", "engineering-incident.yml", "config.yml"):
            self.assertTrue((ROOT / ".github/ISSUE_TEMPLATE" / name).is_file())
        self.assertTrue((ROOT / ".github/PULL_REQUEST_TEMPLATE.md").is_file())
        for name in (
            "MISSION_LIFECYCLE.md", "DEFINITION_OF_READY.md",
            "DEFINITION_OF_DONE.md", "INCIDENT_AND_ROLLBACK.md",
        ):
            self.assertTrue((ROOT / "docs/engineering-os" / name).is_file())


if __name__ == "__main__":
    unittest.main()
