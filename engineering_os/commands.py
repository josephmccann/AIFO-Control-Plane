"""Stable command parsing and immutable event-proposal construction."""

import argparse
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
import json
import re
import sys
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from .canonical import content_sha256
from .lease import (
    _rfc3339,
    _timestamp,
    claim_mission,
    find_orphans,
    heartbeat_lease,
    release_mission,
)
from .limits import LIMIT_NAMES, evaluate_limits
from .mission import MISSION_BEGIN, MISSION_END, MissionParseError, parse_issue_body, validate_ready
from .schema import validate_document
from .state import MissionProjection, authorize_transition, project_state


_COMMANDS = {
    "claim": 0,
    "heartbeat": 1,
    "release": 1,
    "recover": 1,
    "ready": 0,
    "start": 0,
    "review": 0,
    "approve": 0,
    "merge": 0,
    "verify": 0,
    "close": 0,
    "park": 0,
    "cancel": 0,
    "authorize-baseline": 1,
    "attempt-baseline": 1,
    "consume-baseline": 1,
}

_COMMAND_EVENTS = {
    "claim": "mission.claimed",
    "heartbeat": "lease.heartbeat",
    "release": "mission.released",
    "ready": "mission.ready",
    "start": "mission.started",
    "review": "review.requested",
    "approve": "approval.granted",
    "merge": "mission.merged",
    "verify": "verification.passed",
    "close": "mission.closed",
    "park": "mission.parked",
    "cancel": "mission.cancelled",
    "authorize-baseline": "test_integrity.baseline.authorized",
    "attempt-baseline": "test_integrity.baseline.consumption_attempted",
    "consume-baseline": "test_integrity.baseline.consumed",
}
_EVENT_MARKER = re.compile(
    r"<!-- EOS:EVENT:BEGIN -->\s*(\{.*?\})\s*<!-- EOS:EVENT:END -->",
    re.S,
)
_EVENT_BEGIN = "EOS:EVENT:BEGIN"
_EVENT_END = "EOS:EVENT:END"
_BOT = "github-actions[bot]"
_RECOVERY_EVENTS = frozenset(("workflow_dispatch",))
_ACTIVATION_AUTHORIZED = "test_integrity.baseline.authorized"
_ACTIVATION_ATTEMPTED = "test_integrity.baseline.consumption_attempted"
_ACTIVATION_CONSUMED = "test_integrity.baseline.consumed"
_ACTIVATION_EVENTS = frozenset((_ACTIVATION_AUTHORIZED, _ACTIVATION_ATTEMPTED, _ACTIVATION_CONSUMED))
_ACTIVATION_REQUIRED = frozenset({
    "repository", "mission_issue", "remediation_head", "remediation_tree",
    "baseline_artifact_sha256", "canonical_inventory_sha256",
    "baseline_generator_identity", "analyzer_identity", "workflow_identity",
    "caller_identity", "immutable_kernel_identity", "manifest_identity",
    "rollback_sha", "activation_nonce", "activation_type", "single_use",
    "founder_authorization_identity", "founder_authorization_sequence",
})
_CONSUMPTION_REQUIRED = _ACTIVATION_REQUIRED | frozenset({
    "authorization_event_hash", "authorization_sequence", "consumer_identity",
    "consumed_at", "consumption_result", "post_consumption_state", "attempt_event_hash",
})


def _activation_tuple(details: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
    """Return a strict activation tuple, rejecting extra or malformed fields."""
    if not isinstance(details, Mapping) or set(details) != _ACTIVATION_REQUIRED:
        return None
    text_fields = _ACTIVATION_REQUIRED - {"mission_issue", "single_use", "founder_authorization_sequence"}
    if any(not isinstance(details[key], str) or not details[key].strip() for key in text_fields):
        return None
    if not isinstance(details["mission_issue"], int) or isinstance(details["mission_issue"], bool):
        return None
    if details["mission_issue"] != 26 or not isinstance(details["single_use"], bool):
        return None
    if (not isinstance(details["founder_authorization_sequence"], int)
            or isinstance(details["founder_authorization_sequence"], bool)
            or details["founder_authorization_sequence"] < 1):
        return None
    if details["single_use"] is not True or details["activation_type"] != "initial_test_integrity_baseline":
        return None
    for key in ("baseline_artifact_sha256", "canonical_inventory_sha256"):
        if re.fullmatch(r"[0-9a-f]{64}", details[key]) is None:
            return None
    if re.fullmatch(r"[0-9a-f]{40}", details["remediation_head"]) is None:
        return None
    if re.fullmatch(r"[0-9a-f]{40}", details["rollback_sha"]) is None:
        return None
    if re.fullmatch(r"[0-9a-f]{40}", details["remediation_tree"]) is None:
        return None
    if len(details["activation_nonce"]) < 32:
        return None
    return dict(details)


def build_activation_event(
    event_type: str,
    details: Mapping[str, Any],
    *,
    actor: str,
    actor_role: str,
    occurred_at: str,
    source_url: str,
    authorization_event: Optional[Mapping[str, Any]] = None,
    attempt_event: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Build one activation proposal; never appends or consumes it."""
    if event_type not in _ACTIVATION_EVENTS or not isinstance(actor, str) or not actor.strip():
        raise ValueError("activation event identity is invalid")
    if event_type == _ACTIVATION_AUTHORIZED:
        if actor_role != "founder" or _activation_tuple(details) is None:
            raise ValueError("authorization requires the founder and exact activation tuple")
    else:
        if actor_role != "system" or not isinstance(details, Mapping):
            raise ValueError("consumption events require the system actor")
        tuple_value = {key: details.get(key) for key in _ACTIVATION_REQUIRED}
        if _activation_tuple(tuple_value) is None:
            raise ValueError("consumption event tuple is invalid")
        if not isinstance(authorization_event, Mapping):
            raise ValueError("consumption event requires an authorization event")
        if details.get("authorization_event_hash") != authorization_event.get("event_hash"):
            raise ValueError("authorization event reference is invalid")
        if event_type == _ACTIVATION_CONSUMED and not isinstance(attempt_event, Mapping):
            raise ValueError("consumed event requires an attempted-consumption event")
        if attempt_event is not None and details.get("attempt_event_hash") != attempt_event.get("event_hash"):
            raise ValueError("attempt event reference is invalid")
    return {
        "schema_version": "1.0.0",
        "type": event_type,
        "actor": actor.strip(),
        "actor_role": actor_role,
        "occurred_at": _rfc3339(occurred_at),
        "source_url": source_url,
        "details": dict(details),
    }


def validate_activation_ledger(
    events: Sequence[Mapping[str, Any]],
    activation: Mapping[str, Any],
    *, repository: str,
    mission_issue: int = 26,
    current_commit: Optional[str] = None,
    current_tree: Optional[str] = None,
) -> Tuple[bool, str, Dict[str, Any]]:
    """Validate the Mission #26 activation protocol without mutating state.

    This validator consumes only an already authenticated, complete event
    history.  It intentionally has no persistence or append capability.
    """
    if not isinstance(events, (list, tuple)) or not isinstance(activation, Mapping):
        return False, "ACTIVATION_INPUT_INVALID", {}
    if any(isinstance(event, Mapping) and event.get("type") in {
        "mission.cancelled", "test_integrity.baseline.superseded",
        "test_integrity.baseline.recovery",
    } for event in events):
        return False, "ACTIVATION_AUTHORIZATION_INVALIDATED", {}
    expected = _activation_tuple(activation)
    if expected is None or expected["repository"] != repository or expected["mission_issue"] != mission_issue:
        return False, "ACTIVATION_TUPLE_INVALID", {}
    if current_commit is not None and expected["remediation_head"] != current_commit:
        return False, "ACTIVATION_COMMIT_MISMATCH", {}
    if current_tree is not None and expected["remediation_tree"] != current_tree:
        return False, "ACTIVATION_TREE_MISMATCH", {}
    authorizations = []
    attempts = []
    consumptions = []
    nonces = set()
    strict_chain = all(
        isinstance(event, Mapping)
        and isinstance(event.get("mission_id"), str)
        and event.get("schema_version") == "1.0.0"
        and isinstance(event.get("occurred_at"), str)
        and isinstance(event.get("source_url"), str)
        and "previous_event_hash" in event
        for event in events
    )
    if not strict_chain:
        return False, "ACTIVATION_HISTORY_INVALID", {}
    activation_events = []
    for event in events:
        if event.get("type") not in _ACTIVATION_EVENTS:
            if isinstance(event.get("type"), str) and event["type"].startswith("test_integrity.baseline."):
                return False, "ACTIVATION_HISTORY_INVALID", {}
            continue
        activation_events.append(event)
        if (not isinstance(event.get("sequence"), int)
                or isinstance(event.get("sequence"), bool)
                or event["sequence"] < 1
                or not isinstance(event.get("event_hash"), str)
                or re.fullmatch(r"[0-9a-f]{64}", event["event_hash"]) is None):
            return False, "ACTIVATION_HISTORY_INVALID", {}
        details = event.get("details")
        if event.get("type") == _ACTIVATION_AUTHORIZED:
            tuple_value = _activation_tuple(details)
        else:
            tuple_value = (
                {key: details.get(key) for key in _ACTIVATION_REQUIRED}
                if isinstance(details, Mapping) and set(details) == _CONSUMPTION_REQUIRED
                else None
            )
            if tuple_value is not None and (
                not isinstance(details.get("authorization_event_hash"), str)
                or not isinstance(details.get("authorization_sequence"), int)
                or isinstance(details.get("authorization_sequence"), bool)
                or not isinstance(details.get("consumer_identity"), str)
                or not isinstance(details.get("consumed_at"), str)
                or not isinstance(details.get("consumption_result"), str)
                or not isinstance(details.get("post_consumption_state"), str)
            ):
                tuple_value = None
        if tuple_value is None or tuple_value != expected:
            return False, "ACTIVATION_TUPLE_MISMATCH", {}
        nonce = tuple_value["activation_nonce"]
        if event.get("type") == _ACTIVATION_AUTHORIZED:
            nonces.add(nonce)
        if event.get("type") == _ACTIVATION_AUTHORIZED:
            if event.get("actor_role") != "founder":
                return False, "ACTIVATION_AUTHORITY_INVALID", {}
            if (not isinstance(details, Mapping)
                    or details.get("founder_authorization_identity") != event.get("actor")):
                return False, "ACTIVATION_AUTHORITY_INVALID", {}
            authorizations.append(event)
        elif event.get("type") == _ACTIVATION_ATTEMPTED:
            if event.get("actor_role") != "system":
                return False, "ACTIVATION_CONSUMER_INVALID", {}
            attempts.append(event)
        else:
            if event.get("actor_role") != "system":
                return False, "ACTIVATION_CONSUMER_INVALID", {}
            consumptions.append(event)
    valid_chain, _chain_code = validate_event_chain([dict(event) for event in events])
    if not valid_chain:
        return False, "ACTIVATION_HISTORY_INVALID", {}
    if len({event.get("sequence") for event in events}) != len(events):
        return False, "ACTIVATION_HISTORY_INVALID", {}
    if len(authorizations) > 1:
        return False, "ACTIVATION_AUTHORIZATION_REPLAY", {}
    if len(nonces) != len(authorizations):
        return False, "ACTIVATION_NONCE_REPLAY", {}
    if len(attempts) > 1:
        return False, "ACTIVATION_ATTEMPT_REPLAY", {}
    if len(consumptions) > 1:
        return False, "ACTIVATION_CONSUMPTION_REPLAY", {}
    if (attempts or consumptions) and not authorizations:
        return False, "ACTIVATION_ORPHAN_CONSUMPTION", {}
    if attempts or consumptions:
        auth = authorizations[0]
        consumed = (consumptions or attempts)[0]
        if consumed.get("details", {}).get("authorization_event_hash") != auth.get("event_hash"):
            return False, "ACTIVATION_AUTHORIZATION_REFERENCE_INVALID", {}
        if consumed.get("details", {}).get("authorization_sequence") != auth.get("sequence"):
            return False, "ACTIVATION_AUTHORIZATION_SEQUENCE_INVALID", {}
        if attempts:
            if attempts[0].get("sequence") != auth.get("sequence") + 1:
                return False, "ACTIVATION_ORDER_INVALID", {}
            if attempts[0].get("details", {}).get("authorization_event_hash") != auth.get("event_hash"):
                return False, "ACTIVATION_AUTHORIZATION_REFERENCE_INVALID", {}
            attempt_details = attempts[0].get("details", {})
            if (attempt_details.get("founder_authorization_identity") != auth.get("actor")
                    or attempt_details.get("consumption_result") != "attempted"
                    or attempt_details.get("post_consumption_state") != "locked"):
                return False, "ACTIVATION_ATTEMPT_BINDING_INVALID", {}
        if consumptions:
            if not attempts or consumptions[0].get("sequence") != attempts[0].get("sequence") + 1:
                return False, "ACTIVATION_ORDER_INVALID", {}
            if consumptions[0].get("details", {}).get("attempt_event_hash") != attempts[0].get("event_hash"):
                return False, "ACTIVATION_ATTEMPT_REFERENCE_INVALID", {}
            consumed_details = consumptions[0].get("details", {})
            if (consumed_details.get("founder_authorization_identity") != auth.get("actor")
                    or consumed_details.get("consumption_result") != "activated"
                    or consumed_details.get("post_consumption_state") != "active"):
                return False, "ACTIVATION_CONSUMPTION_BINDING_INVALID", {}
        if attempts and not consumptions:
            return True, "ACTIVATION_ATTEMPTED", {"consumed": False, "locked": True}
        return True, "ACTIVATION_ALREADY_CONSUMED", {"consumed": True}
    return bool(authorizations), ("ACTIVATION_AUTHORIZED" if authorizations else "ACTIVATION_NOT_AUTHORIZED"), {
        "consumed": False,
        "authorization_event_hash": authorizations[0].get("event_hash") if authorizations else None,
    }


@dataclass(frozen=True)
class HistoryDecision:
    allowed: bool
    code: str
    events: Tuple[Dict[str, Any], ...] = ()
    projection: MissionProjection = field(default_factory=MissionProjection)
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProposalDecision:
    allowed: bool
    code: str
    events: Tuple[Dict[str, Any], ...] = ()
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RepositoryLeaseDecision:
    allowed: bool
    code: str
    events: Tuple[Dict[str, Any], ...] = ()
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RepositoryDiscoveryDecision:
    allowed: bool
    code: str
    candidates: Tuple[Dict[str, Any], ...] = ()
    details: Dict[str, Any] = field(default_factory=dict)


def parse_command(text: str) -> Optional[Tuple[str, Tuple[str, ...]]]:
    """Parse only a complete, single-line, lower-case ``/eos`` command."""

    if not isinstance(text, str) or re.fullmatch(r"/eos [a-z]+(?:-[a-z]+)*(?: [A-Za-z0-9._:-]+)?", text) is None:
        return None
    fields = text.split(" ")
    name, arguments = fields[1], tuple(fields[2:])
    if name not in _COMMANDS or len(arguments) != _COMMANDS[name]:
        return None
    return name, arguments


def concurrency_key(repository: str, issue: int) -> str:
    """Build the stable workflow serialization key for one mission issue."""

    if not isinstance(repository, str) or repository.count("/") != 1 or not isinstance(issue, int) or issue < 1:
        raise ValueError("repository and positive issue number are required")
    return "eos-mission-%s-%d" % (repository.replace("/", "-"), issue)


def flatten_paginated(pages: Sequence[Sequence[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Flatten ``gh api --paginate --slurp`` output without dropping pages."""

    if not isinstance(pages, list) or any(not isinstance(page, list) for page in pages):
        raise ValueError("paginated API output must be an array of arrays")
    return [item for page in pages for item in page]


def discover_repository_mission_candidates(
    issues: Sequence[Mapping[str, Any]],
    comments_by_issue: Mapping[str, Sequence[Mapping[str, Any]]],
) -> RepositoryDiscoveryDecision:
    """Find all state-independent declaration or event-bearing mission issues."""

    if not isinstance(issues, list) or not isinstance(comments_by_issue, Mapping):
        return RepositoryDiscoveryDecision(False, "REPOSITORY_DISCOVERY_INPUT_INVALID")
    candidates = []
    seen_issues = set()
    for issue in issues:
        if not isinstance(issue, Mapping):
            return RepositoryDiscoveryDecision(False, "REPOSITORY_DISCOVERY_INPUT_INVALID")
        issue_number = issue.get("number")
        comments = comments_by_issue.get(str(issue_number))
        body = issue.get("body") or ""
        if (
            not isinstance(issue_number, int)
            or isinstance(issue_number, bool)
            or issue_number < 1
            or issue_number in seen_issues
            or not isinstance(body, str)
            or not isinstance(comments, list)
        ):
            return RepositoryDiscoveryDecision(
                False, "REPOSITORY_DISCOVERY_INPUT_INVALID",
                details={"issue_number": issue_number},
            )
        seen_issues.add(issue_number)
        declaration_bearing = MISSION_BEGIN in body or MISSION_END in body
        event_bearing = any(
            isinstance(comment, Mapping)
            and isinstance(comment.get("body"), str)
            and (_EVENT_BEGIN in comment["body"] or _EVENT_END in comment["body"])
            for comment in comments
        )
        if not declaration_bearing and not event_bearing:
            continue
        try:
            mission = parse_issue_body(body)
        except MissionParseError as error:
            return RepositoryDiscoveryDecision(
                False, "REPOSITORY_MISSION_DECLARATION_INVALID",
                details={"issue_number": issue_number, "error": str(error)},
            )
        candidates.append({
            "issue_number": issue_number,
            "mission": mission,
            "comments": comments,
        })
    return RepositoryDiscoveryDecision(
        True, "REPOSITORY_MISSION_CANDIDATES_DISCOVERED", tuple(candidates)
    )


def recovery_mutation_allowed(event_name: str, dry_run: bool, policy: Mapping[str, Any]) -> bool:
    """Permit mutation only for an explicit invocation and versioned opt-in."""

    return (
        event_name == "workflow_dispatch"
        and dry_run is False
        and isinstance(policy, Mapping)
        and policy.get("orphan_recovery_enabled") is True
    )


def propose_event(
    *, mission_id: str, event_type: str, actor: str, actor_role: str,
    occurred_at: str, source_url: str, nonce: str, details: Dict[str, Any],
) -> Dict[str, Any]:
    """Create a hashed proposal; sequencing and audit hashes belong to the adapter."""

    if actor_role not in {"producer", "adversary", "founder", "system"}:
        raise ValueError("unknown actor role")
    if not all(isinstance(value, str) and value.strip() for value in (
        mission_id, event_type, actor, source_url, nonce
    )):
        raise ValueError("proposal identity fields must be non-empty strings")
    if not isinstance(details, dict):
        raise ValueError("proposal details must be an object")
    normalized_details = dict(details)
    normalized_details["nonce"] = nonce.strip()
    proposal = {
        "schema_version": "1.0.0",
        "mission_id": mission_id.strip(),
        "type": event_type.strip(),
        "actor": actor.strip(),
        "actor_role": actor_role,
        "occurred_at": _rfc3339(occurred_at),
        "source_url": source_url.strip(),
        "details": normalized_details,
    }
    proposal["proposal_hash"] = content_sha256(proposal)
    return proposal


def validate_event_chain(events: Sequence[Dict[str, Any]]) -> Tuple[bool, str]:
    """Validate the closed audit schema, sequence, and complete hash chain."""

    if not isinstance(events, list):
        return False, "EVENT_CHAIN_INVALID"
    previous = None
    mission_id = None
    for index, event in enumerate(events, start=1):
        if not isinstance(event, dict) or validate_document("audit-event", event):
            return False, "EVENT_SCHEMA_INVALID"
        if event.get("sequence") != index:
            return False, "EVENT_SEQUENCE_INVALID"
        if mission_id is None:
            mission_id = event.get("mission_id")
        elif event.get("mission_id") != mission_id:
            return False, "EVENT_MISSION_MISMATCH"
        if event.get("previous_event_hash") != previous:
            return False, "EVENT_PREVIOUS_HASH_INVALID"
        if event.get("event_hash") != content_sha256(event):
            return False, "EVENT_HASH_INVALID"
        previous = event["event_hash"]
    return True, "EVENT_CHAIN_VALID"


def _actor_roles(actor: str, mission: Mapping[str, Any], policy: Mapping[str, Any]) -> set:
    roles = set()
    founders = policy.get("founder_identities", [])
    if isinstance(founders, list) and any(
        isinstance(founder, str) and founder.casefold() == actor.casefold()
        for founder in founders
    ):
        roles.add("founder")
    assignments = mission.get("assignments", {})
    if isinstance(assignments, Mapping):
        for role in ("producer", "adversary"):
            assignment = assignments.get(role, {})
            identity = assignment.get("identity") if isinstance(assignment, Mapping) else None
            if isinstance(identity, str) and identity.casefold() == actor.casefold():
                roles.add(role)
    return roles


def _deny_history(code: str, events: Sequence[Dict[str, Any]], projection: MissionProjection, **details: Any) -> HistoryDecision:
    return HistoryDecision(False, code, tuple(events), projection, details)


def _extract_event_comments(
    comments: Sequence[Mapping[str, Any]],
) -> Tuple[Optional[str], List[Dict[str, Any]], List[Any]]:
    events: List[Dict[str, Any]] = []
    groups: List[Any] = []
    for comment in comments:
        body = comment.get("body")
        if not isinstance(body, str):
            continue
        begins = body.count(_EVENT_BEGIN)
        ends = body.count(_EVENT_END)
        matches = list(_EVENT_MARKER.finditer(body))
        if begins == 0 and ends == 0:
            continue
        if not matches or begins != len(matches) or ends != len(matches):
            return "EVENT_COMMENT_FORMAT_INVALID", events, groups
        if comment.get("user", {}).get("login") != _BOT:
            return "EVENT_COMMENT_ACTOR_INVALID", events, groups
        if _EVENT_MARKER.sub("", body).strip():
            return "EVENT_COMMENT_FORMAT_INVALID", events, groups
        for match in matches:
            try:
                event = json.loads(match.group(1))
            except json.JSONDecodeError:
                return "EVENT_JSON_INVALID", events, groups
            if not isinstance(event, dict):
                return "EVENT_JSON_INVALID", events, groups
            events.append(event)
            groups.append(comment.get("html_url"))
    return None, events, groups


def validate_recovery_run(
    run: Mapping[str, Any], repository: str, source_url: str,
    policy: Mapping[str, Any],
) -> bool:
    """Authenticate one recovery source against independently fetched run metadata."""

    if not isinstance(run, Mapping) or not isinstance(repository, str):
        return False
    run_id = run.get("id")
    expected_url = (
        "https://github.com/%s/actions/runs/%s" % (repository, run_id)
        if isinstance(run_id, int) and not isinstance(run_id, bool) and run_id > 0
        else None
    )
    run_repository = run.get("repository")
    allowed_paths = policy.get("recovery_workflow_paths", ())
    return (
        source_url == expected_url
        and run.get("html_url") == expected_url
        and isinstance(run.get("name"), str)
        and bool(run["name"].strip())
        and isinstance(allowed_paths, list)
        and run.get("path") in allowed_paths
        and run.get("event") in _RECOVERY_EVENTS
        and isinstance(run_repository, Mapping)
        and run_repository.get("full_name") == repository
    )


def validate_activation_run(run: Mapping[str, Any], repository: str, source_url: str,
                            expected_head_sha: Optional[str] = None) -> bool:
    """Authenticate the existing mission-command workflow as activation source."""
    if not isinstance(run, Mapping) or not isinstance(repository, str):
        return False
    run_id = run.get("id")
    expected = "https://github.com/%s/actions/runs/%s" % (repository, run_id)
    return (
        isinstance(run_id, int) and not isinstance(run_id, bool) and run_id > 0
        and source_url == expected and run.get("html_url") == expected
        and run.get("path") == ".github/workflows/mission-command.yml"
        and run.get("event") == "issue_comment"
        and isinstance(run.get("repository"), Mapping)
        and run["repository"].get("full_name") == repository
        and (expected_head_sha is None or run.get("head_sha") == expected_head_sha)
    )
def effective_limits(mission: Mapping[str, Any], policy: Mapping[str, Any]) -> Dict[str, Any]:
    """Return the most restrictive declared mission/repository cap per resource."""

    mission_caps = mission.get("budgets", {})
    repository_caps = policy.get("default_limits", {})
    return {
        name: min(mission_caps.get(name), repository_caps.get(name))
        for name in LIMIT_NAMES
    }


def derive_measurements(events: Sequence[Mapping[str, Any]], observed_at: str) -> Dict[str, Any]:
    """Derive cumulative resource observations only from authenticated events."""

    observed = _timestamp(observed_at)
    measured: Dict[str, Any] = {name: 0 for name in LIMIT_NAMES}
    lease_starts = []
    for event in events:
        details = event.get("details", {})
        if not isinstance(details, Mapping):
            continue
        for name in ("model_cost_usd", "model_tokens", "ci_reruns"):
            value = details.get(name)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                measured[name] += value
        concurrent = details.get("concurrent_agents")
        if isinstance(concurrent, (int, float)) and not isinstance(concurrent, bool):
            measured["concurrent_agents"] = max(measured["concurrent_agents"], concurrent)
        if event.get("type") == "finding.valid":
            measured["remediation_cycles"] += 1
        if event.get("type") == "mission.claimed" and isinstance(details.get("lease_start"), str):
            lease_starts.append(_timestamp(details["lease_start"]))
    if lease_starts:
        measured["wall_clock_minutes"] = max(
            0, (observed - min(lease_starts)).total_seconds() / 60
        )
    return measured


def authenticate_event_history(
    comments: Sequence[Mapping[str, Any]],
    mission: Mapping[str, Any],
    policy: Mapping[str, Any],
    *,
    repository: str,
    actions_runs: Sequence[Mapping[str, Any]] = (),
) -> HistoryDecision:
    """Authenticate GitHub-backed events, authority, lifecycle, and projection."""

    projection = MissionProjection()
    if not isinstance(comments, list) or not isinstance(mission, Mapping) or not isinstance(policy, Mapping):
        return _deny_history("EVENT_HISTORY_INPUT_INVALID", (), projection)
    policy_violations = validate_document("repository-policy", dict(policy))
    if policy_violations:
        return _deny_history(
            "REPOSITORY_POLICY_INVALID", (), projection,
            violations=[asdict(item) for item in policy_violations],
        )
    if policy.get("repository") != repository or mission.get("repository") != repository:
        return _deny_history("EVENT_REPOSITORY_MISMATCH", (), projection)
    if not isinstance(actions_runs, (list, tuple)) or any(
        not isinstance(run, Mapping) for run in actions_runs
    ):
        return _deny_history("EVENT_SYSTEM_RUNS_INVALID", (), projection)
    comment_urls: Dict[str, Mapping[str, Any]] = {}
    for comment in comments:
        if not isinstance(comment, Mapping) or not isinstance(comment.get("html_url"), str):
            continue
        if comment["html_url"] in comment_urls:
            return _deny_history("EVENT_SOURCE_DUPLICATE", (), projection)
        comment_urls[comment["html_url"]] = comment
    extraction_error, events, event_groups = _extract_event_comments(comments)
    if extraction_error:
        return _deny_history(extraction_error, events, projection)
    valid, code = validate_event_chain(events)
    if not valid:
        return _deny_history(code, events, projection)

    system_indexes = {
        index for index, event in enumerate(events)
        if (event.get("actor") == "system" or event.get("actor_role") == "system")
        and event.get("type") not in _ACTIVATION_EVENTS
    }
    expected_system_source = (
        r"https://github\.com/%s/actions/runs/[1-9][0-9]*" % re.escape(repository)
    )
    for index in sorted(system_indexes):
        event = events[index]
        if (
            event.get("actor") != "system"
            or event.get("actor_role") != "system"
            or not isinstance(event.get("source_url"), str)
            or re.fullmatch(expected_system_source, event["source_url"]) is None
            or event.get("type") not in {"mission.orphaned", "mission.released", *_ACTIVATION_EVENTS}
        ):
            return _deny_history("EVENT_SYSTEM_SOURCE_INVALID", events[:index], projection)
    recovery_pairs: Dict[int, int] = {}
    for index in sorted(system_indexes):
        if index in recovery_pairs or index - 1 in recovery_pairs:
            continue
        group_indexes = [
            candidate for candidate, group in enumerate(event_groups)
            if group == event_groups[index]
        ]
        if group_indexes != [index, index + 1] or index + 1 >= len(events):
            return _deny_history("EVENT_SYSTEM_BUNDLE_INVALID", events[:index], projection)
        first, second = events[index], events[index + 1]
        if (
            first.get("type") != "mission.orphaned"
            or second.get("type") != "mission.released"
            or any(
                item.get("actor") != "system" or item.get("actor_role") != "system"
                for item in (first, second)
            )
        ):
            return _deny_history("EVENT_SYSTEM_BUNDLE_INVALID", events[:index], projection)
        if any(
            first.get(key) != second.get(key)
            for key in ("mission_id", "actor", "actor_role", "occurred_at", "source_url", "details")
        ):
            return _deny_history("EVENT_SYSTEM_BUNDLE_MISMATCH", events[:index], projection)
        recovery_pairs[index] = index + 1

    accepted: List[Dict[str, Any]] = []
    for index, event in enumerate(events):
        if event.get("mission_id") != mission.get("mission_id"):
            return _deny_history("EVENT_MISSION_MISMATCH", accepted, projection)
        try:
            _rfc3339(event.get("occurred_at"))
        except (TypeError, ValueError):
            return _deny_history("EVENT_TIMESTAMP_INVALID", accepted, projection)
        event_type = event.get("type")
        source_url = event.get("source_url")
        system_event = event.get("actor") == "system" or event.get("actor_role") == "system"
        if system_event:
            expected = r"https://github\.com/%s/actions/runs/[1-9][0-9]*" % re.escape(repository)
            if (
                event.get("actor") != "system"
                or event.get("actor_role") != "system"
                or not isinstance(source_url, str)
                or re.fullmatch(expected, source_url) is None
                or event_type not in {"mission.orphaned", "mission.released", *_ACTIVATION_EVENTS}
            ):
                return _deny_history("EVENT_SYSTEM_SOURCE_INVALID", accepted, projection)
            matching_runs = [run for run in actions_runs if run.get("html_url") == source_url]
            if not matching_runs:
                return _deny_history("EVENT_SYSTEM_RUN_NOT_FOUND", accepted, projection)
            run_valid = (
                validate_activation_run(matching_runs[0], repository, source_url)
                if event_type in _ACTIVATION_EVENTS
                else validate_recovery_run(matching_runs[0], repository, source_url, policy)
            )
            if len(matching_runs) != 1 or not run_valid:
                return _deny_history("EVENT_SYSTEM_RUN_INVALID", accepted, projection)
        else:
            source = comment_urls.get(source_url)
            if source is None:
                return _deny_history("EVENT_SOURCE_NOT_FOUND", accepted, projection)
            parsed = parse_command(source.get("body"))
            if parsed is None:
                return _deny_history("EVENT_COMMAND_INVALID", accepted, projection)
            command, arguments = parsed
            if _COMMAND_EVENTS.get(command) != event_type:
                return _deny_history("EVENT_COMMAND_MISMATCH", accepted, projection)
            actor = source.get("user", {}).get("login")
            if event.get("actor") != actor or event.get("occurred_at") != source.get("created_at"):
                return _deny_history("EVENT_ACTOR_MISMATCH", accepted, projection)
            roles = _actor_roles(actor, mission, policy) if isinstance(actor, str) else set()
            if event.get("actor_role") not in roles:
                return _deny_history("EVENT_ROLE_MISMATCH", accepted, projection)
            nonce_key = "activation_nonce" if event_type in _ACTIVATION_EVENTS else "lease_nonce"
            if arguments and str(event.get("details", {}).get(nonce_key, "")).strip() != arguments[0].strip():
                return _deny_history("EVENT_NONCE_MISMATCH", accepted, projection)

        if event_type in {"mission.ready", "mission.claimed"} and validate_ready(dict(mission)):
            return _deny_history("MISSION_NOT_READY", accepted, projection)
        if event_type == "mission.ready":
            recorded_hash = event.get("details", {}).get("mission_sha256")
            if not isinstance(recorded_hash, str) or re.fullmatch(r"[0-9a-f]{64}", recorded_hash) is None:
                return _deny_history("MISSION_DECLARATION_HASH_INVALID", accepted, projection)
            if recorded_hash != content_sha256(mission):
                return _deny_history("MISSION_DECLARATION_CHANGED", accepted, projection)
        transition = authorize_transition(projection, event, policy)
        if not transition.allowed:
            return _deny_history(transition.code, accepted, projection, **transition.details)

        prior_lease_events = [item for item in accepted if item.get("type") in {
            "mission.claimed", "lease.heartbeat", "mission.orphaned", "mission.released",
        }]
        lifecycle = None
        details = event.get("details", {})
        if index in recovery_pairs:
            lifecycle = release_mission(
                prior_lease_events, mission_id=event["mission_id"],
                owner="system", now=event["occurred_at"],
                nonce=details.get("lease_nonce"), recovery=True,
            )
            if not lifecycle.allowed:
                return _deny_history(lifecycle.code, accepted, projection, **lifecycle.details)
            expected_pair = lifecycle.events
            actual_pair = (event, events[recovery_pairs[index]])
            if len(expected_pair) != 2 or any(
                any(actual.get(key) != expected.get(key) for key in (
                    "mission_id", "type", "actor", "actor_role", "occurred_at", "details",
                ))
                for actual, expected in zip(actual_pair, expected_pair)
            ):
                return _deny_history("EVENT_SYSTEM_BUNDLE_MISMATCH", accepted, projection)
            lifecycle = None
        elif event_type == "mission.claimed":
            lifecycle = claim_mission(
                prior_lease_events,
                mission_id=event["mission_id"], owner=event["actor"],
                actor_role=event["actor_role"], now=event["occurred_at"],
                expires_at=details.get("lease_expires_at"),
                nonce=details.get("lease_nonce"), paths=details.get("paths"),
                wall_clock_minutes=effective_limits(mission, policy).get("wall_clock_minutes"),
            )
        elif event_type == "lease.heartbeat":
            lifecycle = heartbeat_lease(
                prior_lease_events, mission_id=event["mission_id"],
                owner=event["actor"], now=event["occurred_at"],
                expires_at=details.get("lease_expires_at"), nonce=details.get("lease_nonce"),
            )
        elif event_type == "mission.released" and index - 1 not in recovery_pairs:
            lifecycle = release_mission(
                prior_lease_events, mission_id=event["mission_id"],
                owner=event["actor"], now=event["occurred_at"],
                nonce=details.get("lease_nonce"), recovery=system_event,
            )
        if lifecycle is not None:
            if not lifecycle.allowed:
                return _deny_history(lifecycle.code, accepted, projection)
            expected_event = lifecycle.event
            if any(event.get(key) != expected_event.get(key) for key in (
                "mission_id", "type", "actor", "actor_role", "occurred_at", "details",
            )):
                return _deny_history("EVENT_LIFECYCLE_MISMATCH", accepted, projection)

        accepted.append(event)
        projection = project_state(accepted, policy)
        if projection.violations:
            return _deny_history("EVENT_PROJECTION_INVALID", accepted, projection)
    return HistoryDecision(True, "EVENT_HISTORY_AUTHENTICATED", tuple(accepted), projection)


def authenticate_repository_lease_events(
    candidates: Sequence[Mapping[str, Any]],
    policy: Mapping[str, Any],
    *,
    repository: str,
) -> RepositoryLeaseDecision:
    """Authenticate every parsed open-mission history before exposing leases."""

    if not isinstance(candidates, list):
        return RepositoryLeaseDecision(False, "REPOSITORY_MISSION_INPUT_INVALID")
    if not isinstance(policy, Mapping) or validate_document("repository-policy", dict(policy)):
        return RepositoryLeaseDecision(False, "REPOSITORY_POLICY_INVALID")
    lease_events: List[Dict[str, Any]] = []
    seen_issues = set()
    seen_missions = set()
    for candidate in candidates:
        if not isinstance(candidate, Mapping):
            return RepositoryLeaseDecision(False, "REPOSITORY_MISSION_INPUT_INVALID")
        issue_number = candidate.get("issue_number")
        mission = candidate.get("mission")
        comments = candidate.get("comments")
        actions_runs = candidate.get("actions_runs")
        mission_id = mission.get("mission_id") if isinstance(mission, Mapping) else None
        if (
            not isinstance(issue_number, int)
            or isinstance(issue_number, bool)
            or issue_number < 1
            or issue_number in seen_issues
            or not isinstance(mission_id, str)
            or not mission_id
            or mission_id in seen_missions
            or not isinstance(comments, list)
            or not isinstance(actions_runs, list)
        ):
            return RepositoryLeaseDecision(
                False, "REPOSITORY_MISSION_INPUT_INVALID",
                details={"issue_number": issue_number},
            )
        seen_issues.add(issue_number)
        seen_missions.add(mission_id)
        history = authenticate_event_history(
            comments, mission, policy, repository=repository,
            actions_runs=actions_runs,
        )
        if not history.allowed:
            return RepositoryLeaseDecision(
                False, "REPOSITORY_MISSION_HISTORY_INVALID",
                details={"issue_number": issue_number, "cause": history.code},
            )
        authenticated_mission_leases = []
        for event in history.events:
            if event.get("type") in {"mission.parked", "mission.cancelled"}:
                authenticated_mission_leases = []
            elif event.get("type") in {
                "mission.claimed", "lease.heartbeat", "mission.orphaned", "mission.released",
            }:
                authenticated_mission_leases.append(event)
        lease_events.extend(authenticated_mission_leases)
    return RepositoryLeaseDecision(
        True, "REPOSITORY_LEASE_EVENTS_AUTHENTICATED", tuple(lease_events)
    )


def _utc_text(value: datetime) -> str:
    normalized = value.astimezone(timezone.utc)
    timespec = "microseconds" if normalized.microsecond else "seconds"
    return normalized.isoformat(timespec=timespec).replace("+00:00", "Z")


def authorize_command_proposal(
    comments: Sequence[Mapping[str, Any]],
    mission: Mapping[str, Any],
    policy: Mapping[str, Any],
    *,
    repository: str,
    command_comment_url: str,
    actions_runs: Sequence[Mapping[str, Any]] = (),
    repository_lease_events: Sequence[Mapping[str, Any]] = (),
    activation: Optional[Mapping[str, Any]] = None,
    activation_source_url: Optional[str] = None,
) -> ProposalDecision:
    """Authorize one authenticated command and return append-only audit events."""

    history = authenticate_event_history(
        comments, mission, policy, repository=repository, actions_runs=actions_runs
    )
    if not history.allowed or history.projection.violations:
        return ProposalDecision(False, history.code)
    source = next(
        (comment for comment in comments if comment.get("html_url") == command_comment_url),
        None,
    )
    if source is None:
        return ProposalDecision(False, "EVENT_SOURCE_NOT_FOUND")
    parsed = parse_command(source.get("body"))
    if parsed is None:
        return ProposalDecision(False, "EVENT_COMMAND_INVALID")
    command, arguments = parsed
    event_type = _COMMAND_EVENTS.get(command)
    if event_type is None:
        return ProposalDecision(False, "EVENT_COMMAND_INVALID")
    actor = source.get("user", {}).get("login")
    occurred_at = source.get("created_at")
    try:
        _rfc3339(occurred_at)
    except (TypeError, ValueError):
        return ProposalDecision(False, "EVENT_TIMESTAMP_INVALID")
    if validate_ready(dict(mission)):
        return ProposalDecision(False, "MISSION_NOT_READY")
    caps = effective_limits(mission, policy)
    measured = derive_measurements(history.events, occurred_at)
    limit_decision = evaluate_limits(
        measured, caps, current_state=history.projection.state
    )
    if not limit_decision.allowed and command not in {"park", "cancel"}:
        return ProposalDecision(False, limit_decision.code, details={
            "preserve_state": limit_decision.preserve_state,
            "recommended_action": limit_decision.recommended_action,
            "breaches": [asdict(item) for item in limit_decision.breaches],
            "measured": measured,
            "caps": caps,
        })
    roles = _actor_roles(actor, mission, policy) if isinstance(actor, str) else set()
    role = None
    activation_system_event = event_type in {_ACTIVATION_ATTEMPTED, _ACTIVATION_CONSUMED}
    command_authority_roles = ("founder",) if activation_system_event else ("founder", "producer", "adversary")
    for candidate in command_authority_roles:
        if candidate not in roles:
            continue
        if activation_system_event and candidate == "founder":
            role = candidate
            break
        decision = authorize_transition(
            history.projection,
            {"type": event_type, "actor_role": candidate},
            policy,
        )
        if decision.allowed:
            role = candidate
            break
    if role is None:
        denied = authorize_transition(
            history.projection,
            {"type": event_type, "actor_role": next(iter(roles), None)},
            policy,
        )
        return ProposalDecision(False, denied.code)
    if activation_system_event:
        # The founder command authorizes intent; only the authenticated current
        # mission-command run may emit the system lifecycle event.
        if "founder" not in roles:
            return ProposalDecision(False, "ACTIVATION_AUTHORITY_INVALID")
        if not isinstance(activation_source_url, str) or not any(
            validate_activation_run(run, repository, activation_source_url)
            for run in actions_runs
        ):
            return ProposalDecision(False, "ACTIVATION_WORKFLOW_PROVENANCE_INVALID")
        role = "system"
    if event_type in {"mission.ready", "mission.claimed"} and validate_ready(dict(mission)):
        return ProposalDecision(False, "MISSION_NOT_READY")

    nonce = "github-comment-%s" % source.get("id")
    lease_events = [event for event in history.events if event.get("type") in {
        "mission.claimed", "lease.heartbeat", "mission.orphaned", "mission.released",
    }]
    if not isinstance(repository_lease_events, (list, tuple)) or any(
        not isinstance(event, Mapping) for event in repository_lease_events
    ):
        return ProposalDecision(False, "REPOSITORY_LEASE_EVENTS_INVALID")
    lease_events.extend(
        dict(event) for event in repository_lease_events
        if event.get("mission_id") != mission.get("mission_id")
        and event.get("type") in {
            "mission.claimed", "lease.heartbeat", "mission.orphaned", "mission.released",
        }
    )
    lifecycle = None
    if command == "claim":
        wall_clock_cap = caps["wall_clock_minutes"]
        expiry = _utc_text(
            _timestamp(occurred_at) + timedelta(minutes=min(15, wall_clock_cap))
        )
        lifecycle = claim_mission(
            lease_events,
            mission_id=mission["mission_id"], owner=actor, actor_role=role,
            now=occurred_at, expires_at=expiry, nonce=nonce,
            paths=mission["allowed_paths"],
            wall_clock_minutes=wall_clock_cap,
        )
    elif command == "heartbeat":
        requested_expiry = _timestamp(occurred_at) + timedelta(minutes=15)
        claims = [event for event in lease_events if event.get("type") == "mission.claimed"]
        if not claims:
            return ProposalDecision(False, "LEASE_NOT_FOUND")
        claim_details = claims[-1]["details"]
        absolute_cap = _timestamp(claim_details["lease_start"]) + timedelta(
            minutes=claim_details["wall_clock_cap_minutes"]
        )
        expiry = _utc_text(min(requested_expiry, absolute_cap))
        lifecycle = heartbeat_lease(
            lease_events,
            mission_id=mission["mission_id"], owner=actor,
            now=occurred_at, expires_at=expiry, nonce=arguments[0],
        )
    elif command == "release":
        lifecycle = release_mission(
            lease_events,
            mission_id=mission["mission_id"], owner=actor,
            now=occurred_at, nonce=arguments[0],
        )

    if lifecycle is not None:
        if not lifecycle.allowed:
            return ProposalDecision(False, lifecycle.code)
        proposals = list(lifecycle.events)
    else:
        if event_type in _ACTIVATION_EVENTS:
            if not isinstance(activation, Mapping):
                return ProposalDecision(False, "ACTIVATION_BINDING_REQUIRED")
            event_details = dict(activation)
            existing_authorization = next((item for item in history.events if item.get("type") == _ACTIVATION_AUTHORIZED), None)
            existing_attempt = next((item for item in history.events if item.get("type") == _ACTIVATION_ATTEMPTED), None)
            existing_consumption = next((item for item in history.events if item.get("type") == _ACTIVATION_CONSUMED), None)
            if event_type == _ACTIVATION_AUTHORIZED and existing_authorization:
                return ProposalDecision(False, "ACTIVATION_AUTHORIZATION_REPLAY")
            if event_type == _ACTIVATION_ATTEMPTED and (existing_attempt or existing_consumption):
                return ProposalDecision(False, "ACTIVATION_ATTEMPT_REPLAY")
            if event_type == _ACTIVATION_CONSUMED and existing_consumption:
                return ProposalDecision(False, "ACTIVATION_CONSUMPTION_REPLAY")
            if event_type != _ACTIVATION_AUTHORIZED:
                prior_auth = existing_authorization
                if prior_auth is None:
                    return ProposalDecision(False, "ACTIVATION_AUTHORIZATION_REQUIRED")
                if event_type == _ACTIVATION_CONSUMED and existing_attempt is None:
                    return ProposalDecision(False, "ACTIVATION_ATTEMPT_REQUIRED")
                event_details.update({
                    "authorization_event_hash": prior_auth.get("event_hash"),
                    "authorization_sequence": prior_auth.get("sequence"),
                    "consumer_identity": "github-actions[bot]/mission-command",
                    "consumed_at": occurred_at,
                    "consumption_result": "attempted" if event_type == _ACTIVATION_ATTEMPTED else "activated",
                    "post_consumption_state": "locked" if event_type == _ACTIVATION_ATTEMPTED else "active",
                    "attempt_event_hash": next((item.get("event_hash") for item in history.events if item.get("type") == _ACTIVATION_ATTEMPTED), ""),
                })
            try:
                build_activation_event(event_type, event_details, actor="system", actor_role=role,
                                       occurred_at=occurred_at, source_url=activation_source_url,
                                       authorization_event=next((item for item in history.events if item.get("type") == _ACTIVATION_AUTHORIZED), None),
                                       attempt_event=next((item for item in history.events if item.get("type") == _ACTIVATION_ATTEMPTED), None))
            except ValueError as error:
                return ProposalDecision(False, str(error))
        else:
            event_details = {"nonce": nonce}
        if event_type == "mission.ready":
            event_details["mission_sha256"] = content_sha256(mission)
        proposals = [{
            "mission_id": mission["mission_id"],
            "type": event_type,
            "actor": "system" if activation_system_event else actor,
            "actor_role": role,
            "occurred_at": occurred_at,
            "source_url": activation_source_url if activation_system_event else command_comment_url,
            "details": event_details,
        }]

    previous = history.events[-1]["event_hash"] if history.events else None
    audited = []
    for offset, proposal in enumerate(proposals, start=1):
        event = dict(proposal)
        event.update({
            "schema_version": "1.0.0",
            "sequence": len(history.events) + offset,
            "source_url": activation_source_url if activation_system_event else command_comment_url,
            "previous_event_hash": previous,
        })
        event["event_hash"] = content_sha256(event)
        audited.append(event)
        previous = event["event_hash"]
    valid, code = validate_event_chain(list(history.events) + audited)
    if not valid:
        return ProposalDecision(False, code)
    projected = project_state(list(history.events) + audited, policy)
    if projected.violations:
        return ProposalDecision(False, "EVENT_PROJECTION_INVALID")
    return ProposalDecision(True, "EVENT_PROPOSAL_AUTHORIZED", tuple(audited))


def _transition(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Emit an EOS event proposal without appending it")
    parser.add_argument("--mission-id", required=True)
    parser.add_argument("--event-type", required=True)
    parser.add_argument("--actor", required=True)
    parser.add_argument("--actor-role", required=True, choices=("producer", "adversary", "founder", "system"))
    parser.add_argument("--occurred-at", required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--nonce", required=True)
    parser.add_argument("--details", default="{}")
    arguments = parser.parse_args(argv)
    try:
        details = json.loads(arguments.details)
        proposal = propose_event(
            mission_id=arguments.mission_id, event_type=arguments.event_type,
            actor=arguments.actor, actor_role=arguments.actor_role,
            occurred_at=arguments.occurred_at, source_url=arguments.source_url,
            nonce=arguments.nonce, details=details,
        )
    except (ValueError, TypeError, json.JSONDecodeError) as error:
        parser.error(str(error))
    json.dump(proposal, sys.stdout, sort_keys=True, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


def _validate_lease(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate and propose a lease heartbeat")
    parser.add_argument("--events", required=True)
    parser.add_argument("--mission-id", required=True)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--now", required=True)
    parser.add_argument("--expires-at", required=True)
    parser.add_argument("--nonce", required=True)
    arguments = parser.parse_args(argv)
    try:
        with open(arguments.events, encoding="utf-8") as stream:
            events = json.load(stream)
        decision = heartbeat_lease(
            events, mission_id=arguments.mission_id, owner=arguments.owner,
            now=arguments.now, expires_at=arguments.expires_at,
            nonce=arguments.nonce,
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    json.dump({
        "allowed": decision.allowed, "code": decision.code,
        "preserve_state": decision.preserve_state, "event": decision.event,
    }, sys.stdout, sort_keys=True, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0 if decision.allowed else 1


def _recover_orphans(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Find expired leases without mutating mission state")
    parser.add_argument("--events", required=True)
    parser.add_argument("--now", required=True)
    parser.add_argument("--propose", action="store_true", help="mark output for adapter review; never appends")
    arguments = parser.parse_args(argv)
    try:
        with open(arguments.events, encoding="utf-8") as stream:
            events = json.load(stream)
        orphans = find_orphans(events, now=arguments.now)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    json.dump({
        "dry_run": not arguments.propose,
        "mutation_performed": False,
        "orphans": [asdict(orphan) for orphan in orphans],
    }, sys.stdout, sort_keys=True, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


def _authenticate_history(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Authenticate a complete GitHub mission event history")
    parser.add_argument("--comments", required=True)
    parser.add_argument("--mission", required=True)
    parser.add_argument("--policy", required=True)
    parser.add_argument("--runs", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--events-output")
    arguments = parser.parse_args(argv)
    try:
        with open(arguments.comments, encoding="utf-8") as stream:
            comments_value = json.load(stream)
        comments = flatten_paginated(comments_value) if comments_value and isinstance(comments_value[0], list) else comments_value
        with open(arguments.mission, encoding="utf-8") as stream:
            mission = json.load(stream)
        with open(arguments.policy, encoding="utf-8") as stream:
            policy = json.load(stream)
        with open(arguments.runs, encoding="utf-8") as stream:
            actions_runs = json.load(stream)
        decision = authenticate_event_history(
            comments, mission, policy, repository=arguments.repository,
            actions_runs=actions_runs,
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    if decision.allowed and arguments.events_output:
        with open(arguments.events_output, "w", encoding="utf-8") as stream:
            json.dump(list(decision.events), stream, sort_keys=True, separators=(",", ":"))
            stream.write("\n")
    json.dump({
        "allowed": decision.allowed,
        "code": decision.code,
        "state": decision.projection.state,
    }, sys.stdout, sort_keys=True, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0 if decision.allowed else 1


def _authenticate_repository_leases(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Authenticate parsed open-mission histories and emit repository leases"
    )
    parser.add_argument("--candidates", required=True)
    parser.add_argument("--policy", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--events-output", required=True)
    arguments = parser.parse_args(argv)
    try:
        with open(arguments.candidates, encoding="utf-8") as stream:
            candidates = json.load(stream)
        with open(arguments.policy, encoding="utf-8") as stream:
            policy = json.load(stream)
        decision = authenticate_repository_lease_events(
            candidates, policy, repository=arguments.repository
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    if decision.allowed:
        with open(arguments.events_output, "w", encoding="utf-8") as stream:
            json.dump(list(decision.events), stream, sort_keys=True, separators=(",", ":"))
            stream.write("\n")
    json.dump({
        "allowed": decision.allowed, "code": decision.code,
        "details": decision.details,
    }, sys.stdout, sort_keys=True, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0 if decision.allowed else 1


def _propose_command(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Authorize one GitHub /eos command proposal")
    parser.add_argument("--comments", required=True)
    parser.add_argument("--mission", required=True)
    parser.add_argument("--policy", required=True)
    parser.add_argument("--runs", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--command-comment-url", required=True)
    parser.add_argument("--body-output", required=True)
    parser.add_argument("--repository-leases")
    parser.add_argument("--activation")
    parser.add_argument("--activation-source-url")
    arguments = parser.parse_args(argv)
    try:
        with open(arguments.comments, encoding="utf-8") as stream:
            comments_value = json.load(stream)
        comments = flatten_paginated(comments_value) if comments_value and isinstance(comments_value[0], list) else comments_value
        with open(arguments.mission, encoding="utf-8") as stream:
            mission = json.load(stream)
        with open(arguments.policy, encoding="utf-8") as stream:
            policy = json.load(stream)
        with open(arguments.runs, encoding="utf-8") as stream:
            actions_runs = json.load(stream)
        if arguments.repository_leases:
            with open(arguments.repository_leases, encoding="utf-8") as stream:
                repository_lease_events = json.load(stream)
        else:
            repository_lease_events = []
        activation = None
        if arguments.activation:
            with open(arguments.activation, encoding="utf-8") as stream:
                activation = json.load(stream)
        decision = authorize_command_proposal(
            comments, mission, policy, repository=arguments.repository,
            command_comment_url=arguments.command_comment_url,
            actions_runs=actions_runs,
            repository_lease_events=repository_lease_events,
            activation=activation,
            activation_source_url=arguments.activation_source_url,
        )
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
    if not decision.allowed:
        print(decision.code, file=sys.stderr)
        return 1
    body = "\n".join(
        "<!-- EOS:EVENT:BEGIN -->\n%s\n<!-- EOS:EVENT:END -->"
        % json.dumps(event, sort_keys=True, separators=(",", ":"))
        for event in decision.events
    )
    with open(arguments.body_output, "w", encoding="utf-8") as stream:
        stream.write(body + "\n")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments:
        raise SystemExit("expected transition, validate-lease, recover-orphans, authenticate-event-history, authenticate-repository-leases, or propose-command")
    command, rest = arguments[0], arguments[1:]
    if command == "transition":
        return _transition(rest)
    if command == "validate-lease":
        return _validate_lease(rest)
    if command == "recover-orphans":
        return _recover_orphans(rest)
    if command == "authenticate-event-history":
        return _authenticate_history(rest)
    if command == "authenticate-repository-leases":
        return _authenticate_repository_leases(rest)
    if command == "propose-command":
        return _propose_command(rest)
    raise SystemExit("unknown command: %s" % command)


if __name__ == "__main__":
    raise SystemExit(main())
