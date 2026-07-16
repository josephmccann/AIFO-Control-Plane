import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = ROOT / ".github" / "workflows"


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


if __name__ == "__main__":
    unittest.main()
