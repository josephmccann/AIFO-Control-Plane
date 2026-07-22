import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SNAP_DIR = ROOT / "outputs" / "eos-activation-readiness"
JSON_PATH = SNAP_DIR / "activation-readiness-snapshot.json"
MD_PATH = SNAP_DIR / "activation-readiness-snapshot.md"
SHA_PATH = SNAP_DIR / "activation-readiness-snapshot.sha256"
VALIDATOR = ROOT / "scripts" / "engineering-os" / "validate-activation-readiness"
RETIRED_NONCE = "1debd522934132f605455acb7f279f4abd2ec343cebb7ecf0f844ec880b723d1"


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ActivationReadinessSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.snapshot = json.loads(JSON_PATH.read_text(encoding="utf-8"))
        self.md = MD_PATH.read_text(encoding="utf-8")

    def test_validator_accepts_the_committed_snapshot(self):
        result = subprocess.run(
            [sys.executable, str(VALIDATOR), str(JSON_PATH), str(MD_PATH)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("READINESS_SNAPSHOT_VALID", result.stdout)

    def test_digest_file_matches_actual_artifacts(self):
        sha_text = SHA_PATH.read_text(encoding="utf-8")
        self.assertIn(_sha256(JSON_PATH), sha_text)
        self.assertIn(_sha256(MD_PATH), sha_text)

    def test_markdown_and_json_reference_the_same_commit_and_tree(self):
        commit = self.snapshot["repository_identity"]["commit"]
        tree = self.snapshot["repository_identity"]["tree"]
        self.assertIn(commit, self.md)
        self.assertIn(tree, self.md)
        self.assertEqual(self.snapshot["metadata"]["source_of_truth_commit"], commit)
        self.assertEqual(
            self.snapshot["baseline_identity"]["active_execution"]["active_execution_commit"], commit)
        self.assertEqual(
            self.snapshot["compatibility_chain"]["active_endpoint_commit"], commit)

    def test_raw_retired_nonce_never_appears(self):
        self.assertNotIn(RETIRED_NONCE, JSON_PATH.read_text(encoding="utf-8"))
        self.assertNotIn(RETIRED_NONCE, self.md)
        auth = self.snapshot["baseline_identity"]["authorization_authenticity"]
        self.assertIs(auth["raw_nonce_disclosed"], False)
        # Only the digest identity of the retired nonce is recorded.
        self.assertEqual(
            auth["retired_nonce_sha256"],
            hashlib.sha256(RETIRED_NONCE.encode()).hexdigest())

    def test_ledger_state_is_fail_closed_preactivation(self):
        ledger = self.snapshot["activation_ledger_state"]
        self.assertEqual(ledger["authorized"], 1)
        self.assertEqual(ledger["attempted"], 0)
        self.assertEqual(ledger["consumed"], 0)
        self.assertEqual(
            ledger["proof_retired_nonce_rejected"]["result"],
            [False, "ACTIVATION_NONCE_RETIRED"])
        self.assertTrue(ledger["no_event_appended_during_validation"])

    def test_compatibility_chain_recorded_valid(self):
        chain = self.snapshot["compatibility_chain"]
        self.assertEqual(chain["validation_result"], "COMPATIBILITY_CHAIN_VALID")
        self.assertTrue(chain["validated"])
        self.assertGreater(chain["commit_count"], 0)

    def test_all_six_mission_bindings_present(self):
        bindings = self.snapshot["mission_bindings"]
        for issue in ("26", "31", "32", "35", "36", "38"):
            self.assertIn(issue, bindings)
            self.assertRegex(bindings[issue]["declaration_digest"], r"^[0-9a-f]{64}$")
            self.assertRegex(bindings[issue]["ready_event_hash"], r"^[0-9a-f]{64}$")

    def test_boundaries_confirm_no_privileged_action(self):
        b = self.snapshot["security_and_operational_boundaries"]
        self.assertFalse(b["deployment_performed"])
        self.assertEqual(b["deployment_record_5528959623_state"], "inactive")
        self.assertFalse(b["pr_24_changed"])
        self.assertFalse(b["authenticated_history_rewritten"])
        self.assertFalse(b["force_push"])

    def test_authority_statement_prefers_git_over_timestamps(self):
        statement = self.snapshot["metadata"]["authority_statement"]
        self.assertIn("authoritative", statement)
        self.assertIn("informational", statement)


if __name__ == "__main__":
    unittest.main()
