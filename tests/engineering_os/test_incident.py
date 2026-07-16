import unittest
from pathlib import Path
import tempfile

from engineering_os.incident import validate_incident
from tests.engineering_os.fake_github import (
    SealedFakeGitHubTransport,
    transported_record,
)
from tests.engineering_os.test_risk import mission, policy


class IncidentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp.cleanup()

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

    def recovery_context(self, index=1, **overrides):
        recovery_mission = mission("Tier 2")
        recovery_mission.update({
            "mission_id": "mission-7",
            "capabilities": ["read", "write"],
        })
        payload = {
            "schema_version": "1.0.0",
            "record_id": f"recovery-record-{index}",
            "authority_id": f"recovery-authority-{index}",
            "repository": "acme/widgets",
            "paths": ["src/reporting/render.py"],
            "capabilities": ["write"],
            "issuer": "founder",
            "subject": "incident-responder",
            "mission_id": "mission-7",
            "pull_request": 42,
            "head_sha": "2" * 40,
            "starts_at": "2026-07-15T00:00:00Z",
            "expires_at": "2026-07-16T00:00:00Z",
            "status": "active",
            "nonce": f"recovery-nonce-{index}",
            "single_use": True,
        }
        authority, evidence = transported_record(
            "authority", payload, comment_id=9000 + index,
        )
        context = {
            "mission": recovery_mission,
            "policy": policy(),
            "changed_files": ["src/reporting/render.py"],
            "authority_records": [authority],
            "recovery_action": "write",
            "head_sha": "2" * 40,
            "now": "2026-07-15T12:00:00Z",
            "subject": "incident-responder",
            "evidence_verifier": SealedFakeGitHubTransport(evidence),
            "consumption_store": str(
                Path(self.temp.name) / "recovery-authority.sqlite"
            ),
        }
        context.update(overrides)
        return context

    def test_incident_preserves_origin_kill_switch_recovery_and_verification(self):
        decision = validate_incident(
            self.incident(), origin_mission_id="mission-7",
            repository="acme/widgets", pull_request=42,
            rollback_class="clean_revert", **self.recovery_context(),
        )
        self.assertTrue(decision.allowed)

    def test_each_rollback_class_is_supported_but_authority_is_independent(self):
        for index, rollback in enumerate((
            "clean_revert", "forward_fix", "point_in_time_restore",
            "data_migration_recovery", "irreversible",
        ), start=1):
            decision = validate_incident(
                self.incident(), origin_mission_id="mission-7",
                repository="acme/widgets", pull_request=42,
                rollback_class=rollback, **self.recovery_context(index),
            )
            self.assertTrue(decision.allowed)
        self.assertEqual(
            validate_incident(
                self.incident(), origin_mission_id="mission-7",
                repository="acme/widgets", pull_request=42,
                rollback_class="clean_revert",
                **self.recovery_context(authority_records=[]),
            ).code,
            "INCIDENT_RECOVERY_AUTHORITY_REQUIRED",
        )

    def test_bare_boolean_cannot_replace_authenticated_recovery_authority(self):
        context = self.recovery_context()
        context["authority_records"] = True
        self.assertEqual(
            validate_incident(
                self.incident(), origin_mission_id="mission-7",
                repository="acme/widgets", pull_request=42,
                rollback_class="irreversible", **context,
            ).code,
            "INCIDENT_RECOVERY_AUTHORITY_REQUIRED",
        )

    def test_read_only_default_cannot_authorize_any_recovery_class(self):
        for rollback in (
            "clean_revert", "forward_fix", "point_in_time_restore",
            "data_migration_recovery", "irreversible",
        ):
            with self.subTest(rollback=rollback):
                self.assertEqual(
                    validate_incident(
                        self.incident(), origin_mission_id="mission-7",
                        repository="acme/widgets", pull_request=42,
                        rollback_class=rollback,
                        **self.recovery_context(
                            recovery_action="read", authority_records=[],
                        ),
                    ).code,
                    "INCIDENT_RECOVERY_AUTHORITY_REQUIRED",
                )

    def test_wrong_linkage_or_missing_recovery_evidence_fails_closed(self):
        self.assertEqual(
            validate_incident(
                self.incident(origin_mission_id="other"),
                origin_mission_id="mission-7", repository="acme/widgets",
                pull_request=42, rollback_class="clean_revert",
                **self.recovery_context(),
            ).code,
            "INCIDENT_ORIGIN_MISMATCH",
        )
        self.assertEqual(
            validate_incident(
                self.incident(verification=[]),
                origin_mission_id="mission-7", repository="acme/widgets",
                pull_request=42, rollback_class="clean_revert",
                **self.recovery_context(),
            ).code,
            "INCIDENT_RECOVERY_INCOMPLETE",
        )


if __name__ == "__main__":
    unittest.main()
