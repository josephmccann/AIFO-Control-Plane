import copy
import json
import os
import unittest
from pathlib import Path

from engineering_os.frozen import validate_frozen_changes
from tests.engineering_os.test_risk import mission


ROOT = Path(__file__).resolve().parents[2]
FROZEN = ROOT / "tests" / "engineering_os" / "fixtures" / "frozen-declarations"
HEAD = "2222222222222222222222222222222222222222"


def declaration():
    return json.loads((FROZEN / "methodology/signal-engine.json").read_text(encoding="utf-8"))


def exception():
    item = declaration()
    return {
        "exception_id": "exception-1",
        "declaration_id": item["declaration_id"],
        "repository": "acme/widgets",
        "mission_id": "mission-123",
        "pull_request": 42,
        "head_sha": HEAD,
        "paths": ["src/engine/model.py"],
        "action": "write",
        "issuer": "founder",
        "issuer_role": "founder",
        "starts_at": "2026-07-15T00:00:00Z",
        "expires_at": "2026-07-16T00:00:00Z",
        "status": "active",
        "pinned_commit": item["pinned_commit"],
        "sealed_manifest_sha256": item["sealed_manifest_sha256"],
        "protected_version": item["protected_version"],
        "release_condition": item["release_condition"],
        "one_shot": True,
    }


def observations(**updates):
    item = declaration()
    value = {
        item["declaration_id"]: {
            "pinned_commit": item["pinned_commit"],
            "sealed_manifest_sha256": item["sealed_manifest_sha256"],
            "protected_version": item["protected_version"],
        }
    }
    value[item["declaration_id"]].update(updates)
    return value


def decide(exceptions=(), **updates):
    context = {
        "repository": "acme/widgets",
        "pull_request": 42,
        "head_sha": HEAD,
        "now": "2026-07-15T12:00:00Z",
        "action": "write",
        "observations": observations(),
        "satisfied_release_conditions": ["founder-approved-methodology-release"],
        "consumed_exception_ids": [],
    }
    context.update(updates)
    return validate_frozen_changes(
        mission("Tier 2"), ["src/engine/model.py"], [declaration()], list(exceptions), **context
    )


class FrozenTests(unittest.TestCase):
    def test_frozen_write_is_denied_without_an_exception(self):
        result = decide()
        self.assertEqual((result.allowed, result.code), (False, "FROZEN_WRITE_DENIED"))

    def test_valid_exception_requires_exact_mission_pr_head_path_and_action(self):
        self.assertEqual((decide([exception()]).allowed, decide([exception()]).code), (True, "FROZEN_EXCEPTION_ALLOWED"))
        mutations = (
            ("mission_id", "mission-other", "FROZEN_EXCEPTION_MISSION_MISMATCH"),
            ("pull_request", 43, "FROZEN_EXCEPTION_PR_MISMATCH"),
            ("head_sha", "3" * 40, "FROZEN_EXCEPTION_HEAD_MISMATCH"),
            ("paths", ["src/engine/other.py"], "FROZEN_EXCEPTION_PATH_MISMATCH"),
            ("action", "merge", "FROZEN_EXCEPTION_ACTION_MISMATCH"),
        )
        for field, value, code in mutations:
            with self.subTest(field=field):
                candidate = exception(); candidate[field] = value
                self.assertEqual(decide([candidate]).code, code)

    def test_stale_expired_or_wrong_sha_exception_is_denied(self):
        stale = exception(); stale["status"] = "revoked"
        expired = exception(); expired["expires_at"] = "2026-07-15T12:00:00Z"
        wrong_sha = exception(); wrong_sha["head_sha"] = "f" * 40
        self.assertEqual(decide([stale]).code, "FROZEN_EXCEPTION_INACTIVE")
        self.assertEqual(decide([expired]).code, "FROZEN_EXCEPTION_EXPIRED")
        self.assertEqual(decide([wrong_sha]).code, "FROZEN_EXCEPTION_HEAD_MISMATCH")

        incomplete = exception(); incomplete.pop("exception_id")
        self.assertEqual(decide([incomplete]).code, "FROZEN_EXCEPTION_INVALID")

    def test_pin_manifest_and_protected_version_must_match(self):
        cases = (
            ({"pinned_commit": "9" * 40}, "FROZEN_PIN_MISMATCH"),
            ({"sealed_manifest_sha256": "9" * 64}, "FROZEN_MANIFEST_MISMATCH"),
            ({"protected_version": "2.0.0"}, "FROZEN_VERSION_MISMATCH"),
        )
        for observed, code in cases:
            with self.subTest(code=code):
                self.assertEqual(decide([exception()], observations=observations(**observed)).code, code)

    def test_release_condition_and_one_shot_marker_are_enforced(self):
        self.assertEqual(decide([exception()], satisfied_release_conditions=[]).code, "FROZEN_RELEASE_CONDITION_UNMET")
        self.assertEqual(decide([exception()], consumed_exception_ids=["exception-1"]).code, "FROZEN_EXCEPTION_CONSUMED")
        candidate = exception(); candidate["one_shot"] = False
        self.assertEqual(decide([candidate]).code, "FROZEN_EXCEPTION_ONE_SHOT_MISMATCH")

    def test_unrelated_changes_pass_and_malformed_paths_fail_closed(self):
        result = validate_frozen_changes(
            mission("Tier 1"), ["src/other.py"], [declaration()], [],
            repository="acme/widgets", pull_request=42, head_sha=HEAD,
            now="2026-07-15T12:00:00Z", action="write",
        )
        self.assertEqual((result.allowed, result.code), (True, "FROZEN_PATHS_UNTOUCHED"))
        malformed = copy.deepcopy(declaration()); malformed["paths"] = ["../escape"]
        denied = validate_frozen_changes(
            mission("Tier 1"), ["src/other.py"], [malformed], [],
            repository="acme/widgets", pull_request=42, head_sha=HEAD,
            now="2026-07-15T12:00:00Z", action="write",
        )
        self.assertEqual(denied.code, "FROZEN_DECLARATION_INVALID")
        incomplete = copy.deepcopy(declaration()); incomplete.pop("schema_version")
        denied = validate_frozen_changes(
            mission("Tier 1"), ["src/other.py"], [incomplete], [],
            repository="acme/widgets", pull_request=42, head_sha=HEAD,
            now="2026-07-15T12:00:00Z", action="write",
        )
        self.assertEqual(denied.code, "FROZEN_DECLARATION_INVALID")

    def test_frozen_wrapper_guard_and_docs_are_present_and_non_mutating(self):
        wrapper = ROOT / "scripts/engineering-os/validate-frozen-artifacts"
        workflow = ROOT / ".github/workflows/reusable-frozen-path-guard.yml"
        document = ROOT / "docs/engineering-os/FROZEN_ARTIFACTS.md"
        self.assertTrue(os.access(wrapper, os.X_OK))
        workflow_text = workflow.read_text(encoding="utf-8")
        self.assertIn("contents: read", workflow_text)
        self.assertNotIn("contents: write", workflow_text)
        self.assertIn("github.event.pull_request.base.sha", workflow_text)
        self.assertIn('git show "$BASE_SHA:.aifo/engineering-os-policy.json"', workflow_text)
        text = document.read_text(encoding="utf-8")
        self.assertIn("one-shot", text)
        self.assertIn("No EDGAR integration is activated", text)


if __name__ == "__main__":
    unittest.main()
