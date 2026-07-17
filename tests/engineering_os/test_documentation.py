import json
import os
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EOS_VERSION = "1.0.0"
CONSTITUTION_SHA = "a255c0976949d8acae91f7d46e85cc083a15e242ccbd62e587c4e3163b29265e"


class DocumentationContractTests(unittest.TestCase):
    def read(self, path):
        return (ROOT / path).read_text(encoding="utf-8")

    def test_required_operational_surface_exists(self):
        required = [
            "docs/engineering-os/README.md",
            "docs/engineering-os/KNOWN_ENFORCEMENT_GAPS.md",
            "docs/engineering-os/HUMAN_ONBOARDING.md",
            "tests/engineering_os/test_documentation.py",
            "scripts/engineering-os/validate-all",
            "schemas/engineering-os/mission.schema.json",
            "schemas/engineering-os/evidence.schema.json",
            "schemas/engineering-os/repository-policy.schema.json",
            ".github/workflows/reusable-mission-validation.yml",
            ".github/workflows/reusable-evidence-manifest.yml",
            ".github/workflows/reusable-merge-authorization.yml",
        ]
        for path in required:
            with self.subTest(path=path):
                self.assertTrue((ROOT / path).is_file(), path)

    def test_entrypoints_pin_version_and_constitution_hash(self):
        for path in (
            "docs/engineering-os/README.md",
            "docs/engineering-os/HUMAN_ONBOARDING.md",
            "AGENTS.md",
            "CONTRIBUTING.md",
            "README.md",
        ):
            with self.subTest(path=path):
                value = self.read(path)
                self.assertIn(EOS_VERSION, value)
                self.assertIn(CONSTITUTION_SHA, value)

    def test_constitution_links_to_founder_manual_in_one_direction_only(self):
        constitution = self.read("docs/engineering-os/ENGINEERING_CONSTITUTION.md")
        founder_manual = self.read("docs/governance/FOUNDER_OPERATING_MANUAL.md")
        self.assertIn("../governance/FOUNDER_OPERATING_MANUAL.md", constitution)
        self.assertNotIn("ENGINEERING_CONSTITUTION", founder_manual)
        self.assertNotIn("engineering-os/ENGINEERING_CONSTITUTION", founder_manual)

    def test_every_constitutional_rule_has_a_control_or_named_gap(self):
        register = self.read("docs/engineering-os/KNOWN_ENFORCEMENT_GAPS.md")
        rows = {}
        for line in register.splitlines():
            if not line.startswith("| C-"):
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            self.assertEqual(7, len(cells), line)
            rule, summary, status, control, risk, owner, closure = cells
            self.assertNotIn(rule, rows)
            self.assertTrue(summary)
            self.assertIn(status, {"Enforced", "Partial", "Gap"})
            self.assertTrue(control)
            self.assertTrue(risk)
            self.assertTrue(owner)
            self.assertTrue(closure)
            rows[rule] = cells
        self.assertEqual({"C-%02d" % number for number in range(1, 11)}, set(rows))

    def test_non_mechanical_limitations_are_named(self):
        register = self.read("docs/engineering-os/KNOWN_ENFORCEMENT_GAPS.md")
        for gap in (
            "GAP-PATH-SCOPED-CREDENTIALS",
            "GAP-DELETABLE-COMMENTS",
            "GAP-BRANCH-PROTECTION",
            "GAP-PRIVATE-ACTIONS-ACCESS",
            "GAP-REQUIRED-REVIEWERS",
            "GAP-STATUS-CHECK-CONTEXT",
        ):
            with self.subTest(gap=gap):
                self.assertIn(gap, register)
        for heading in ("Status", "Risk", "Mitigation", "Owner", "Closure path"):
            self.assertIn(heading, register)

    def test_onboarding_uses_the_same_human_and_agent_path(self):
        onboarding = self.read("docs/engineering-os/HUMAN_ONBOARDING.md")
        self.assertRegex(onboarding.lower(), r"human.*agent|agent.*human")
        self.assertIn("<!-- EOS:MISSION:BEGIN -->", onboarding)
        self.assertIn("<!-- AIFO-EOS-MISSION-ISSUE:", onboarding)
        self.assertIn("Problem", onboarding)
        self.assertIn("Solution", onboarding)
        self.assertIn("Verification", onboarding)
        self.assertIn("Rollback", onboarding)
        self.assertIn("founder approval", onboarding.lower())
        self.assertNotIn("## Constitutional rules", onboarding)

    def test_high_risk_capabilities_remain_disabled(self):
        policy = json.loads(self.read(".aifo/engineering-os-policy.json"))
        for name in (
            "auto_merge_enabled",
            "airtable_live_enabled",
            "deployment_enabled",
            "edgar_integration_enabled",
            "orphan_recovery_enabled",
        ):
            with self.subTest(name=name):
                self.assertIs(policy[name], False)
        for path in ("AGENTS.md", "CONTRIBUTING.md", "docs/engineering-os/README.md"):
            value = self.read(path).lower()
            self.assertNotIn("edgar integration is enabled", value)
            self.assertNotIn("auto-merge is enabled", value)

    def test_all_engineering_os_wrappers_are_executable(self):
        wrappers = sorted((ROOT / "scripts/engineering-os").iterdir())
        self.assertGreater(len(wrappers), 0)
        for wrapper in wrappers:
            with self.subTest(wrapper=wrapper.name):
                self.assertTrue(wrapper.is_file())
                self.assertTrue(os.access(wrapper, os.X_OK), wrapper)

    def test_validate_all_is_offline_and_complete(self):
        wrapper = self.read("scripts/engineering-os/validate-all")
        for expected in (
            "unittest discover",
            "py_compile",
            "bash -n",
            "YAML.load_file",
            "json.tool",
            "git diff --check",
        ):
            self.assertIn(expected, wrapper)
        for forbidden in (
            "gh api",
            "curl ",
            "wget ",
            "terraform apply",
            "terraform destroy",
            "aws ",
        ):
            self.assertNotIn(forbidden, wrapper)

    def test_no_generated_or_sensitive_outputs_are_tracked(self):
        tracked = subprocess.check_output(
            ["git", "ls-files"], cwd=ROOT, text=True, encoding="utf-8"
        ).splitlines()
        forbidden_parts = ("__pycache__", ".pytest_cache", ".tfstate", ".tfplan")
        for path in tracked:
            with self.subTest(path=path):
                self.assertFalse(any(part in path for part in forbidden_parts), path)
                self.assertFalse(path.startswith("build/"), path)
                self.assertFalse(path.startswith("diagnostics/"), path)

    def test_repository_entrypoints_link_operational_docs_and_state(self):
        readme = self.read("README.md")
        agents = self.read("AGENTS.md")
        contributing = self.read("CONTRIBUTING.md")
        for path in (
            "docs/engineering-os/README.md",
            "docs/engineering-os/KNOWN_ENFORCEMENT_GAPS.md",
            "docs/engineering-os/HUMAN_ONBOARDING.md",
            "memory/current-state.md",
            "memory/known-risks.md",
            "memory/open-decisions.md",
            "workqueue/README.md",
        ):
            self.assertIn(path, readme)
        self.assertIn("docs/engineering-os/README.md", agents)
        self.assertIn("docs/engineering-os/HUMAN_ONBOARDING.md", contributing)

    def test_actionlint_compatibility_is_exact_and_path_scoped(self):
        config_path = ROOT / ".github/actionlint.yaml"
        self.assertTrue(config_path.is_file())
        config = json.loads(
            subprocess.check_output(
                [
                    "ruby",
                    "-ryaml",
                    "-rjson",
                    "-e",
                    "print JSON.generate(YAML.load_file(ARGV.fetch(0)))",
                    str(config_path),
                ],
                cwd=ROOT,
                text=True,
                encoding="utf-8",
            )
        )
        workflows = ROOT / ".github/workflows"
        expected_paths = {
            str(path.relative_to(ROOT))
            for path in workflows.glob("reusable-*.yml")
            if "job.workflow_repository" in path.read_text(encoding="utf-8")
            or "job.workflow_sha" in path.read_text(encoding="utf-8")
        }
        expected_ignores = [
            '^property "workflow_repository" is not defined in object type ',
            '^property "workflow_sha" is not defined in object type ',
        ]
        self.assertEqual({"paths"}, set(config))
        self.assertEqual(expected_paths, set(config["paths"]))
        for path, path_config in config["paths"].items():
            with self.subTest(path=path):
                self.assertEqual({"ignore": expected_ignores}, path_config)

    def test_actionlint_compatibility_has_removal_contract(self):
        register = self.read("docs/engineering-os/KNOWN_ENFORCEMENT_GAPS.md")
        self.assertIn(
            "This compatibility rule exists solely because the currently pinned "
            "actionlint version does not yet recognize officially supported GitHub "
            "reusable-workflow context fields.",
            register,
        )
        self.assertIn(
            "The compatibility rule must be removed once the pinned actionlint release "
            "supports these properties.",
            register,
        )
        self.assertIn("job.workflow_repository", register)
        self.assertIn("job.workflow_sha", register)
        self.assertIn(
            "https://docs.github.com/en/actions/reference/workflows-and-actions/contexts",
            register,
        )
        self.assertIn("https://github.com/rhysd/actionlint/pull/661", register)


if __name__ == "__main__":
    unittest.main()
