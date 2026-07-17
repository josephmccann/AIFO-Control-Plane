import copy
import math
import unittest

from engineering_os.canonical import canonical_json, content_sha256
from engineering_os.schema import DOCUMENT_KINDS, validate_document

from tests.engineering_os.helpers import load_fixture


class CanonicalTests(unittest.TestCase):
    def test_canonical_json_is_sorted_and_compact(self):
        self.assertEqual(canonical_json({"z": 1, "a": [3, 2]}), '{"a":[3,2],"z":1}')

    def test_audit_hash_ignores_its_event_hash(self):
        event = {"sequence": 1, "type": "mission.ready", "event_hash": "stale"}
        self.assertEqual(content_sha256(event), content_sha256({"sequence": 1, "type": "mission.ready"}))

    def test_canonical_json_rejects_non_finite_numbers(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    canonical_json({"value": value})


class SchemaTests(unittest.TestCase):
    def test_all_contract_schema_kinds_are_available(self):
        self.assertEqual(
            set(DOCUMENT_KINDS),
            {
                "mission",
                "evidence",
                "approval",
                "audit-event",
                "repository-policy",
                "frozen-path",
                "incident",
                "mission-state",
                "finding",
                "authority",
                "metrics",
                "airtable-record",
            },
        )

    def test_each_contract_schema_is_present_and_loadable(self):
        for kind in DOCUMENT_KINDS:
            with self.subTest(kind=kind):
                codes = {item.code for item in validate_document(kind, {})}
                self.assertNotIn("SCHEMA_NOT_FOUND", codes)
                self.assertNotIn("SCHEMA_INVALID", codes)

    def test_valid_mission_and_policy_conform(self):
        self.assertEqual(validate_document("mission", load_fixture("mission-valid.json")), [])
        policy = load_fixture("policy-control-plane.json")
        self.assertEqual(validate_document("repository-policy", policy), [])
        self.assertIs(policy["orphan_recovery_enabled"], False)

    def test_every_required_mission_field_is_enforced(self):
        mission = load_fixture("mission-valid.json")
        for field in mission:
            with self.subTest(field=field):
                candidate = copy.deepcopy(mission)
                del candidate[field]
                violations = validate_document("mission", candidate)
                self.assertIn("MISSION_FIELD_REQUIRED", {item.code for item in violations})

    def test_closed_records_reject_unknown_properties(self):
        mission = load_fixture("mission-valid.json")
        mission["unreviewed_escape_hatch"] = True
        violations = validate_document("mission", mission)
        self.assertIn("SCHEMA_ADDITIONAL_PROPERTY", {item.code for item in violations})

    def test_explicit_enums_reject_unknown_tier_and_rollback(self):
        mission = load_fixture("mission-valid.json")
        mission["risk_tier"] = "Tier 9"
        mission["rollback"]["class"] = "magic"
        codes = {item.code for item in validate_document("mission", mission)}
        self.assertIn("SCHEMA_ENUM", codes)

    def test_schema_number_validation_rejects_non_finite_values(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                mission = load_fixture("mission-valid.json")
                mission["budgets"]["model_cost_usd"] = value
                codes = {item.code for item in validate_document("mission", mission)}
                self.assertIn("SCHEMA_NUMBER_NOT_FINITE", codes)

    def test_policy_schema_rejects_role_loosening_and_unknown_transitions(self):
        policy = load_fixture("policy-control-plane.json")
        policy["transition_roles"] = {
            "approval.granted": ["producer"],
            "mission.teleport": ["founder"],
        }
        codes = {item.code for item in validate_document("repository-policy", policy)}
        self.assertIn("SCHEMA_ENUM", codes)
        self.assertIn("SCHEMA_ADDITIONAL_PROPERTY", codes)

    def test_policy_schema_accepts_closed_recovery_workflow_path_allowlist(self):
        policy = load_fixture("policy-control-plane.json")
        policy["recovery_workflow_paths"] = [
            ".github/workflows/reusable-orphan-recovery.yml",
            ".github/workflows/mission-recovery-dispatch.yml",
        ]
        self.assertEqual(validate_document("repository-policy", policy), [])

    def test_unknown_document_kind_fails_closed(self):
        violations = validate_document("not-a-contract", {})
        self.assertEqual([item.code for item in violations], ["SCHEMA_KIND_UNKNOWN"])

    def test_activation_schema_conditionals_are_enforced(self):
        event = {
            "schema_version": "1.0.0", "mission_id": "mission-26", "sequence": 1,
            "type": "test_integrity.baseline.authorized", "actor": "founder",
            "actor_role": "system", "occurred_at": "2026-07-17T20:00:00Z",
            "source_url": "https://github.com/example", "previous_event_hash": None,
            "event_hash": "a" * 64, "details": {},
        }
        codes = {item.code for item in validate_document("audit-event", event)}
        self.assertIn("SCHEMA_CONST", codes)
        self.assertIn("SCHEMA_FIELD_REQUIRED", codes)


if __name__ == "__main__":
    unittest.main()
