import unittest

from engineering_os.lease import (
    claim_mission,
    find_orphans,
    heartbeat_lease,
    release_mission,
)
from tests.engineering_os.helpers import load_fixture


NOW = "2026-07-15T10:05:00Z"
EXPIRY = "2026-07-15T10:20:00Z"


class LeaseTests(unittest.TestCase):
    def test_first_claim_is_atomic_and_only_a_producer_can_hold_it(self):
        decision = claim_mission(
            [], mission_id="aifo-200", owner="agent-a", actor_role="producer",
            now=NOW, expires_at=EXPIRY, nonce="nonce-200", paths=["src/**"],
            wall_clock_minutes=240,
        )
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.event["type"], "mission.claimed")
        self.assertEqual(decision.event["details"]["lease_owner"], "agent-a")
        self.assertEqual(decision.event["details"]["lease_nonce"], "nonce-200")
        self.assertFalse(claim_mission(
            [], mission_id="aifo-200", owner="reviewer", actor_role="adversary",
            now=NOW, expires_at=EXPIRY, nonce="nonce-review", paths=["src/**"],
            wall_clock_minutes=240,
        ).allowed)

    def test_duplicate_and_concurrent_claims_are_rejected(self):
        events = load_fixture("events/concurrent-claim.json")[:1]
        duplicate = claim_mission(
            events, mission_id="aifo-103", owner="agent-a", actor_role="producer",
            now=NOW, expires_at=EXPIRY, nonce="nonce-first", paths=["engineering_os/**"],
            wall_clock_minutes=240,
        )
        concurrent = claim_mission(
            events, mission_id="aifo-103", owner="agent-b", actor_role="producer",
            now=NOW, expires_at=EXPIRY, nonce="nonce-new", paths=["engineering_os/**"],
            wall_clock_minutes=240,
        )
        self.assertEqual(duplicate.code, "LEASE_NONCE_REUSED")
        self.assertEqual(concurrent.code, "LEASE_ALREADY_CLAIMED")

    def test_expiry_is_explicit_and_does_not_implicitly_release_or_change_state(self):
        events = load_fixture("events/expired-lease.json")
        claim = claim_mission(
            events, mission_id="aifo-102", owner="agent-b", actor_role="producer",
            now=NOW, expires_at=EXPIRY, nonce="nonce-new", paths=["engineering_os/**"],
            wall_clock_minutes=240,
        )
        self.assertFalse(claim.allowed)
        self.assertEqual(claim.code, "LEASE_RECOVERY_REQUIRED")
        self.assertTrue(claim.preserve_state)

    def test_heartbeat_requires_exact_live_owner_and_nonce(self):
        events = load_fixture("events/valid-lifecycle.json")[:1]
        valid = heartbeat_lease(
            events, mission_id="aifo-101", owner="agent-a", now=NOW,
            expires_at=EXPIRY, nonce="nonce-101",
        )
        wrong_owner = heartbeat_lease(
            events, mission_id="aifo-101", owner="agent-b", now=NOW,
            expires_at=EXPIRY, nonce="nonce-101",
        )
        wrong_nonce = heartbeat_lease(
            events, mission_id="aifo-101", owner="agent-a", now=NOW,
            expires_at=EXPIRY, nonce="wrong",
        )
        self.assertTrue(valid.allowed)
        self.assertEqual(valid.event["type"], "lease.heartbeat")
        self.assertEqual(wrong_owner.code, "LEASE_OWNER_MISMATCH")
        self.assertEqual(wrong_nonce.code, "LEASE_NONCE_MISMATCH")

    def test_heartbeat_after_timeout_is_denied_and_orphan_is_found(self):
        events = load_fixture("events/heartbeat-timeout.json")
        denied = heartbeat_lease(
            events, mission_id="aifo-104", owner="agent-a", now=NOW,
            expires_at=EXPIRY, nonce="nonce-104",
        )
        self.assertEqual(denied.code, "LEASE_EXPIRED")
        orphans = find_orphans(events, now=NOW)
        self.assertEqual([orphan.mission_id for orphan in orphans], ["aifo-104"])
        self.assertEqual(orphans[0].recommended_action, "Parked")
        self.assertTrue(orphans[0].preserve_state)

    def test_lease_is_expired_at_its_explicit_expiry_instant(self):
        events = load_fixture("events/expired-lease.json")
        at_expiry = "2026-07-15T09:15:00Z"
        denied = heartbeat_lease(
            events, mission_id="aifo-102", owner="agent-a", now=at_expiry,
            expires_at="2026-07-15T09:30:00Z", nonce="nonce-102",
        )
        self.assertEqual(denied.code, "LEASE_EXPIRED")
        self.assertEqual(len(find_orphans(events, now=at_expiry)), 1)

    def test_release_is_owner_safe_and_enables_reclaim(self):
        events = load_fixture("events/valid-lifecycle.json")
        denied = release_mission(
            events, mission_id="aifo-101", owner="agent-b", now=NOW, nonce="nonce-101",
        )
        released = release_mission(
            events, mission_id="aifo-101", owner="agent-a", now=NOW, nonce="nonce-101",
        )
        self.assertEqual(denied.code, "LEASE_OWNER_MISMATCH")
        self.assertTrue(released.allowed)
        self.assertEqual(released.event["type"], "mission.released")
        reclaimed = claim_mission(
            events + [released.event], mission_id="aifo-101", owner="agent-b",
            actor_role="producer", now=NOW, expires_at=EXPIRY,
            nonce="nonce-reclaim", paths=["engineering_os/**"], wall_clock_minutes=240,
        )
        self.assertTrue(reclaimed.allowed)

    def test_path_conflict_persists_after_expiry_until_explicit_recovery(self):
        events = load_fixture("events/expired-lease.json")
        blocked = claim_mission(
            events, mission_id="aifo-999", owner="agent-b", actor_role="producer",
            now=NOW, expires_at=EXPIRY, nonce="nonce-999", paths=["engineering_os/lease.py"],
            wall_clock_minutes=240,
        )
        self.assertEqual(blocked.code, "LEASE_PATH_CONFLICT")
        recovered = release_mission(
            events, mission_id="aifo-102", owner="system", now=NOW,
            nonce="nonce-102", recovery=True,
        )
        self.assertTrue(recovered.allowed)
        self.assertEqual(
            [event["type"] for event in recovered.events],
            ["mission.orphaned", "mission.released"],
        )
        admitted = claim_mission(
            events + [recovered.event], mission_id="aifo-999", owner="agent-b",
            actor_role="producer", now=NOW, expires_at=EXPIRY,
            nonce="nonce-999", paths=["engineering_os/lease.py"], wall_clock_minutes=240,
        )
        self.assertTrue(admitted.allowed)

    def test_claim_records_start_and_heartbeat_cannot_exceed_wall_clock_cap(self):
        claim = claim_mission(
            [], mission_id="aifo-cap", owner="agent-a", actor_role="producer",
            now="2026-07-15T10:00:00.125Z", expires_at="2026-07-15T10:10:00.125Z",
            nonce="cap-nonce", paths=["src/**"], wall_clock_minutes=30,
        )
        self.assertTrue(claim.allowed)
        self.assertEqual(claim.event["details"]["lease_start"], "2026-07-15T10:00:00.125Z")
        self.assertEqual(claim.event["details"]["wall_clock_cap_minutes"], 30)
        heartbeat = heartbeat_lease(
            [claim.event], mission_id="aifo-cap", owner="agent-a",
            now="2026-07-15T10:05:00.125Z", expires_at="2026-07-15T10:30:00.126Z",
            nonce="cap-nonce",
        )
        self.assertEqual(heartbeat.code, "LEASE_WALL_CLOCK_CAP_EXCEEDED")

    def test_recovery_rechecks_current_history_after_heartbeat(self):
        refreshed = load_fixture("events/heartbeat-timeout.json")
        raced = release_mission(
            refreshed, mission_id="aifo-104", owner="system",
            now="2026-07-15T09:20:00Z", nonce="nonce-104", recovery=True,
        )
        self.assertEqual(raced.code, "LEASE_NOT_EXPIRED")

    def test_root_wildcard_patterns_conflict_conservatively(self):
        first = claim_mission(
            [], mission_id="aifo-pattern-a", owner="agent-a", actor_role="producer",
            now=NOW, expires_at=EXPIRY, nonce="pattern-a", paths=["*.py"],
            wall_clock_minutes=240,
        )
        second = claim_mission(
            [first.event], mission_id="aifo-pattern-b", owner="agent-b", actor_role="producer",
            now=NOW, expires_at=EXPIRY, nonce="pattern-b", paths=["test*"],
            wall_clock_minutes=240,
        )
        self.assertEqual(second.code, "LEASE_PATH_CONFLICT")

    def test_nonce_is_normalized_before_reuse_comparison(self):
        first = claim_mission(
            [], mission_id="aifo-nonce-a", owner="agent-a", actor_role="producer",
            now=NOW, expires_at=EXPIRY, nonce="  shared-nonce  ", paths=["src/**"],
            wall_clock_minutes=240,
        )
        released = release_mission(
            [first.event], mission_id="aifo-nonce-a", owner="agent-a",
            now=NOW, nonce="shared-nonce",
        )
        reused = claim_mission(
            [first.event, released.event], mission_id="aifo-nonce-b", owner="agent-b",
            actor_role="producer", now=NOW, expires_at=EXPIRY,
            nonce="shared-nonce", paths=["docs/**"], wall_clock_minutes=240,
        )
        self.assertEqual(reused.code, "LEASE_NONCE_REUSED")

    def test_heartbeat_normalizes_nonce_in_proposed_event(self):
        events = load_fixture("events/valid-lifecycle.json")[:1]
        heartbeat = heartbeat_lease(
            events, mission_id="aifo-101", owner="agent-a", now=NOW,
            expires_at=EXPIRY, nonce="  nonce-101  ",
        )
        self.assertTrue(heartbeat.allowed)
        self.assertEqual(heartbeat.event["details"]["lease_nonce"], "nonce-101")

    def test_timestamps_require_z_and_preserve_fractional_seconds(self):
        strict = claim_mission(
            [], mission_id="aifo-time", owner="agent-a", actor_role="producer",
            now="2026-07-15T10:05:00.123456Z", expires_at="2026-07-15T10:20:00.654321Z",
            nonce="time-nonce", paths=["src/**"], wall_clock_minutes=240,
        )
        self.assertTrue(strict.allowed)
        self.assertEqual(strict.event["occurred_at"], "2026-07-15T10:05:00.123456Z")
        non_zulu = claim_mission(
            [], mission_id="aifo-time", owner="agent-a", actor_role="producer",
            now="2026-07-15T10:05:00+00:00", expires_at=EXPIRY,
            nonce="time-nonce", paths=["src/**"], wall_clock_minutes=240,
        )
        self.assertEqual(non_zulu.code, "LEASE_TIMESTAMP_INVALID")


if __name__ == "__main__":
    unittest.main()
