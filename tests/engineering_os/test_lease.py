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
        )
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.event["type"], "mission.claimed")
        self.assertEqual(decision.event["details"]["lease_owner"], "agent-a")
        self.assertEqual(decision.event["details"]["lease_nonce"], "nonce-200")
        self.assertFalse(claim_mission(
            [], mission_id="aifo-200", owner="reviewer", actor_role="adversary",
            now=NOW, expires_at=EXPIRY, nonce="nonce-review", paths=["src/**"],
        ).allowed)

    def test_duplicate_and_concurrent_claims_are_rejected(self):
        events = load_fixture("events/concurrent-claim.json")[:1]
        duplicate = claim_mission(
            events, mission_id="aifo-103", owner="agent-a", actor_role="producer",
            now=NOW, expires_at=EXPIRY, nonce="nonce-first", paths=["engineering_os/**"],
        )
        concurrent = claim_mission(
            events, mission_id="aifo-103", owner="agent-b", actor_role="producer",
            now=NOW, expires_at=EXPIRY, nonce="nonce-new", paths=["engineering_os/**"],
        )
        self.assertEqual(duplicate.code, "LEASE_NONCE_REUSED")
        self.assertEqual(concurrent.code, "LEASE_ALREADY_CLAIMED")

    def test_expiry_is_explicit_and_does_not_implicitly_release_or_change_state(self):
        events = load_fixture("events/expired-lease.json")
        claim = claim_mission(
            events, mission_id="aifo-102", owner="agent-b", actor_role="producer",
            now=NOW, expires_at=EXPIRY, nonce="nonce-new", paths=["engineering_os/**"],
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
        reclaimed = claim_mission(
            events + [released.event], mission_id="aifo-101", owner="agent-b",
            actor_role="producer", now=NOW, expires_at=EXPIRY,
            nonce="nonce-reclaim", paths=["engineering_os/**"],
        )
        self.assertTrue(reclaimed.allowed)

    def test_path_conflict_persists_after_expiry_until_explicit_recovery(self):
        events = load_fixture("events/expired-lease.json")
        blocked = claim_mission(
            events, mission_id="aifo-999", owner="agent-b", actor_role="producer",
            now=NOW, expires_at=EXPIRY, nonce="nonce-999", paths=["engineering_os/lease.py"],
        )
        self.assertEqual(blocked.code, "LEASE_PATH_CONFLICT")
        recovered = release_mission(
            events, mission_id="aifo-102", owner="system", now=NOW,
            nonce="nonce-102", recovery=True,
        )
        self.assertTrue(recovered.allowed)
        admitted = claim_mission(
            events + [recovered.event], mission_id="aifo-999", owner="agent-b",
            actor_role="producer", now=NOW, expires_at=EXPIRY,
            nonce="nonce-999", paths=["engineering_os/lease.py"],
        )
        self.assertTrue(admitted.allowed)


if __name__ == "__main__":
    unittest.main()
