import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/engineering-os/validate-activation-closure"


class ActivationClosureTests(unittest.TestCase):
    def artifact(self):
        return json.loads(
            (ROOT / "docs/engineering-os/ACTIVATION_DEPENDENCY_CLOSURE.json").read_text(
                encoding="utf-8"
            )
        )

    def run_validator(self, artifact):
        with tempfile.NamedTemporaryFile("w", suffix=".json") as stream:
            json.dump(artifact, stream)
            stream.flush()
            return subprocess.run([str(SCRIPT), stream.name, artifact["final"]["sha"]], cwd=ROOT,
                                  text=True, capture_output=True)

    def test_exact_mission_32_closure_is_accepted(self):
        result = self.run_validator(self.artifact())
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_shipped_closure_replays_from_git_and_ignores_worktree_tamper(self):
        with tempfile.TemporaryDirectory() as directory:
            clone = Path(directory) / "clone"
            subprocess.run(
                ["git", "clone", "--quiet", "--no-local", str(ROOT), str(clone)],
                check=True,
            )
            closure_path = clone / "docs/engineering-os/ACTIVATION_DEPENDENCY_CLOSURE.json"
            closure = json.loads(closure_path.read_text(encoding="utf-8"))
            command = [
                str(clone / "scripts/engineering-os/validate-activation-closure"),
                str(closure_path),
                closure["final"]["sha"],
            ]
            clean = subprocess.run(command, cwd=clone, text=True, capture_output=True)
            self.assertEqual(clean.returncode, 0, clean.stderr)

            records = clone / closure["records"]["path"]
            records.write_text('{"tampered":true}\n', encoding="utf-8")
            tampered = subprocess.run(command, cwd=clone, text=True, capture_output=True)
            self.assertEqual(tampered.returncode, 0, tampered.stderr)

    def test_mission_ready_identity_and_scope_fail_closed(self):
        mutations = []
        issue = self.artifact(); issue["mission"]["issue"] = 31; mutations.append(issue)
        ready = self.artifact(); ready["mission"]["ready_event"]["event_hash"] = "0" * 64; mutations.append(ready)
        declaration = self.artifact(); declaration["mission"]["declaration_sha256"] = "0" * 64; mutations.append(declaration)
        scope = self.artifact(); scope["mission"]["allowed_paths"].pop(); mutations.append(scope)
        for artifact in mutations:
            with self.subTest(artifact=artifact):
                self.assertNotEqual(self.run_validator(artifact).returncode, 0)

    def test_historical_evidence_classification_and_reconciliation_fail_closed(self):
        mutations = []
        historical = self.artifact(); historical["historical"]["mission_31"]["candidate"]["sha"] = "0" * 40; mutations.append(historical)
        classification = self.artifact(); classification["classification"]["unknown_executable"] = "ignore"; mutations.append(classification)
        reconciliation = self.artifact(); reconciliation["reconciliation"]["result"] = "fail"; mutations.append(reconciliation)
        stale = self.artifact(); stale["reconciliation"]["sha256"] = "0" * 64; mutations.append(stale)
        for artifact in mutations:
            with self.subTest(artifact=artifact):
                self.assertNotEqual(self.run_validator(artifact).returncode, 0)

    def test_missing_extra_stale_and_contradictory_records_fail(self):
        mutations = []
        missing = self.artifact(); missing["files"].pop(); mutations.append(missing)
        stale = self.artifact(); stale["files"][0]["sha256"] = "0" * 64; mutations.append(stale)
        review = self.artifact(); review["reviews"][1]["important"] = 1; mutations.append(review)
        edge = self.artifact(); edge["edges"][0]["to"] = "outside"; mutations.append(edge)
        for artifact in mutations:
            with self.subTest(artifact=artifact):
                self.assertNotEqual(self.run_validator(artifact).returncode, 0)


if __name__ == "__main__":
    unittest.main()
