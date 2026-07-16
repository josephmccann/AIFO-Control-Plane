import unittest

from engineering_os.incident import validate_incident


class IncidentTests(unittest.TestCase):
    def incident(self, **overrides):
        value = {
            "schema_version": "1.0.0", "incident_id": "incident-1",
            "origin_mission_id": "mission-7", "repository": "acme/widgets",
            "pull_request": 42, "severity": "SEV1", "status": "recovering",
            "summary": "Regression after merge.", "kill_switch": "Disable feature flag.",
            "recovery_actions": ["Revert commit."],
            "verification": ["Run deterministic regression suite."],
        }
        value.update(overrides)
        return value

    def test_incident_preserves_origin_kill_switch_recovery_and_verification(self):
        decision = validate_incident(
            self.incident(), origin_mission_id="mission-7",
            repository="acme/widgets", pull_request=42,
            rollback_class="clean_revert", recovery_authorized=True,
        )
        self.assertTrue(decision.allowed)

    def test_each_rollback_class_is_supported_but_authority_is_independent(self):
        for rollback in (
            "clean_revert", "forward_fix", "point_in_time_restore",
            "data_migration_recovery", "irreversible",
        ):
            decision = validate_incident(
                self.incident(), origin_mission_id="mission-7",
                repository="acme/widgets", pull_request=42,
                rollback_class=rollback, recovery_authorized=True,
            )
            self.assertTrue(decision.allowed)
        self.assertEqual(
            validate_incident(
                self.incident(), origin_mission_id="mission-7",
                repository="acme/widgets", pull_request=42,
                rollback_class="clean_revert", recovery_authorized=False,
            ).code,
            "INCIDENT_RECOVERY_AUTHORITY_REQUIRED",
        )

    def test_wrong_linkage_or_missing_recovery_evidence_fails_closed(self):
        self.assertEqual(
            validate_incident(
                self.incident(origin_mission_id="other"),
                origin_mission_id="mission-7", repository="acme/widgets",
                pull_request=42, rollback_class="clean_revert",
                recovery_authorized=True,
            ).code,
            "INCIDENT_ORIGIN_MISMATCH",
        )
        self.assertEqual(
            validate_incident(
                self.incident(verification=[]),
                origin_mission_id="mission-7", repository="acme/widgets",
                pull_request=42, rollback_class="clean_revert",
                recovery_authorized=True,
            ).code,
            "INCIDENT_RECOVERY_INCOMPLETE",
        )


if __name__ == "__main__":
    unittest.main()
