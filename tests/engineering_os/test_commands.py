import copy
import json
import subprocess
import unittest
from pathlib import Path

from engineering_os.canonical import content_sha256
from engineering_os.commands import (
    authenticate_event_history,
    authorize_command_proposal,
    concurrency_key,
    flatten_paginated,
    parse_command,
    propose_event,
    recovery_mutation_allowed,
)
from tests.engineering_os.helpers import load_fixture


ROOT = Path(__file__).resolve().parents[2]
REPOSITORY = "josephmccann/AIFO-Control-Plane"
BOT = "github-actions[bot]"
RECOVERY_WORKFLOW = ".github/workflows/reusable-orphan-recovery.yml"


def audit_event(event_type, actor, role, source_url, occurred_at, sequence, previous, details=None):
    event = {
        "schema_version": "1.0.0",
        "mission_id": "aifo-control-plane-101",
        "sequence": sequence,
        "type": event_type,
        "actor": actor,
        "actor_role": role,
        "occurred_at": occurred_at,
        "source_url": source_url,
        "previous_event_hash": previous,
        "event_hash": "",
        "details": details or {},
    }
    event["event_hash"] = content_sha256(event)
    return event


def source_comment(comment_id, actor, body, created_at="2026-07-15T10:00:00Z"):
    return {
        "id": comment_id,
        "body": body,
        "created_at": created_at,
        "html_url": "https://github.com/%s/issues/101#issuecomment-%s" % (REPOSITORY, comment_id),
        "user": {"login": actor},
    }


def event_comment(comment_id, events, actor=BOT):
    body = "\n".join(
        "<!-- EOS:EVENT:BEGIN -->\n%s\n<!-- EOS:EVENT:END -->"
        % json.dumps(event, sort_keys=True, separators=(",", ":"))
        for event in events
    )
    return {
        "id": comment_id,
        "body": body,
        "created_at": "2026-07-15T10:00:01Z",
        "html_url": "https://github.com/%s/issues/101#issuecomment-%s" % (REPOSITORY, comment_id),
        "user": {"login": actor},
    }


def valid_context():
    mission = load_fixture("mission-valid.json")
    mission["assignments"]["producer"]["identity"] = "agent-a"
    return mission, load_fixture("policy-control-plane.json")


def ready_details(mission, nonce, **measurements):
    return {"nonce": nonce, "mission_sha256": content_sha256(mission), **measurements}


def recovery_run(run_id=67890, **overrides):
    value = {
        "id": run_id,
        "html_url": "https://github.com/%s/actions/runs/%s" % (REPOSITORY, run_id),
        "name": "Reusable orphan recovery",
        "path": RECOVERY_WORKFLOW,
        "event": "workflow_dispatch",
        "repository": {"full_name": REPOSITORY},
    }
    value.update(overrides)
    return value


def recovery_fixture(recovery_time="2026-07-15T09:15:00Z"):
    mission, policy = valid_context()
    ready_source = source_comment(130, "agent-a", "/eos ready", "2026-07-15T08:59:00Z")
    ready = audit_event(
        "mission.ready", "agent-a", "producer", ready_source["html_url"],
        ready_source["created_at"], 1, None, ready_details(mission, "ready-130"),
    )
    claim_source = source_comment(131, "agent-a", "/eos claim", "2026-07-15T09:00:00Z")
    claim = audit_event(
        "mission.claimed", "agent-a", "producer", claim_source["html_url"],
        claim_source["created_at"], 2, ready["event_hash"],
        {"lease_owner": "agent-a", "lease_nonce": "github-comment-131",
         "lease_start": "2026-07-15T09:00:00Z", "lease_expires_at": "2026-07-15T09:15:00Z",
         "wall_clock_cap_minutes": 240, "paths": mission["allowed_paths"]},
    )
    run = recovery_run()
    shared = {
        "lease_owner": "agent-a", "lease_nonce": "github-comment-131",
        "lease_start": "2026-07-15T09:00:00Z", "lease_expires_at": "2026-07-15T09:15:00Z",
        "recovery": True, "recommended_action": "Parked",
    }
    orphaned = audit_event(
        "mission.orphaned", "system", "system", run["html_url"],
        recovery_time, 3, claim["event_hash"], copy.deepcopy(shared),
    )
    released = audit_event(
        "mission.released", "system", "system", run["html_url"],
        recovery_time, 4, orphaned["event_hash"], copy.deepcopy(shared),
    )
    base_comments = [
        ready_source, event_comment(132, [ready]), claim_source,
        event_comment(133, [claim]),
    ]
    return mission, policy, base_comments, orphaned, released, run


class CommandTests(unittest.TestCase):
    def test_only_exact_supported_eos_commands_parse(self):
        self.assertEqual(parse_command("/eos claim"), ("claim", ()))
        self.assertEqual(parse_command("/eos heartbeat nonce-1"), ("heartbeat", ("nonce-1",)))
        for text in ("please /eos claim", "/eos claim now", "/EOS claim", "/eos", "/eos deploy"):
            with self.subTest(text=text):
                self.assertIsNone(parse_command(text))

    def test_concurrency_key_is_stable_per_repository_issue(self):
        self.assertEqual(
            concurrency_key(REPOSITORY, 123),
            "eos-mission-josephmccann-AIFO-Control-Plane-123",
        )

    def test_event_proposal_preserves_fractional_metadata_nonce_and_hash(self):
        proposal = propose_event(
            mission_id="aifo-101",
            event_type="lease.heartbeat",
            actor="Agent-A",
            actor_role="producer",
            occurred_at="2026-07-15T10:05:00.123Z",
            source_url="https://github.com/example/repo/issues/1#issuecomment-2",
            nonce="nonce-1",
            details={"lease_owner": "Agent-A"},
        )
        self.assertEqual(proposal["occurred_at"], "2026-07-15T10:05:00.123Z")
        self.assertEqual(proposal["details"]["nonce"], "nonce-1")
        self.assertEqual(len(proposal["proposal_hash"]), 64)
        self.assertNotIn("sequence", proposal)
        self.assertNotIn("event_hash", proposal)

    def test_authenticated_history_derives_actor_and_authorizes_transition(self):
        mission, policy = valid_context()
        source = source_comment(1, "agent-a", "/eos ready")
        ready = audit_event(
            "mission.ready", "agent-a", "producer", source["html_url"],
            source["created_at"], 1, None, ready_details(mission, "ready-1"),
        )
        history = authenticate_event_history(
            [source, event_comment(2, [ready])], mission, policy, repository=REPOSITORY
        )
        self.assertTrue(history.allowed)
        self.assertEqual(history.projection.state, "Ready")

    def test_claim_proposal_revalidates_ready_state_and_records_lease_start(self):
        mission, policy = valid_context()
        ready_source = source_comment(20, "agent-a", "/eos ready")
        ready = audit_event(
            "mission.ready", "agent-a", "producer", ready_source["html_url"],
            ready_source["created_at"], 1, None, ready_details(mission, "ready-20"),
        )
        claim_source = source_comment(21, "agent-a", "/eos claim", "2026-07-15T10:01:00.125Z")
        comments = [ready_source, event_comment(22, [ready]), claim_source]
        proposal = authorize_command_proposal(
            comments, mission, policy, repository=REPOSITORY,
            command_comment_url=claim_source["html_url"],
        )
        self.assertTrue(proposal.allowed)
        self.assertEqual(proposal.events[0]["type"], "mission.claimed")
        self.assertEqual(
            proposal.events[0]["details"]["lease_start"],
            "2026-07-15T10:01:00.125Z",
        )

    def test_forged_founder_event_and_wrong_source_command_are_rejected(self):
        mission, policy = valid_context()
        source = source_comment(3, "agent-a", "/eos ready")
        forged = audit_event(
            "approval.granted", "josephmccann", "founder", source["html_url"],
            source["created_at"], 1, None,
        )
        history = authenticate_event_history(
            [source, event_comment(4, [forged])], mission, policy, repository=REPOSITORY
        )
        self.assertFalse(history.allowed)
        self.assertIn(history.code, {"EVENT_ACTOR_MISMATCH", "EVENT_COMMAND_MISMATCH"})

    def test_event_record_must_be_bot_authored(self):
        mission, policy = valid_context()
        source = source_comment(5, "agent-a", "/eos ready")
        ready = audit_event(
            "mission.ready", "agent-a", "producer", source["html_url"], source["created_at"], 1, None
        )
        history = authenticate_event_history(
            [source, event_comment(6, [ready], actor="agent-a")], mission, policy,
            repository=REPOSITORY,
        )
        self.assertEqual(history.code, "EVENT_COMMENT_ACTOR_INVALID")

    def test_forged_system_event_source_is_rejected(self):
        mission, policy = valid_context()
        forged = audit_event(
            "mission.orphaned", "system", "system",
            "https://github.com/attacker/repo/actions/runs/123",
            "2026-07-15T10:00:00Z", 1, None,
        )
        history = authenticate_event_history(
            [event_comment(7, [forged])], mission, policy, repository=REPOSITORY
        )
        self.assertEqual(history.code, "EVENT_SYSTEM_SOURCE_INVALID")

    def test_ready_rejects_mission_that_fails_definition_of_ready(self):
        mission = load_fixture("mission-not-ready.json")
        mission["mission_id"] = "aifo-control-plane-101"
        mission["assignments"]["producer"]["identity"] = "agent-a"
        policy = load_fixture("policy-control-plane.json")
        source = source_comment(8, "agent-a", "/eos ready")
        ready = audit_event(
            "mission.ready", "agent-a", "producer", source["html_url"], source["created_at"], 1, None
        )
        history = authenticate_event_history(
            [source, event_comment(9, [ready])], mission, policy, repository=REPOSITORY
        )
        self.assertEqual(history.code, "MISSION_NOT_READY")

    def test_claim_rejects_invalid_transition_and_projection(self):
        mission, policy = valid_context()
        source = source_comment(10, "agent-a", "/eos claim")
        claim = audit_event(
            "mission.claimed", "agent-a", "producer", source["html_url"],
            source["created_at"], 1, None,
            {
                "lease_owner": "agent-a", "lease_nonce": "claim-1",
                "lease_start": source["created_at"],
                "lease_expires_at": "2026-07-15T10:15:00Z",
                "wall_clock_cap_minutes": 240, "paths": mission["allowed_paths"],
            },
        )
        history = authenticate_event_history(
            [source, event_comment(11, [claim])], mission, policy, repository=REPOSITORY
        )
        self.assertEqual(history.code, "STATE_TRANSITION_DENIED")
        self.assertEqual(history.projection.state, "Proposed")

    def test_recovery_bundle_has_one_bot_comment_for_atomic_append(self):
        source_url = "https://github.com/%s/actions/runs/12345" % REPOSITORY
        orphaned = audit_event(
            "mission.orphaned", "system", "system", source_url,
            "2026-07-15T10:00:00Z", 1, None,
        )
        released = audit_event(
            "mission.released", "system", "system", source_url,
            "2026-07-15T10:00:00Z", 2, orphaned["event_hash"],
        )
        bundled = event_comment(12, [orphaned, released])
        self.assertEqual(bundled["body"].count("EOS:EVENT:BEGIN"), 2)
        self.assertEqual(bundled["user"]["login"], BOT)

    def test_authenticated_recovery_bundle_projects_orphan_then_ready(self):
        mission, policy = valid_context()
        ready_source = source_comment(30, "agent-a", "/eos ready", "2026-07-15T08:59:00Z")
        ready = audit_event("mission.ready", "agent-a", "producer", ready_source["html_url"], ready_source["created_at"], 1, None, ready_details(mission, "ready-30"))
        claim_source = source_comment(31, "agent-a", "/eos claim", "2026-07-15T09:00:00Z")
        claim = audit_event(
            "mission.claimed", "agent-a", "producer", claim_source["html_url"], claim_source["created_at"], 2, ready["event_hash"],
            {"lease_owner": "agent-a", "lease_nonce": "github-comment-31", "lease_start": "2026-07-15T09:00:00Z", "lease_expires_at": "2026-07-15T09:15:00Z", "wall_clock_cap_minutes": 240, "paths": mission["allowed_paths"]},
        )
        action_url = "https://github.com/%s/actions/runs/67890" % REPOSITORY
        orphaned = audit_event(
            "mission.orphaned", "system", "system", action_url,
            "2026-07-15T09:15:00Z", 3, claim["event_hash"],
            {"lease_owner": "agent-a", "lease_nonce": "github-comment-31", "lease_start": "2026-07-15T09:00:00Z", "lease_expires_at": "2026-07-15T09:15:00Z", "recovery": True, "recommended_action": "Parked"},
        )
        released = audit_event(
            "mission.released", "system", "system", action_url,
            "2026-07-15T09:15:00Z", 4, orphaned["event_hash"],
            {"lease_owner": "agent-a", "lease_nonce": "github-comment-31", "lease_start": "2026-07-15T09:00:00Z", "lease_expires_at": "2026-07-15T09:15:00Z", "recovery": True, "recommended_action": "Parked"},
        )
        history = authenticate_event_history(
            [ready_source, event_comment(32, [ready]), claim_source,
             event_comment(33, [claim]), event_comment(34, [orphaned, released])],
            mission, policy, repository=REPOSITORY, actions_runs=[recovery_run()],
        )
        self.assertTrue(history.allowed, history.code)
        self.assertEqual(history.projection.state, "Ready")

    def test_system_recovery_requires_existing_exact_workflow_run(self):
        mission, policy, comments, orphaned, released, run = recovery_fixture()
        bundled = comments + [event_comment(134, [orphaned, released])]
        missing = authenticate_event_history(
            bundled, mission, policy, repository=REPOSITORY, actions_runs=[]
        )
        self.assertEqual(missing.code, "EVENT_SYSTEM_RUN_NOT_FOUND")
        wrong_run = dict(run, path=".github/workflows/other.yml")
        wrong = authenticate_event_history(
            bundled, mission, policy, repository=REPOSITORY, actions_runs=[wrong_run]
        )
        self.assertEqual(wrong.code, "EVENT_SYSTEM_RUN_INVALID")

    def test_system_recovery_must_be_atomic_consecutive_matching_pair(self):
        mission, policy, comments, orphaned, released, run = recovery_fixture()
        standalone = authenticate_event_history(
            comments + [event_comment(135, [orphaned])], mission, policy,
            repository=REPOSITORY, actions_runs=[run],
        )
        self.assertEqual(standalone.code, "EVENT_SYSTEM_BUNDLE_INVALID")

        mismatched = copy.deepcopy(released)
        mismatched["details"]["lease_nonce"] = "different"
        mismatched["event_hash"] = content_sha256(mismatched)
        mismatch = authenticate_event_history(
            comments + [event_comment(136, [orphaned, mismatched])], mission, policy,
            repository=REPOSITORY, actions_runs=[run],
        )
        self.assertEqual(mismatch.code, "EVENT_SYSTEM_BUNDLE_MISMATCH")

    def test_system_recovery_is_recomputed_and_rejects_pre_expiry_pair(self):
        mission, policy, comments, orphaned, released, run = recovery_fixture(
            recovery_time="2026-07-15T09:14:59Z"
        )
        history = authenticate_event_history(
            comments + [event_comment(137, [orphaned, released])], mission, policy,
            repository=REPOSITORY, actions_runs=[run],
        )
        self.assertIn(history.code, {"LEASE_NOT_EXPIRED", "EVENT_SYSTEM_BUNDLE_MISMATCH"})

    def test_ready_hash_binds_immutable_mission_declaration(self):
        mission, policy = valid_context()
        source = source_comment(140, "agent-a", "/eos ready")
        ready = audit_event(
            "mission.ready", "agent-a", "producer", source["html_url"],
            source["created_at"], 1, None, ready_details(mission, "ready-140"),
        )
        edited = copy.deepcopy(mission)
        edited["objective"] = "Edited after readiness"
        history = authenticate_event_history(
            [source, event_comment(141, [ready])], edited, policy, repository=REPOSITORY
        )
        self.assertEqual(history.code, "MISSION_DECLARATION_CHANGED")

    def test_shared_kernel_rejects_invalid_repository_policy_schema(self):
        mission, policy = valid_context()
        policy["unversioned_escape"] = True
        history = authenticate_event_history([], mission, policy, repository=REPOSITORY)
        self.assertEqual(history.code, "REPOSITORY_POLICY_INVALID")

    def test_short_positive_mission_clamps_initial_lease_to_absolute_cap(self):
        mission, policy = valid_context()
        mission["budgets"]["wall_clock_minutes"] = 5
        ready_source = source_comment(150, "agent-a", "/eos ready", "2026-07-15T10:00:00Z")
        ready = audit_event(
            "mission.ready", "agent-a", "producer", ready_source["html_url"],
            ready_source["created_at"], 1, None, ready_details(mission, "ready-150"),
        )
        claim_source = source_comment(151, "agent-a", "/eos claim", "2026-07-15T10:01:00Z")
        proposal = authorize_command_proposal(
            [ready_source, event_comment(152, [ready]), claim_source],
            mission, policy, repository=REPOSITORY,
            command_comment_url=claim_source["html_url"],
        )
        self.assertTrue(proposal.allowed, proposal.code)
        self.assertEqual(proposal.events[0]["details"]["lease_expires_at"], "2026-07-15T10:06:00Z")

    def test_crossed_effective_limit_blocks_work_but_allows_explicit_park(self):
        mission, policy = valid_context()
        policy["default_limits"]["model_cost_usd"] = 5.0
        ready_source = source_comment(160, "agent-a", "/eos ready", "2026-07-15T10:00:00Z")
        ready = audit_event(
            "mission.ready", "agent-a", "producer", ready_source["html_url"],
            ready_source["created_at"], 1, None,
            ready_details(mission, "ready-160", model_cost_usd=5.01),
        )
        claim_source = source_comment(161, "agent-a", "/eos claim", "2026-07-15T10:01:00Z")
        comments = [ready_source, event_comment(162, [ready]), claim_source]
        blocked = authorize_command_proposal(
            comments, mission, policy, repository=REPOSITORY,
            command_comment_url=claim_source["html_url"],
        )
        self.assertFalse(blocked.allowed)
        self.assertEqual(blocked.code, "LIMIT_EXCEEDED")
        self.assertTrue(blocked.details["preserve_state"])
        self.assertEqual(blocked.details["recommended_action"], "Parked")
        self.assertEqual(blocked.details["breaches"][0]["cap"], 5.0)

        park_source = source_comment(163, "agent-a", "/eos park", "2026-07-15T10:01:00Z")
        parked = authorize_command_proposal(
            [ready_source, event_comment(162, [ready]), park_source],
            mission, policy, repository=REPOSITORY,
            command_comment_url=park_source["html_url"],
        )
        self.assertTrue(parked.allowed, parked.code)

    def test_pagination_and_recovery_policy_are_pure_and_fail_closed(self):
        self.assertEqual(flatten_paginated([[{"id": 1}], [{"id": 2}]]), [{"id": 1}, {"id": 2}])
        policy = load_fixture("policy-control-plane.json")
        self.assertFalse(recovery_mutation_allowed("schedule", False, policy))
        self.assertFalse(recovery_mutation_allowed("workflow_dispatch", False, policy))
        policy["orphan_recovery_enabled"] = True
        self.assertTrue(recovery_mutation_allowed("workflow_dispatch", False, policy))
        self.assertFalse(recovery_mutation_allowed("workflow_dispatch", True, policy))

    def test_transition_wrapper_emits_proposal_without_mutation(self):
        command = ROOT / "scripts/engineering-os/transition-mission"
        result = subprocess.run(
            [str(command), "--mission-id", "aifo-101", "--event-type", "mission.ready",
             "--actor", "agent-a", "--actor-role", "producer",
             "--occurred-at", "2026-07-15T10:05:00Z", "--source-url", "https://example.test/1",
             "--nonce", "nonce-cli"],
            cwd=ROOT, check=True, capture_output=True, text=True,
        )
        proposal = json.loads(result.stdout)
        self.assertEqual(proposal["type"], "mission.ready")
        self.assertEqual(proposal["details"]["nonce"], "nonce-cli")

    def test_mission_workflow_uses_default_policy_and_authenticated_history(self):
        workflow = (ROOT / ".github/workflows/mission-command.yml").read_text(encoding="utf-8")
        self.assertIn("eos-mission-${{ github.repository }}-${{ github.event.issue.number }}", workflow)
        self.assertIn("authenticate-event-history", workflow)
        self.assertIn("actions/runs", workflow)
        self.assertIn("--runs", workflow)
        self.assertIn("default_branch", workflow)
        self.assertIn("cancel-in-progress: false", workflow)
        self.assertNotIn("pull-requests: write", workflow)

    def test_orphan_recovery_is_explicit_policy_gated_and_per_mission(self):
        workflow = (ROOT / ".github/workflows/reusable-orphan-recovery.yml").read_text(encoding="utf-8")
        self.assertIn("schedule:", workflow)
        self.assertIn("default: true", workflow)
        self.assertIn("github.event_name != 'schedule'", workflow)
        self.assertIn("orphan_recovery_enabled", workflow)
        self.assertNotIn("vars.EOS_ORPHAN_RECOVERY_ENABLED", workflow)
        self.assertIn("eos-mission-${{ github.repository }}-${{ inputs.issue_number", workflow)
        self.assertIn("--slurp", workflow)
        self.assertIn("jq 'add'", workflow)
        self.assertIn("Re-fetch and revalidate", workflow)
        self.assertIn("=~ ^[1-9][0-9]*$", workflow)
        self.assertIn("recovery_mutation_allowed", workflow)
        self.assertIn("contents/.aifo/engineering-os-policy.json", workflow)
        self.assertIn("actions/runs/${GITHUB_RUN_ID}", workflow)

    def test_reusable_validation_is_read_only_and_flattens_pagination(self):
        workflow = (ROOT / ".github/workflows/reusable-mission-validation.yml").read_text(encoding="utf-8")
        self.assertIn("workflow_call:", workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn("issues: read", workflow)
        self.assertIn("authenticate-event-history", workflow)
        self.assertIn("actions/runs", workflow)
        self.assertIn("--runs", workflow)
        self.assertIn("--slurp", workflow)
        self.assertNotIn("issues: write", workflow)


if __name__ == "__main__":
    unittest.main()
