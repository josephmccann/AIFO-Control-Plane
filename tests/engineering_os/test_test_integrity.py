import copy
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from engineering_os.test_integrity import (
    CoverageAttestation,
    analyze_test_integrity,
    validate_test_override,
)
from engineering_os.canonical import content_sha256
from tests.engineering_os.fake_github import SealedFakeGitHubTransport, transported_record


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "engineering_os" / "fixtures" / "test-integrity"
BASE_SHA = "1" * 40
HEAD_SHA = "2" * 40


def _hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest(root):
    result = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        payload = path.read_bytes()
        result[path.relative_to(root).as_posix()] = {
            "sha256": hashlib.sha256(payload).hexdigest(),
            "git_blob_sha": hashlib.sha1(
                b"blob " + str(len(payload)).encode("ascii") + b"\0" + payload
            ).hexdigest(),
        }
    return result


def policy(base, head):
    value = {
        "schema_version": "1.0.0",
        "repository": "acme/widgets",
        "base_sha": BASE_SHA,
        "head_sha": HEAD_SHA,
        "evaluated_at": "2026-07-15T12:00:00Z",
        "base_manifest": _manifest(base),
        "head_manifest": _manifest(head),
        "coverage_attestations": None,
        "founder_identities": ["founder"],
        "mission": {
            "mission_id": "mission-123", "mission_issue": 10,
            "pull_request": 42, "mission_sha256": "3" * 64,
            "mission_event_hash": "4" * 64,
            "declared_tier": "Tier 1", "computed_tier": "Tier 1",
            "effective_tier": "Tier 1", "producer_identity": "producer",
            "producer_model_family": "openai", "adversary_identity": "adversary",
            "adversary_model_family": "anthropic",
        },
        "configuration": {
            "test_globs": ["tests/**/test_*.py", "tests/**/*.test.js", "tests/**/*.spec.js"],
            "fixture_globs": ["tests/**/fixtures/**"],
            "validation_workflow_globs": [".github/workflows/**"],
            "test_config_globs": [
                "**/pyproject.toml", "**/pytest.ini", "**/setup.cfg", "**/tox.ini",
                "**/package.json", "**/jest.config.js", "**/jest.config.ts",
                "**/jest.config.mjs", "**/jest.config.cjs", "**/jest.config.json",
                "**/jest.config.yml", "**/jest.config.yaml", "**/vitest.config.js",
                "**/vitest.config.ts", "**/vitest.config.mjs", "**/vitest.config.cjs",
                "**/vitest.config.json", "**/vitest.config.yml", "**/vitest.config.yaml",
            ],
            "coverage_paths": ["coverage.json", "coverage-summary.json", ".eos/coverage.json"],
            "material_coverage_decline": 1.0,
            "assertion_patterns": [r"\bassert\b", r"\bexpect\s*\(", r"\.assert[A-Z]\w*\s*\("],
            "skip_patterns": [r"\bskip(?:If|Unless|Test)?\b", r"\.(?:skip|todo|disabled)\b", r"\bdisabled\b"],
            "max_file_bytes": 1048576,
            "coverage_max_age_seconds": 86400,
            "max_files": 10000,
            "max_total_bytes": 67108864,
            "max_path_bytes": 1024,
            "max_git_record_bytes": 4096,
            "max_github_pages": 20,
            "max_github_items": 2000,
            "max_github_response_bytes": 8388608,
            "max_coverage_bytes": 1048576,
        },
    }
    coverage_paths = value["configuration"]["coverage_paths"]
    present_base = [path for path in coverage_paths if path in value["base_manifest"]]
    present_head = [path for path in coverage_paths if path in value["head_manifest"]]
    if len(present_base) == len(present_head) == 1:
        def sealed(root, manifest, commit, path, number):
            document = json.loads((root / path).read_text(encoding="utf-8"))
            source = {name: evidence for name, evidence in manifest.items() if name not in coverage_paths}
            return CoverageAttestation(
                "1.0.0", value["repository"], commit,
                hashlib.sha256(json.dumps(source, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest(),
                document.get("generated_at", ""), document.get("generated_at", ""),
                ".github/workflows/coverage.yml",
                commit, 1000 + number, 2000 + number, hashlib.sha256(("artifact-%d" % number).encode()).hexdigest(),
                path, manifest[path]["sha256"], "success", "sealed-test-github-actions:v1",
            )
        try:
            value["coverage_attestations"] = {
                "base": sealed(base, value["base_manifest"], value["base_sha"], present_base[0], 1),
                "head": sealed(head, value["head_manifest"], value["head_sha"], present_head[0], 2),
            }
        except (json.JSONDecodeError, UnicodeDecodeError):
            value["coverage_attestations"] = None
    return value


def write_coverage(root, configured, commit_sha, percent, *, generated_at="2026-07-15T11:00:00Z"):
    manifest = _manifest(root)
    source = {
        path: evidence for path, evidence in manifest.items()
        if path not in configured["configuration"]["coverage_paths"]
    }
    path = root / "coverage-summary.json"
    path.write_text(json.dumps({
        "schema_version": "1.0.0", "repository": configured["repository"],
        "commit_sha": commit_sha,
        "source_manifest_sha256": hashlib.sha256(
            json.dumps(source, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest(),
        "generated_at": generated_at, "coverage": {"lines_percent": percent},
    }), encoding="utf-8")


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
        configured = policy(self.base, self.head)
        write_coverage(self.base, configured, configured["base_sha"], 90.0)
        write_coverage(self.head, configured, configured["head_sha"], 88.9)
        report = self.analyze()
        self.assertIn("TEST_COVERAGE_DECLINE", codes(report))
        self.assertEqual(report.deltas["coverage_percent"], -1.1)
        configured = policy(self.base, self.head)
        write_coverage(self.head, configured, configured["head_sha"], 91.0)
        self.assertNotIn("TEST_COVERAGE_DECLINE", codes(self.analyze()))

    def test_missing_or_malformed_coverage_fails_closed(self):
        configured = policy(self.base, self.head)
        write_coverage(self.base, configured, configured["base_sha"], 90.0)
        (self.base / "coverage-summary.json").rename(self.base / "coverage.json")
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
        self.store = str(root / "consumption.sqlite")

    def tearDown(self):
        self.temp.cleanup()

    def analyze(self):
        return analyze_test_integrity(self.base, self.head, policy(self.base, self.head))

    def set_tier_two(self):
        configured = policy(self.base, self.head)
        for field in ("declared_tier", "computed_tier", "effective_tier"):
            configured["mission"][field] = "Tier 2"
        self.report = analyze_test_integrity(self.base, self.head, configured)

    def records(self, *, approval=False):
        report = self.report
        override_payload = {
            "schema_version": "1.0.0", "record_id": "override-record-1",
            "override_id": "override-1", "mission_id": report.mission_id,
            "mission_issue": report.mission_issue, "repository": report.repository,
            "pull_request": report.pull_request, "base_sha": report.base_sha,
            "head_sha": report.head_sha, "mission_sha256": report.mission_sha256,
            "mission_event_hash": report.mission_event_hash,
            "risk_tier": report.effective_tier, "report_sha256": report.report_sha256,
            "finding_codes": sorted(codes(report)),
            "reason": "Behavior was intentionally removed.",
            "behavior_removed": "Legacy behavior is no longer supported.",
            "producer_identity": report.producer_identity,
            "adversary_identity": report.adversary_identity,
            "issued_at": "2026-07-15T12:10:00Z", "expires_at": "2026-07-15T14:00:00Z",
            "nonce": "override-nonce-1", "single_use": True,
        }
        override, first = transported_record(
            "test_override", override_payload, actor=report.producer_identity,
            created_at=override_payload["issued_at"], head_sha=report.head_sha,
        )
        override_digest = content_sha256(override_payload)
        review_payload = {
            "schema_version": "1.0.0", "record_id": "review-record-1", "review_id": "review-1",
            "status": "approved", "override_id": override["override_id"],
            "override_sha256": override_digest, "mission_id": report.mission_id,
            "mission_issue": report.mission_issue, "repository": report.repository,
            "pull_request": report.pull_request, "head_sha": report.head_sha,
            "report_sha256": report.report_sha256,
            "reviewer_identity": report.adversary_identity, "reviewer_role": "adversary",
            "reviewed_at": "2026-07-15T12:20:00Z", "nonce": "review-nonce-1",
            "single_use": True,
        }
        review, second = transported_record(
            "test_override_review", review_payload, actor=report.adversary_identity,
            created_at=review_payload["reviewed_at"], head_sha=report.head_sha,
            comment_id=9002,
        )
        approval_record = None
        evidence = [first, second]
        if approval:
            approval_payload = {
                "schema_version": "1.0.0", "record_id": "approval-record-1",
                "approval_id": "approval-1", "status": "approved",
                "action": "test-removal-override", "override_id": override["override_id"],
                "override_sha256": override_digest, "review_id": review["review_id"],
                "review_sha256": content_sha256(review_payload), "mission_id": report.mission_id,
                "mission_issue": report.mission_issue, "repository": report.repository,
                "pull_request": report.pull_request, "head_sha": report.head_sha,
                "report_sha256": report.report_sha256, "issuer": "founder",
                "approved_at": "2026-07-15T12:30:00Z", "expires_at": "2026-07-15T14:00:00Z",
                "nonce": "approval-nonce-1", "single_use": True,
            }
            approval_record, third = transported_record(
                "test_override_approval", approval_payload, actor="founder",
                created_at=approval_payload["approved_at"], head_sha=report.head_sha,
                comment_id=9003,
            )
            evidence.append(third)
        return override, review, approval_record, SealedFakeGitHubTransport(evidence)

    def decide(self, override, review, approval, transport):
        return validate_test_override(
            self.report, override, review, approval, now="2026-07-15T13:00:00Z",
            evidence_verifier=transport, consumption_store=self.store,
        )

    def test_valid_bounded_override_allows_but_preserves_findings_and_deltas(self):
        override, review, approval, transport = self.records()
        decision = self.decide(override, review, approval, transport)
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.code, "TEST_INTEGRITY_OVERRIDE_ALLOWED")
        self.assertEqual({item["code"] for item in decision.details["findings"]}, codes(self.report))
        self.assertEqual(decision.details["deltas"], self.report.deltas)

    def test_wrong_context_or_forged_source_is_denied(self):
        override, review, approval, transport = self.records()
        override["pull_request"] = 99
        self.assertEqual(self.decide(override, review, approval, transport).code, "TEST_OVERRIDE_PR_MISMATCH")
        override, review, approval, transport = self.records()
        override["reason"] = "forged"
        self.assertEqual(self.decide(override, review, approval, transport).code, "TEST_OVERRIDE_SOURCE_UNAUTHENTICATED")

    def test_exact_records_are_atomically_single_use(self):
        override, review, approval, transport = self.records()
        self.assertTrue(self.decide(override, review, approval, transport).allowed)
        self.assertEqual(self.decide(override, review, approval, transport).code, "TEST_OVERRIDE_REPLAYED")

    def test_tier_two_requires_exact_founder_approval(self):
        self.set_tier_two()
        override, review, _, transport = self.records()
        self.assertEqual(self.decide(override, review, None, transport).code, "TEST_OVERRIDE_FOUNDER_APPROVAL_REQUIRED")
        override, review, approval, transport = self.records(approval=True)
        self.assertTrue(self.decide(override, review, approval, transport).allowed)

    def test_unknown_override_review_or_approval_fields_fail_closed(self):
        override, review, approval, transport = self.records()
        override["unknown"] = True
        self.assertEqual(self.decide(override, review, approval, transport).code, "TEST_OVERRIDE_INVALID")
        override, review, approval, transport = self.records()
        review["unknown"] = True
        self.assertEqual(self.decide(override, review, approval, transport).code, "TEST_OVERRIDE_INVALID")
        self.set_tier_two()
        override, review, approval, transport = self.records(approval=True)
        approval["unknown"] = True
        self.assertEqual(self.decide(override, review, approval, transport).code, "TEST_OVERRIDE_APPROVAL_INVALID")
