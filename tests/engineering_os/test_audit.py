import unittest

from engineering_os.audit import normalize_audit_event, validate_audit_chain
from engineering_os.canonical import content_sha256


class AuditTests(unittest.TestCase):
    def source(self, **overrides):
        value = {
            "actor": "agent-reviewer",
            "actor_role": "adversary",
            "occurred_at": "2026-07-15T12:00:00Z",
            "source_url": "https://github.com/acme/widgets/issues/7#issuecomment-10",
        }
        value.update(overrides)
        return value

    def test_authenticated_source_overrides_producer_actor_and_time(self):
        event = normalize_audit_event(
            {
                "schema_version": "1.0.0",
                "mission_id": "mission-7",
                "type": "review.passed",
                "actor": "producer-forgery",
                "actor_role": "founder",
                "occurred_at": "2099-01-01T00:00:00Z",
                "source_url": "https://example.invalid",
                "details": {"finding_count": 0},
            },
            self.source(),
            sequence=1,
            previous_event_hash=None,
        )
        self.assertEqual(event["actor"], "agent-reviewer")
        self.assertEqual(event["actor_role"], "adversary")
        self.assertEqual(event["occurred_at"], "2026-07-15T12:00:00Z")
        self.assertEqual(event["source_url"], self.source()["source_url"])
        self.assertEqual(event["event_hash"], content_sha256(event))

    def test_order_mission_previous_hash_and_event_hash_are_exact(self):
        first = normalize_audit_event(
            {
                "schema_version": "1.0.0", "mission_id": "mission-7",
                "type": "mission.ready", "details": {},
            },
            self.source(actor_role="producer"),
            sequence=1,
            previous_event_hash=None,
        )
        second = normalize_audit_event(
            {
                "schema_version": "1.0.0", "mission_id": "mission-7",
                "type": "review.passed", "details": {},
            },
            self.source(),
            sequence=2,
            previous_event_hash=first["event_hash"],
        )
        decision = validate_audit_chain([first, second])
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.head_hash, second["event_hash"])

        for field, value, code in (
            ("sequence", 3, "AUDIT_SEQUENCE_INVALID"),
            ("mission_id", "other", "AUDIT_MISSION_MISMATCH"),
            ("previous_event_hash", "0" * 64, "AUDIT_PREVIOUS_HASH_INVALID"),
            ("event_hash", "0" * 64, "AUDIT_EVENT_HASH_INVALID"),
        ):
            broken = [dict(first), dict(second)]
            broken[1][field] = value
            self.assertEqual(validate_audit_chain(broken).code, code)

    def test_malformed_unknown_or_non_utc_input_fails_closed(self):
        with self.assertRaises(ValueError):
            normalize_audit_event(
                {
                    "schema_version": "1.0.0", "mission_id": "mission-7",
                    "type": "review.passed", "details": {}, "unknown": True,
                },
                self.source(),
                sequence=1,
                previous_event_hash=None,
            )
        with self.assertRaises(ValueError):
            normalize_audit_event(
                {
                    "schema_version": "1.0.0", "mission_id": "mission-7",
                    "type": "review.passed", "details": {},
                },
                self.source(occurred_at="2026-07-15T12:00:00-07:00"),
                sequence=1,
                previous_event_hash=None,
            )


if __name__ == "__main__":
    unittest.main()
