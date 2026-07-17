import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = ROOT / ".github" / "workflows"
KERNEL_ACTION = ROOT / ".github" / "actions" / "materialize-kernel" / "action.yml"
AUTHORIZED_CALLER = "josephmccann/AI.FO-Demo"
AUTHORIZED_OWNER = "josephmccann"
KERNEL_REPOSITORY = "josephmccann/AIFO-Control-Plane"
KERNEL_ACTION_SHA = "19143443fbc70e4363a932e7eb7211a2ce32ec25"
PINNED_TRANSPORT_PATHS = (
    ".github/actions/materialize-kernel/action.yml",
    "engineering_os",
    "scripts/engineering-os",
    "schemas/engineering-os",
)
DEMO_CALLER_PATHS = {
    "reusable-airtable-mirror.yml": ".github/workflows/eos-airtable-mirror.yml",
    "reusable-orphan-recovery.yml": ".github/workflows/eos-orphan-recovery.yml",
}
DEFAULT_DEMO_CALLER_PATH = ".github/workflows/eos-pull-request.yml"


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
        "kernel transport": (
            "uses: josephmccann/AIFO-Control-Plane/.github/actions/"
            "materialize-kernel@" + KERNEL_ACTION_SHA
        ),
        "kernel revision": "expected_kernel_sha: " + KERNEL_ACTION_SHA,
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

    def test_pinned_action_commit_matches_reviewed_transport_and_kernel(self):
        comparison = subprocess.run(
            [
                "git",
                "diff",
                "--no-ext-diff",
                "--exit-code",
                KERNEL_ACTION_SHA,
                "--",
                *PINNED_TRANSPORT_PATHS,
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(
            0,
            comparison.returncode,
            "pinned private-action transport or kernel differs from the reviewed "
            "working tree; publish the changed paths, repin every reusable "
            "workflow, and review the resulting head:\n" + comparison.stdout,
        )
        untracked = subprocess.check_output(
            [
                "git",
                "ls-files",
                "--others",
                "--exclude-standard",
                "--",
                *PINNED_TRANSPORT_PATHS,
            ],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual("", untracked)

    def test_canonical_ci_fetches_pinned_kernel_history(self):
        workflow = load_workflow("terraform-validate.yml")
        checkouts = [
            step
            for step in workflow["jobs"]["validate"]["steps"]
            if step.get("uses") == "actions/checkout@v4"
        ]
        self.assertEqual(1, len(checkouts))
        self.assertEqual(0, checkouts[0]["with"]["fetch-depth"])

    def test_private_kernel_action_materializes_only_authenticated_source(self):
        rendered = subprocess.check_output(
            [
                "ruby",
                "-ryaml",
                "-rjson",
                "-e",
                "print JSON.generate(YAML.load_file(ARGV.fetch(0)))",
                str(KERNEL_ACTION),
            ],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
        )
        action = json.loads(rendered)
        self.assertEqual("composite", action["runs"]["using"])
        self.assertTrue(action["inputs"]["expected_kernel_sha"]["required"])
        step = action["runs"]["steps"][0]
        self.assertEqual("${{ github.action_ref }}", step["env"]["ACTION_REF"])
        self.assertEqual(
            "${{ inputs.expected_kernel_sha }}", step["env"]["EXPECTED_KERNEL_SHA"]
        )
        self.assertEqual("${{ github.repository }}", step["env"]["CALLER_REPOSITORY"])
        self.assertEqual("${{ github.repository_owner }}", step["env"]["CALLER_OWNER"])
        self.assertEqual("${{ github.workflow_ref }}", step["env"]["CALLER_WORKFLOW_REF"])
        self.assertIn('[[ "$ACTION_REF" == "$EXPECTED_KERNEL_SHA" ]]', step["run"])
        self.assertIn('"$GITHUB_WORKSPACE/kernel"', step["run"])
        self.assertIn("engineering_os", step["run"])
        self.assertIn("scripts/engineering-os", step["run"])
        with tempfile.TemporaryDirectory() as directory:
            environment = {
                **os.environ,
                "ACTION_REF": "a" * 40,
                "EXPECTED_KERNEL_SHA": "a" * 40,
                "GITHUB_ACTION_PATH": str(KERNEL_ACTION.parent),
                "GITHUB_WORKSPACE": directory,
                "CALLER_REPOSITORY": AUTHORIZED_CALLER,
                "CALLER_OWNER": AUTHORIZED_OWNER,
                "CALLER_EVENT_NAME": "pull_request",
                "CALLER_REF": "refs/pull/17/merge",
                "CALLER_WORKFLOW_REF": (
                    AUTHORIZED_CALLER
                    + "/.github/workflows/eos-pull-request.yml@refs/pull/17/merge"
                ),
            }
            accepted = subprocess.run(
                ["bash", "-c", step["run"]],
                env=environment,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, accepted.returncode, accepted.stderr)
            self.assertTrue((Path(directory) / "kernel" / "engineering_os").is_dir())
            self.assertFalse((Path(directory) / "kernel" / "docs").exists())
        with tempfile.TemporaryDirectory() as directory:
            rejected = subprocess.run(
                ["bash", "-c", step["run"]],
                env={
                    **os.environ,
                    "ACTION_REF": "a" * 40,
                    "EXPECTED_KERNEL_SHA": "b" * 40,
                    "GITHUB_ACTION_PATH": str(KERNEL_ACTION.parent),
                    "GITHUB_WORKSPACE": directory,
                    "CALLER_REPOSITORY": AUTHORIZED_CALLER,
                    "CALLER_OWNER": AUTHORIZED_OWNER,
                    "CALLER_EVENT_NAME": "pull_request",
                    "CALLER_REF": "refs/pull/17/merge",
                    "CALLER_WORKFLOW_REF": (
                        AUTHORIZED_CALLER
                        + "/.github/workflows/eos-pull-request.yml@refs/pull/17/merge"
                    ),
                },
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, rejected.returncode)
            self.assertIn("kernel materialization denied", rejected.stderr)
        with tempfile.TemporaryDirectory() as directory:
            unauthorized = subprocess.run(
                ["bash", "-c", step["run"]],
                env={
                    **environment,
                    "GITHUB_WORKSPACE": directory,
                    "CALLER_REPOSITORY": "josephmccann/AI-CFO",
                    "CALLER_WORKFLOW_REF": (
                        "josephmccann/AI-CFO/.github/workflows/eos-pull-request.yml@"
                        "refs/pull/17/merge"
                    ),
                },
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, unauthorized.returncode)
            self.assertFalse((Path(directory) / "kernel").exists())
        allowed_callers = (
            {
                "CALLER_REPOSITORY": AUTHORIZED_CALLER,
                "CALLER_EVENT_NAME": "schedule",
                "CALLER_REF": "refs/heads/master",
                "CALLER_WORKFLOW_REF": (
                    AUTHORIZED_CALLER
                    + "/.github/workflows/eos-airtable-mirror.yml@refs/heads/master"
                ),
            },
            {
                "CALLER_REPOSITORY": AUTHORIZED_CALLER,
                "CALLER_EVENT_NAME": "workflow_dispatch",
                "CALLER_REF": "refs/heads/master",
                "CALLER_WORKFLOW_REF": (
                    AUTHORIZED_CALLER
                    + "/.github/workflows/eos-orphan-recovery.yml@refs/heads/master"
                ),
            },
            {
                "CALLER_REPOSITORY": KERNEL_REPOSITORY,
                "CALLER_EVENT_NAME": "pull_request_target",
                "CALLER_REF": "refs/heads/main",
                "CALLER_WORKFLOW_REF": (
                    KERNEL_REPOSITORY
                    + "/.github/workflows/test-integrity.yml@refs/heads/main"
                ),
            },
            {
                "CALLER_REPOSITORY": KERNEL_REPOSITORY,
                "CALLER_EVENT_NAME": "schedule",
                "CALLER_REF": "refs/heads/main",
                "CALLER_WORKFLOW_REF": (
                    KERNEL_REPOSITORY
                    + "/.github/workflows/reusable-orphan-recovery.yml@refs/heads/main"
                ),
            },
        )
        for caller in allowed_callers:
            with self.subTest(caller=caller["CALLER_WORKFLOW_REF"]):
                with tempfile.TemporaryDirectory() as directory:
                    accepted = subprocess.run(
                        ["bash", "-c", step["run"]],
                        env={
                            **environment,
                            **caller,
                            "GITHUB_WORKSPACE": directory,
                        },
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(0, accepted.returncode, accepted.stderr)

        rejected_callers = (
            ({}, {"CALLER_EVENT_NAME": "push"}),
            (allowed_callers[0], {"CALLER_REF": "refs/heads/feature"}),
            (allowed_callers[1], {"CALLER_EVENT_NAME": "push"}),
            (allowed_callers[2], {"CALLER_REF": "refs/heads/feature"}),
            (allowed_callers[3], {"CALLER_EVENT_NAME": "pull_request"}),
        )
        for caller, mutation in rejected_callers:
            with self.subTest(rejected_caller=caller, mutation=mutation):
                with tempfile.TemporaryDirectory() as directory:
                    rejected = subprocess.run(
                        ["bash", "-c", step["run"]],
                        env={
                            **environment,
                            **caller,
                            **mutation,
                            "GITHUB_WORKSPACE": directory,
                        },
                        capture_output=True,
                        text=True,
                    )
                    self.assertNotEqual(0, rejected.returncode)
                    self.assertIn("kernel materialization denied", rejected.stderr)
                    self.assertFalse((Path(directory) / "kernel").exists())

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
                expected_caller_path = DEMO_CALLER_PATHS.get(
                    name, DEFAULT_DEMO_CALLER_PATH
                )
                expected_environment = {
                    "CALLER_EVENT_NAME": "${{ github.event_name }}",
                    "CALLER_REPOSITORY": "${{ github.repository }}",
                    "CALLER_OWNER": "${{ github.repository_owner }}",
                    "CALLER_REF": "${{ github.ref }}",
                    "CALLER_WORKFLOW_REF": "${{ github.workflow_ref }}",
                    "CALLER_WORKFLOW_SHA": "${{ github.workflow_sha }}",
                    "WORKFLOW_REPOSITORY": "${{ job.workflow_repository }}",
                    "WORKFLOW_SHA": "${{ job.workflow_sha }}",
                    "WORKFLOW_FILE_PATH": "${{ job.workflow_file_path }}",
                    "EXPECTED_WORKFLOW_SHA": "${{ inputs.expected_workflow_sha }}",
                    "EXPECTED_WORKFLOW_FILE_PATH": ".github/workflows/%s" % name,
                    "EXPECTED_CALLER_WORKFLOW_PATH": expected_caller_path,
                }
                self.assertEqual(expected_environment, step["env"])
                scripts.add(step["run"])
                direct_event_check = 'deny "direct workflow provenance"'
                if name == "reusable-orphan-recovery.yml":
                    self.assertIn(direct_event_check, step["run"])
                else:
                    self.assertNotIn(direct_event_check, step["run"])
                self.assertIn("expected_workflow_sha:", self.read(name))
                self.assertIn("required: true", self.read(name).split(
                    "expected_workflow_sha:", 1
                )[1].split("jobs:", 1)[0])
                self.assertIn(
                    "josephmccann/AIFO-Control-Plane/.github/actions/"
                    "materialize-kernel@" + KERNEL_ACTION_SHA,
                    self.read(name),
                )
                self.assertIn("expected_kernel_sha: " + KERNEL_ACTION_SHA, self.read(name))
                self.assertNotIn("repository: ${{ job.workflow_repository }}", self.read(name))

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
        self.assertEqual(4, len(scripts))

    def test_caller_authorization_script_fails_closed(self):
        workflow = load_workflow("reusable-mission-validation.yml")
        self.assertIn("caller-authorization", workflow["jobs"])
        script = workflow["jobs"]["caller-authorization"]["steps"][0]["run"]
        valid = {
            "CALLER_EVENT_NAME": "pull_request",
            "CALLER_REPOSITORY": AUTHORIZED_CALLER,
            "CALLER_OWNER": AUTHORIZED_OWNER,
            "CALLER_REF": "refs/pull/17/merge",
            "CALLER_WORKFLOW_REF": (
                AUTHORIZED_CALLER
                + "/.github/workflows/eos-pull-request.yml@refs/pull/17/merge"
            ),
            "CALLER_WORKFLOW_SHA": "c" * 40,
            "WORKFLOW_REPOSITORY": KERNEL_REPOSITORY,
            "WORKFLOW_SHA": "a" * 40,
            "WORKFLOW_FILE_PATH": ".github/workflows/reusable-mission-validation.yml",
            "EXPECTED_WORKFLOW_SHA": "a" * 40,
            "EXPECTED_WORKFLOW_FILE_PATH": ".github/workflows/reusable-mission-validation.yml",
            "EXPECTED_CALLER_WORKFLOW_PATH": DEFAULT_DEMO_CALLER_PATH,
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
            "wrong event": {"CALLER_EVENT_NAME": "push"},
            "wrong caller workflow": {
                "CALLER_WORKFLOW_REF": (
                    AUTHORIZED_CALLER + "/.github/workflows/other.yml@refs/pull/17/merge"
                )
            },
            "wrong caller ref": {"CALLER_REF": "refs/heads/master"},
            "malformed caller revision": {"CALLER_WORKFLOW_SHA": "master"},
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
            "CALLER_WORKFLOW_REF": (
                KERNEL_REPOSITORY
                + "/.github/workflows/reusable-orphan-recovery.yml@refs/heads/main"
            ),
            "CALLER_WORKFLOW_SHA": "a" * 40,
            "EXPECTED_CALLER_WORKFLOW_PATH": ".github/workflows/eos-orphan-recovery.yml",
        }
        accepted = subprocess.run(
            ["bash", "-c", script], env={**os.environ, **direct}, capture_output=True, text=True
        )
        self.assertEqual(0, accepted.returncode, accepted.stderr)
        for mutation in (
            {"CALLER_REPOSITORY": AUTHORIZED_CALLER},
            {"CALLER_REF": "refs/heads/feature"},
            {"CALLER_EVENT_NAME": "pull_request"},
            {"CALLER_WORKFLOW_SHA": "b" * 40},
            {
                "CALLER_WORKFLOW_REF": (
                    KERNEL_REPOSITORY
                    + "/.github/workflows/reusable-orphan-recovery.yml@refs/heads/feature"
                )
            },
        ):
            rejected = subprocess.run(
                ["bash", "-c", script],
                env={**os.environ, **direct, **mutation},
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, rejected.returncode)

    def test_control_plane_test_integrity_caller_is_exactly_authorized(self):
        workflow = load_workflow("reusable-test-integrity.yml")
        script = workflow["jobs"]["caller-authorization"]["steps"][0]["run"]
        valid = {
            "CALLER_EVENT_NAME": "pull_request_target",
            "CALLER_REPOSITORY": KERNEL_REPOSITORY,
            "CALLER_OWNER": AUTHORIZED_OWNER,
            "CALLER_REF": "refs/heads/main",
            "CALLER_WORKFLOW_REF": (
                KERNEL_REPOSITORY + "/.github/workflows/test-integrity.yml@refs/heads/main"
            ),
            "CALLER_WORKFLOW_SHA": "c" * 40,
            "WORKFLOW_REPOSITORY": KERNEL_REPOSITORY,
            "WORKFLOW_SHA": "a" * 40,
            "WORKFLOW_FILE_PATH": ".github/workflows/reusable-test-integrity.yml",
            "EXPECTED_WORKFLOW_SHA": "a" * 40,
            "EXPECTED_WORKFLOW_FILE_PATH": ".github/workflows/reusable-test-integrity.yml",
            "EXPECTED_CALLER_WORKFLOW_PATH": DEFAULT_DEMO_CALLER_PATH,
        }
        accepted = subprocess.run(
            ["bash", "-c", script], env={**os.environ, **valid}, capture_output=True, text=True
        )
        self.assertEqual(0, accepted.returncode, accepted.stderr)
        for mutation in (
            {"CALLER_EVENT_NAME": "pull_request"},
            {"CALLER_REF": "refs/heads/feature"},
            {
                "CALLER_WORKFLOW_REF": (
                    KERNEL_REPOSITORY + "/.github/workflows/other.yml@refs/heads/main"
                )
            },
            {"CALLER_WORKFLOW_SHA": "main"},
            {"EXPECTED_WORKFLOW_SHA": "b" * 40},
        ):
            rejected = subprocess.run(
                ["bash", "-c", script],
                env={**os.environ, **valid, **mutation},
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(0, rejected.returncode)

    def test_demo_scheduled_callers_are_default_branch_only(self):
        for name in ("reusable-airtable-mirror.yml", "reusable-orphan-recovery.yml"):
            with self.subTest(workflow=name):
                workflow = load_workflow(name)
                script = workflow["jobs"]["caller-authorization"]["steps"][0]["run"]
                caller_path = DEMO_CALLER_PATHS[name]
                valid = {
                    "CALLER_EVENT_NAME": "schedule",
                    "CALLER_REPOSITORY": AUTHORIZED_CALLER,
                    "CALLER_OWNER": AUTHORIZED_OWNER,
                    "CALLER_REF": "refs/heads/master",
                    "CALLER_WORKFLOW_REF": (
                        AUTHORIZED_CALLER + "/" + caller_path + "@refs/heads/master"
                    ),
                    "CALLER_WORKFLOW_SHA": "c" * 40,
                    "WORKFLOW_REPOSITORY": KERNEL_REPOSITORY,
                    "WORKFLOW_SHA": "a" * 40,
                    "WORKFLOW_FILE_PATH": ".github/workflows/" + name,
                    "EXPECTED_WORKFLOW_SHA": "a" * 40,
                    "EXPECTED_WORKFLOW_FILE_PATH": ".github/workflows/" + name,
                    "EXPECTED_CALLER_WORKFLOW_PATH": caller_path,
                }
                accepted = subprocess.run(
                    ["bash", "-c", script],
                    env={**os.environ, **valid},
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(0, accepted.returncode, accepted.stderr)
                for mutation in (
                    {"CALLER_REF": "refs/heads/feature"},
                    {"CALLER_EVENT_NAME": "push"},
                    {
                        "CALLER_WORKFLOW_REF": (
                            AUTHORIZED_CALLER + "/" + caller_path + "@refs/heads/feature"
                        )
                    },
                ):
                    rejected = subprocess.run(
                        ["bash", "-c", script],
                        env={**os.environ, **valid, **mutation},
                        capture_output=True,
                        text=True,
                    )
                    self.assertNotEqual(0, rejected.returncode)

    def test_reusable_workflows_separate_immutable_kernel_and_target(self):
        for name in self.boundary_workflows:
            with self.subTest(workflow=name):
                self.assertEqual(cross_repository_boundary_errors(self.read(name)), [])
                self.assertNotIn("repository: ${{ job.workflow_repository }}", self.read(name))

    def test_first_policy_bootstrap_is_exact_and_shared_by_every_consumer(self):
        consumers = (
            "reusable-mission-validation.yml",
            "reusable-tier-path-guard.yml",
            "reusable-frozen-path-guard.yml",
            "reusable-test-integrity.yml",
            "reusable-evidence-manifest.yml",
        )
        expected = (
            "kernel/scripts/engineering-os/resolve-base-policy",
            "--bootstrap-repository josephmccann/AI.FO-Demo",
            "--bootstrap-base-sha 52ca01c7c8b034b212feede58ddcc77d9c37c388",
            "--bootstrap-policy-sha256 "
            "60bc2bdb34359062af092934e19dd75fb363d8672ebe70bdabfd204609e3c42f",
            '--output "$RUNNER_TEMP/base-policy.json"',
        )
        for name in consumers:
            with self.subTest(workflow=name):
                workflow = self.read(name)
                for value in expected:
                    self.assertEqual(1, workflow.count(value), value)
                self.assertNotIn(
                    '--base-policy "$GITHUB_WORKSPACE/base/.aifo/'
                    'engineering-os-policy.json"',
                    workflow,
                )

    def test_boundary_check_rejects_representative_regressions(self):
        valid = """
          uses: josephmccann/AIFO-Control-Plane/.github/actions/materialize-kernel@19143443fbc70e4363a932e7eb7211a2ce32ec25
          expected_kernel_sha: 19143443fbc70e4363a932e7eb7211a2ce32ec25
          repository: ${{ github.repository }}
          ref: ${{ github.event.repository.default_branch }}
          path: target
          PYTHONPATH: ${{ github.workspace }}/kernel
          kernel/scripts/engineering-os/validate-paths
          --policy target/.aifo/engineering-os-policy.json
        """
        self.assertEqual(cross_repository_boundary_errors(valid), [])

        no_kernel_identity = valid.replace(
            "materialize-kernel@19143443fbc70e4363a932e7eb7211a2ce32ec25",
            "materialize-kernel@main",
            1,
        )
        self.assertIn("kernel transport", cross_repository_boundary_errors(no_kernel_identity))

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
        normalized_architecture = " ".join(architecture.split())
        self.assertIn("immutable enforcement-kernel materialization", architecture.lower())
        self.assertIn("scoped installation token", normalized_architecture)
        self.assertIn("materialize-kernel", architecture)
        self.assertIn("target-repository checkout", architecture)
        self.assertIn("must never supply executable EOS code", normalized_architecture)
        self.assertIn("josephmccann/AI.FO-Demo", architecture)
        self.assertIn("expected_workflow_sha", architecture)
        self.assertIn("job.workflow_file_path", architecture)
        self.assertIn("github.workflow_ref", architecture)
        self.assertIn("eos-pull-request.yml", architecture)
        self.assertIn("eos-orphan-recovery.yml", architecture)
        self.assertIn("eos-airtable-mirror.yml", architecture)
        self.assertIn("Control Plane test-integrity caller", architecture)


if __name__ == "__main__":
    unittest.main()
