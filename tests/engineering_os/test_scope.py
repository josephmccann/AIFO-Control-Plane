import json
import os
import subprocess
import unittest
from pathlib import Path

from engineering_os.scope import detect_mission_conflicts, validate_scope
from tests.engineering_os.test_risk import mission, policy


ROOT = Path(__file__).resolve().parents[2]
ACTIVE = ROOT / "tests" / "engineering_os" / "fixtures" / "active-missions"


def active(name):
    return json.loads((ACTIVE / name).read_text(encoding="utf-8"))


class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.mission = mission("Tier 1")
        self.mission["allowed_paths"] = ["src/reporting/**", "tests/reporting/**"]
        self.mission["prohibited_paths"] = ["src/reporting/private/**"]

    def test_allowed_paths_pass_and_outside_or_prohibited_paths_fail(self):
        self.assertEqual(validate_scope(self.mission, policy(), ["src/reporting/render.py"]), [])
        outside = validate_scope(self.mission, policy(), ["README.md"])
        prohibited = validate_scope(self.mission, policy(), ["src/reporting/private/key.py"])
        self.assertIn("SCOPE_PATH_NOT_ALLOWED", {item.code for item in outside})
        self.assertIn("SCOPE_PATH_PROHIBITED", {item.code for item in prohibited})

    def test_paths_are_posix_normalized_and_absolute_or_traversal_is_rejected(self):
        self.assertEqual(validate_scope(self.mission, policy(), ["src//reporting/./render.py"]), [])
        for bad in ("/etc/passwd", "src/reporting/../../secret", "src\\reporting\\render.py"):
            with self.subTest(path=bad):
                codes = {item.code for item in validate_scope(self.mission, policy(), [bad])}
                self.assertIn("SCOPE_PATH_INVALID", codes)

    def test_tier_one_cannot_touch_a_tier_two_path(self):
        self.mission["allowed_paths"].append(".github/**")
        codes = {item.code for item in validate_scope(self.mission, policy(), [".github/workflows/ci.yml"])}
        self.assertIn("SCOPE_TIER_2_PATH", codes)

    def test_path_and_semantic_conflicts_are_denied(self):
        path_conflicts = detect_mission_conflicts(
            self.mission, policy(), ["src/reporting/render.py"],
            active("conflicting/path-overlap.json"),
        )
        semantic_conflicts = detect_mission_conflicts(
            self.mission, policy(), ["src/reporting/new.py"],
            active("conflicting/semantic-overlap.json"),
        )
        self.assertIn("MISSION_PATH_CONFLICT", {item.code for item in path_conflicts})
        self.assertIn("MISSION_SEMANTIC_CONFLICT", {item.code for item in semantic_conflicts})

    def test_coordinated_overlap_requires_exact_missions_and_scopes(self):
        records = [{
            "status": "active",
            "issuer_role": "founder",
            "mission_ids": ["mission-123", "mission-other"],
            "scopes": {
                "mission-123": ["src/reporting/render.py"],
                "mission-other": ["src/reporting/**"],
            },
        }]
        conflicts = detect_mission_conflicts(
            self.mission, policy(), ["src/reporting/render.py"],
            active("conflicting/path-overlap.json"), coordination_records=records,
        )
        self.assertEqual(conflicts, [])
        records[0]["scopes"]["mission-123"] = ["src/reporting/other.py"]
        self.assertTrue(detect_mission_conflicts(
            self.mission, policy(), ["src/reporting/render.py"],
            active("conflicting/path-overlap.json"), coordination_records=records,
        ))

    def test_malformed_policy_globs_fail_closed(self):
        broken = policy()
        broken["tier_2_paths"] = ["../outside/**"]
        codes = {item.code for item in validate_scope(self.mission, broken, ["src/reporting/render.py"])}
        self.assertIn("SCOPE_POLICY_INVALID", codes)

    def test_path_wrapper_and_reusable_guard_use_base_policy_read_only(self):
        wrapper = ROOT / "scripts" / "engineering-os" / "validate-paths"
        workflow = ROOT / ".github" / "workflows" / "reusable-tier-path-guard.yml"
        self.assertTrue(os.access(wrapper, os.X_OK))
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("contents: read", text)
        self.assertNotIn("contents: write", text)
        self.assertIn("github.event.pull_request.base.sha", text)
        self.assertIn('git show "$BASE_SHA:.aifo/engineering-os-policy.json"', text)
        self.assertIn("validate-tier", text)
        self.assertIn("validate-paths", text)

    def test_documented_model_keeps_ownership_separate_from_lifecycle(self):
        authority = (ROOT / "docs/engineering-os/AUTHORITY_MODEL.md").read_text(encoding="utf-8")
        self.assertIn("do not alter mission lifecycle authority", authority)
        self.assertIn("exact mission", authority)


if __name__ == "__main__":
    unittest.main()
