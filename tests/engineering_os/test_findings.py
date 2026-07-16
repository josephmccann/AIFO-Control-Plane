import unittest

from engineering_os.findings import normalize_findings


class FindingTests(unittest.TestCase):
    def finding(self, **overrides):
        value = {
            "schema_version": "1.0.0",
            "finding_id": "finding-1",
            "mission_id": "mission-7",
            "reviewer": "agent-reviewer",
            "summary": "The approval can be replayed.",
            "evidence": ["tests/test_approval.py::test_replay"],
            "severity": "critical",
            "disposition": "valid",
        }
        value.update(overrides)
        return value

    def decide(self, findings, **overrides):
        values = {
            "mission_id": "mission-7",
            "producer_identity": "agent-producer",
            "producer_model_family": "gpt",
            "adversary_identity": "agent-reviewer",
            "adversary_model_family": "claude",
            "require_distinct_model_family": True,
        }
        values.update(overrides)
        return normalize_findings(findings, **values)

    def test_all_dispositions_are_normalized_without_a_rejection_quota(self):
        findings = [
            self.finding(finding_id="valid", disposition="valid"),
            self.finding(finding_id="invalid", disposition="invalid", severity="low"),
            self.finding(finding_id="duplicate", disposition="duplicate", severity="medium"),
            self.finding(
                finding_id="decision", disposition="founder_decision",
                severity="informational",
            ),
        ]
        decision = self.decide(findings)
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.counts, {
            "valid": 1, "invalid": 1, "duplicate": 1, "founder_decision": 1,
        })

    def test_producer_adversary_reviewer_and_model_family_must_be_separate(self):
        self.assertEqual(
            self.decide(
                [self.finding()],
                adversary_identity="agent-producer",
            ).code,
            "FINDING_IDENTITY_CONFLICT",
        )
        self.assertEqual(
            self.decide(
                [self.finding()],
                adversary_model_family="gpt",
            ).code,
            "FINDING_MODEL_FAMILY_CONFLICT",
        )
        self.assertEqual(
            self.decide([self.finding(reviewer="someone-else")]).code,
            "FINDING_REVIEWER_MISMATCH",
        )

    def test_wrong_mission_duplicates_and_unknown_fields_fail_closed(self):
        self.assertEqual(
            self.decide([self.finding(mission_id="other")]).code,
            "FINDING_MISSION_MISMATCH",
        )
        self.assertEqual(
            self.decide([self.finding(), self.finding()]).code,
            "FINDING_DUPLICATE_ID",
        )
        self.assertEqual(
            self.decide([self.finding(unknown=True)]).code,
            "FINDING_SCHEMA_INVALID",
        )


if __name__ == "__main__":
    unittest.main()
