import json
import os
import subprocess
import unittest
from pathlib import Path

import engineering_os.scope as scope_kernel
from engineering_os.scope import detect_mission_conflicts, validate_scope
from tests.engineering_os.fake_github import SealedFakeGitHubTransport, transported_record
from tests.engineering_os.test_risk import mission, policy


ROOT = Path(__file__).resolve().parents[2]
ACTIVE = ROOT / "tests" / "engineering_os" / "fixtures" / "active-missions"


def active(name):
    return json.loads((ACTIVE / name).read_text(encoding="utf-8"))


def github_record(record_kind, payload, *, comment_id=9001, issue_number=10, actor="founder"):
    record, evidence = transported_record(
        record_kind, payload, subject_kind="issue", subject_number=issue_number,
        comment_id=comment_id, actor=actor, created_at="2026-07-15T10:00:00Z",
        head_sha="2" * 40,
    )
    return record, SealedFakeGitHubTransport(evidence)


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

    def test_git_globs_are_segment_aware(self):
        self.mission["allowed_paths"] = ["src/reporting/*"]
        nested = validate_scope(self.mission, policy(), ["src/reporting/deep/render.py"])
        self.assertIn("SCOPE_PATH_NOT_ALLOWED", {item.code for item in nested})
        self.mission["allowed_paths"] = ["src/reporting/**"]
        self.assertEqual(validate_scope(self.mission, policy(), ["src/reporting/deep/render.py"]), [])

    def test_every_matching_pattern_intersects_its_concrete_path(self):
        intersects = getattr(
            scope_kernel, "patterns_overlap", scope_kernel._patterns_overlap,
        )
        cases = (
            ("src/**", "src/deep/render.py"),
            ("tests/**/reporting/**", "tests/reporting/report.py"),
            ("tests/**/reporting/**", "tests/unit/reporting/report.py"),
            ("src/[!a-c]*/?.py", "src/delta/x.py"),
            ("src/[a-c][0-9].py", "src/b7.py"),
        )
        for pattern, concrete in cases:
            with self.subTest(pattern=pattern, concrete=concrete):
                self.assertTrue(scope_kernel.path_matches(concrete, pattern))
                self.assertTrue(intersects(pattern, concrete))

    def test_glob_intersection_uses_the_same_negated_classes_as_matching(self):
        intersects = getattr(
            scope_kernel, "patterns_overlap", scope_kernel._patterns_overlap,
        )
        self.assertTrue(intersects("src/[!a-c].py", "src/d.py"))
        self.assertFalse(intersects("src/[!a-c].py", "src/b.py"))
        self.assertFalse(intersects("src/[a-c].py", "src/[d-f].py"))
        self.assertTrue(intersects("src/[!a-c].py", "src/[d-f].py"))

    def test_unsupported_recursive_and_character_class_forms_fail_closed(self):
        unsupported = (
            "src/foo**bar/file.py", "src/**bar/file.py", "src/foo***/file.py",
            "src/[z-a]/file.py", "src/[]/file.py", "src/[!]/file.py",
            "src/[abc/file.py", "src/[a/b]/file.py",
        )
        for pattern in unsupported:
            with self.subTest(pattern=pattern):
                candidate = dict(self.mission)
                candidate["allowed_paths"] = [pattern]
                codes = {item.code for item in validate_scope(
                    candidate, policy(), ["src/reporting/render.py"],
                )}
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

    def test_semantic_domains_intersect_declared_globs_conservatively(self):
        intersecting = [{
            "mission_id": "mission-other", "state": "Claimed",
            "paths": ["tests/**/reporting/**"],
        }]
        conflicts = detect_mission_conflicts(
            self.mission, policy(), ["src/reporting/new.py"], intersecting,
        )
        self.assertIn("MISSION_SEMANTIC_CONFLICT", {item.code for item in conflicts})

        for disjoint in ("tests/billing/**", "clients/**/*.js", "docs/private/**"):
            with self.subTest(disjoint=disjoint):
                active_missions = [{
                    "mission_id": "mission-other", "state": "Claimed", "paths": [disjoint],
                }]
                self.assertEqual(detect_mission_conflicts(
                    self.mission, policy(), ["src/reporting/new.py"], active_missions,
                ), [])

    def test_proposed_and_ready_do_not_reserve_scope_but_claimed_does(self):
        for state in ("Proposed", "Ready"):
            with self.subTest(state=state):
                self.assertEqual(detect_mission_conflicts(
                    self.mission, policy(), ["src/reporting/render.py"], [{
                        "mission_id": "mission-other", "state": state, "paths": ["**"],
                    }],
                ), [])
        self.assertEqual(detect_mission_conflicts(
            self.mission, policy(), ["src/reporting/render.py"], [{
                "mission_id": "mission-proposed-malformed-scope",
                "state": "Proposed", "paths": ["src/[z-a]/**"],
            }],
        ), [])
        claimed = detect_mission_conflicts(
            self.mission, policy(), ["src/reporting/render.py"], [{
                "mission_id": "mission-other", "state": "Claimed", "paths": ["**"],
            }],
        )
        self.assertIn("MISSION_PATH_CONFLICT", {item.code for item in claimed})

    def test_fabricated_coordination_cannot_reuse_a_copied_source(self):
        fabricated_payload = {
            "record_id": "coordination-forged", "repository": "acme/widgets",
            "status": "active", "issuer": "founder",
            "mission_ids": ["mission-123", "mission-other"], "pull_request": 42,
            "head_sha": "2" * 40, "starts_at": "2026-07-15T00:00:00Z",
            "expires_at": "2026-07-16T00:00:00Z", "nonce": "forged-nonce",
            "scopes": {
                "mission-123": ["src/reporting/render.py"],
                "mission-other": ["src/reporting/**"],
            },
        }
        legitimate_payload = dict(fabricated_payload)
        legitimate_payload["scopes"] = {
            "mission-123": ["src/reporting/other.py"],
            "mission-other": ["src/reporting/**"],
        }
        legitimate, transport = github_record("coordination", legitimate_payload)
        fabricated = dict(fabricated_payload)
        fabricated["source"] = legitimate["source"]
        conflicts = detect_mission_conflicts(
            self.mission, policy(), ["src/reporting/render.py"],
            active("conflicting/path-overlap.json"), coordination_records=[fabricated],
            repository="acme/widgets", pull_request=42, head_sha="2" * 40,
            now="2026-07-15T12:00:00Z", evidence_verifier=transport,
        )
        self.assertIn("MISSION_PATH_CONFLICT", {item.code for item in conflicts})

    def test_coordinated_overlap_requires_exact_missions_and_scopes(self):
        payload = {
            "record_id": "coordination-1",
            "repository": "acme/widgets",
            "status": "active",
            "issuer": "founder",
            "mission_ids": ["mission-123", "mission-other"],
            "pull_request": 42,
            "head_sha": "2" * 40,
            "starts_at": "2026-07-15T00:00:00Z",
            "expires_at": "2026-07-16T00:00:00Z",
            "nonce": "coordination-nonce-1",
            "scopes": {
                "mission-123": ["src/reporting/render.py"],
                "mission-other": ["src/reporting/**"],
            },
        }
        authenticated, transport = github_record("coordination", payload)
        records = [authenticated]
        conflicts = detect_mission_conflicts(
            self.mission, policy(), ["src/reporting/render.py"],
            active("conflicting/path-overlap.json"), coordination_records=records,
            repository="acme/widgets", pull_request=42, head_sha="2" * 40,
            now="2026-07-15T12:00:00Z", evidence_verifier=transport,
        )
        self.assertEqual(conflicts, [])
        records[0]["scopes"]["mission-123"] = ["src/reporting/other.py"]
        self.assertTrue(detect_mission_conflicts(
            self.mission, policy(), ["src/reporting/render.py"],
            active("conflicting/path-overlap.json"), coordination_records=records,
            repository="acme/widgets", pull_request=42, head_sha="2" * 40,
            now="2026-07-15T12:00:00Z", evidence_verifier=transport,
        ))

    def test_coordination_rejects_wrong_founder_or_missing_authenticated_source(self):
        payload = {
            "record_id": "coordination-1", "repository": "acme/widgets",
            "status": "active", "issuer": "outsider",
            "mission_ids": ["mission-123", "mission-other"], "pull_request": 42,
            "head_sha": "2" * 40, "starts_at": "2026-07-15T00:00:00Z",
            "expires_at": "2026-07-16T00:00:00Z", "nonce": "nonce",
            "scopes": {"mission-123": ["src/reporting/render.py"], "mission-other": ["src/reporting/**"]},
        }
        authenticated, transport = github_record("coordination", payload, actor="outsider")
        conflicts = detect_mission_conflicts(
            self.mission, policy(), ["src/reporting/render.py"],
            active("conflicting/path-overlap.json"), coordination_records=[authenticated],
            repository="acme/widgets", pull_request=42, head_sha="2" * 40,
            now="2026-07-15T12:00:00Z", evidence_verifier=transport,
        )
        self.assertIn("MISSION_PATH_CONFLICT", {item.code for item in conflicts})

    def test_active_missions_fail_closed_on_malformed_duplicate_or_unknown_state(self):
        cases = (
            [None],
            [{"mission_id": "other", "state": "Teleporting", "paths": ["src/other/**"]}],
            [
                {"mission_id": "other", "state": "Claimed", "paths": ["src/a/**"]},
                {"mission_id": "other", "state": "In Progress", "paths": ["src/b/**"]},
            ],
        )
        for active_missions in cases:
            with self.subTest(active_missions=active_missions):
                codes = {item.code for item in detect_mission_conflicts(
                    self.mission, policy(), ["src/reporting/render.py"], active_missions,
                )}
                self.assertIn("MISSION_CONFLICT_INPUT_INVALID", codes)

    def test_disjoint_suffix_globs_do_not_false_conflict(self):
        active_missions = [{
            "mission_id": "mission-other", "state": "Claimed",
            "paths": ["src/misc/*.js"],
        }]
        self.assertEqual(detect_mission_conflicts(
            self.mission, policy(), ["src/misc/file.py"], active_missions,
        ), [])

    def test_malformed_policy_globs_fail_closed(self):
        broken = policy()
        broken["tier_2_paths"] = ["../outside/**"]
        codes = {item.code for item in validate_scope(self.mission, broken, ["src/reporting/render.py"])}
        self.assertIn("SCOPE_POLICY_INVALID", codes)

    def test_malformed_regex_ranges_fail_closed_without_exceptions(self):
        malformed_mission = dict(self.mission)
        malformed_mission["allowed_paths"] = ["src/[z-a]/**"]
        codes = {item.code for item in validate_scope(
            malformed_mission, policy(), ["src/reporting/render.py"],
        )}
        self.assertIn("SCOPE_PATH_INVALID", codes)

        conflicts = detect_mission_conflicts(
            self.mission, policy(), ["src/reporting/render.py"], [{
                "mission_id": "mission-other", "state": "Claimed", "paths": ["src/[z-a]/**"],
            }],
        )
        self.assertIn("MISSION_CONFLICT_INPUT_INVALID", {item.code for item in conflicts})

    def test_complete_mission_and_policy_schemas_are_required(self):
        incomplete_mission = dict(self.mission)
        incomplete_mission.pop("objective")
        incomplete_policy = policy()
        incomplete_policy.pop("required_status_checks")
        self.assertIn("SCOPE_MISSION_INVALID", {item.code for item in validate_scope(incomplete_mission, policy(), ["src/reporting/render.py"])})
        self.assertIn("SCOPE_POLICY_INVALID", {item.code for item in validate_scope(self.mission, incomplete_policy, ["src/reporting/render.py"])})

    def test_path_wrapper_and_reusable_guard_use_base_policy_read_only(self):
        wrapper = ROOT / "scripts" / "engineering-os" / "validate-paths"
        workflow = ROOT / ".github" / "workflows" / "reusable-tier-path-guard.yml"
        self.assertTrue(os.access(wrapper, os.X_OK))
        text = workflow.read_text(encoding="utf-8")
        self.assertIn("contents: read", text)
        self.assertNotIn("contents: write", text)
        self.assertIn("github.event.pull_request.base.sha", text)
        self.assertIn("kernel/scripts/engineering-os/resolve-base-policy", text)
        self.assertIn('--output "$RUNNER_TEMP/base-policy.json"', text)
        self.assertIn("fetch-depth: 0", text)
        self.assertIn('git -C target cat-file -e "$BASE_SHA^{commit}"', text)
        self.assertIn('git -C target diff --name-only -z "$BASE_SHA" "$HEAD_SHA"', text)
        self.assertNotIn("pulls/${{ github.event.pull_request.number }}/files", text)
        self.assertNotIn("coordination_records_json", text)
        self.assertNotIn("active_missions_json", text)
        self.assertNotIn("mission_json", text)
        self.assertIn("discover_repository_mission_candidates", text)
        self.assertIn("authenticate_event_history", text)
        self.assertIn("issues?state=all", text)
        self.assertIn('"state": checked.projection.state', text)
        self.assertIn("validate-tier", text)
        self.assertIn("validate-paths", text)
        self.assertNotIn("--coordination-records", wrapper.read_text(encoding="utf-8"))

    def test_documented_model_keeps_ownership_separate_from_lifecycle(self):
        authority = (ROOT / "docs/engineering-os/AUTHORITY_MODEL.md").read_text(encoding="utf-8")
        self.assertIn("do not alter mission lifecycle authority", authority)
        self.assertIn("exact mission", authority)
        self.assertIn("authenticated GitHub source", authority)
        self.assertIn("caller-supplied coordination", authority)
        self.assertIn("blocked", authority)
        self.assertIn("Proposed and Ready", authority)


if __name__ == "__main__":
    unittest.main()
