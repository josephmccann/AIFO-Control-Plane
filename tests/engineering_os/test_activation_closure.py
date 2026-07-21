import json
import os
import shutil
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
            "materialization_required": True,
            "required_contexts": ["Validate Terraform", "GitGuardian Security Checks"],
            "checks": [
                {"name": "Validate Terraform", "conclusion": "failure", "required": True, "check_run_id": 1},
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
        def validate(candidate, evidence_text=evidence):
            with tempfile.NamedTemporaryFile("w", suffix=".json") as disposition_file:
                with tempfile.NamedTemporaryFile("w", suffix=".log") as evidence_file:
                    json.dump(candidate, disposition_file)
                    disposition_file.flush()
                    evidence_file.write(evidence_text)
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
        for target, field in (("checks", "check_run_id"), ("test_integrity", "run_id"),
                              ("test_integrity", "artifact_id")):
            prefix = json.loads(json.dumps(disposition))
            if target == "checks":
                prefix[target][0][field] = 8
            else:
                prefix[target][field] = 2 if field == "run_id" else 8
            mutations.append(prefix)
        allowed = json.loads(json.dumps(disposition))
        allowed["test_integrity"]["allowed"] = True
        mutations.append(allowed)
        required = json.loads(json.dumps(disposition))
        required["required_contexts"].append("Test Integrity")
        mutations.append(required)
        activation = json.loads(json.dumps(disposition))
        activation["activation_events"].append("test_integrity.baseline.authorized")
        mutations.append(activation)
        deployment = json.loads(json.dumps(disposition))
        deployment["deployment_audit"]["state"] = "active"
        mutations.append(deployment)
        for candidate in mutations:
            with self.subTest(candidate=candidate):
                self.assertNotEqual(validate(candidate).returncode, 0)
        for contradictory in (
            "Job ID: 1",
            "GitGuardian check run ID: 1",
            "Test Integrity caller job ID: 1",
            "Test Integrity run ID: 2",
            "Test Integrity run attempt: 2",
            "Test Integrity analysis job ID: 1",
            "Test Integrity report SHA-256: " + "0" * 64,
            "Test Integrity artifact ID: 1",
            "Test Integrity artifact digest: " + "1" * 64,
        ):
            with self.subTest(contradictory=contradictory):
                self.assertNotEqual(
                    validate(disposition, evidence + "\n" + contradictory).returncode,
                    0,
                )

    def test_ci_validation_record_requires_exact_identifier_lines(self):
        head = "a" * 40
        record = {
            "head": head, "command": "validate-all", "result": "pass",
            "workflow_path": ".github/workflows/terraform-validate.yml",
            "run_id": 29804158042, "run_attempt": 1,
        }
        evidence = "\n".join((
            "HEAD: " + head,
            "Command: validate-all",
            "Workflow: .github/workflows/terraform-validate.yml",
            "Run ID: 29804158042",
            "Run attempt: 1",
            "Terraform: PASS", "Actionlint: PASS", "ShellCheck: PASS",
            "Python: PASS", "Classification: PASS", "Closure: PASS",
            "Ran 499 tests in 19.963s", "OK", "Conclusion: success", "Validation complete",
        ))

        def validate(candidate, evidence_text=evidence):
            with tempfile.NamedTemporaryFile("w", suffix=".json") as record_file:
                with tempfile.NamedTemporaryFile("w", suffix=".log") as evidence_file:
                    json.dump(candidate, record_file)
                    record_file.flush()
                    evidence_file.write(evidence_text)
                    evidence_file.flush()
                    return subprocess.run([
                        str(SCRIPT), "--validate-ci-record", record_file.name,
                        evidence_file.name, head,
                    ], cwd=ROOT, text=True, capture_output=True)

        self.assertEqual(validate(record).returncode, 0)
        prefix = dict(record)
        prefix["run_id"] = 2
        self.assertNotEqual(validate(prefix).returncode, 0)

        materialization = dict(record)
        materialization["result"] = "expected_materialization_denial"
        denied_evidence = evidence.replace(
            "Closure: PASS", "Closure: EXPECTED MATERIALIZATION DENIAL",
        ).replace("\nConclusion: success", "").replace("\nValidation complete", "") + (
            "\nConclusion: failure"
            "\nExpected terminal: closure materialization must be the direct child of the reviewed head"
        )
        denied = validate(materialization, denied_evidence)
        self.assertEqual(denied.returncode, 0, denied.stderr)
        for contradictory in (
            "Terraform: FAIL",
            "Python: FAIL",
            "Closure: PASS",
            "Conclusion: success",
            "Validation complete",
            "Expected terminal: unit tests failed",
        ):
            with self.subTest(contradictory=contradictory):
                self.assertNotEqual(
                    validate(materialization, denied_evidence + "\n" + contradictory).returncode,
                    0,
                )

    def test_materialization_requires_one_evidence_only_child(self):
        local_environment = {
            key: value for key, value in os.environ.items()
            if key not in {"GITHUB_ACTIONS", "GITHUB_EVENT_NAME"}
        }
        accepted = subprocess.run([
            str(SCRIPT), "--validate-materialization-range",
            "dc8ef949c8da6fd343628e92cc377003071530c6",
            "0fc6d91d93a1fad24b76c4fead81dd3d3e18ea2a",
        ], cwd=ROOT, text=True, capture_output=True, env=local_environment)
        self.assertEqual(accepted.returncode, 0, accepted.stderr)

        stale = subprocess.run([
            str(SCRIPT), "--validate-materialization-range",
            "dc8ef949c8da6fd343628e92cc377003071530c6",
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        ], cwd=ROOT, text=True, capture_output=True)
        self.assertNotEqual(stale.returncode, 0)

        code_child = subprocess.run([
            str(SCRIPT), "--validate-materialization-range",
            "0a07d5fd62c4844dd12449376ffdd0761db5b371",
            "a60088c1114bcf96cf400ffbbe14c81fcf93a19b",
        ], cwd=ROOT, text=True, capture_output=True)
        self.assertNotEqual(code_child.returncode, 0)

        with tempfile.TemporaryDirectory() as directory:
            clone = Path(directory) / "clone"
            subprocess.run(["git", "clone", "--quiet", "--no-local", str(ROOT), str(clone)], check=True)
            shutil.copy2(
                SCRIPT,
                clone / "scripts/engineering-os/validate-activation-closure",
            )
            tree = subprocess.check_output(
                ["git", "rev-parse", "0fc6d91d93a1fad24b76c4fead81dd3d3e18ea2a^{tree}"],
                cwd=clone, text=True,
            ).strip()
            merge = subprocess.run([
                "git", "commit-tree", tree,
                "-p", "77af0e93780134349abb15bd8d8b665c6de939a3",
                "-p", "0fc6d91d93a1fad24b76c4fead81dd3d3e18ea2a",
            ], cwd=clone, text=True, input="synthetic PR merge\n", capture_output=True,
               env={**os.environ,
                    "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "test@example.com",
                    "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "test@example.com"})
            self.assertEqual(merge.returncode, 0, merge.stderr)
            merged = subprocess.run([
                str(clone / "scripts/engineering-os/validate-activation-closure"),
                "--validate-materialization-range",
                "dc8ef949c8da6fd343628e92cc377003071530c6", merge.stdout.strip(),
            ], cwd=clone, text=True, capture_output=True, env=local_environment)
            self.assertEqual(merged.returncode, 0, merged.stderr)
            ci_environment = {
                **os.environ,
                "GITHUB_ACTIONS": "true",
                "GITHUB_EVENT_NAME": "pull_request",
            }
            ci_merged = subprocess.run([
                str(clone / "scripts/engineering-os/validate-activation-closure"),
                "--validate-materialization-range",
                "dc8ef949c8da6fd343628e92cc377003071530c6", merge.stdout.strip(),
            ], cwd=clone, text=True, capture_output=True, env=ci_environment)
            self.assertEqual(ci_merged.returncode, 0, ci_merged.stderr)
            ci_direct = subprocess.run([
                str(clone / "scripts/engineering-os/validate-activation-closure"),
                "--validate-materialization-range",
                "dc8ef949c8da6fd343628e92cc377003071530c6",
                "0fc6d91d93a1fad24b76c4fead81dd3d3e18ea2a",
            ], cwd=clone, text=True, capture_output=True, env=ci_environment)
            self.assertNotEqual(ci_direct.returncode, 0)
            dispatch_environment = {
                **ci_environment,
                "GITHUB_EVENT_NAME": "workflow_dispatch",
            }
            dispatched = subprocess.run([
                str(clone / "scripts/engineering-os/validate-activation-closure"),
                "--validate-materialization-range",
                "dc8ef949c8da6fd343628e92cc377003071530c6", merge.stdout.strip(),
            ], cwd=clone, text=True, capture_output=True, env=dispatch_environment)
            self.assertNotEqual(dispatched.returncode, 0)

    def test_review_and_reconciliation_status_lines_are_closed(self):
        review = "\n".join((
            "Reviewer: reviewer-a", "HEAD: `%s`" % ("a" * 40),
            "Critical: 0", "Important: 0", "PASS", "Checkpoint: " + "b" * 64,
        ))
        reconciliation = "\n".join((
            "HEAD: `%s`" % ("a" * 40), "Critical: 0", "Important: 0",
            "Reconciliation: PASS",
        ))

        def validate(mode, content):
            with tempfile.NamedTemporaryFile("w", suffix=".md") as stream:
                stream.write(content)
                stream.flush()
                return subprocess.run(
                    [str(SCRIPT), mode, stream.name], cwd=ROOT, text=True, capture_output=True,
                )

        self.assertEqual(validate("--validate-review-status", review).returncode, 0)
        self.assertEqual(validate("--validate-reconciliation-status", reconciliation).returncode, 0)
        for candidate in (
            review.replace("Critical: 0", "Critical: 01"),
            review.replace("Important: 0", "Important: 01"),
            review.replace("PASS", "Verdict: FAIL — not PASS"),
            review + "\nCritical: 1",
            review + "\nFAIL",
        ):
            self.assertNotEqual(validate("--validate-review-status", candidate).returncode, 0)
        for candidate in (
            reconciliation.replace("Critical: 0", "Critical: 01"),
            reconciliation.replace("Important: 0", "Important: 01"),
            reconciliation.replace("Reconciliation: PASS", "Reconciliation: PASSIVE"),
            reconciliation + "\nReconciliation: FAIL",
        ):
            self.assertNotEqual(validate("--validate-reconciliation-status", candidate).returncode, 0)

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
