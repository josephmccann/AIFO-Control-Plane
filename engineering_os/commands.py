"""Stable command parsing and immutable event-proposal construction."""

import argparse
from dataclasses import asdict
import json
import re
import sys
from typing import Any, Dict, Optional, Sequence, Tuple

from .canonical import content_sha256
from .lease import _rfc3339, find_orphans, heartbeat_lease
from .schema import validate_document


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
}


def parse_command(text: str) -> Optional[Tuple[str, Tuple[str, ...]]]:
    """Parse only a complete, single-line, lower-case ``/eos`` command."""

    if not isinstance(text, str) or re.fullmatch(r"/eos [a-z]+(?: [A-Za-z0-9._:-]+)?", text) is None:
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


def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if not arguments:
        raise SystemExit("expected transition, validate-lease, or recover-orphans")
    command, rest = arguments[0], arguments[1:]
    if command == "transition":
        return _transition(rest)
    if command == "validate-lease":
        return _validate_lease(rest)
    if command == "recover-orphans":
        return _recover_orphans(rest)
    raise SystemExit("unknown command: %s" % command)


if __name__ == "__main__":
    raise SystemExit(main())
