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
# The retired activation nonce is referenced only by its digest identity. The
# raw preimage is deliberately NOT embedded here — committing it would disclose
# the very value the readiness evidence says must be represented by digest only.
RETIRED_NONCE_SHA256 = "db6eaa2a8221f6e4529b85cb3fc80019318e00f491ed04858cc1f81c604f2512"


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

    def _run_validator(self, sha_override=None):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / JSON_PATH.name).write_bytes(JSON_PATH.read_bytes())
            (tmp / MD_PATH.name).write_bytes(MD_PATH.read_bytes())
            (tmp / SHA_PATH.name).write_text(
                sha_override if sha_override is not None else SHA_PATH.read_text(encoding="utf-8"),
                encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(VALIDATOR), str(tmp / JSON_PATH.name), str(tmp / MD_PATH.name)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def test_conflicting_digest_line_fails_closed(self):
        # Correct digests plus an extra contradictory line must be rejected.
        tampered = SHA_PATH.read_text(encoding="utf-8") + "\nactivation-readiness-snapshot.json  %s\n" % ("0" * 64)
        result = self._run_validator(sha_override=tampered)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("READINESS_SNAPSHOT_INVALID", result.stderr)

    def test_extra_unexpected_digest_entry_fails_closed(self):
        tampered = SHA_PATH.read_text(encoding="utf-8") + "\nrogue-artifact.bin  %s\n" % ("a" * 64)
        result = self._run_validator(sha_override=tampered)
        self.assertNotEqual(result.returncode, 0)

    def test_stale_identity_row_in_markdown_fails_closed(self):
        import hashlib
        import tempfile
        commit = self.snapshot["repository_identity"]["commit"]
        stale_md = self.md.replace(
            "| commit | `%s` |" % commit, "| commit | `%s` |" % ("0" * 40), 1)
        self.assertNotEqual(stale_md, self.md)
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / JSON_PATH.name).write_bytes(JSON_PATH.read_bytes())
            (tmp / MD_PATH.name).write_text(stale_md, encoding="utf-8")
            (tmp / SHA_PATH.name).write_text(
                "# digests\n%s  %s\n%s  %s\n" % (
                    JSON_PATH.name, hashlib.sha256(JSON_PATH.read_bytes()).hexdigest(),
                    MD_PATH.name, hashlib.sha256(stale_md.encode()).hexdigest()),
                encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), str(tmp / JSON_PATH.name), str(tmp / MD_PATH.name)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("identity fields disagree", result.stderr)

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

    def test_retired_nonce_represented_only_by_digest_identity(self):
        auth = self.snapshot["baseline_identity"]["authorization_authenticity"]
        self.assertIs(auth["raw_nonce_disclosed"], False)
        # Only the digest identity of the retired nonce is recorded, and it
        # matches the known digest. The raw preimage is never embedded, so this
        # test cannot and does not reproduce it.
        self.assertEqual(auth["retired_nonce_sha256"], RETIRED_NONCE_SHA256)

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
