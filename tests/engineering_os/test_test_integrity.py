import copy
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from engineering_os.test_integrity import (
    analyze_test_integrity,
    validate_test_override,
)


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "engineering_os" / "fixtures" / "test-integrity"
BASE_SHA = "1" * 40
HEAD_SHA = "2" * 40


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest(root):
    return {
        path.relative_to(root).as_posix(): _hash(path)
        for path in sorted(root.rglob("*")) if path.is_file()
    }


def policy(base, head):
    return {
        "schema_version": "1.0.0",
        "repository": "acme/widgets",
        "base_sha": BASE_SHA,
        "head_sha": HEAD_SHA,
        "evaluated_at": "2026-07-15T12:00:00Z",
        "base_manifest": _manifest(base),
        "head_manifest": _manifest(head),
        "founder_identities": ["founder"],
        "reviewer_identities": ["adversary"],
        "configuration": {
            "test_globs": ["tests/**/test_*.py", "tests/**/*.test.js", "tests/**/*.spec.js"],
            "fixture_globs": ["tests/**/fixtures/**"],
            "validation_workflow_globs": [".github/workflows/*validate*.yml", ".github/workflows/*test*.yml"],
            "test_config_globs": ["pyproject.toml", "pytest.ini", "setup.cfg", "tox.ini", "package.json", "*vitest*.js", "*jest*.js"],
            "coverage_paths": ["coverage.json", "coverage-summary.json", ".eos/coverage.json"],
            "material_coverage_decline": 1.0,
            "assertion_patterns": [r"\bassert\b", r"\bexpect\s*\(", r"\.assert[A-Z]\w*\s*\("],
            "skip_patterns": [r"\bskip(?:If|Unless|Test)?\b", r"\.(?:skip|todo|disabled)\b", r"\bdisabled\b"],
        },
    }


def codes(report):
    return {finding.code for finding in report.findings}


class TestIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.base = root / "base"
        self.head = root / "head"
        shutil.copytree(FIXTURES / "base", self.base)
        shutil.copytree(FIXTURES / "head", self.head)

    def tearDown(self):
        self.temp.cleanup()

    def analyze(self, config=None):
        configured = policy(self.base, self.head)
        if config:
            configured["configuration"].update(config)
        configured["base_manifest"] = _manifest(self.base)
        configured["head_manifest"] = _manifest(self.head)
        return analyze_test_integrity(self.base, self.head, configured)

    def test_deleted_test_and_case_are_reported(self):
        (self.head / "tests/test_service.py").unlink()
        report = self.analyze()
        self.assertIn("TEST_FILE_DELETED", codes(report))
        self.assertIn("TEST_CASE_REMOVED", codes(report))

    def test_duplicate_test_names_are_counted_as_distinct_cases(self):
        for root in (self.base, self.head):
            (root / "tests/test_duplicate.py").write_text(
                "def test_sourced_value():\n    assert True\n", encoding="utf-8",
            )
        (self.head / "tests/test_duplicate.py").unlink()
        self.assertIn("TEST_CASE_REMOVED", codes(self.analyze()))

    def test_effective_rename_that_loses_coverage_is_reported(self):
        original = self.head / "tests/test_service.py"
        renamed = self.head / "tests/test_renamed.py"
        renamed.write_text("def test_sourced_value():\n    assert True\n", encoding="utf-8")
        original.unlink()
        self.assertIn("TEST_RENAME_COVERAGE_REDUCED", codes(self.analyze()))

    def test_ambiguous_copy_or_rename_fails_closed(self):
        original = self.head / "tests/test_service.py"
        text = original.read_text(encoding="utf-8")
        (self.head / "tests/test_copy_one.py").write_text(text, encoding="utf-8")
        (self.head / "tests/test_copy_two.py").write_text(text, encoding="utf-8")
        original.unlink()
        self.assertIn("TEST_RENAME_AMBIGUOUS", codes(self.analyze()))

    def test_ordinary_refactor_and_exact_rename_do_not_false_block(self):
        path = self.head / "tests/test_service.py"
        path.write_text(path.read_text(encoding="utf-8").replace("value = 2", "value = 1 + 1"), encoding="utf-8")
        self.assertEqual(codes(self.analyze()), set())
        path.rename(self.head / "tests/test_service_renamed.py")
        self.assertEqual(codes(self.analyze()), set())

    def test_new_skip_alias_decorator_and_disabled_test_are_reported(self):
        path = self.head / "tests/test_service.py"
        path.write_text(
            "from unittest import skip as disabled\n@disabled('later')\ndef test_sourced_value():\n    assert True\n\n"
            "def test_property_invariant():\n    return\n",
            encoding="utf-8",
        )
        found = codes(self.analyze())
        self.assertIn("TEST_SKIP_ADDED", found)
        self.assertIn("TEST_ASSERTION_DECLINE", found)

    def test_javascript_skip_alias_and_config_level_disablement_are_reported(self):
        for root in (self.base, self.head):
            (root / "tests/sample.test.js").write_text("test('works', () => { expect(1).toBe(1); });\n", encoding="utf-8")
            (root / "package.json").write_text('{"scripts":{"test":"vitest"}}\n', encoding="utf-8")
        (self.head / "tests/sample.test.js").write_text("test.skip('works', () => { expect(1).toBe(1); });\n", encoding="utf-8")
        (self.head / "package.json").write_text('{"scripts":{"test":"vitest --passWithNoTests"}}\n', encoding="utf-8")
        found = codes(self.analyze())
        self.assertIn("TEST_SKIP_ADDED", found)
        self.assertIn("TEST_CONFIGURATION_WEAKENED", found)

    def test_assertion_and_sourcing_or_property_removal_are_reported(self):
        path = self.head / "tests/test_service.py"
        path.write_text(
            "def test_sourced_value():\n    source = 'authoritative'\n\n"
            "def test_property_invariant():\n    value = 2\n    return value\n",
            encoding="utf-8",
        )
        found = codes(self.analyze())
        self.assertIn("TEST_ASSERTION_DECLINE", found)
        self.assertIn("TEST_SOURCING_ASSERTION_REMOVED", found)
        self.assertIn("TEST_PROPERTY_ASSERTION_REMOVED", found)

    def test_validation_workflow_deletion_and_weakening_are_reported(self):
        for root in (self.base, self.head):
            workflow = root / ".github/workflows/tests-validate.yml"
            workflow.parent.mkdir(parents=True, exist_ok=True)
            workflow.write_text("steps:\n  - run: pytest\n", encoding="utf-8")
        (self.head / ".github/workflows/tests-validate.yml").unlink()
        self.assertIn("VALIDATION_WORKFLOW_DELETED", codes(self.analyze()))
        (self.head / ".github/workflows/tests-validate.yml").write_text("steps:\n  - run: pytest || true\n", encoding="utf-8")
        self.assertIn("VALIDATION_WORKFLOW_WEAKENED", codes(self.analyze()))

    def test_fixture_substitution_reducing_cases_is_reported(self):
        fixture = self.head / "tests/fixtures/cases.json"
        fixture.write_text('[{"input":1,"output":2}]\n', encoding="utf-8")
        report = self.analyze()
        self.assertIn("TEST_FIXTURE_CASE_DECLINE", codes(report))
        self.assertEqual(report.deltas["fixture_cases"], -1)

    def test_material_coverage_decline_is_reported_and_increase_passes(self):
        (self.base / "coverage-summary.json").write_text('{"total":{"lines":{"pct":90.0}}}', encoding="utf-8")
        (self.head / "coverage-summary.json").write_text('{"total":{"lines":{"pct":88.9}}}', encoding="utf-8")
        report = self.analyze()
        self.assertIn("TEST_COVERAGE_DECLINE", codes(report))
        self.assertEqual(report.deltas["coverage_percent"], -1.1)
        (self.head / "coverage-summary.json").write_text('{"total":{"lines":{"pct":91.0}}}', encoding="utf-8")
        self.assertNotIn("TEST_COVERAGE_DECLINE", codes(self.analyze()))

    def test_missing_or_malformed_coverage_fails_closed(self):
        (self.base / "coverage.json").write_text('{"totals":{"percent_covered":90}}', encoding="utf-8")
        self.assertIn("TEST_COVERAGE_EVIDENCE_MISSING", codes(self.analyze()))
        (self.head / "coverage.json").write_text("not-json", encoding="utf-8")
        self.assertIn("TEST_COVERAGE_EVIDENCE_INVALID", codes(self.analyze()))

    def test_nested_paths_and_invalid_utf8_fail_closed_without_crashing(self):
        nested = self.head / "tests/deep/unit/test_binary.py"
        nested.parent.mkdir(parents=True)
        nested.write_bytes(b"def test_bad():\n    assert \xff\n")
        report = self.analyze()
        self.assertIn("TEST_FILE_UNREADABLE", codes(report))

    def test_no_absolute_test_count_minimum(self):
        shutil.rmtree(self.base / "tests")
        shutil.rmtree(self.head / "tests")
        report = self.analyze()
        self.assertEqual(report.findings, ())
        self.assertTrue(report.allowed)

    def test_manifest_incomplete_swapped_or_malformed_evidence_fails_closed(self):
        configured = policy(self.base, self.head)
        configured["head_manifest"].pop("tests/test_service.py")
        self.assertIn("TEST_CHECKOUT_INCOMPLETE", codes(analyze_test_integrity(self.base, self.head, configured)))
        configured = policy(self.base, self.head)
        configured["base_sha"] = configured["head_sha"]
        self.assertIn("TEST_REVISION_EVIDENCE_INVALID", codes(analyze_test_integrity(self.base, self.head, configured)))
        configured = policy(self.base, self.head)
        configured["base_manifest"] = configured["head_manifest"]
        (self.head / "tests/test_service.py").write_text("def test_other():\n    assert True\n", encoding="utf-8")
        self.assertIn("TEST_CHECKOUT_MISMATCH", codes(analyze_test_integrity(self.base, self.head, configured)))

    def test_unknown_or_malformed_policy_fails_closed(self):
        configured = policy(self.base, self.head)
        configured["unexpected"] = True
        self.assertIn("TEST_INTEGRITY_POLICY_INVALID", codes(analyze_test_integrity(self.base, self.head, configured)))
        configured = policy(self.base, self.head)
        configured["configuration"]["mystery"] = []
        self.assertIn("TEST_INTEGRITY_POLICY_INVALID", codes(analyze_test_integrity(self.base, self.head, configured)))
        configured = policy(self.base, self.head)
        configured["configuration"]["assertion_patterns"] = ["["]
        self.assertIn("TEST_INTEGRITY_POLICY_INVALID", codes(analyze_test_integrity(self.base, self.head, configured)))

    def test_human_and_agent_changes_use_identical_analysis(self):
        path = self.head / "tests/test_service.py"
        path.write_text("def test_sourced_value():\n    pass\n", encoding="utf-8")
        configured = policy(self.base, self.head)
        human = analyze_test_integrity(self.base, self.head, copy.deepcopy(configured))
        agent = analyze_test_integrity(self.base, self.head, copy.deepcopy(configured))
        self.assertEqual(human.to_dict(), agent.to_dict())

    def test_read_only_workflow_uses_base_guard_and_retains_machine_report(self):
        workflow = (ROOT / ".github/workflows/reusable-test-integrity.yml").read_text(encoding="utf-8")
        wrapper = ROOT / "scripts/engineering-os/validate-test-integrity"
        validation = (ROOT / "scripts/validate.sh").read_text(encoding="utf-8")
        terraform_workflow = (ROOT / ".github/workflows/terraform-validate.yml").read_text(encoding="utf-8")
        self.assertTrue(wrapper.stat().st_mode & 0o111)
        self.assertIn("permissions: {}", workflow)
        self.assertIn("contents: read", workflow)
        self.assertNotIn("issues: write", workflow)
        self.assertNotIn("pull-requests: write", workflow)
        self.assertIn("repository: ${{ job.workflow_repository }}", workflow)
        self.assertIn("ref: ${{ job.workflow_sha }}", workflow)
        self.assertIn("kernel/scripts/engineering-os/validate-test-integrity", workflow)
        self.assertNotIn("head/scripts/engineering-os/validate-test-integrity", workflow)
        self.assertNotIn("base/scripts/engineering-os/validate-test-integrity", workflow)
        self.assertIn("base/.aifo/engineering-os-policy.json", workflow)
        self.assertIn("actions/upload-artifact@v4", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("unittest discover", validation)
        self.assertIn("terraform fmt -check -recursive", validation)
        self.assertIn("./scripts/validate.sh", terraform_workflow)


class OverrideTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.base = root / "base"
        self.head = root / "head"
        shutil.copytree(FIXTURES / "base", self.base)
        shutil.copytree(FIXTURES / "head", self.head)
        (self.head / "tests/test_service.py").write_text("def test_sourced_value():\n    assert True\n", encoding="utf-8")
        self.report = self.analyze()

    def tearDown(self):
        self.temp.cleanup()

    def analyze(self):
        return analyze_test_integrity(self.base, self.head, policy(self.base, self.head))

    def override(self, tier="Tier 1"):
        value = json.loads((FIXTURES / "overrides/valid.json").read_text(encoding="utf-8"))
        value["report_sha256"] = self.report.report_sha256
        value["finding_codes"] = sorted(codes(self.report))
        value["risk_tier"] = tier
        return value

    def review(self, override=None):
        override = override or self.override()
        return {
            "schema_version": "1.0.0", "status": "approved",
            "override_id": override["override_id"], "mission_id": override["mission_id"],
            "repository": override["repository"], "pull_request": override["pull_request"],
            "head_sha": override["head_sha"], "report_sha256": override["report_sha256"],
            "reviewer_identity": "adversary", "reviewer_role": "adversary",
            "reviewed_at": "2026-07-15T11:00:00Z", "nonce": "review-nonce-1",
        }

    def approval(self, override=None):
        override = override or self.override("Tier 2")
        return {
            "schema_version": "1.0.0", "status": "approved", "action": "test-removal-override",
            "override_id": override["override_id"], "mission_id": override["mission_id"],
            "repository": override["repository"], "pull_request": override["pull_request"],
            "head_sha": override["head_sha"], "report_sha256": override["report_sha256"],
            "issuer": "founder", "approved_at": "2026-07-15T11:30:00Z",
            "expires_at": "2026-07-15T14:00:00Z", "nonce": "approval-nonce-1",
        }

    def test_valid_bounded_override_allows_but_preserves_findings_and_deltas(self):
        override = self.override()
        decision = validate_test_override(self.report, override, self.review(override), None)
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.code, "TEST_INTEGRITY_OVERRIDE_ALLOWED")
        self.assertEqual({item["code"] for item in decision.details["findings"]}, codes(self.report))
        self.assertEqual(decision.details["deltas"], self.report.deltas)

    def test_wrong_mission_repository_pr_sha_or_report_is_denied(self):
        mutations = {
            "mission_id": "mission-other", "repository": "other/repo", "pull_request": 99,
            "head_sha": "3" * 40, "base_sha": "4" * 40, "report_sha256": "5" * 64,
        }
        expected = {
            "mission_id": "TEST_OVERRIDE_REVIEW_MISMATCH", "repository": "TEST_OVERRIDE_REPOSITORY_MISMATCH",
            "pull_request": "TEST_OVERRIDE_REVIEW_MISMATCH", "head_sha": "TEST_OVERRIDE_HEAD_MISMATCH",
            "base_sha": "TEST_OVERRIDE_BASE_MISMATCH", "report_sha256": "TEST_OVERRIDE_REPORT_MISMATCH",
        }
        for field, value in mutations.items():
            with self.subTest(field=field):
                override = self.override()
                override[field] = value
                decision = validate_test_override(self.report, override, self.review(), None)
                self.assertEqual(decision.code, expected[field])

    def test_missing_rejected_or_forged_reviewer_is_denied(self):
        override = self.override()
        self.assertEqual(validate_test_override(self.report, override, None, None).code, "TEST_OVERRIDE_REVIEW_REQUIRED")
        review = self.review(override)
        review["status"] = "rejected"
        self.assertEqual(validate_test_override(self.report, override, review, None).code, "TEST_OVERRIDE_REVIEW_DENIED")
        review = self.review(override)
        review["reviewer_identity"] = "producer"
        self.assertEqual(validate_test_override(self.report, override, review, None).code, "TEST_OVERRIDE_REVIEWER_DENIED")

    def test_stale_expired_duplicate_and_replayed_override_is_denied(self):
        override = self.override()
        override["expires_at"] = "2026-07-15T11:59:59Z"
        self.assertEqual(validate_test_override(self.report, override, self.review(override), None).code, "TEST_OVERRIDE_EXPIRED")
        override = self.override()
        override["finding_codes"].append(override["finding_codes"][0])
        self.assertEqual(validate_test_override(self.report, override, self.review(override), None).code, "TEST_OVERRIDE_INVALID")
        override = self.override()
        override["consumed_at"] = "2026-07-15T11:30:00Z"
        self.assertEqual(validate_test_override(self.report, override, self.review(override), None).code, "TEST_OVERRIDE_REPLAYED")

    def test_tier_two_requires_exact_founder_approval(self):
        override = self.override("Tier 2")
        review = self.review(override)
        self.assertEqual(validate_test_override(self.report, override, review, None).code, "TEST_OVERRIDE_FOUNDER_APPROVAL_REQUIRED")
        approval = self.approval(override)
        approval["issuer"] = "outsider"
        self.assertEqual(validate_test_override(self.report, override, review, approval).code, "TEST_OVERRIDE_FOUNDER_DENIED")
        approval = self.approval(override)
        self.assertTrue(validate_test_override(self.report, override, review, approval).allowed)

    def test_unknown_override_review_or_approval_fields_fail_closed(self):
        override = self.override()
        override["unknown"] = True
        self.assertEqual(validate_test_override(self.report, override, self.review(), None).code, "TEST_OVERRIDE_INVALID")
        override = self.override()
        review = self.review(override)
        review["unknown"] = True
        self.assertEqual(validate_test_override(self.report, override, review, None).code, "TEST_OVERRIDE_REVIEW_INVALID")
        override = self.override("Tier 2")
        approval = self.approval(override)
        approval["unknown"] = True
        self.assertEqual(validate_test_override(self.report, override, self.review(override), approval).code, "TEST_OVERRIDE_APPROVAL_INVALID")
