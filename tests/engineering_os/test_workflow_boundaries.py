import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = ROOT / ".github" / "workflows"
AUTHORIZED_CALLER = "josephmccann/AI.FO-Demo"
AUTHORIZED_OWNER = "josephmccann"
KERNEL_REPOSITORY = "josephmccann/AIFO-Control-Plane"


def load_workflow(name: str) -> dict:
    rendered = subprocess.check_output(
        [
            "ruby",
            "-ryaml",
            "-rjson",
            "-e",
            "print JSON.generate(YAML.load_file(ARGV.fetch(0)))",
            str(WORKFLOW_ROOT / name),
        ],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    )
    return json.loads(rendered)


def cross_repository_boundary_errors(workflow: str) -> list[str]:
    required = {
        "kernel repository": "repository: ${{ job.workflow_repository }}",
        "kernel revision": "ref: ${{ job.workflow_sha }}",
        "kernel path": "path: kernel",
        "target repository": "repository: ${{ github.repository }}",
        "target path": "path: target",
        "kernel Python path": "PYTHONPATH: ${{ github.workspace }}/kernel",
    }
    errors = [label for label, token in required.items() if token not in workflow]
    forbidden = {
        "root policy": r"(?m)^\s+--policy \.aifo/engineering-os-policy\.json",
        "root recovery script": r"(?m)^\s+scripts/engineering-os/recover-orphaned-mission",
        "root tier script": r"(?m)^\s+scripts/engineering-os/validate-tier",
        "root path script": r"(?m)^\s+scripts/engineering-os/validate-paths",
        "root frozen script": r"(?m)^\s+scripts/engineering-os/validate-frozen-artifacts",
    }
    errors.extend(label for label, pattern in forbidden.items() if re.search(pattern, workflow))
    return errors


class ReusableWorkflowBoundaryTests(unittest.TestCase):
    boundary_workflows = (
        "reusable-mission-validation.yml",
        "reusable-tier-path-guard.yml",
        "reusable-frozen-path-guard.yml",
        "reusable-orphan-recovery.yml",
    )

    def read(self, name: str) -> str:
        return (WORKFLOW_ROOT / name).read_text(encoding="utf-8")

    def test_demo_only_reusable_workflows_authenticate_caller_and_provenance(self):
        expected_names = {path.name for path in WORKFLOW_ROOT.glob("reusable-*.yml")}
        self.assertGreater(len(expected_names), 0)
        scripts = set()
        for name in sorted(expected_names):
            with self.subTest(workflow=name):
                workflow = load_workflow(name)
                jobs = workflow["jobs"]
                self.assertIn("caller-authorization", jobs)
                authorization = jobs["caller-authorization"]
                self.assertEqual({}, authorization["permissions"])
                step = authorization["steps"][0]
                expected_environment = {
                    "CALLER_EVENT_NAME": "${{ github.event_name }}",
                    "CALLER_REPOSITORY": "${{ github.repository }}",
                    "CALLER_OWNER": "${{ github.repository_owner }}",
                    "CALLER_REF": "${{ github.ref }}",
                    "WORKFLOW_REPOSITORY": "${{ job.workflow_repository }}",
                    "WORKFLOW_SHA": "${{ job.workflow_sha }}",
                    "WORKFLOW_FILE_PATH": "${{ job.workflow_file_path }}",
                    "EXPECTED_WORKFLOW_SHA": "${{ inputs.expected_workflow_sha }}",
                    "EXPECTED_WORKFLOW_FILE_PATH": ".github/workflows/%s" % name,
                }
                self.assertEqual(expected_environment, step["env"])
                scripts.add(step["run"])
                direct_event_check = '"$CALLER_EVENT_NAME" == "schedule"'
                if name == "reusable-orphan-recovery.yml":
                    self.assertIn(direct_event_check, step["run"])
                else:
                    self.assertNotIn(direct_event_check, step["run"])
                self.assertIn("expected_workflow_sha:", self.read(name))
                self.assertIn("required: true", self.read(name).split(
                    "expected_workflow_sha:", 1
                )[1].split("jobs:", 1)[0])

                def reaches_authorization(job_name: str, seen: set[str]) -> bool:
                    if job_name == "caller-authorization":
                        return True
                    if job_name in seen:
                        return False
                    seen = seen | {job_name}
                    needs = jobs[job_name].get("needs", [])
                    if isinstance(needs, str):
                        needs = [needs]
                    return any(reaches_authorization(need, seen) for need in needs)

                for job_name in jobs:
                    with self.subTest(workflow=name, job=job_name):
                        self.assertTrue(reaches_authorization(job_name, set()))
                        job_condition = jobs[job_name].get("if")
                        if job_condition:
                            self.assertIn("success()", job_condition)
        self.assertEqual(2, len(scripts))

    def test_caller_authorization_script_fails_closed(self):
        workflow = load_workflow("reusable-mission-validation.yml")
        self.assertIn("caller-authorization", workflow["jobs"])
        script = workflow["jobs"]["caller-authorization"]["steps"][0]["run"]
        valid = {
            "CALLER_EVENT_NAME": "workflow_call",
            "CALLER_REPOSITORY": AUTHORIZED_CALLER,
            "CALLER_OWNER": AUTHORIZED_OWNER,
            "WORKFLOW_REPOSITORY": KERNEL_REPOSITORY,
            "WORKFLOW_SHA": "a" * 40,
            "WORKFLOW_FILE_PATH": ".github/workflows/reusable-mission-validation.yml",
            "EXPECTED_WORKFLOW_SHA": "a" * 40,
            "EXPECTED_WORKFLOW_FILE_PATH": ".github/workflows/reusable-mission-validation.yml",
        }
        accepted = subprocess.run(
            ["bash", "-c", script], env={**os.environ, **valid}, capture_output=True, text=True
        )
        self.assertEqual(0, accepted.returncode, accepted.stderr)
        regressions = {
            "wrong caller": {"CALLER_REPOSITORY": "josephmccann/AI-CFO"},
            "wrong owner": {"CALLER_OWNER": "untrusted"},
            "wrong kernel": {"WORKFLOW_REPOSITORY": "untrusted/kernel"},
            "wrong workflow": {"WORKFLOW_FILE_PATH": ".github/workflows/other.yml"},
            "malformed provenance": {"WORKFLOW_SHA": "main", "EXPECTED_WORKFLOW_SHA": "main"},
            "contradictory provenance": {"EXPECTED_WORKFLOW_SHA": "b" * 40},
            "missing evidence": {"EXPECTED_WORKFLOW_SHA": ""},
        }
        for label, mutation in regressions.items():
            with self.subTest(regression=label):
                rejected = subprocess.run(
                    ["bash", "-c", script],
                    env={**os.environ, **valid, **mutation},
                    capture_output=True,
                    text=True,
                )
                self.assertNotEqual(0, rejected.returncode)
                self.assertIn("caller authorization denied", rejected.stderr)

    def test_orphan_direct_runs_are_limited_to_control_plane_main(self):
        workflow = load_workflow("reusable-orphan-recovery.yml")
        self.assertIn("caller-authorization", workflow["jobs"])
        step = workflow["jobs"]["caller-authorization"]["steps"][0]
        script = step["run"]
        direct = {
            "CALLER_EVENT_NAME": "schedule",
            "CALLER_REPOSITORY": KERNEL_REPOSITORY,
            "CALLER_OWNER": AUTHORIZED_OWNER,
            "WORKFLOW_REPOSITORY": KERNEL_REPOSITORY,
            "WORKFLOW_SHA": "a" * 40,
            "WORKFLOW_FILE_PATH": ".github/workflows/reusable-orphan-recovery.yml",
            "EXPECTED_WORKFLOW_SHA": "",
            "EXPECTED_WORKFLOW_FILE_PATH": ".github/workflows/reusable-orphan-recovery.yml",
            "CALLER_REF": "refs/heads/main",
        }
        accepted = subprocess.run(
            ["bash", "-c", script], env={**os.environ, **direct}, capture_output=True, text=True
        )
        self.assertEqual(0, accepted.returncode, accepted.stderr)
        for mutation in (
            {"CALLER_REPOSITORY": AUTHORIZED_CALLER},
            {"CALLER_REF": "refs/heads/feature"},
            {"CALLER_EVENT_NAME": "pull_request"},
        ):
            rejected = subprocess.run(
                ["bash", "-c", script],
                env={**os.environ, **direct, **mutation},
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, rejected.returncode)

    def test_reusable_workflows_separate_immutable_kernel_and_target(self):
        for name in self.boundary_workflows:
            with self.subTest(workflow=name):
                self.assertEqual(cross_repository_boundary_errors(self.read(name)), [])

    def test_boundary_check_rejects_representative_regressions(self):
        valid = """
          repository: ${{ job.workflow_repository }}
          ref: ${{ job.workflow_sha }}
          path: kernel
          repository: ${{ github.repository }}
          ref: ${{ github.event.repository.default_branch }}
          path: target
          PYTHONPATH: ${{ github.workspace }}/kernel
          kernel/scripts/engineering-os/validate-paths
          --policy target/.aifo/engineering-os-policy.json
        """
        self.assertEqual(cross_repository_boundary_errors(valid), [])

        no_kernel_identity = valid.replace(
            "repository: ${{ job.workflow_repository }}",
            "repository: ${{ github.repository }}",
            1,
        )
        self.assertIn("kernel repository", cross_repository_boundary_errors(no_kernel_identity))

        caller_script = valid.replace(
            "kernel/scripts/engineering-os/validate-paths",
            "scripts/engineering-os/validate-paths",
        )
        self.assertIn("root path script", cross_repository_boundary_errors(caller_script))

        caller_policy = valid.replace(
            "--policy target/.aifo/engineering-os-policy.json",
            "--policy .aifo/engineering-os-policy.json",
        )
        self.assertIn("root policy", cross_repository_boundary_errors(caller_policy))

    def test_mission_validation_composes_all_approved_package_8_gates(self):
        workflow = self.read("reusable-mission-validation.yml")
        expected = (
            "uses: ./.github/workflows/reusable-tier-path-guard.yml",
            "uses: ./.github/workflows/reusable-frozen-path-guard.yml",
            "uses: ./.github/workflows/reusable-test-integrity.yml",
            "uses: ./.github/workflows/reusable-evidence-manifest.yml",
            "uses: ./.github/workflows/reusable-merge-authorization.yml",
        )
        for called_workflow in expected:
            self.assertEqual(workflow.count(called_workflow), 1)
        self.assertIn(
            "needs: [mission-history, tier-path, frozen-path, test-integrity, evidence]",
            workflow,
        )
        producer_input = workflow.split("producer_validation_command:", 1)[1].split(
            "permissions:", 1
        )[0]
        self.assertIn("required: true", producer_input)
        evidence_job = workflow.split("\n  evidence:", 1)[1].split(
            "\n  merge-authorization:", 1
        )[0]
        self.assertIn(
            "producer_validation_command: ${{ inputs.producer_validation_command }}",
            evidence_job,
        )
        self.assertNotIn("issues: write", workflow)
        self.assertNotIn("pull-requests: write", workflow)

    def test_frozen_wrapper_uses_target_git_tree_not_kernel_git_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target"
            target.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=target, check=True)
            subprocess.run(["git", "config", "user.email", "eos@example.test"], cwd=target, check=True)
            subprocess.run(["git", "config", "user.name", "EOS Test"], cwd=target, check=True)
            (target / "README.md").write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=target, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=target, check=True)
            base_sha = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=target, text=True
            ).strip()
            documentation = target / "docs" / "engineering-os" / "example.md"
            documentation.parent.mkdir(parents=True)
            documentation.write_text("head\n", encoding="utf-8")
            subprocess.run(["git", "add", str(documentation.relative_to(target))], cwd=target, check=True)
            subprocess.run(["git", "commit", "-qm", "head"], cwd=target, check=True)
            head_sha = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=target, text=True
            ).strip()

            declarations = Path(directory) / "declarations.json"
            exceptions = Path(directory) / "exceptions.json"
            mission_path = Path(directory) / "mission.json"
            policy_path = ROOT / "tests" / "engineering_os" / "fixtures" / "policy-control-plane.json"
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            mission = json.loads((
                ROOT / "tests" / "engineering_os" / "fixtures" / "mission-valid.json"
            ).read_text(encoding="utf-8"))
            mission["eos"]["constitution_sha256"] = policy["constitution_sha256"]
            mission_path.write_text(json.dumps(mission), encoding="utf-8")
            declarations.write_text("[]\n", encoding="utf-8")
            exceptions.write_text("[]\n", encoding="utf-8")
            command = [
                str(ROOT / "scripts" / "engineering-os" / "validate-frozen-artifacts"),
                "--mission", str(mission_path),
                "--policy", str(policy_path),
                "--declarations", str(declarations),
                "--exceptions", str(exceptions),
                "--repository", "josephmccann/AIFO-Control-Plane",
                "--pull-request", "42",
                "--base-sha", base_sha,
                "--head-sha", head_sha,
                "--now", "2026-07-16T12:00:00Z",
                "--action", "write",
            ]
            environment = dict(os.environ)
            environment.update({
                "GIT_DIR": str(target / ".git"),
                "GIT_WORK_TREE": str(target),
            })
            accepted = subprocess.run(
                command, cwd=ROOT, env=environment, capture_output=True, text=True
            )
            self.assertEqual(accepted.returncode, 0, accepted.stdout + accepted.stderr)
            self.assertTrue(json.loads(accepted.stdout)["allowed"])

            wrong_tree = subprocess.run(
                command, cwd=ROOT, capture_output=True, text=True
            )
            self.assertNotEqual(wrong_tree.returncode, 0)

    def test_architecture_documents_cross_repository_workflow_boundary(self):
        architecture = (ROOT / "docs" / "engineering-os" / "ARCHITECTURE.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("immutable enforcement-kernel checkout", architecture)
        self.assertIn("target-repository checkout", architecture)
        self.assertIn("must never supply executable EOS code", architecture)
        self.assertIn("josephmccann/AI.FO-Demo", architecture)
        self.assertIn("expected_workflow_sha", architecture)
        self.assertIn("job.workflow_file_path", architecture)


if __name__ == "__main__":
    unittest.main()
