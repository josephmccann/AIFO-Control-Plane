import copy
import json
import subprocess
import unittest
from pathlib import Path

from engineering_os import commands as command_kernel
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
from engineering_os.mission import MISSION_BEGIN, MISSION_END
from tests.engineering_os.helpers import load_fixture


ROOT = Path(__file__).resolve().parents[2]
REPOSITORY = "josephmccann/AIFO-Control-Plane"
ACTIVE_COMMIT = "a" * 40
ACTIVE_TREE = "b" * 40


def activation_proof(**overrides):
    """A Model B proof bound to the historical baseline and active execution."""
    blobs = {path: "%040x" % (index + 1)
             for index, path in enumerate(command_kernel._INVARIANT_BASELINE_PATHS)}
    value = {
        "model": "reviewed_compatibility_chain",
        "chain_sha256": "c" * 64,
        "chain_path": "outputs/mission-35-compatibility-chain.json",
        "baseline_commit": "b3c0a2c7c85fbd45167d61ae29fc1f21dfafad9e",
        "baseline_tree": "9fd7af9c8f231759ebbee851836dd83a097418d6",
        "active_commit": ACTIVE_COMMIT, "active_tree": ACTIVE_TREE,
        "commit_count": 1,
        "invariant_paths": list(command_kernel._INVARIANT_BASELINE_PATHS),
        "invariant_digest": content_sha256(blobs),
    }
    value.update(overrides)
    return value
BOT = "github-actions[bot]"
RECOVERY_WORKFLOW = ".github/workflows/reusable-orphan-recovery.yml"


def audit_event(
    event_type, actor, role, source_url, occurred_at, sequence, previous,
    details=None, mission_id="aifo-control-plane-101",
):
    event = {
        "schema_version": "1.0.0",
        "mission_id": mission_id,
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


def source_comment(
    comment_id, actor, body, created_at="2026-07-15T10:00:00Z", issue=101,
):
    return {
        "id": comment_id,
        "body": body,
        "created_at": created_at,
        "html_url": "https://github.com/%s/issues/%s#issuecomment-%s" % (REPOSITORY, issue, comment_id),
        "user": {"login": actor},
    }


def event_comment(comment_id, events, actor=BOT, issue=101):
    body = "\n".join(
        "<!-- EOS:EVENT:BEGIN -->\n%s\n<!-- EOS:EVENT:END -->"
        % json.dumps(event, sort_keys=True, separators=(",", ":"))
        for event in events
    )
    return {
        "id": comment_id,
        "body": body,
        "created_at": "2026-07-15T10:00:01Z",
        "html_url": "https://github.com/%s/issues/%s#issuecomment-%s" % (REPOSITORY, issue, comment_id),
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


def claimed_mission_candidate(*, issue=202, paths=None, expires_at="2026-07-15T10:15:00Z"):
    mission = load_fixture("mission-valid.json")
    mission["mission_id"] = "aifo-control-plane-%s" % issue
    mission["assignments"]["producer"]["identity"] = "agent-b"
    mission["allowed_paths"] = list(paths or ["engineering_os/**"])
    ready_source = source_comment(
        issue * 10, "agent-b", "/eos ready", "2026-07-15T08:59:00Z", issue=issue,
    )
    ready = audit_event(
        "mission.ready", "agent-b", "producer", ready_source["html_url"],
        ready_source["created_at"], 1, None,
        ready_details(mission, "ready-%s" % issue), mission_id=mission["mission_id"],
    )
    claim_source = source_comment(
        issue * 10 + 1, "agent-b", "/eos claim", "2026-07-15T09:00:00Z", issue=issue,
    )
    claim = audit_event(
        "mission.claimed", "agent-b", "producer", claim_source["html_url"],
        claim_source["created_at"], 2, ready["event_hash"],
        {
            "lease_owner": "agent-b", "lease_nonce": "github-comment-%s" % (issue * 10 + 1),
            "lease_start": "2026-07-15T09:00:00Z", "lease_expires_at": expires_at,
            "wall_clock_cap_minutes": 240, "paths": mission["allowed_paths"],
        },
        mission_id=mission["mission_id"],
    )
    return {
        "issue_number": issue,
        "mission": mission,
        "comments": [
            ready_source, event_comment(issue * 10 + 2, [ready], issue=issue),
            claim_source, event_comment(issue * 10 + 3, [claim], issue=issue),
        ],
        "actions_runs": [],
    }


def issue_record(candidate, *, state="closed", body=None):
    declaration = "%s\n%s\n%s" % (
        MISSION_BEGIN,
        json.dumps(candidate["mission"], sort_keys=True, separators=(",", ":")),
        MISSION_END,
    )
    return {
        "number": candidate["issue_number"],
        "state": state,
        "body": declaration if body is None else body,
    }


def terminal_candidate(event_type):
    candidate = claimed_mission_candidate()
    claim = json.loads(command_kernel._EVENT_MARKER.search(candidate["comments"][-1]["body"]).group(1))
    comment_id = 2090 + {"mission.released": 1, "mission.parked": 2, "mission.cancelled": 3}[event_type]
    nonce = claim["details"]["lease_nonce"]
    if event_type == "mission.released":
        actor, role, command = "agent-b", "producer", "/eos release %s" % nonce
        details = {
            "lease_owner": "agent-b", "lease_nonce": nonce,
            "recovery": False, "recommended_action": "Ready",
        }
    elif event_type == "mission.parked":
        actor, role, command = "agent-b", "producer", "/eos park"
        details = {"nonce": "github-comment-%s" % comment_id}
    else:
        actor, role, command = "josephmccann", "founder", "/eos cancel"
        details = {"nonce": "github-comment-%s" % comment_id}
    source = source_comment(
        comment_id, actor, command, "2026-07-15T09:05:00Z", issue=candidate["issue_number"],
    )
    terminal = audit_event(
        event_type, actor, role, source["html_url"], source["created_at"],
        3, claim["event_hash"], details, mission_id=candidate["mission"]["mission_id"],
    )
    candidate["comments"].extend([
        source,
        event_comment(comment_id + 10, [terminal], issue=candidate["issue_number"]),
    ])
    return candidate


class CommandTests(unittest.TestCase):
    def test_activation_run_rejects_copied_stale_or_contradictory_provenance(self):
        sha = "3" * 40
        url = "https://github.com/%s/actions/runs/31" % REPOSITORY
        run = {"id": 31, "html_url": url, "path": ".github/workflows/mission-command.yml",
               "event": "issue_comment", "run_attempt": 2, "head_sha": sha,
               "actor": {"login": "josephmccann"}, "repository": {"full_name": REPOSITORY}}
        provenance = {"repository": REPOSITORY, "workflow_path": run["path"],
                      "workflow_ref": "%s/%s@%s" % (REPOSITORY, run["path"], sha),
                      "workflow_sha": sha, "run_id": 31, "run_attempt": 2, "job": "append",
                      "actor": BOT, "trigger_actor": "josephmccann", "event": "issue_comment",
                      "head_sha": sha, "head_tree": "4" * 40}
        self.assertFalse(command_kernel.validate_activation_run(run, REPOSITORY, url))
        self.assertTrue(command_kernel.validate_activation_run(run, REPOSITORY, url, provenance=provenance))
        for field, value in (("run_id", 32), ("run_attempt", 1), ("trigger_actor", "attacker"),
                             ("workflow_sha", "5" * 40), ("head_sha", "6" * 40),
                             ("repository", "attacker/repo")):
            candidate = {**provenance, field: value}
            self.assertFalse(command_kernel.validate_activation_run(run, REPOSITORY, url, provenance=candidate), field)

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

    def test_activation_consumption_command_requires_authenticated_workflow_run(self):
        mission, policy = valid_context()
        ready_source = source_comment(23, "agent-a", "/eos ready")
        ready = audit_event(
            "mission.ready", "agent-a", "producer", ready_source["html_url"],
            ready_source["created_at"], 1, None, ready_details(mission, "ready-23"),
        )
        command = source_comment(24, "josephmccann", "/eos attempt-baseline nonce-012345678901234567890123456789")
        activation = {
            "repository": REPOSITORY, "mission_issue": 26,
            "remediation_head": "b3c0a2c7c85fbd45167d61ae29fc1f21dfafad9e",
            "remediation_tree": "9fd7af9c8f231759ebbee851836dd83a097418d6",
            "baseline_generation_commit": "b3c0a2c7c85fbd45167d61ae29fc1f21dfafad9e",
            "baseline_generation_tree": "9fd7af9c8f231759ebbee851836dd83a097418d6",
            "active_execution_commit": ACTIVE_COMMIT,
            "active_execution_tree": ACTIVE_TREE,
            "compatibility_proof": activation_proof(),
            "baseline_artifact_sha256": "3bd53aa718599ae33a5093b5b5c6e1d416216631e7818acf5472128ea9e38bce",
            "canonical_inventory_sha256": "23211f7a871c8a9a9f15cb5c010fd5167a1f21314bceebe43c2a38d8d1f04c0e",
            "baseline_generator_identity": "engineering_os.test_integrity_cli:initial-baseline-v1",
            "analyzer_identity": "engineering_os.test_integrity_cli:b3c0a2c7",
            "workflow_identity": "reusable-test-integrity@b3142f5bbed547a97a70f29bda33682294948aed",
            "caller_identity": "test-integrity-caller@80256915bdca989edc7580898971dbad1b199170",
            "immutable_kernel_identity": "5a273627a1a4d4addfcf81129dcdbda4dc58c383",
            "manifest_identity": "db1f444bad41ecf1db5057c8cbbae6390ffb7f5f7477e0c7a3bd8ae35a7a6dab",
            "rollback_sha": "77af0e93780134349abb15bd8d8b665c6de939a3",
            "activation_nonce": "nonce-012345678901234567890123456789",
            "activation_type": "initial_test_integrity_baseline", "single_use": True,
            "founder_authorization_identity": "josephmccann", "founder_authorization_sequence": 1,
        }
        proposal = authorize_command_proposal(
            [ready_source, event_comment(25, [ready]), command], mission, policy,
            repository=REPOSITORY, command_comment_url=command["html_url"], activation=activation,
        )
        self.assertFalse(proposal.allowed)
        self.assertEqual(proposal.code, "ACTIVATION_WORKFLOW_PROVENANCE_INVALID")

    def test_activation_consumption_proposal_uses_validator_terminal_result(self):
        """The production consume proposal must satisfy the append validator."""
        mission, policy = valid_context()
        ready_source = source_comment(26, "agent-a", "/eos ready", issue=26)
        ready = audit_event(
            "mission.ready", "agent-a", "producer", ready_source["html_url"],
            ready_source["created_at"], 1, None, ready_details(mission, "ready-26"),
        )
        activation = {
            "repository": REPOSITORY, "mission_issue": 26,
            "remediation_head": "b3c0a2c7c85fbd45167d61ae29fc1f21dfafad9e",
            "remediation_tree": "9fd7af9c8f231759ebbee851836dd83a097418d6",
            "baseline_generation_commit": "b3c0a2c7c85fbd45167d61ae29fc1f21dfafad9e",
            "baseline_generation_tree": "9fd7af9c8f231759ebbee851836dd83a097418d6",
            "active_execution_commit": ACTIVE_COMMIT,
            "active_execution_tree": ACTIVE_TREE,
            "compatibility_proof": activation_proof(),
            "baseline_artifact_sha256": "3bd53aa718599ae33a5093b5b5c6e1d416216631e7818acf5472128ea9e38bce",
            "canonical_inventory_sha256": "23211f7a871c8a9a9f15cb5c010fd5167a1f21314bceebe43c2a38d8d1f04c0e",
            "baseline_generator_identity": "engineering_os.test_integrity_cli:initial-baseline-v1",
            "analyzer_identity": "engineering_os.test_integrity_cli:b3c0a2c7",
            "workflow_identity": "reusable-test-integrity@b3142f5bbed547a97a70f29bda33682294948aed",
            "caller_identity": "test-integrity-caller@80256915bdca989edc7580898971dbad1b199170",
            "immutable_kernel_identity": "5a273627a1a4d4addfcf81129dcdbda4dc58c383",
            "manifest_identity": "db1f444bad41ecf1db5057c8cbbae6390ffb7f5f7477e0c7a3bd8ae35a7a6dab",
            "rollback_sha": "77af0e93780134349abb15bd8d8b665c6de939a3",
            "activation_nonce": "nonce-012345678901234567890123456789",
            "activation_type": "initial_test_integrity_baseline", "single_use": True,
            "founder_authorization_identity": "josephmccann", "founder_authorization_sequence": 1,
        }
        workflow_sha = "3" * 40
        provenance = {
            "repository": REPOSITORY, "workflow_path": ".github/workflows/mission-command.yml",
            "workflow_ref": "%s/.github/workflows/mission-command.yml@%s" % (REPOSITORY, workflow_sha),
            "workflow_sha": workflow_sha, "run_id": 27, "run_attempt": 1, "job": "prepare",
            "actor": BOT, "trigger_actor": "josephmccann", "event": "issue_comment",
            "head_sha": workflow_sha, "head_tree": "4" * 40,
        }
        activation.update({
            "mission_issue_identity": {
                "repository": REPOSITORY, "number": 26, "node_id": "I_kwDOmission26",
                "url": "https://github.com/%s/issues/26" % REPOSITORY, "state": "open",
                "ready_event_hash": ready["event_hash"], "ready_sequence": ready["sequence"],
                "ready_declaration_sha256": ready["details"]["mission_sha256"],
            },
            "authorization_provenance": provenance,
        })
        auth_source = source_comment(27, "josephmccann", "/eos authorize-baseline nonce-012345678901234567890123456789", issue=26)
        run_url = "https://github.com/%s/actions/runs/27" % REPOSITORY
        run = {"id": 27, "html_url": run_url, "name": "Mission command", "path": ".github/workflows/mission-command.yml",
               "event": "issue_comment", "run_attempt": 1, "head_sha": workflow_sha,
               "actor": {"login": "josephmccann"}, "repository": {"full_name": REPOSITORY}}
        auth = audit_event("test_integrity.baseline.authorized", "josephmccann", "founder", auth_source["html_url"],
                           auth_source["created_at"], 2, ready["event_hash"], copy.deepcopy(activation))
        self.assertEqual(command_kernel.validate_document("audit-event", auth), [])
        attempt_source = source_comment(28, "josephmccann", "/eos attempt-baseline nonce-012345678901234567890123456789", issue=26)
        activation["consumer_provenance"] = {**provenance, "job": "append"}
        attempt = authorize_command_proposal(
            [ready_source, event_comment(29, [ready], issue=26), auth_source, event_comment(30, [auth], issue=26), attempt_source],
            mission, policy, repository=REPOSITORY, command_comment_url=attempt_source["html_url"],
            actions_runs=[run], activation=activation, activation_source_url=run_url,
        )
        self.assertTrue(attempt.allowed, attempt.code)
        consume_source = source_comment(31, "josephmccann", "/eos consume-baseline nonce-012345678901234567890123456789", issue=26)
        consume = authorize_command_proposal(
            [ready_source, event_comment(29, [ready], issue=26), auth_source, event_comment(30, [auth], issue=26), attempt_source,
             event_comment(32, [attempt.events[0]], issue=26) , consume_source],
            mission, policy, repository=REPOSITORY, command_comment_url=consume_source["html_url"],
            actions_runs=[run], activation=activation, activation_source_url=run_url,
        )
        self.assertTrue(consume.allowed)
        self.assertEqual(consume.events[0]["details"]["consumption_result"], "activated")

    def _retired_nonce_context(self, proposed_nonce):
        """Build a history containing a superseded legacy authorization and an
        ``/eos authorize-baseline`` command proposing ``proposed_nonce``."""
        mission, policy = valid_context()
        ready_source = source_comment(40, "agent-a", "/eos ready", issue=26)
        ready = audit_event(
            "mission.ready", "agent-a", "producer", ready_source["html_url"],
            ready_source["created_at"], 1, None, ready_details(mission, "ready-40"),
        )
        workflow_sha = "3" * 40
        provenance = {
            "repository": REPOSITORY, "workflow_path": ".github/workflows/mission-command.yml",
            "workflow_ref": "%s/.github/workflows/mission-command.yml@%s" % (REPOSITORY, workflow_sha),
            "workflow_sha": workflow_sha, "run_id": 41, "run_attempt": 1, "job": "prepare",
            "actor": BOT, "trigger_actor": "josephmccann", "event": "issue_comment",
            "head_sha": workflow_sha, "head_tree": "4" * 40,
        }
        identity = {
            "repository": REPOSITORY, "number": 26, "node_id": "I_kwDOmission26",
            "url": "https://github.com/%s/issues/26" % REPOSITORY, "state": "open",
            "ready_event_hash": ready["event_hash"], "ready_sequence": ready["sequence"],
            "ready_declaration_sha256": ready["details"]["mission_sha256"],
        }
        full = {
            "repository": REPOSITORY, "mission_issue": 26,
            "mission_issue_identity": identity, "authorization_provenance": provenance,
            "remediation_head": "b3c0a2c7c85fbd45167d61ae29fc1f21dfafad9e",
            "remediation_tree": "9fd7af9c8f231759ebbee851836dd83a097418d6",
            "baseline_generation_commit": "b3c0a2c7c85fbd45167d61ae29fc1f21dfafad9e",
            "baseline_generation_tree": "9fd7af9c8f231759ebbee851836dd83a097418d6",
            "active_execution_commit": ACTIVE_COMMIT, "active_execution_tree": ACTIVE_TREE,
            "compatibility_proof": activation_proof(),
            "baseline_artifact_sha256": "3bd53aa718599ae33a5093b5b5c6e1d416216631e7818acf5472128ea9e38bce",
            "canonical_inventory_sha256": "23211f7a871c8a9a9f15cb5c010fd5167a1f21314bceebe43c2a38d8d1f04c0e",
            "baseline_generator_identity": "engineering_os.test_integrity_cli:initial-baseline-v1",
            "analyzer_identity": "engineering_os.test_integrity_cli:b3c0a2c7",
            "workflow_identity": "reusable-test-integrity@b3142f5bbed547a97a70f29bda33682294948aed",
            "caller_identity": "test-integrity-caller@80256915bdca989edc7580898971dbad1b199170",
            "immutable_kernel_identity": "5a273627a1a4d4addfcf81129dcdbda4dc58c383",
            "manifest_identity": "db1f444bad41ecf1db5057c8cbbae6390ffb7f5f7477e0c7a3bd8ae35a7a6dab",
            "rollback_sha": "77af0e93780134349abb15bd8d8b665c6de939a3",
            "activation_type": "initial_test_integrity_baseline", "single_use": True,
            "founder_authorization_identity": "josephmccann", "founder_authorization_sequence": 2,
        }
        # Superseded legacy authorization already on the issue, carrying the
        # retired nonce.
        RETIRED = "retired-nonce-012345678901234567890123456789"
        legacy = {k: v for k, v in full.items() if k not in (
            "baseline_generation_commit", "baseline_generation_tree",
            "active_execution_commit", "active_execution_tree", "compatibility_proof",
        )}
        legacy["activation_nonce"] = RETIRED
        legacy["founder_authorization_sequence"] = 1
        legacy_source = source_comment(42, "josephmccann",
                                       "/eos authorize-baseline %s" % RETIRED, issue=26)
        legacy_event = audit_event(
            "test_integrity.baseline.authorized", "josephmccann", "founder",
            legacy_source["html_url"], legacy_source["created_at"], 2,
            ready["event_hash"], copy.deepcopy(legacy),
        )
        proposed = copy.deepcopy(full)
        proposed["activation_nonce"] = proposed_nonce
        run_url = "https://github.com/%s/actions/runs/41" % REPOSITORY
        run = {"id": 41, "html_url": run_url, "name": "Mission command",
               "path": ".github/workflows/mission-command.yml", "event": "issue_comment",
               "run_attempt": 1, "head_sha": workflow_sha,
               "actor": {"login": "josephmccann"}, "repository": {"full_name": REPOSITORY}}
        cmd = source_comment(44, "josephmccann",
                             "/eos authorize-baseline %s" % proposed_nonce, issue=26)
        comments = [ready_source, event_comment(43, [ready], issue=26),
                    legacy_source, event_comment(45, [legacy_event], issue=26), cmd]
        return dict(comments=comments, mission=mission, policy=policy,
                    activation=proposed, run=run, run_url=run_url, cmd=cmd, retired=RETIRED)

    def test_authorize_proposal_rejects_retired_nonce(self):
        """A replacement authorization reusing a superseded nonce fails closed
        before any event can be appended."""
        ctx = self._retired_nonce_context(proposed_nonce="retired-nonce-012345678901234567890123456789")
        proposal = authorize_command_proposal(
            ctx["comments"], ctx["mission"], ctx["policy"], repository=REPOSITORY,
            command_comment_url=ctx["cmd"]["html_url"], actions_runs=[ctx["run"]],
            activation=ctx["activation"], activation_source_url=ctx["run_url"],
        )
        self.assertFalse(proposal.allowed)
        self.assertEqual(proposal.code, "ACTIVATION_NONCE_RETIRED")

    def test_authorize_proposal_allows_distinct_replacement_nonce(self):
        """A distinct fresh nonce still produces a valid replacement proposal."""
        ctx = self._retired_nonce_context(proposed_nonce="fresh-distinct-nonce-98765432109876543210")
        proposal = authorize_command_proposal(
            ctx["comments"], ctx["mission"], ctx["policy"], repository=REPOSITORY,
            command_comment_url=ctx["cmd"]["html_url"], actions_runs=[ctx["run"]],
            activation=ctx["activation"], activation_source_url=ctx["run_url"],
        )
        self.assertTrue(proposal.allowed, proposal.code)
        self.assertEqual(proposal.events[0]["type"], "test_integrity.baseline.authorized")
        self.assertEqual(
            proposal.events[0]["details"]["activation_nonce"],
            "fresh-distinct-nonce-98765432109876543210",
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

    def test_incomplete_or_unmatched_event_markers_fail_closed(self):
        mission, policy = valid_context()
        malformed_bodies = {
            "begin-only": "<!-- EOS:EVENT:BEGIN -->",
            "end-only": "<!-- EOS:EVENT:END -->",
            "duplicate-begin": "<!-- EOS:EVENT:BEGIN --><!-- EOS:EVENT:BEGIN -->{}<!-- EOS:EVENT:END -->",
        }
        for name, body in malformed_bodies.items():
            with self.subTest(name=name):
                malformed = {
                    "id": 70,
                    "body": body,
                    "created_at": "2026-07-15T10:00:00Z",
                    "html_url": "https://github.com/%s/issues/101#issuecomment-70" % REPOSITORY,
                    "user": {"login": BOT},
                }
                history = authenticate_event_history(
                    [malformed], mission, policy, repository=REPOSITORY,
                )
                self.assertFalse(history.allowed)
                self.assertEqual(history.code, "EVENT_COMMENT_FORMAT_INVALID")

    def test_partialized_last_claim_cannot_truncate_prior_authenticated_chain(self):
        mission, policy = valid_context()
        ready_source = source_comment(71, "agent-a", "/eos ready", "2026-07-15T09:59:00Z")
        ready = audit_event(
            "mission.ready", "agent-a", "producer", ready_source["html_url"],
            ready_source["created_at"], 1, None, ready_details(mission, "ready-71"),
        )
        claim_source = source_comment(72, "agent-a", "/eos claim", "2026-07-15T10:00:00Z")
        claim = audit_event(
            "mission.claimed", "agent-a", "producer", claim_source["html_url"],
            claim_source["created_at"], 2, ready["event_hash"],
            {
                "lease_owner": "agent-a", "lease_nonce": "github-comment-72",
                "lease_start": claim_source["created_at"],
                "lease_expires_at": "2026-07-15T10:15:00Z",
                "wall_clock_cap_minutes": 240, "paths": mission["allowed_paths"],
            },
        )
        partial_claim = {
            "id": 74,
            "body": "<!-- EOS:EVENT:BEGIN -->\n%s" % json.dumps(claim, sort_keys=True),
            "created_at": "2026-07-15T10:00:01Z",
            "html_url": "https://github.com/%s/issues/101#issuecomment-74" % REPOSITORY,
            "user": {"login": BOT},
        }
        history = authenticate_event_history(
            [ready_source, event_comment(73, [ready]), claim_source, partial_claim],
            mission, policy, repository=REPOSITORY,
        )
        self.assertFalse(history.allowed)
        self.assertEqual(history.code, "EVENT_COMMENT_FORMAT_INVALID")

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

    def test_malformed_ready_command_fails_stably_before_effective_limit_access(self):
        for mutation, expected in (
            (lambda mission, policy: mission.pop("budgets"), "MISSION_NOT_READY"),
            (lambda mission, policy: mission.__setitem__("budgets", "not-an-object"), "MISSION_NOT_READY"),
            (lambda mission, policy: policy["default_limits"].pop("model_tokens"), "REPOSITORY_POLICY_INVALID"),
        ):
            with self.subTest(expected=expected):
                mission, policy = valid_context()
                mutation(mission, policy)
                source = source_comment(90, "agent-a", "/eos ready")
                decision = authorize_command_proposal(
                    [source], mission, policy, repository=REPOSITORY,
                    command_comment_url=source["html_url"],
                )
                self.assertFalse(decision.allowed)
                self.assertEqual(decision.code, expected)

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

    def test_recovery_run_path_uses_versioned_caller_allowlist_and_manual_event(self):
        mission, policy, comments, orphaned, released, run = recovery_fixture()
        caller_path = ".github/workflows/mission-recovery-dispatch.yml"
        policy["recovery_workflow_paths"] = [RECOVERY_WORKFLOW, caller_path]
        bundled = comments + [event_comment(138, [orphaned, released])]

        direct = authenticate_event_history(
            bundled, mission, policy, repository=REPOSITORY, actions_runs=[run],
        )
        self.assertTrue(direct.allowed, direct.code)

        caller = dict(run, name="Mission recovery dispatch", path=caller_path)
        configured = authenticate_event_history(
            bundled, mission, policy, repository=REPOSITORY, actions_runs=[caller],
        )
        self.assertTrue(configured.allowed, configured.code)

        unconfigured_policy = copy.deepcopy(policy)
        unconfigured_policy["recovery_workflow_paths"] = [RECOVERY_WORKFLOW]
        unconfigured = authenticate_event_history(
            bundled, mission, unconfigured_policy, repository=REPOSITORY,
            actions_runs=[caller],
        )
        self.assertEqual(unconfigured.code, "EVENT_SYSTEM_RUN_INVALID")

        for forbidden_event in ("schedule", "workflow_call"):
            with self.subTest(event=forbidden_event):
                forbidden = authenticate_event_history(
                    bundled, mission, policy, repository=REPOSITORY,
                    actions_runs=[dict(caller, event=forbidden_event)],
                )
                self.assertEqual(forbidden.code, "EVENT_SYSTEM_RUN_INVALID")

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

    def test_repository_history_authentication_fails_closed_on_malformed_candidate(self):
        mission, policy = valid_context()
        candidate = claimed_mission_candidate()
        authenticated = command_kernel.authenticate_repository_lease_events(
            [candidate], policy, repository=REPOSITORY,
        )
        self.assertTrue(authenticated.allowed, authenticated.code)
        self.assertEqual(authenticated.events[-1]["type"], "mission.claimed")

        malformed = copy.deepcopy(candidate)
        malformed["comments"][-1]["user"]["login"] = "agent-b"
        denied = command_kernel.authenticate_repository_lease_events(
            [malformed], policy, repository=REPOSITORY,
        )
        self.assertFalse(denied.allowed)
        self.assertEqual(denied.code, "REPOSITORY_MISSION_HISTORY_INVALID")

        invalid_policy = copy.deepcopy(policy)
        invalid_policy["unversioned_escape"] = True
        invalid = command_kernel.authenticate_repository_lease_events(
            [], invalid_policy, repository=REPOSITORY,
        )
        self.assertFalse(invalid.allowed)
        self.assertEqual(invalid.code, "REPOSITORY_POLICY_INVALID")

    def test_claim_considers_overlapping_active_leases_from_other_missions(self):
        mission, policy = valid_context()
        ready_source = source_comment(170, "agent-a", "/eos ready", "2026-07-15T10:00:00Z")
        ready = audit_event(
            "mission.ready", "agent-a", "producer", ready_source["html_url"],
            ready_source["created_at"], 1, None, ready_details(mission, "ready-170"),
        )
        claim_source = source_comment(171, "agent-a", "/eos claim", "2026-07-15T10:01:00Z")
        comments = [ready_source, event_comment(172, [ready]), claim_source]

        for expires_at in ("2026-07-15T10:15:00Z", "2026-07-15T09:15:00Z"):
            with self.subTest(expires_at=expires_at):
                repository_history = command_kernel.authenticate_repository_lease_events(
                    [claimed_mission_candidate(expires_at=expires_at)],
                    policy, repository=REPOSITORY,
                )
                decision = authorize_command_proposal(
                    comments, mission, policy, repository=REPOSITORY,
                    command_comment_url=claim_source["html_url"],
                    repository_lease_events=repository_history.events,
                )
                self.assertFalse(decision.allowed)
                self.assertEqual(decision.code, "LEASE_PATH_CONFLICT")

    def test_closed_issue_with_active_lease_remains_a_repository_candidate(self):
        mission, policy = valid_context()
        candidate = claimed_mission_candidate()
        discovery = command_kernel.discover_repository_mission_candidates(
            [issue_record(candidate, state="closed")],
            {str(candidate["issue_number"]): candidate["comments"]},
        )
        self.assertTrue(discovery.allowed, discovery.code)
        self.assertEqual(discovery.candidates[0]["issue_number"], candidate["issue_number"])
        repository_history = command_kernel.authenticate_repository_lease_events(
            [dict(discovery.candidates[0], actions_runs=[])],
            policy, repository=REPOSITORY,
        )
        ready_source = source_comment(190, "agent-a", "/eos ready", "2026-07-15T10:00:00Z")
        ready = audit_event(
            "mission.ready", "agent-a", "producer", ready_source["html_url"],
            ready_source["created_at"], 1, None, ready_details(mission, "ready-190"),
        )
        claim_source = source_comment(191, "agent-a", "/eos claim", "2026-07-15T10:01:00Z")
        decision = authorize_command_proposal(
            [ready_source, event_comment(192, [ready]), claim_source],
            mission, policy, repository=REPOSITORY,
            command_comment_url=claim_source["html_url"],
            repository_lease_events=repository_history.events,
        )
        self.assertEqual(decision.code, "LEASE_PATH_CONFLICT")

    def test_event_bearing_issue_without_complete_current_declaration_fails_closed(self):
        candidate = claimed_mission_candidate()
        comments = {str(candidate["issue_number"]): candidate["comments"]}
        cases = {
            "removed": "mission declaration was removed",
            "partial-marker": "%s\n{}" % MISSION_BEGIN,
        }
        for name, body in cases.items():
            with self.subTest(name=name):
                discovery = command_kernel.discover_repository_mission_candidates(
                    [issue_record(candidate, body=body)], comments,
                )
                self.assertFalse(discovery.allowed)
                self.assertEqual(discovery.code, "REPOSITORY_MISSION_DECLARATION_INVALID")

        skipped = command_kernel.discover_repository_mission_candidates(
            [{"number": 303, "state": "closed", "body": "ordinary issue"}],
            {"303": []},
        )
        self.assertTrue(skipped.allowed, skipped.code)
        self.assertEqual(skipped.candidates, ())

    def test_pull_request_records_follow_the_same_mission_candidate_rules(self):
        candidate = claimed_mission_candidate(issue=404)
        plain_pr = {
            "number": 403, "state": "closed", "body": "ordinary pull request",
            "pull_request": {"url": "https://api.github.test/pulls/403"},
        }
        mission_pr = issue_record(candidate, state="closed")
        mission_pr["pull_request"] = {"url": "https://api.github.test/pulls/404"}
        discovery = command_kernel.discover_repository_mission_candidates(
            [plain_pr, mission_pr],
            {"403": [], "404": candidate["comments"]},
        )
        self.assertTrue(discovery.allowed, discovery.code)
        self.assertEqual(
            [item["issue_number"] for item in discovery.candidates], [404],
        )
        mission, policy = valid_context()
        authenticated = command_kernel.authenticate_repository_lease_events(
            [dict(discovery.candidates[0], actions_runs=[])],
            policy, repository=REPOSITORY,
        )
        self.assertTrue(authenticated.allowed, authenticated.code)
        self.assertEqual(authenticated.events[-1]["type"], "mission.claimed")

        missing_declaration_pr = copy.deepcopy(mission_pr)
        missing_declaration_pr["body"] = "declaration removed from pull request"
        denied = command_kernel.discover_repository_mission_candidates(
            [missing_declaration_pr], {"404": candidate["comments"]},
        )
        self.assertFalse(denied.allowed)
        self.assertEqual(denied.code, "REPOSITORY_MISSION_DECLARATION_INVALID")

    def test_authenticated_release_park_or_cancellation_clears_repository_lease(self):
        mission, policy = valid_context()
        ready_source = source_comment(200, "agent-a", "/eos ready", "2026-07-15T10:00:00Z")
        ready = audit_event(
            "mission.ready", "agent-a", "producer", ready_source["html_url"],
            ready_source["created_at"], 1, None, ready_details(mission, "ready-200"),
        )
        claim_source = source_comment(201, "agent-a", "/eos claim", "2026-07-15T10:01:00Z")
        comments = [ready_source, event_comment(202, [ready]), claim_source]
        for terminal_type in ("mission.released", "mission.parked", "mission.cancelled"):
            with self.subTest(terminal_type=terminal_type):
                repository_history = command_kernel.authenticate_repository_lease_events(
                    [terminal_candidate(terminal_type)], policy, repository=REPOSITORY,
                )
                self.assertTrue(repository_history.allowed, repository_history.code)
                decision = authorize_command_proposal(
                    comments, mission, policy, repository=REPOSITORY,
                    command_comment_url=claim_source["html_url"],
                    repository_lease_events=repository_history.events,
                )
                self.assertTrue(decision.allowed, decision.code)

    def test_claim_allows_authenticated_non_overlapping_repository_lease(self):
        mission, policy = valid_context()
        ready_source = source_comment(180, "agent-a", "/eos ready", "2026-07-15T10:00:00Z")
        ready = audit_event(
            "mission.ready", "agent-a", "producer", ready_source["html_url"],
            ready_source["created_at"], 1, None, ready_details(mission, "ready-180"),
        )
        claim_source = source_comment(181, "agent-a", "/eos claim", "2026-07-15T10:01:00Z")
        repository_history = command_kernel.authenticate_repository_lease_events(
            [claimed_mission_candidate(paths=["unrelated/**"])],
            policy, repository=REPOSITORY,
        )
        decision = authorize_command_proposal(
            [ready_source, event_comment(182, [ready]), claim_source],
            mission, policy, repository=REPOSITORY,
            command_comment_url=claim_source["html_url"],
            repository_lease_events=repository_history.events,
        )
        self.assertTrue(decision.allowed, decision.code)

    def test_pagination_and_recovery_policy_are_pure_and_fail_closed(self):
        self.assertEqual(flatten_paginated([[{"id": 1}], [{"id": 2}]]), [{"id": 1}, {"id": 2}])
        policy = load_fixture("policy-control-plane.json")
        self.assertFalse(recovery_mutation_allowed("schedule", False, policy))
        self.assertFalse(recovery_mutation_allowed("workflow_dispatch", False, policy))
        policy["orphan_recovery_enabled"] = True
        self.assertTrue(recovery_mutation_allowed("workflow_dispatch", False, policy))
        self.assertFalse(recovery_mutation_allowed("workflow_call", False, policy))
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

    def test_claim_adapter_refetches_paginated_repository_histories_under_claim_lock(self):
        workflow = (ROOT / ".github/workflows/mission-command.yml").read_text(encoding="utf-8")
        self.assertIn("group: eos-claim-${{ github.repository }}", workflow)
        self.assertIn("issues?state=all&per_page=100", workflow)
        self.assertIn("--paginate --slurp", workflow)
        self.assertIn("authenticate-repository-leases", workflow)
        self.assertIn("--repository-leases", workflow)
        self.assertIn("EOS:MISSION:BEGIN", workflow)
        self.assertIn("EOS:EVENT:BEGIN", workflow)
        self.assertNotIn('select(has("pull_request") | not)', workflow)
        self.assertIn("cancel-in-progress: false", workflow)

    def test_orphan_recovery_is_explicit_policy_gated_and_per_mission(self):
        workflow = (ROOT / ".github/workflows/reusable-orphan-recovery.yml").read_text(encoding="utf-8")
        self.assertIn("schedule:", workflow)
        self.assertIn("default: true", workflow)
        self.assertIn("issues?state=all&per_page=100", workflow)
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
