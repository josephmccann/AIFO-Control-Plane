import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from engineering_os.test_integrity_cli import establish_initial_baseline


ROOT = Path(__file__).resolve().parents[2]
CANONICAL_SHA = "23211f7a871c8a9a9f15cb5c010fd5167a1f21314bceebe43c2a38d8d1f04c0e"


class InitialBaselineTests(unittest.TestCase):
    def test_baseline_binds_exact_tree_and_complete_governed_surface(self):
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
        ).strip()
        with tempfile.TemporaryDirectory() as directory:
            value = establish_initial_baseline(
                ROOT, commit, Path(directory) / "baseline.json",
                canonical_inventory_sha256=CANONICAL_SHA,
            )
        self.assertEqual(commit, value["commit_sha"])
        self.assertEqual(
            subprocess.check_output(
                ["git", "rev-parse", "HEAD^{tree}"], cwd=ROOT, text=True,
            ).strip(),
            value["tree_sha"],
        )
        self.assertEqual("pending_independent_review", value["activation_state"])
        self.assertTrue(value["single_use"])
        paths = {item["path"] for item in value["records"]}
        self.assertIn("engineering_os/test_integrity.py", paths)
        self.assertIn("tests/engineering_os/test_test_integrity_baseline.py", paths)
        self.assertGreater(value["resource_usage"]["files"], 0)

    def test_baseline_rejects_wrong_commit_and_canonical_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "baseline.json"
            with self.assertRaisesRegex(ValueError, "TEST_BASELINE_HEAD_MISMATCH"):
                establish_initial_baseline(
                    ROOT, "0" * 40, output, canonical_inventory_sha256=CANONICAL_SHA,
                )
            commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
            ).strip()
            with self.assertRaisesRegex(ValueError, "TEST_BASELINE_CANONICAL_INVALID"):
                establish_initial_baseline(ROOT, commit, output, canonical_inventory_sha256="bad")

    def test_baseline_output_is_closed_and_deterministic(self):
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
        ).strip()
        with tempfile.TemporaryDirectory() as directory:
            first = Path(directory) / "first.json"
            second = Path(directory) / "second.json"
            establish_initial_baseline(ROOT, commit, first, canonical_inventory_sha256=CANONICAL_SHA)
            establish_initial_baseline(ROOT, commit, second, canonical_inventory_sha256=CANONICAL_SHA)
            self.assertEqual(json.loads(first.read_text()), json.loads(second.read_text()))


if __name__ == "__main__":
    unittest.main()
