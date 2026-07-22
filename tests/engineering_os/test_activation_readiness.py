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

    def test_required_ci_name_matches_branch_protection_context(self):
        contexts = set(self.snapshot["repository_identity"]["branch_protection_required_contexts"])
        ci_names = {c["name"] for c in self.snapshot["validation_and_review"]["required_ci_on_main"]}
        # Every recorded required-CI evidence name must be an actual required context.
        self.assertTrue(ci_names <= contexts, (ci_names, contexts))

    def _tamper_and_validate(self, replace_old, replace_new):
        import hashlib
        import tempfile
        tampered = self.md.replace(replace_old, replace_new, 1)
        self.assertNotEqual(tampered, self.md)
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / JSON_PATH.name).write_bytes(JSON_PATH.read_bytes())
            (tmp / MD_PATH.name).write_text(tampered, encoding="utf-8")
            (tmp / SHA_PATH.name).write_text(
                "# d\n%s  %s\n%s  %s\n" % (
                    JSON_PATH.name, hashlib.sha256(JSON_PATH.read_bytes()).hexdigest(),
                    MD_PATH.name, hashlib.sha256(tampered.encode()).hexdigest()),
                encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(VALIDATOR), str(tmp / JSON_PATH.name), str(tmp / MD_PATH.name)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def test_drifted_boundary_rows_fail_closed(self):
        for row in ("| deployment_performed | `False` |",
                    "| credential_or_secret_changed | `False` |",
                    "| authenticated_history_rewritten | `False` |"):
            result = self._tamper_and_validate(row, row.replace("`False`", "`True`"))
            self.assertNotEqual(result.returncode, 0, row)
            self.assertIn("disagrees with the JSON", result.stderr)

    def test_wrong_governing_mission_number_fails_closed(self):
        result = self._tamper_and_validate(
            "Governing mission:** #40 (Ready", "Governing mission:** #99 (Ready")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("governing-mission", result.stderr)

    def test_incomplete_mission_binding_set_fails_closed(self):
        # Drop a predecessor binding from BOTH JSON and Markdown and refresh all
        # digests so only the required-set check can catch it.
        import hashlib
        import re
        import tempfile
        snap = json.loads(JSON_PATH.read_text(encoding="utf-8"))
        snap["mission_bindings"].pop("38")
        new_json = json.dumps(snap, indent=2, sort_keys=True) + "\n"
        json_digest = hashlib.sha256(new_json.encode()).hexdigest()
        md = "\n".join(l for l in self.md.splitlines() if not l.startswith("| #38 |")) + "\n"
        md = re.sub(r"(Machine artifact:\*\* `[^`]+` — sha256 `)[0-9a-f]{64}(`)",
                    r"\g<1>%s\g<2>" % json_digest, md)
        md_digest = hashlib.sha256(md.encode()).hexdigest()
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            (tmp / JSON_PATH.name).write_text(new_json, encoding="utf-8")
            (tmp / MD_PATH.name).write_text(md, encoding="utf-8")
            (tmp / SHA_PATH.name).write_text(
                "# d\n%s  %s\n%s  %s\n" % (JSON_PATH.name, json_digest, MD_PATH.name, md_digest),
                encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), str(tmp / JSON_PATH.name), str(tmp / MD_PATH.name)],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("required predecessor set", result.stderr)

    def test_drifted_mission_binding_and_table_rows_fail_closed(self):
        # A drifted mission-binding hash, ledger count, or historical field in
        # the Markdown must fail closed even when the digest file is refreshed.
        h26 = self.snapshot["mission_bindings"]["26"]["ready_event_hash"]
        cases = [
            ("`%s` |" % h26, "`%s` |" % ("0" * 64)),
            ("| authorized | `1` |", "| authorized | `9` |"),
            ("| rollback_sha | `%s` |" % self.snapshot["baseline_identity"]["historical"]["rollback_sha"],
             "| rollback_sha | `%s` |" % ("0" * 40)),
        ]
        for old, new in cases:
            result = self._tamper_and_validate(old, new)
            self.assertNotEqual(result.returncode, 0, (old, new))
            self.assertIn("READINESS_SNAPSHOT_INVALID", result.stderr)

    def test_stale_active_endpoint_rows_fail_closed(self):
        commit = self.snapshot["repository_identity"]["commit"]
        for row in ("active_execution_commit", "active_endpoint_commit"):
            result = self._tamper_and_validate(
                "| %s | `%s` |" % (row, commit), "| %s | `%s` |" % (row, "0" * 40))
            self.assertNotEqual(result.returncode, 0, row)
            self.assertIn(row, result.stderr)

    def test_stale_event_hash_in_markdown_fails_closed(self):
        auth_hash = self.snapshot["baseline_identity"]["authorization_authenticity"]["authorization_event_hash"]
        result = self._tamper_and_validate(
            "event hash `%s`" % auth_hash, "event hash `%s`" % ("0" * 64))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("authorization event hash", result.stderr)

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
