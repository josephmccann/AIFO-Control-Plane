import copy
import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/engineering-os/validate-activation-closure"
SUBJECT = "da301963cc430883bdd3623e734aed0e06d52d18"
BASE = "d3a5e29f47ab53a5190e32f3bb0edfd2cbdc1533"


class ActivationClosureTests(unittest.TestCase):
    def artifact(self):
        paths = subprocess.check_output(
            ["git", "diff", "--name-only", BASE, SUBJECT], cwd=ROOT, text=True
        ).splitlines()
        allowed = sorted(set(paths) | {"docs/engineering-os/ACTIVATION_DEPENDENCY_CLOSURE.json"})
        files = []
        for path in paths:
            data = subprocess.check_output(["git", "show", "%s:%s" % (SUBJECT, path)], cwd=ROOT)
            files.append({"path": path, "sha256": hashlib.sha256(data).hexdigest(), "reason": "Mission 31 closure"})
        evidence = []
        for path in ("outputs/mission-31-analysis/implementation-plan.md", "outputs/mission-31-analysis/state-record.md"):
            evidence.append({"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()})
        return {
            "schema_version": "1.0.0",
            "mission": {"repository": "josephmccann/AIFO-Control-Plane", "issue": 31,
                        "declaration_path": "outputs/successor-mission-declaration.md",
                        "declaration_sha256": "69f1acaee16c266ae727af7261c1ea8b33f0812c133cf9b730be71ec1561ab62",
                        "ready_declaration_sha256": "9996e5ebebd26b297e5ce57bcc4d4e78b01723d78052bea0b385a1ad5b95a9e0",
                        "allowed_paths": allowed},
            "base": {"sha": BASE, "tree": subprocess.check_output(["git", "rev-parse", BASE + "^{tree}"], cwd=ROOT, text=True).strip()},
            "final": {"sha": SUBJECT, "tree": subprocess.check_output(["git", "rev-parse", SUBJECT + "^{tree}"], cwd=ROOT, text=True).strip()},
            "files": files,
            "edges": [{"from": paths[1], "to": paths[0], "kind": "validates"}],
            "pins": [], "tests": [{"command": "focused", "result": "pass", "head": SUBJECT,
                "evidence_path": "outputs/mission-31-analysis/implementation-plan.md",
                "evidence_sha256": hashlib.sha256((ROOT / "outputs/mission-31-analysis/implementation-plan.md").read_bytes()).hexdigest()}],
            "evidence": evidence,
            "reviews": [
                {"reviewer": "review-a", "checkpoint": "1" * 64, "head": SUBJECT, "critical": 0, "important": 0,
                 "report_path": "outputs/mission-31-review/reviewer-a/final-review.md",
                 "report_sha256": hashlib.sha256((ROOT / "outputs/mission-31-review/reviewer-a/final-review.md").read_bytes()).hexdigest()},
                {"reviewer": "review-b", "checkpoint": "2" * 64, "head": SUBJECT, "critical": 0, "important": 0,
                 "report_path": "outputs/mission-31-review/reviewer-a/final-review.md",
                 "report_sha256": hashlib.sha256((ROOT / "outputs/mission-31-review/reviewer-a/final-review.md").read_bytes()).hexdigest()},
            ],
        }

    def run_validator(self, artifact):
        with tempfile.NamedTemporaryFile("w", suffix=".json") as stream:
            json.dump(artifact, stream)
            stream.flush()
            return subprocess.run([str(SCRIPT), stream.name, SUBJECT], cwd=ROOT,
                                  text=True, capture_output=True)

    def test_exact_closure_is_accepted(self):
        result = self.run_validator(self.artifact())
        self.assertEqual(result.returncode, 0, result.stderr)

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
