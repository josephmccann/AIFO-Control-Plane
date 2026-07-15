import copy
import json
import math
import unittest

from engineering_os.canonical import content_sha256
from engineering_os.mission import MissionParseError, parse_issue_body, validate_ready

from .helpers import ROOT, load_fixture


class MissionTests(unittest.TestCase):
    def setUp(self):
        self.mission = load_fixture("mission-valid.json")

    def test_parses_exactly_one_complete_machine_readable_declaration(self):
        body = "Context\n<!-- EOS:MISSION:BEGIN -->\n{}\n<!-- EOS:MISSION:END -->\nNotes".format(
            json.dumps(self.mission, indent=2)
        )
        self.assertEqual(parse_issue_body(body), self.mission)

    def test_missing_or_duplicate_markers_are_rejected(self):
        with self.assertRaises(MissionParseError):
            parse_issue_body(json.dumps(self.mission))
        block = "<!-- EOS:MISSION:BEGIN -->\n{}\n<!-- EOS:MISSION:END -->".format(json.dumps(self.mission))
        with self.assertRaises(MissionParseError):
            parse_issue_body(block + "\n" + block)

    def test_invalid_json_is_rejected(self):
        with self.assertRaises(MissionParseError):
            parse_issue_body("<!-- EOS:MISSION:BEGIN -->\n{broken\n<!-- EOS:MISSION:END -->")

    def test_non_finite_json_numbers_are_rejected(self):
        for token in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(token=token):
                body = "<!-- EOS:MISSION:BEGIN -->\n{\"value\": %s}\n<!-- EOS:MISSION:END -->" % token
                with self.assertRaises(MissionParseError):
                    parse_issue_body(body)

    def test_reversed_markers_raise_mission_parse_error(self):
        body = "<!-- EOS:MISSION:END -->\n{}\n<!-- EOS:MISSION:BEGIN -->".format(json.dumps(self.mission))
        with self.assertRaises(MissionParseError):
            parse_issue_body(body)

    def test_complete_mission_is_ready(self):
        self.assertEqual(validate_ready(self.mission), [])

    def test_every_required_field_produces_stable_code(self):
        for field in self.mission:
            with self.subTest(field=field):
                candidate = copy.deepcopy(self.mission)
                del candidate[field]
                self.assertIn("MISSION_FIELD_REQUIRED", {v.code for v in validate_ready(candidate)})

    def test_eos_version_and_exact_constitution_hash_are_pinned(self):
        wrong_version = copy.deepcopy(self.mission)
        wrong_version["eos"]["version"] = "0.9.0"
        self.assertIn("MISSION_EOS_VERSION_MISMATCH", {v.code for v in validate_ready(wrong_version)})

        expected = content_sha256((ROOT / "docs/engineering-os/ENGINEERING_CONSTITUTION.md").read_bytes())
        self.assertEqual(self.mission["eos"]["constitution_sha256"], expected)
        wrong_hash = copy.deepcopy(self.mission)
        wrong_hash["eos"]["constitution_sha256"] = "0" * 64
        self.assertIn("MISSION_EOS_HASH_MISMATCH", {v.code for v in validate_ready(wrong_hash)})

    def test_definition_of_ready_rejects_incomplete_or_unsafe_values(self):
        mission = load_fixture("mission-not-ready.json")
        violations = validate_ready(mission)
        self.assertIn("MISSION_NOT_READY", {v.code for v in violations})
        details = [v.details for v in violations if v.code == "MISSION_NOT_READY"]
        self.assertTrue(any(item.get("field") == "acceptance_criteria" for item in details))
        self.assertTrue(any(item.get("field") == "assignments" for item in details))

    def test_definition_of_ready_rejects_non_finite_budgets(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                mission = copy.deepcopy(self.mission)
                mission["budgets"]["model_cost_usd"] = value
                codes = {item.code for item in validate_ready(mission)}
                self.assertIn("MISSION_NOT_READY", codes)


if __name__ == "__main__":
    unittest.main()
