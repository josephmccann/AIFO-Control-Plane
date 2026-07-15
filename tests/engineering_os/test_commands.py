import json
import subprocess
import unittest
from pathlib import Path

from engineering_os.commands import concurrency_key, parse_command, propose_event


ROOT = Path(__file__).resolve().parents[2]


class CommandTests(unittest.TestCase):
    def test_only_exact_supported_eos_commands_parse(self):
        self.assertEqual(parse_command("/eos claim"), ("claim", ()))
        self.assertEqual(parse_command("/eos heartbeat nonce-1"), ("heartbeat", ("nonce-1",)))
        for text in ("please /eos claim", "/eos claim now", "/EOS claim", "/eos", "/eos deploy"):
            with self.subTest(text=text):
                self.assertIsNone(parse_command(text))

    def test_concurrency_key_is_stable_per_repository_issue(self):
        self.assertEqual(
            concurrency_key("josephmccann/AIFO-Control-Plane", 123),
            "eos-mission-josephmccann-AIFO-Control-Plane-123",
        )

    def test_event_proposal_uses_normalized_metadata_nonce_and_hash(self):
        proposal = propose_event(
            mission_id="aifo-101", event_type="lease.heartbeat", actor="Agent-A",
            actor_role="producer", occurred_at="2026-07-15T10:05:00+00:00",
            source_url="https://github.com/example/repo/issues/1#issuecomment-2",
            nonce="nonce-1", details={"lease_owner": "Agent-A"},
        )
        self.assertEqual(proposal["occurred_at"], "2026-07-15T10:05:00Z")
        self.assertEqual(proposal["details"]["nonce"], "nonce-1")
        self.assertEqual(len(proposal["proposal_hash"]), 64)
        self.assertNotIn("sequence", proposal)
        self.assertNotIn("event_hash", proposal)

    def test_transition_wrapper_emits_proposal_without_mutation(self):
        command = ROOT / "scripts/engineering-os/transition-mission"
        result = subprocess.run(
            [str(command), "--mission-id", "aifo-101", "--event-type", "mission.ready",
             "--actor", "agent-a", "--actor-role", "producer",
             "--occurred-at", "2026-07-15T10:05:00Z", "--source-url", "https://example.test/1",
             "--nonce", "nonce-cli"],
            cwd=ROOT, check=True, capture_output=True, text=True,
        )
        proposal = json.loads(result.stdout)
        self.assertEqual(proposal["type"], "mission.ready")
        self.assertEqual(proposal["details"]["nonce"], "nonce-cli")

    def test_mission_workflow_is_exact_authorized_and_serialized(self):
        workflow = (ROOT / ".github/workflows/mission-command.yml").read_text(encoding="utf-8")
        self.assertIn("issues: write", workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn("eos-mission-${{ github.repository }}-${{ github.event.issue.number }}", workflow)
        self.assertIn("parse_command", workflow)
        self.assertIn("founder_identities", workflow)
        self.assertIn("validate_event_chain", workflow)
        self.assertIn("comments_by_url", workflow)
        self.assertIn("source = comments_by_url.get(event[\"source_url\"])", workflow)
        self.assertIn("cancel-in-progress: false", workflow)
        self.assertNotIn("pull-requests: write", workflow)

    def test_orphan_recovery_is_dry_run_unless_disabled_policy_flag_is_enabled(self):
        workflow = (ROOT / ".github/workflows/reusable-orphan-recovery.yml").read_text(encoding="utf-8")
        self.assertIn("schedule:", workflow)
        self.assertIn("dry_run", workflow)
        self.assertIn("default: true", workflow)
        self.assertIn("vars.EOS_ORPHAN_RECOVERY_ENABLED == 'true'", workflow)
        self.assertIn("issues: read", workflow)
        self.assertIn("issues: write", workflow)
        self.assertIn("mutation_performed", workflow)
        self.assertIn("release_mission", workflow)
        self.assertIn("validate_event_chain", workflow)
        self.assertIn("-f body=\"$body\"", workflow)

    def test_reusable_validation_has_read_only_permissions(self):
        workflow = (ROOT / ".github/workflows/reusable-mission-validation.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_call:", workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn("issues: read", workflow)
        self.assertIn("comments_by_url", workflow)
        self.assertNotIn("issues: write", workflow)


if __name__ == "__main__":
    unittest.main()
