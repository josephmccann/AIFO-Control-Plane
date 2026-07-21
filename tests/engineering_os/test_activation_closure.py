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

    def bootstrap_disposition(self, artifact):
        return {
            "pull_request": 33,
            "base": {
                "sha": "77af0e93780134349abb15bd8d8b665c6de939a3",
                "tree": "6baecd54d0fd73a6e8e436b436c218ce0d64897b",
            },
            "candidate": dict(artifact["final"]),
            "prior_interim_closure_sha256":
                "1a92c72f1b1631f1d6f5382a776cacfc72020f7d0c4fe0203f655fdd52c3a1a8",
            "required_contexts": ["Validate Terraform", "GitGuardian Security Checks"],
            "checks": [
                {"name": "Validate Terraform", "conclusion": "success", "required": True, "check_run_id": 1},
                {"name": "GitGuardian Security Checks", "conclusion": "success", "required": True, "check_run_id": 2},
                {"name": "Test Integrity / Authorize exact caller and workflow provenance", "conclusion": "success", "required": False, "check_run_id": 3},
                {"name": "Test Integrity / Test Integrity", "conclusion": "failure", "required": False, "check_run_id": 4},
            ],
            "test_integrity": {
                "head": artifact["final"]["sha"], "run_id": 1, "run_attempt": 1,
                "caller_authorized": True, "allowed": False,
                "expected_bootstrap_denial": True, "suppressed": False,
                "overridden": False,
                "finding_counts": {
                    "TEST_FILE_UNPARSABLE": 55,
                    "VALIDATION_WORKFLOW_CHANGE_AMBIGUOUS": 10,
                },
                "report_sha256":
                    "918ebaa3f50bf82b14f006295a9f1dcfe7a5e0d7f54b7122c159b975bb51f02e",
                "artifact_id": 8481441480,
                "artifact_digest":
                    "0bbc386232a92680b31727a7474999310d6dd474fe0daab40f2043ed30bd9eac",
            },
            "deployment_audit": {
                "deployment_id": 5528959623, "status_id": 15719997167,
                "state": "inactive", "environment": "production",
                "sha": "dc8ef949c8da6fd343628e92cc377003071530c6",
                "description": "Accidental API audit record; no deployment executed",
                "runtime_executed": False,
            },
            "activation_events": [], "runtime_deployment": False,
            "preserved_pull_request": {
                "number": 24, "state": "open",
                "head": "066529950a94a6bb3a5f213af51beceb4fe9790f",
                "merged": False,
            },
        }

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

    def test_legacy_closure_cannot_accept_attached_bootstrap_evidence(self):
        artifact = self.artifact()
        artifact["bootstrap_disposition"] = self.bootstrap_disposition(artifact)
        disposition = artifact["bootstrap_disposition"]
        self.assertEqual(disposition["pull_request"], 33)
        self.assertFalse(disposition["test_integrity"]["allowed"])
        self.assertEqual(
            disposition["test_integrity"]["finding_counts"],
            {
                "TEST_FILE_UNPARSABLE": 55,
                "VALIDATION_WORKFLOW_CHANGE_AMBIGUOUS": 10,
            },
        )
        self.assertEqual(
            disposition["test_integrity"]["report_sha256"],
            "918ebaa3f50bf82b14f006295a9f1dcfe7a5e0d7f54b7122c159b975bb51f02e",
        )
        self.assertEqual(disposition["deployment_audit"]["state"], "inactive")
        self.assertEqual(disposition["activation_events"], [])
        result = self.run_validator(artifact)
        self.assertNotEqual(result.returncode, 0)

    def test_bootstrap_transport_evidence_is_exactly_bound(self):
        final = {"sha": "a" * 40, "tree": "b" * 40}
        artifact = {"final": final}
        disposition = self.bootstrap_disposition(artifact)
        disposition["test_integrity"].update({
            "head": final["sha"],
            "run_id": 29801088238,
            "run_attempt": 1,
            "report_sha256": "7f403811adbbffa817325b4e74c43d69da344ddab4e3ccfa35230871ed94ce3c",
            "artifact_id": 8483765340,
            "artifact_digest": "0653b33641d65dac59ea84748f6c02724c5459d8f0d63d24e337f08be4d01688",
        })
        check_ids = (88542158751, 88542153998, 88542156542, 88542167314)
        for check, check_id in zip(disposition["checks"], check_ids):
            check["check_run_id"] = check_id
        evidence = "\n".join((
            "Job ID: 88542158751",
            "GitGuardian check run ID: 88542153998",
            "Test Integrity caller job ID: 88542156542",
            "Test Integrity run ID: 29801088238",
            "Test Integrity run attempt: 1",
            "Test Integrity analysis job ID: 88542167314",
            "Test Integrity report SHA-256: 7f403811adbbffa817325b4e74c43d69da344ddab4e3ccfa35230871ed94ce3c",
            "Test Integrity artifact ID: 8483765340",
            "Test Integrity artifact digest: 0653b33641d65dac59ea84748f6c02724c5459d8f0d63d24e337f08be4d01688",
        ))
        def validate(candidate):
            with tempfile.NamedTemporaryFile("w", suffix=".json") as disposition_file:
                with tempfile.NamedTemporaryFile("w", suffix=".log") as evidence_file:
                    json.dump(candidate, disposition_file)
                    disposition_file.flush()
                    evidence_file.write(evidence)
                    evidence_file.flush()
                    return subprocess.run([
                        str(SCRIPT), "--validate-bootstrap-transport",
                        disposition_file.name, evidence_file.name,
                        final["sha"], final["tree"],
                    ], cwd=ROOT, text=True, capture_output=True)

        self.assertEqual(validate(disposition).returncode, 0)

        mutations = []
        for field, value in (
            ("run_id", 1),
            ("run_attempt", 2),
            ("report_sha256", "0" * 64),
            ("artifact_id", 999999999),
            ("artifact_digest", "1" * 64),
        ):
            candidate = json.loads(json.dumps(disposition))
            candidate["test_integrity"][field] = value
            mutations.append(candidate)
        duplicate = json.loads(json.dumps(disposition))
        duplicate["checks"][1]["check_run_id"] = duplicate["checks"][0]["check_run_id"]
        mutations.append(duplicate)
        mismatched = json.loads(json.dumps(disposition))
        mismatched["checks"][3]["check_run_id"] += 1
        mutations.append(mismatched)
        for candidate in mutations:
            with self.subTest(candidate=candidate):
                self.assertNotEqual(validate(candidate).returncode, 0)

    def test_bootstrap_disposition_is_fail_closed(self):
        artifact = self.artifact()

        mutations = []
        for key, value in (("allowed", True),):
            candidate = self.artifact()
            candidate["bootstrap_disposition"] = self.bootstrap_disposition(candidate)
            candidate["bootstrap_disposition"]["test_integrity"][key] = value
            mutations.append(candidate)
        required = self.artifact(); required["bootstrap_disposition"] = self.bootstrap_disposition(required); required["bootstrap_disposition"]["required_contexts"].append("Test Integrity"); mutations.append(required)
        activation = self.artifact(); activation["bootstrap_disposition"] = self.bootstrap_disposition(activation); activation["bootstrap_disposition"]["activation_events"].append("test_integrity.baseline.authorized"); mutations.append(activation)
        deployment = self.artifact(); deployment["bootstrap_disposition"] = self.bootstrap_disposition(deployment); deployment["bootstrap_disposition"]["deployment_audit"]["state"] = "active"; mutations.append(deployment)
        for candidate in mutations:
            with self.subTest(candidate=candidate):
                self.assertNotEqual(self.run_validator(candidate).returncode, 0)

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
