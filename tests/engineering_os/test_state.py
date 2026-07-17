import unittest

from engineering_os.state import MissionProjection, authorize_transition, project_state


POLICY = {"transition_roles": {}}


def event(event_type, role):
    return {"type": event_type, "actor_role": role}


class MissionStateTests(unittest.TestCase):
    def test_complete_allowed_lifecycle_projects_to_closed(self):
        events = [
            event("mission.ready", "producer"),
            event("mission.claimed", "producer"),
            event("mission.started", "producer"),
            event("review.requested", "producer"),
            event("review.passed", "adversary"),
            event("approval.granted", "founder"),
            event("mission.merged", "founder"),
            event("verification.passed", "adversary"),
            event("mission.closed", "founder"),
        ]
        projection = project_state(events)
        self.assertEqual(projection.state, "Closed")
        self.assertEqual(projection.violations, ())

    def test_each_event_is_denied_from_every_invalid_state(self):
        valid_sources = {
            "mission.ready": {"Proposed"},
            "mission.claimed": {"Ready"},
            "mission.started": {"Claimed"},
            "review.requested": {"In Progress"},
            "finding.valid": {"Adversarial Review"},
            "review.passed": {"Adversarial Review"},
            "approval.granted": {"Founder Approval"},
            "mission.merged": {"Merge Authorized"},
            "verification.passed": {"Merged"},
            "mission.closed": {"Verified"},
            "mission.parked": {"Proposed", "Ready", "Claimed", "In Progress", "Adversarial Review", "Founder Approval"},
            "mission.cancelled": {"Proposed", "Ready", "Claimed", "In Progress", "Adversarial Review", "Founder Approval"},
            "mission.recovered": {"Parked"},
            "incident.opened": {"Merged", "Verified", "Closed"},
            "incident.verified": {"Incident"},
            "incident.closed": {"Incident"},
        }
        roles = {
            "review.passed": "adversary",
            "finding.valid": "adversary",
            "verification.passed": "adversary",
            "approval.granted": "founder",
            "mission.merged": "founder",
            "mission.closed": "founder",
            "mission.cancelled": "founder",
            "mission.recovered": "founder",
            "incident.verified": "adversary",
            "incident.closed": "founder",
        }
        states = {
            "Proposed", "Ready", "Claimed", "In Progress", "Adversarial Review",
            "Founder Approval", "Merge Authorized", "Merged", "Verified", "Closed",
            "Parked", "Incident", "Cancelled",
        }
        for event_type, sources in valid_sources.items():
            for state in states - sources:
                with self.subTest(event=event_type, state=state):
                    decision = authorize_transition(
                        MissionProjection(state=state), event(event_type, roles.get(event_type, "producer")), POLICY
                    )
                    self.assertFalse(decision.allowed)
                    self.assertEqual(decision.code, "STATE_TRANSITION_DENIED")

    def test_role_authority_is_enforced(self):
        projection = MissionProjection(state="Adversarial Review")
        denied = authorize_transition(projection, event("review.passed", "producer"), POLICY)
        self.assertFalse(denied.allowed)
        self.assertEqual(denied.code, "STATE_ROLE_DENIED")

    def test_policy_cannot_grant_producer_founder_only_authority(self):
        cases = (
            ("Founder Approval", "approval.granted"),
            ("Merge Authorized", "mission.merged"),
        )
        for state, event_type in cases:
            with self.subTest(event=event_type):
                policy = {"transition_roles": {event_type: ["producer"]}}
                decision = authorize_transition(MissionProjection(state=state), event(event_type, "producer"), policy)
                self.assertFalse(decision.allowed)
                self.assertEqual(decision.code, "STATE_POLICY_INVALID")

    def test_malformed_policy_role_values_fail_closed(self):
        malformed_values = (None, "founder", {"founder": True}, ["founder", 7], ["unknown-role"])
        for value in malformed_values:
            with self.subTest(value=value):
                policy = {"transition_roles": {"approval.granted": value}}
                decision = authorize_transition(
                    MissionProjection(state="Founder Approval"),
                    event("approval.granted", "founder"),
                    policy,
                )
                self.assertFalse(decision.allowed)
                self.assertEqual(decision.code, "STATE_POLICY_INVALID")

    def test_policy_can_only_tighten_default_roles(self):
        policy = {"transition_roles": {"mission.parked": ["adversary"]}}
        producer = authorize_transition(MissionProjection(), event("mission.parked", "producer"), policy)
        adversary = authorize_transition(MissionProjection(), event("mission.parked", "adversary"), policy)
        self.assertFalse(producer.allowed)
        self.assertEqual(producer.code, "STATE_ROLE_DENIED")
        self.assertTrue(adversary.allowed)

    def test_valid_finding_returns_to_in_progress_and_counts_remediation(self):
        projection = MissionProjection(state="Adversarial Review", remediation_cycles=0)
        decision = authorize_transition(projection, event("finding.valid", "adversary"), POLICY)
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.details["to_state"], "In Progress")
        projected = project_state([
            event("mission.ready", "producer"), event("mission.claimed", "producer"),
            event("mission.started", "producer"), event("review.requested", "producer"),
            event("finding.valid", "adversary"),
        ])
        self.assertEqual(projected.remediation_cycles, 1)

    def test_parked_recovery_incident_and_cancelled_paths(self):
        parked = project_state([event("mission.parked", "producer")])
        self.assertEqual(parked.state, "Parked")
        ordinary_ready = authorize_transition(parked, event("mission.ready", "producer"), POLICY)
        self.assertFalse(ordinary_ready.allowed)
        self.assertEqual(ordinary_ready.code, "STATE_TRANSITION_DENIED")
        recovered = authorize_transition(parked, event("mission.recovered", "founder"), POLICY)
        self.assertTrue(recovered.allowed)
        self.assertEqual(recovered.details["to_state"], "Ready")

        cancelled = project_state([event("mission.cancelled", "founder")])
        self.assertEqual(cancelled.state, "Cancelled")

        incident = authorize_transition(MissionProjection(state="Closed"), event("incident.opened", "producer"), POLICY)
        self.assertTrue(incident.allowed)
        self.assertEqual(incident.details["to_state"], "Incident")

    def test_unknown_event_is_denied_by_default(self):
        decision = authorize_transition(MissionProjection(), event("mission.teleport", "founder"), POLICY)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.code, "STATE_EVENT_UNKNOWN")

    def test_lifecycle_control_events_are_authorized_and_state_explicit(self):
        heartbeat = authorize_transition(
            MissionProjection(state="Claimed"), event("lease.heartbeat", "producer"), POLICY
        )
        released = authorize_transition(
            MissionProjection(state="In Progress"), event("mission.released", "producer"), POLICY
        )
        orphaned = authorize_transition(
            MissionProjection(state="In Progress"), event("mission.orphaned", "system"), POLICY
        )
        recovered = authorize_transition(
            MissionProjection(state="Parked"), event("mission.released", "system"), POLICY
        )
        self.assertTrue(all(item.allowed for item in (heartbeat, released, orphaned, recovered)))
        self.assertEqual(heartbeat.details["to_state"], "Claimed")
        self.assertEqual(released.details["to_state"], "Ready")
        self.assertEqual(orphaned.details["to_state"], "Parked")
        self.assertEqual(recovered.details["to_state"], "Ready")

    def test_system_cannot_release_without_orphaned_parked_state(self):
        denied = authorize_transition(
            MissionProjection(state="In Progress"), event("mission.released", "system"), POLICY
        )
        self.assertFalse(denied.allowed)
        self.assertEqual(denied.code, "STATE_ROLE_DENIED")

    def test_invalid_projection_event_preserves_state_and_records_violation(self):
        projection = project_state([event("mission.merged", "founder")])
        self.assertEqual(projection.state, "Proposed")
        self.assertEqual(projection.violations[0].code, "STATE_TRANSITION_DENIED")

    def test_projector_fails_closed_on_malformed_falsy_policy(self):
        for policy in ([], "", 0):
            with self.subTest(policy=policy):
                projection = project_state([event("mission.ready", "producer")], policy=policy)
                self.assertEqual(projection.state, "Proposed")
                self.assertEqual(projection.violations[0].code, "STATE_POLICY_INVALID")


if __name__ == "__main__":
    unittest.main()
