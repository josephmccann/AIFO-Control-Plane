"""Frozen-artifact enforcement over complete git and authenticated evidence."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import re
import subprocess
from typing import Any, Dict, Mapping, Sequence

from .canonical import content_sha256
from .consumption import ConsumptionBinding, consume_once
from .records import VerifiedRecordEnvelope, verify_record_envelope
from .schema import validate_document
from .scope import PathInputError, normalize_paths, path_matches


_ACTIONS = frozenset((
    "write", "merge", "deploy", "cloud_mutation", "secrets", "customer_data",
    "spend", "cutover",
))
_EXCEPTION_FIELDS = frozenset((
    "exception_id", "declaration_id", "repository", "mission_id", "pull_request",
    "head_sha", "paths", "action", "issuer", "issuer_role", "starts_at",
    "expires_at", "status", "pinned_commit", "sealed_manifest_sha256",
    "protected_version", "release_condition", "one_shot", "nonce", "source",
))
_RELEASE_FIELDS = frozenset((
    "record_id", "repository", "mission_id", "pull_request", "head_sha",
    "condition", "issuer", "expires_at", "source",
))
_RESERVATION_FIELDS = frozenset((
    "reservation_id", "exception_id", "repository", "mission_id",
    "pull_request", "head_sha", "status", "nonce", "created_at",
    "expires_at", "source",
))


@dataclass(frozen=True)
class FrozenDecision:
    allowed: bool
    code: str
    declaration_id: str = ""
    exception_id: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


def _time(value: str) -> datetime:
    if not isinstance(value, str) or re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z", value
    ) is None:
        raise ValueError("timestamp must be strict UTC RFC3339")
    return datetime.fromisoformat(value[:-1] + "+00:00").astimezone(timezone.utc)


def _decision(
    allowed: bool, code: str, declaration: Mapping[str, Any] = None,
    exception: Mapping[str, Any] = None,
) -> FrozenDecision:
    return FrozenDecision(
        allowed, code,
        declaration.get("declaration_id", "") if isinstance(declaration, Mapping) else "",
        exception.get("exception_id", "") if isinstance(exception, Mapping) else "",
    )


def _declaration_valid(declaration: Mapping[str, Any], repository: str) -> bool:
    try:
        if validate_document("frozen-path", dict(declaration)):
            return False
        paths = normalize_paths(declaration.get("paths", []), allow_glob=True)
        for pattern in paths:
            path_matches("eos-glob-validation", pattern)
        expiry = declaration.get("expires_at")
        if expiry is not None:
            _time(expiry)
        pinned = declaration.get("pinned_commit")
        sealed = declaration.get("sealed_manifest_sha256")
        version = declaration.get("protected_version")
        return bool(paths) and all((
            declaration.get("repository") == repository,
            declaration.get("exception_authority") == "founder",
            isinstance(declaration.get("release_condition"), str) and bool(declaration.get("release_condition")),
            isinstance(declaration.get("one_shot"), bool),
            pinned is None or (isinstance(pinned, str) and re.fullmatch(r"[0-9a-f]{40}", pinned) is not None),
            sealed is None or (isinstance(sealed, str) and re.fullmatch(r"[0-9a-f]{64}", sealed) is not None),
            version is None or (isinstance(version, str) and bool(version)),
        ))
    except (PathInputError, TypeError, ValueError):
        return False


def _git_files(value: Any) -> Dict[str, str]:
    if not isinstance(value, Mapping):
        raise ValueError("git file evidence must be an object")
    normalized = {}
    for path, digest in value.items():
        clean = normalize_paths([path])[0]
        if clean in normalized or not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise ValueError("git file evidence is invalid")
        normalized[clean] = digest
    return normalized


def _validate_git_evidence(
    evidence: Any, *, repository: str, head_sha: str, changed_files: Sequence[str],
) -> tuple:
    if not isinstance(evidence, Mapping) or evidence.get("complete") is not True:
        raise ValueError("git evidence is incomplete")
    base_sha = evidence.get("base_sha")
    if (
        evidence.get("repository") != repository
        or evidence.get("head_sha") != head_sha
        or not isinstance(base_sha, str) or re.fullmatch(r"[0-9a-f]{40}", base_sha) is None
        or re.fullmatch(r"[0-9a-f]{40}", str(head_sha)) is None
    ):
        raise ValueError("git evidence identity is invalid")
    base_files = _git_files(evidence.get("base_files"))
    head_files = _git_files(evidence.get("head_files"))
    evidence_changed = normalize_paths(evidence.get("changed_files"))
    derived_changed = tuple(sorted(
        path for path in set(base_files) | set(head_files)
        if base_files.get(path) != head_files.get(path)
    ))
    expected_changed = tuple(sorted(changed_files))
    if (
        tuple(sorted(evidence_changed)) != expected_changed
        or derived_changed != expected_changed
        or len(evidence_changed) != len(set(evidence_changed))
    ):
        raise ValueError("git evidence changed paths are incomplete")
    return base_sha, base_files, head_files


def derive_git_evidence(
    repository: str, base_sha: str, head_sha: str, *, worktree: str = ".",
) -> Dict[str, Any]:
    """Derive complete evidence from exact commits in the local Git object DB."""

    if (
        not isinstance(repository, str) or not repository
        or not isinstance(base_sha, str) or re.fullmatch(r"[0-9a-f]{40}", base_sha) is None
        or not isinstance(head_sha, str) or re.fullmatch(r"[0-9a-f]{40}", head_sha) is None
        or not isinstance(worktree, str) or not worktree
    ):
        raise ValueError("git identity is invalid")

    def output(arguments: Sequence[str]) -> bytes:
        return subprocess.check_output(
            ["git", *arguments], cwd=worktree, stderr=subprocess.DEVNULL,
        )

    for revision in (base_sha, head_sha):
        resolved = output(["rev-parse", "--verify", revision + "^{commit}"]).decode().strip()
        if resolved != revision:
            raise ValueError("git commit does not resolve exactly")
    output(["merge-base", base_sha, head_sha])

    changed_raw = output(["diff", "--name-only", "-z", "--no-renames", base_sha, head_sha, "--"])
    changed = [item.decode("utf-8") for item in changed_raw.split(b"\0") if item]
    normalized_changed = normalize_paths(changed)
    if len(normalized_changed) != len(set(normalized_changed)):
        raise ValueError("git diff contains duplicate paths")

    def tree(revision: str) -> Dict[str, str]:
        entries = output(["ls-tree", "-r", "-z", "--full-tree", revision]).split(b"\0")
        files: Dict[str, str] = {}
        for entry in entries:
            if not entry:
                continue
            try:
                metadata, raw_path = entry.split(b"\t", 1)
                _mode, object_type, object_id = metadata.decode("ascii").split(" ")
                path = normalize_paths([raw_path.decode("utf-8")])[0]
            except (UnicodeDecodeError, ValueError, PathInputError) as error:
                raise ValueError("git tree entry is invalid") from error
            if path in files:
                raise ValueError("git tree contains duplicate paths")
            if object_type == "blob":
                content = output(["cat-file", "blob", object_id])
            elif object_type == "commit":
                content = ("gitlink:" + object_id).encode("ascii")
            else:
                raise ValueError("git tree object type is unsupported")
            files[path] = hashlib.sha256(content).hexdigest()
        return files

    return {
        "repository": repository,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "complete": True,
        "changed_files": list(normalized_changed),
        "base_files": tree(base_sha),
        "head_files": tree(head_sha),
    }


def _manifest_sha256(patterns: Sequence[str], files: Mapping[str, str]) -> str:
    manifest = {
        path: digest for path, digest in files.items()
        if any(path_matches(path, pattern) for pattern in patterns)
    }
    encoded = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _release_allowed(
    declaration: Mapping[str, Any], records: Sequence[Mapping[str, Any]], *,
    mission_id: str, repository: str, pull_request: int, head_sha: str,
    current: datetime, founders: set,
    verified_envelopes: Sequence[VerifiedRecordEnvelope],
) -> bool:
    for record in records:
        if not isinstance(record, Mapping) or set(record) != _RELEASE_FIELDS:
            continue
        try:
            expires = _time(record.get("expires_at"))
        except (TypeError, ValueError):
            continue
        issuer = record.get("issuer")
        if (
            isinstance(record.get("record_id"), str) and record.get("record_id")
            and record.get("condition") == declaration.get("release_condition")
            and record.get("repository") == repository
            and record.get("mission_id") == mission_id
            and record.get("pull_request") == pull_request
            and record.get("head_sha") == head_sha
            and issuer in founders and current < expires
            and verify_record_envelope(
                record, "frozen_release", verified_envelopes,
                repository=repository, actor=issuer,
            )
        ):
            return True
    return False


def _reserved(
    exception: Mapping[str, Any], reservations: Sequence[Mapping[str, Any]], *,
    mission_id: str, repository: str, pull_request: int, head_sha: str,
    current: datetime, verified_envelopes: Sequence[VerifiedRecordEnvelope],
) -> bool:
    matches = []
    for reservation in reservations:
        if not isinstance(reservation, Mapping) or set(reservation) != _RESERVATION_FIELDS:
            continue
        try:
            created, expires = _time(reservation.get("created_at")), _time(reservation.get("expires_at"))
        except (TypeError, ValueError):
            continue
        if (
            isinstance(reservation.get("reservation_id"), str) and reservation.get("reservation_id")
            and reservation.get("exception_id") == exception.get("exception_id")
            and reservation.get("nonce") == exception.get("nonce")
            and reservation.get("repository") == repository
            and reservation.get("mission_id") == mission_id
            and reservation.get("pull_request") == pull_request
            and reservation.get("head_sha") == head_sha
            and reservation.get("status") == "reserved"
            and created <= current < expires
            and isinstance(reservation.get("source"), Mapping)
            and verify_record_envelope(
                reservation, "frozen_reservation", verified_envelopes,
                repository=repository, actor=reservation.get("source", {}).get("actor"),
            )
        ):
            matches.append(reservation)
    return len(matches) == 1


def validate_frozen_changes(
    mission: Mapping[str, Any], policy: Mapping[str, Any], changed_files: Sequence[str],
    declarations: Sequence[Mapping[str, Any]], exceptions: Sequence[Mapping[str, Any]], *,
    repository: str, pull_request: int, head_sha: str, now: str, action: str,
    git_evidence: Mapping[str, Any],
    verified_envelopes: Sequence[VerifiedRecordEnvelope],
    release_records: Sequence[Mapping[str, Any]],
    durable_reservations: Sequence[Mapping[str, Any]],
    consumption_store: str = "",
) -> FrozenDecision:
    """Deny frozen writes unless exact authenticated evidence and reservation exist."""

    if not isinstance(mission, Mapping) or validate_document("mission", dict(mission)):
        return _decision(False, "FROZEN_MISSION_INVALID")
    if not isinstance(policy, Mapping) or validate_document("repository-policy", dict(policy)):
        return _decision(False, "FROZEN_POLICY_INVALID")
    collections = (
        declarations, exceptions, verified_envelopes, release_records,
        durable_reservations,
    )
    if (
        any(not isinstance(value, (list, tuple)) for value in collections)
        or any(not isinstance(item, VerifiedRecordEnvelope) for item in verified_envelopes)
        or not isinstance(consumption_store, str)
        or not isinstance(repository, str) or policy.get("repository") != repository
        or mission.get("repository") != repository
        or not isinstance(pull_request, int) or isinstance(pull_request, bool) or pull_request < 1
        or not isinstance(head_sha, str) or re.fullmatch(r"[0-9a-f]{40}", head_sha) is None
        or action not in _ACTIONS
    ):
        return _decision(False, "FROZEN_INPUT_INVALID")
    if any(not isinstance(item, Mapping) for item in exceptions):
        return _decision(False, "FROZEN_EXCEPTION_INVALID")
    if (
        any(not isinstance(item, Mapping) for item in release_records)
        or any(not isinstance(item, Mapping) for item in durable_reservations)
    ):
        return _decision(False, "FROZEN_INPUT_INVALID")
    try:
        changed = normalize_paths(changed_files)
        current = _time(now)
    except (PathInputError, TypeError, ValueError):
        return _decision(False, "FROZEN_INPUT_INVALID")

    affected = []
    for declaration in declarations:
        if not isinstance(declaration, Mapping) or not _declaration_valid(declaration, repository):
            return _decision(False, "FROZEN_DECLARATION_INVALID", declaration)
        try:
            patterns = normalize_paths(declaration.get("paths", []), allow_glob=True)
            expiry = declaration.get("expires_at")
            if expiry is not None and current >= _time(expiry):
                continue
            touched = tuple(path for path in changed if any(path_matches(path, pattern) for pattern in patterns))
        except (PathInputError, TypeError, ValueError):
            return _decision(False, "FROZEN_DECLARATION_INVALID", declaration)
        if touched:
            affected.append((declaration, patterns, touched))

    try:
        base_sha, base_files, _ = _validate_git_evidence(
            git_evidence, repository=repository, head_sha=head_sha, changed_files=changed,
        )
    except (PathInputError, TypeError, ValueError):
        return _decision(False, "FROZEN_GIT_EVIDENCE_INCOMPLETE")
    if not affected:
        return _decision(True, "FROZEN_PATHS_UNTOUCHED")

    exception_ids = [item.get("exception_id") for item in exceptions if isinstance(item, Mapping)]
    nonces = [item.get("nonce") for item in exceptions if isinstance(item, Mapping)]
    if (
        all(isinstance(value, str) for value in exception_ids + nonces)
        and (len(exception_ids) != len(set(exception_ids)) or len(nonces) != len(set(nonces)))
    ):
        return _decision(False, "FROZEN_EXCEPTION_DUPLICATE")

    founders = set(policy["founder_identities"])
    consumption_bindings = []
    last_exception = None
    for declaration, patterns, touched in affected:
        if declaration.get("pinned_commit") is not None and declaration.get("pinned_commit") != base_sha:
            return _decision(False, "FROZEN_PIN_MISMATCH", declaration)
        if (
            declaration.get("sealed_manifest_sha256") is not None
            and declaration.get("sealed_manifest_sha256") != _manifest_sha256(patterns, base_files)
        ):
            return _decision(False, "FROZEN_MANIFEST_MISMATCH", declaration)
        matching = [
            item for item in exceptions
            if isinstance(item, Mapping) and item.get("declaration_id") == declaration.get("declaration_id")
        ]
        if not matching:
            return _decision(False, "FROZEN_WRITE_DENIED", declaration)
        last = _decision(False, "FROZEN_WRITE_DENIED", declaration)
        for exception in matching:
            if set(exception) != _EXCEPTION_FIELDS:
                last = _decision(False, "FROZEN_EXCEPTION_INVALID", declaration, exception)
                continue
            try:
                paths = normalize_paths(exception.get("paths", []))
                starts, expires = _time(exception.get("starts_at")), _time(exception.get("expires_at"))
                if (
                    starts >= expires
                    or not isinstance(exception.get("exception_id"), str) or not exception.get("exception_id")
                    or not isinstance(exception.get("nonce"), str) or not exception.get("nonce")
                    or not isinstance(exception.get("issuer"), str) or not exception.get("issuer")
                    or not isinstance(exception.get("pull_request"), int) or isinstance(exception.get("pull_request"), bool)
                    or re.fullmatch(r"[0-9a-f]{40}", str(exception.get("head_sha", ""))) is None
                    or not isinstance(exception.get("one_shot"), bool)
                ):
                    raise ValueError("invalid exception")
            except (PathInputError, TypeError, ValueError):
                last = _decision(False, "FROZEN_EXCEPTION_INVALID", declaration, exception)
                continue
            issuer = exception.get("issuer")
            checks = (
                (exception.get("repository") != repository, "FROZEN_EXCEPTION_REPOSITORY_MISMATCH"),
                (exception.get("mission_id") != mission.get("mission_id"), "FROZEN_EXCEPTION_MISSION_MISMATCH"),
                (exception.get("pull_request") != pull_request, "FROZEN_EXCEPTION_PR_MISMATCH"),
                (exception.get("head_sha") != head_sha, "FROZEN_EXCEPTION_HEAD_MISMATCH"),
                (set(paths) != set(touched) or len(paths) != len(touched), "FROZEN_EXCEPTION_PATH_MISMATCH"),
                (exception.get("action") != action, "FROZEN_EXCEPTION_ACTION_MISMATCH"),
                (issuer not in founders or exception.get("issuer_role") != "founder", "FROZEN_EXCEPTION_ISSUER_DENIED"),
                (exception.get("status") != "active", "FROZEN_EXCEPTION_INACTIVE"),
                (current < starts, "FROZEN_EXCEPTION_NOT_STARTED"),
                (current >= expires, "FROZEN_EXCEPTION_EXPIRED"),
                (exception.get("pinned_commit") != declaration.get("pinned_commit"), "FROZEN_PIN_MISMATCH"),
                (exception.get("sealed_manifest_sha256") != declaration.get("sealed_manifest_sha256"), "FROZEN_MANIFEST_MISMATCH"),
                (exception.get("protected_version") != declaration.get("protected_version"), "FROZEN_VERSION_MISMATCH"),
                (exception.get("release_condition") != declaration.get("release_condition"), "FROZEN_RELEASE_CONDITION_MISMATCH"),
                (exception.get("one_shot") is not declaration.get("one_shot"), "FROZEN_EXCEPTION_ONE_SHOT_MISMATCH"),
                (
                    not verify_record_envelope(
                        exception, "frozen_exception", verified_envelopes,
                        repository=repository, actor=issuer,
                    ),
                    "FROZEN_EXCEPTION_SOURCE_UNAUTHENTICATED",
                ),
                (
                    not _release_allowed(
                        declaration, release_records,
                        mission_id=mission["mission_id"], repository=repository,
                        pull_request=pull_request, head_sha=head_sha, current=current,
                        founders=founders, verified_envelopes=verified_envelopes,
                    ),
                    "FROZEN_RELEASE_CONDITION_UNMET",
                ),
                (
                    not _reserved(
                        exception, durable_reservations,
                        mission_id=mission["mission_id"], repository=repository,
                        pull_request=pull_request, head_sha=head_sha,
                        current=current,
                        verified_envelopes=verified_envelopes,
                    ),
                    "FROZEN_EXCEPTION_RESERVATION_REQUIRED",
                ),
            )
            failed = next((code for condition, code in checks if condition), None)
            if failed:
                last = _decision(False, failed, declaration, exception)
                continue
            payload = dict(exception)
            del payload["source"]
            consumption_bindings.append(ConsumptionBinding(
                "frozen_exception", exception["exception_id"], exception["nonce"],
                content_sha256(payload),
            ))
            last_exception = exception
            last = _decision(True, "FROZEN_EXCEPTION_ALLOWED", declaration, exception)
            break
        if not last.allowed:
            return last
    if not consume_once(consumption_store, consumption_bindings):
        return _decision(
            False, "FROZEN_EXCEPTION_CONSUMED", affected[-1][0], last_exception,
        )
    return _decision(
        True, "FROZEN_EXCEPTION_ALLOWED", affected[-1][0], last_exception,
    )
