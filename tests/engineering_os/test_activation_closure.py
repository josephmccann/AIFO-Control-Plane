import copy
import hashlib
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/engineering-os/validate-activation-closure"
BASE = "283f37b97a9df24ca056c5115197464043312185"
READY_SHA = "72a5059b338fca592333f6a77d64eafef9ee13ea51d6da7d32e4859b12ba54a9"
READY_EVENT_HASH = "f83d273132d927f3c31eb5f931cc6aacba9ad93cd475b8f669179ceea1c5a16d"
PRE_READY_HEAD = "7fd26fecc00f6d0c6ce4a7535a66b01aace064a7"
PRE_READY_TREE = "aae7823d40235779f914a5486aa90ea91b106c1d"
PRE_READY_CLOSURE_SHA = "7c51214965441ef93008fdff629c0637e3e208de626c1e933920cb5308e70ebb"
ALLOWED_PATHS = [
    "docs/engineering-os/ACTIVATION_DEPENDENCY_CLOSURE.json",
    "outputs/mission-31-review/closure-records-d68c5da.json",
    "outputs/mission-31-review/mission-32-review-a-final-r2.md",
    "outputs/mission-31-review/mission-32-review-b-final-r2.md",
    "outputs/mission-31-validation/ci-29772912364.log",
    "outputs/mission-32-closure-records-ready.json",
    "outputs/mission-32-reconciliation-ready.md",
    "outputs/mission-32-reconciliation.md",
    "outputs/mission-32-review-a-ready.md",
    "outputs/mission-32-review-b-ready.md",
    "outputs/mission-32-validation/exact-head-ci-ready.log",
    "schemas/engineering-os/activation-closure.schema.json",
    "scripts/engineering-os/validate-activation-closure",
    "scripts/validate.sh",
    "tests/engineering_os/test_activation_closure.py",
    "tests/engineering_os/test_validation_classification.py",
]


class ActivationClosureTests(unittest.TestCase):
    def subject(self):
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()

    def setUp(self):
        self.saved = {}
        self.paths = {
            "historical_ci": ROOT / "outputs/mission-31-validation/ci-29772912364.log",
            "historical_a": ROOT / "outputs/mission-31-review/mission-32-review-a-final-r2.md",
            "historical_b": ROOT / "outputs/mission-31-review/mission-32-review-b-final-r2.md",
            "records": ROOT / "outputs/mission-32-closure-records-ready.json",
            "validation": ROOT / "outputs/mission-32-validation/exact-head-ci-ready.log",
            "review_a": ROOT / "outputs/mission-32-review-a-ready.md",
            "review_b": ROOT / "outputs/mission-32-review-b-ready.md",
            "reconciliation": ROOT / "outputs/mission-32-reconciliation-ready.md",
        }
        for path in self.paths.values():
            self.saved[path] = path.read_bytes() if path.is_file() else None
            path.parent.mkdir(parents=True, exist_ok=True)
        for key in ("historical_ci", "historical_a", "historical_b"):
            if not self.paths[key].is_file():
                self.paths[key].write_text("preserved Mission 31 evidence\n", encoding="utf-8")
        self.paths["records"].write_text('{"fixture":true}\n', encoding="utf-8")
        result = subprocess.run(
            ["python3", "-m", "unittest", "tests.engineering_os.test_schema"],
            cwd=ROOT, env={**os.environ, "PYTHONPATH": "."}, text=True,
            capture_output=True, check=True,
        )
        self.paths["validation"].write_text(
            "Command: validate-all\nWorkflow: .github/workflows/terraform-validate.yml\n"
            "Run ID: 1\nRun attempt: 1\n%s%sHEAD: %s\n"
            "Terraform: PASS\nActionlint: PASS\nShellCheck: PASS\nPython: PASS\n"
            "Classification: PASS\nClosure: PASS\nValidation complete\n"
            % (result.stdout, result.stderr, self.subject()), encoding="utf-8",
        )
        self._write_review("review_a", "mission-32-reviewer-a-ready")
        self._write_review("review_b", "mission-32-reviewer-b-ready")
        self.paths["reconciliation"].write_text(
            "HEAD: `%s`\nCritical: 0\nImportant: 0\nReconciliation: PASS\n" % self.subject(),
            encoding="utf-8",
        )
        self.addCleanup(self.restore_evidence)

    def restore_evidence(self):
        for path, content in self.saved.items():
            if content is None:
                path.unlink(missing_ok=True)
            else:
                path.write_bytes(content)

    def _write_review(self, key, reviewer):
        body = (
            "Reviewer: %s\nHEAD: `%s`\nCritical: 0\nImportant: 0\nPASS\n"
            % (reviewer, self.subject())
        )
        checkpoint = hashlib.sha256(body.encode()).hexdigest()
        self.paths[key].write_text(body + "Checkpoint: " + checkpoint + "\n", encoding="utf-8")
        return checkpoint

    def file_record(self, path):
        return {"path": path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    def artifact(self):
        subject = self.subject()
        paths = subprocess.check_output(
            ["git", "diff", "--name-only", BASE, subject], cwd=ROOT, text=True
        ).splitlines()
        files = []
        for path in paths:
            data = subprocess.check_output(["git", "show", "%s:%s" % (subject, path)], cwd=ROOT)
            files.append({"path": path, "sha256": hashlib.sha256(data).hexdigest(), "reason": "Mission 32 implementation"})
        checkpoint_a = self._write_review("review_a", "mission-32-reviewer-a-ready")
        checkpoint_b = self._write_review("review_b", "mission-32-reviewer-b-ready")
        return {
            "schema_version": "1.0.0",
            "mission": {
                "repository": "josephmccann/AIFO-Control-Plane",
                "issue": 32,
                "mission_id": "aifo-control-plane-validation-classification-successor-ready-exception-2026-07-20",
                "declaration_path": "https://github.com/josephmccann/AIFO-Control-Plane/issues/32",
                "declaration_sha256": READY_SHA,
                "ready_declaration_sha256": READY_SHA,
                "ready_event": {
                    "event_hash": READY_EVENT_HASH,
                    "sequence": 1,
                    "actor": "josephmccann",
                    "occurred_at": "2026-07-20T20:25:03Z",
                    "source_url": "https://github.com/josephmccann/AIFO-Control-Plane/issues/32#issuecomment-5026935272",
                },
                "allowed_paths": ALLOWED_PATHS,
            },
            "historical": {
                "mission_31": {
                    "issue": 31,
                    "ready_declaration_sha256": "9996e5ebebd26b297e5ce57bcc4d4e78b01723d78052bea0b385a1ad5b95a9e0",
                    "ready_event_hash": "7c796c64513b21732975999db7bbca695d3209207c5f26bcbdd7b313c489bb47",
                    "candidate": {"sha": PRE_READY_HEAD, "tree": PRE_READY_TREE},
                    "superseded_closure_sha256": PRE_READY_CLOSURE_SHA,
                    "evidence": [self.file_record(self.paths[key]) for key in ("historical_ci", "historical_a", "historical_b")],
                }
            },
            "base": {"sha": BASE, "tree": subprocess.check_output(["git", "rev-parse", BASE + "^{tree}"], cwd=ROOT, text=True).strip()},
            "final": {"sha": subject, "tree": subprocess.check_output(["git", "rev-parse", subject + "^{tree}"], cwd=ROOT, text=True).strip()},
            "files": files,
            "edges": [
                {"from": test, "to": source, "kind": "tests"}
                for test in sorted(path for path in paths if path.startswith("tests/"))
                for source in sorted(path for path in paths if not path.startswith("tests/"))
            ],
            "pins": [],
            "classification": {
                "discovery_roots": ["scripts", "tests"],
                "extensionless_python": ["scripts/engineering-os/validate-activation-closure"],
                "python_extensions": [".py"],
                "shell_extensions": [".sh"],
                "python_interpreters": ["python", "python3", "python3.x"],
                "shell_interpreters": ["bash", "dash", "ksh", "sh"],
                "conflicting_signals": "fail",
                "symlink_path": "fail",
                "unknown_executable": "fail",
            },
            "records": self.file_record(self.paths["records"]),
            "tests": [{
                "command": "validate-all", "result": "pass", "head": subject,
                "workflow_path": ".github/workflows/terraform-validate.yml", "run_id": 1,
                "run_attempt": 1, "evidence_path": self.paths["validation"].relative_to(ROOT).as_posix(),
                "evidence_sha256": hashlib.sha256(self.paths["validation"].read_bytes()).hexdigest(),
            }],
            "evidence": [self.file_record(self.paths[key]) for key in ("historical_ci", "historical_a", "historical_b")],
            "reviews": [
                {"reviewer": "mission-32-reviewer-a-ready", "checkpoint": checkpoint_a, "head": subject,
                 "critical": 0, "important": 0, "report_path": self.paths["review_a"].relative_to(ROOT).as_posix(),
                 "report_sha256": hashlib.sha256(self.paths["review_a"].read_bytes()).hexdigest()},
                {"reviewer": "mission-32-reviewer-b-ready", "checkpoint": checkpoint_b, "head": subject,
                 "critical": 0, "important": 0, "report_path": self.paths["review_b"].relative_to(ROOT).as_posix(),
                 "report_sha256": hashlib.sha256(self.paths["review_b"].read_bytes()).hexdigest()},
            ],
            "reconciliation": {
                "head": subject, "critical": 0, "important": 0, "result": "pass",
                "path": self.paths["reconciliation"].relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(self.paths["reconciliation"].read_bytes()).hexdigest(),
            },
        }

    def run_validator(self, artifact):
        with tempfile.NamedTemporaryFile("w", suffix=".json") as stream:
            json.dump(artifact, stream)
            stream.flush()
            return subprocess.run([str(SCRIPT), stream.name, self.subject()], cwd=ROOT,
                                  text=True, capture_output=True)

    def test_exact_mission_32_closure_is_accepted(self):
        result = self.run_validator(self.artifact())
        self.assertEqual(result.returncode, 0, result.stderr)

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
