import copy
import hashlib
import json
import os
import unittest
from pathlib import Path

from engineering_os.frozen import validate_frozen_changes
from tests.engineering_os.test_risk import mission, policy


ROOT = Path(__file__).resolve().parents[2]
FROZEN = ROOT / "tests" / "engineering_os" / "fixtures" / "frozen-declarations"
HEAD = "2222222222222222222222222222222222222222"
BASE = "1111111111111111111111111111111111111111"
CONTENT_HASH = "b" * 64


def declaration():
    item = json.loads((FROZEN / "methodology/signal-engine.json").read_text(encoding="utf-8"))
    item["pinned_commit"] = BASE
    manifest = json.dumps(
        {"src/engine/model.py": CONTENT_HASH}, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    item["sealed_manifest_sha256"] = hashlib.sha256(manifest).hexdigest()
    return item


def source():
    return {
        "provider": "github", "repository": "acme/widgets", "issue_number": 123,
        "comment_id": 9002, "url": "https://github.com/acme/widgets/issues/123#issuecomment-9002",
        "actor": "founder", "created_at": "2026-07-15T00:00:00Z",
        "content_sha256": "c" * 64,
    }


def exception():
    item = declaration()
    return {
        "exception_id": "exception-1",
        "declaration_id": item["declaration_id"],
        "repository": "acme/widgets",
        "mission_id": "mission-123",
        "pull_request": 42,
        "head_sha": HEAD,
        "paths": ["src/engine/model.py"],
        "action": "write",
        "issuer": "founder",
        "issuer_role": "founder",
        "starts_at": "2026-07-15T00:00:00Z",
        "expires_at": "2026-07-16T00:00:00Z",
        "status": "active",
        "pinned_commit": item["pinned_commit"],
        "sealed_manifest_sha256": item["sealed_manifest_sha256"],
        "protected_version": item["protected_version"],
        "release_condition": item["release_condition"],
        "one_shot": True,
        "nonce": "frozen-exception-nonce-1",
        "source": source(),
    }


def git_evidence(**updates):
    value = {
        "repository": "acme/widgets",
        "base_sha": BASE,
        "head_sha": HEAD,
        "complete": True,
        "changed_files": ["src/engine/model.py"],
        "base_files": {"src/engine/model.py": CONTENT_HASH},
        "head_files": {"src/engine/model.py": "d" * 64},
    }
    value.update(updates)
    return value


def release_record():
    return {
        "record_id": "release-1", "repository": "acme/widgets",
        "mission_id": "mission-123", "pull_request": 42, "head_sha": HEAD,
        "condition": "founder-approved-methodology-release", "issuer": "founder",
        "expires_at": "2026-07-16T00:00:00Z", "source": source(),
    }


def reservation():
    return {
        "reservation_id": "reservation-1", "exception_id": "exception-1",
        "repository": "acme/widgets", "mission_id": "mission-123",
        "pull_request": 42, "head_sha": HEAD, "status": "reserved",
        "nonce": "frozen-exception-nonce-1",
        "created_at": "2026-07-15T11:00:00Z",
        "expires_at": "2026-07-15T13:00:00Z",
        "source": source(),
    }


def decide(exceptions=(), **updates):
    context = {
        "repository": "acme/widgets",
        "pull_request": 42,
        "head_sha": HEAD,
        "now": "2026-07-15T12:00:00Z",
        "action": "write",
        "git_evidence": git_evidence(),
        "authenticated_sources": [source()],
        "authenticated_release_records": [release_record()],
        "durable_reservations": [reservation()],
        "consumed_exception_ids": [],
        "consumed_nonces": [],
    }
    context.update(updates)
    return validate_frozen_changes(
        mission("Tier 2"), policy(), ["src/engine/model.py"], [declaration()], list(exceptions), **context
    )


class FrozenTests(unittest.TestCase):
    def test_frozen_write_is_denied_without_an_exception(self):
        result = decide()
        self.assertEqual((result.allowed, result.code), (False, "FROZEN_WRITE_DENIED"))

    def test_valid_exception_requires_exact_mission_pr_head_path_and_action(self):
        self.assertEqual((decide([exception()]).allowed, decide([exception()]).code), (True, "FROZEN_EXCEPTION_ALLOWED"))
        mutations = (
            ("mission_id", "mission-other", "FROZEN_EXCEPTION_MISSION_MISMATCH"),
            ("pull_request", 43, "FROZEN_EXCEPTION_PR_MISMATCH"),
            ("head_sha", "3" * 40, "FROZEN_EXCEPTION_HEAD_MISMATCH"),
            ("paths", ["src/engine/other.py"], "FROZEN_EXCEPTION_PATH_MISMATCH"),
            ("action", "merge", "FROZEN_EXCEPTION_ACTION_MISMATCH"),
        )
        for field, value, code in mutations:
            with self.subTest(field=field):
                candidate = exception(); candidate[field] = value
                self.assertEqual(decide([candidate]).code, code)

    def test_exception_requires_exact_base_policy_founder_and_authenticated_source(self):
        outsider = exception(); outsider["issuer"] = "outsider"; outsider["source"]["actor"] = "outsider"
        self.assertEqual(decide([outsider], authenticated_sources=[outsider["source"]]).code, "FROZEN_EXCEPTION_ISSUER_DENIED")
        self.assertEqual(decide([exception()], authenticated_sources=[]).code, "FROZEN_EXCEPTION_SOURCE_UNAUTHENTICATED")

    def test_stale_expired_or_wrong_sha_exception_is_denied(self):
        stale = exception(); stale["status"] = "revoked"
        expired = exception(); expired["expires_at"] = "2026-07-15T12:00:00Z"
        wrong_sha = exception(); wrong_sha["head_sha"] = "f" * 40
        self.assertEqual(decide([stale]).code, "FROZEN_EXCEPTION_INACTIVE")
        self.assertEqual(decide([expired]).code, "FROZEN_EXCEPTION_EXPIRED")
        self.assertEqual(decide([wrong_sha]).code, "FROZEN_EXCEPTION_HEAD_MISMATCH")

        incomplete = exception(); incomplete.pop("exception_id")
        self.assertEqual(decide([incomplete]).code, "FROZEN_EXCEPTION_INVALID")

    def test_pin_and_manifest_are_derived_from_complete_git_evidence(self):
        self.assertEqual(decide([exception()], git_evidence=git_evidence(base_sha="9" * 40)).code, "FROZEN_PIN_MISMATCH")
        self.assertEqual(decide([exception()], git_evidence=git_evidence(base_files={"src/engine/model.py": "9" * 64})).code, "FROZEN_MANIFEST_MISMATCH")
        self.assertEqual(decide([exception()], git_evidence=git_evidence(complete=False)).code, "FROZEN_GIT_EVIDENCE_INCOMPLETE")
        self.assertEqual(decide([exception()], git_evidence=git_evidence(changed_files=[])).code, "FROZEN_GIT_EVIDENCE_INCOMPLETE")

    def test_protected_version_must_match_exact_exception(self):
        candidate = exception(); candidate["protected_version"] = "2.0.0"
        self.assertEqual(decide([candidate]).code, "FROZEN_VERSION_MISMATCH")

    def test_release_condition_and_one_shot_marker_are_enforced(self):
        self.assertEqual(decide([exception()], authenticated_release_records=[]).code, "FROZEN_RELEASE_CONDITION_UNMET")
        self.assertEqual(decide([exception()], durable_reservations=[]).code, "FROZEN_EXCEPTION_RESERVATION_REQUIRED")
        incomplete_reservation = reservation(); incomplete_reservation.pop("expires_at")
        self.assertEqual(decide([exception()], durable_reservations=[incomplete_reservation]).code, "FROZEN_EXCEPTION_RESERVATION_REQUIRED")
        self.assertEqual(decide([exception()], consumed_exception_ids=["exception-1"]).code, "FROZEN_EXCEPTION_CONSUMED")
        self.assertEqual(decide([exception()], consumed_nonces=["frozen-exception-nonce-1"]).code, "FROZEN_EXCEPTION_CONSUMED")
        candidate = exception(); candidate["one_shot"] = False
        self.assertEqual(decide([candidate]).code, "FROZEN_EXCEPTION_ONE_SHOT_MISMATCH")

    def test_unrelated_changes_pass_and_malformed_paths_fail_closed(self):
        result = validate_frozen_changes(
            mission("Tier 1"), policy(), ["src/other.py"], [declaration()], [],
            repository="acme/widgets", pull_request=42, head_sha=HEAD,
            now="2026-07-15T12:00:00Z", action="write",
            git_evidence=git_evidence(
                changed_files=["src/other.py"],
                head_files={"src/engine/model.py": CONTENT_HASH, "src/other.py": "d" * 64},
                base_files={"src/engine/model.py": CONTENT_HASH},
            ), authenticated_sources=[], authenticated_release_records=[],
            durable_reservations=[], consumed_exception_ids=[], consumed_nonces=[],
        )
        self.assertEqual((result.allowed, result.code), (True, "FROZEN_PATHS_UNTOUCHED"))
        malformed = copy.deepcopy(declaration()); malformed["paths"] = ["../escape"]
        denied = validate_frozen_changes(
            mission("Tier 1"), policy(), ["src/other.py"], [malformed], [],
            repository="acme/widgets", pull_request=42, head_sha=HEAD,
            now="2026-07-15T12:00:00Z", action="write",
            git_evidence=git_evidence(), authenticated_sources=[], authenticated_release_records=[],
            durable_reservations=[], consumed_exception_ids=[], consumed_nonces=[],
        )
        self.assertEqual(denied.code, "FROZEN_DECLARATION_INVALID")
        incomplete = copy.deepcopy(declaration()); incomplete.pop("schema_version")
        denied = validate_frozen_changes(
            mission("Tier 1"), policy(), ["src/other.py"], [incomplete], [],
            repository="acme/widgets", pull_request=42, head_sha=HEAD,
            now="2026-07-15T12:00:00Z", action="write",
            git_evidence=git_evidence(), authenticated_sources=[], authenticated_release_records=[],
            durable_reservations=[], consumed_exception_ids=[], consumed_nonces=[],
        )
        self.assertEqual(denied.code, "FROZEN_DECLARATION_INVALID")

    def test_malformed_structures_boolean_pr_and_unknown_action_fail_stably(self):
        base = dict(
            repository="acme/widgets", head_sha=HEAD, now="2026-07-15T12:00:00Z",
            git_evidence=git_evidence(), authenticated_sources=[], authenticated_release_records=[],
            durable_reservations=[], consumed_exception_ids=[], consumed_nonces=[],
        )
        for field, value in (("declarations", None), ("exceptions", None)):
            args = {"declarations": [declaration()], "exceptions": []}
            args[field] = value
            with self.subTest(field=field):
                result = validate_frozen_changes(
                    mission("Tier 2"), policy(), ["src/engine/model.py"],
                    args["declarations"], args["exceptions"], pull_request=42, action="write", **base,
                )
                self.assertEqual(result.code, "FROZEN_INPUT_INVALID")
        result = validate_frozen_changes(
            mission("Tier 2"), policy(), ["src/engine/model.py"], [declaration()], [],
            pull_request=True, action="write", **base,
        )
        self.assertEqual(result.code, "FROZEN_INPUT_INVALID")
        result = validate_frozen_changes(
            mission("Tier 2"), policy(), ["src/engine/model.py"], [declaration()], [None],
            pull_request=42, action="write", **base,
        )
        self.assertEqual(result.code, "FROZEN_EXCEPTION_INVALID")
        extra = exception(); extra["untrusted_claim"] = True
        self.assertEqual(decide([extra]).code, "FROZEN_EXCEPTION_INVALID")
        malformed_release = [None]
        self.assertEqual(decide([exception()], authenticated_release_records=malformed_release).code, "FROZEN_INPUT_INVALID")
        result = validate_frozen_changes(
            mission("Tier 2"), policy(), ["src/engine/model.py"], [declaration()], [],
            pull_request=42, action="teleport", **base,
        )
        self.assertEqual(result.code, "FROZEN_INPUT_INVALID")

    def test_frozen_wrapper_guard_and_docs_are_present_and_non_mutating(self):
        wrapper = ROOT / "scripts/engineering-os/validate-frozen-artifacts"
        workflow = ROOT / ".github/workflows/reusable-frozen-path-guard.yml"
        document = ROOT / "docs/engineering-os/FROZEN_ARTIFACTS.md"
        self.assertTrue(os.access(wrapper, os.X_OK))
        workflow_text = workflow.read_text(encoding="utf-8")
        self.assertIn("contents: read", workflow_text)
        self.assertNotIn("contents: write", workflow_text)
        self.assertIn("github.event.pull_request.base.sha", workflow_text)
        self.assertIn('git show "$BASE_SHA:.aifo/engineering-os-policy.json"', workflow_text)
        self.assertIn("fetch-depth: 0", workflow_text)
        self.assertIn('git cat-file -e "$HEAD_SHA^{commit}"', workflow_text)
        self.assertIn('git diff --name-only -z "$BASE_SHA" "$HEAD_SHA"', workflow_text)
        self.assertNotIn("pulls/${{ github.event.pull_request.number }}/files", workflow_text)
        for raw_input in ("mission_json", "exceptions_json", "observations_json", "release_conditions_json", "consumed_exceptions_json"):
            self.assertNotIn(raw_input, workflow_text)
        self.assertIn("authenticate_event_history", workflow_text)
        self.assertIn("eos-frozen-${{ github.repository }}-${{ inputs.issue_number }}", workflow_text)
        self.assertIn("Task 5", workflow_text)
        text = document.read_text(encoding="utf-8")
        self.assertIn("one-shot", text)
        self.assertIn("No EDGAR integration is activated", text)
        self.assertIn("complete base and head Git trees", text)
        self.assertIn("Task 5", text)
        self.assertIn("no exception is accepted", text)


if __name__ == "__main__":
    unittest.main()
