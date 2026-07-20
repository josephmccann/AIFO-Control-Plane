import copy
import hashlib
import json
import subprocess
import tempfile
import unittest
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/engineering-os/validate-activation-closure"
SUBJECT = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
BASE = "c4cd413d0f77a9213bccb8f8f908dec0b292e41d"


class ActivationClosureTests(unittest.TestCase):
    def setUp(self):
        self.review_dir = ROOT / "outputs/mission-31-review"
        self.review_dir.mkdir(parents=True, exist_ok=True)
        self.review_paths = []
        self.addCleanup(self.cleanup_review_fixtures)

    def cleanup_review_fixtures(self):
        for path in self.review_paths:
            if path.exists():
                path.unlink()

    def review_fixture(self, reviewer):
        path = self.review_dir / (reviewer + "-generated.md")
        body = (
            "Reviewer: %s\n"
            "HEAD: `%s`\n"
            "Critical: 0\n"
            "Important: 0\n"
            "PASS\n"
        ) % (reviewer, SUBJECT)
        checkpoint = hashlib.sha256(body.encode()).hexdigest()
        path.write_text(body + "Checkpoint: " + checkpoint + "\n", encoding="utf-8")
        self.review_paths.append(path)
        return path, checkpoint

    def artifact(self):
        paths = subprocess.check_output(
            ["git", "diff", "--name-only", BASE, SUBJECT], cwd=ROOT, text=True
        ).splitlines()
        pins = []
        pattern = re.compile(r"josephmccann/AIFO-Control-Plane/.github/actions/materialize-kernel@([0-9a-f]{40})")
        for path in sorted(path for path in paths if path.startswith(".github/workflows/")):
            content = subprocess.check_output(["git", "show", "%s:%s" % (SUBJECT, path)], cwd=ROOT, text=True)
            pins.extend({"consumer": path, "sha": sha} for sha in sorted(set(pattern.findall(content))))
        declaration = (ROOT / "outputs/successor-mission-declaration.md").read_text()
        allowed = sorted(json.loads(re.search(r"<!-- EOS:MISSION:BEGIN -->\s*(\{.*?\})\s*<!-- EOS:MISSION:END -->", declaration, re.S).group(1))["allowed_paths"])
        files = []
        for path in paths:
            data = subprocess.check_output(["git", "show", "%s:%s" % (SUBJECT, path)], cwd=ROOT)
            files.append({"path": path, "sha256": hashlib.sha256(data).hexdigest(), "reason": "Mission 31 closure"})
        evidence = []
        for path in ("docs/engineering-os/ACTIVATION_INTEGRATION_SCOPE.md", "docs/engineering-os/EVIDENCE_AND_AUDIT.md"):
            evidence.append({"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()})
        review_a, checkpoint_a = self.review_fixture("test-a")
        review_b, checkpoint_b = self.review_fixture("test-b")
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
            "edges": [{"from": test, "to": source, "kind": "tests"}
                      for test in sorted(path for path in paths if path.startswith("tests/"))
                      for source in sorted(path for path in paths if not path.startswith("tests/"))],
            "pins": pins, "tests": [{"command": "fixture", "result": "pass", "head": SUBJECT,
                "evidence_path": "docs/engineering-os/ACTIVATION_INTEGRATION_SCOPE.md",
                "evidence_sha256": hashlib.sha256((ROOT / "docs/engineering-os/ACTIVATION_INTEGRATION_SCOPE.md").read_bytes()).hexdigest()}],
            "evidence": evidence,
            "reviews": [
                {"reviewer": "test-a", "checkpoint": checkpoint_a, "head": SUBJECT, "critical": 0, "important": 0,
                 "report_path": review_a.relative_to(ROOT).as_posix(),
                 "report_sha256": hashlib.sha256(review_a.read_bytes()).hexdigest()},
                {"reviewer": "test-b", "checkpoint": checkpoint_b, "head": SUBJECT, "critical": 0, "important": 0,
                 "report_path": review_b.relative_to(ROOT).as_posix(),
                 "report_sha256": hashlib.sha256(review_b.read_bytes()).hexdigest()},
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
