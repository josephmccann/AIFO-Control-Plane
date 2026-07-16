import copy
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from engineering_os.frozen import validate_frozen_changes
from engineering_os.records import authenticate_github_record_comment, record_comment_body
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


def github_record(record_kind, payload, comment_id):
    comment = {
        "id": comment_id,
        "html_url": "https://github.com/acme/widgets/issues/123#issuecomment-%d" % comment_id,
        "issue_url": "https://api.github.com/repos/acme/widgets/issues/123",
        "user": {"login": "founder"},
        "created_at": "2026-07-15T00:00:00Z",
        "body": record_comment_body(record_kind, payload),
    }
    return authenticate_github_record_comment(comment, "acme/widgets")


def exception():
    item = declaration()
    payload = {
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
    }
    return github_record("frozen_exception", payload, 9002)[0]


def exception_envelope():
    item = exception()
    item.pop("source")
    return github_record("frozen_exception", item, 9002)[1]


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
    payload = {
        "record_id": "release-1", "repository": "acme/widgets",
        "mission_id": "mission-123", "pull_request": 42, "head_sha": HEAD,
        "condition": "founder-approved-methodology-release", "issuer": "founder",
        "expires_at": "2026-07-16T00:00:00Z",
    }
    return github_record("frozen_release", payload, 9003)[0]


def release_envelope():
    item = release_record()
    item.pop("source")
    return github_record("frozen_release", item, 9003)[1]


def reservation():
    payload = {
        "reservation_id": "reservation-1", "exception_id": "exception-1",
        "repository": "acme/widgets", "mission_id": "mission-123",
        "pull_request": 42, "head_sha": HEAD, "status": "reserved",
        "nonce": "frozen-exception-nonce-1",
        "created_at": "2026-07-15T11:00:00Z",
        "expires_at": "2026-07-15T13:00:00Z",
    }
    return github_record("frozen_reservation", payload, 9004)[0]


def reservation_envelope():
    item = reservation()
    item.pop("source")
    return github_record("frozen_reservation", item, 9004)[1]


def decide(exceptions=(), **updates):
    consumption_store = updates.pop("consumption_store", None)
    if consumption_store is None:
        with tempfile.TemporaryDirectory() as directory:
            return decide(
                exceptions, consumption_store=str(Path(directory) / "consumed.sqlite3"),
                **updates,
            )
    context = {
        "repository": "acme/widgets",
        "pull_request": 42,
        "head_sha": HEAD,
        "now": "2026-07-15T12:00:00Z",
        "action": "write",
        "git_evidence": git_evidence(),
        "verified_envelopes": [
            exception_envelope(), release_envelope(), reservation_envelope(),
        ],
        "release_records": [release_record()],
        "durable_reservations": [reservation()],
        "consumption_store": consumption_store,
    }
    context.update(updates)
    return validate_frozen_changes(
        mission("Tier 2"), policy(), ["src/engine/model.py"], [declaration()], list(exceptions), **context
    )


class FrozenTests(unittest.TestCase):
    def test_forged_release_and_reservation_cannot_reuse_exception_source(self):
        forged_release = release_record()
        forged_release["source"] = exception()["source"]
        forged_reservation = reservation()
        forged_reservation["source"] = exception()["source"]
        result = decide(
            [exception()],
            verified_envelopes=[exception_envelope()],
            release_records=[forged_release],
            durable_reservations=[forged_reservation],
        )
        self.assertEqual(result.code, "FROZEN_RELEASE_CONDITION_UNMET")

    def test_one_shot_exception_is_consumed_once_sequentially(self):
        with tempfile.TemporaryDirectory() as directory:
            store = str(Path(directory) / "consumed.sqlite3")
            first = decide([exception()], consumption_store=store)
            second = decide([exception()], consumption_store=store)
        self.assertEqual((first.allowed, second.code), (True, "FROZEN_EXCEPTION_CONSUMED"))

    def test_one_shot_exception_is_consumed_once_concurrently(self):
        with tempfile.TemporaryDirectory() as directory:
            store = str(Path(directory) / "consumed.sqlite3")
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(
                    lambda _: decide([exception()], consumption_store=store), range(2),
                ))
        self.assertEqual(sum(result.allowed for result in results), 1)
        self.assertEqual(sum(result.code == "FROZEN_EXCEPTION_CONSUMED" for result in results), 1)

    def test_public_cli_rejects_raw_evidence_and_authentication_bundles(self):
        wrapper_path = ROOT / "scripts/engineering-os/validate-frozen-artifacts"
        wrapper = wrapper_path.read_text(encoding="utf-8")
        for raw_option in (
            "--git-evidence", "--authenticated-sources", "--release-records",
            "--durable-reservations", "--consumed-exceptions", "--consumed-nonces",
            "--consumption-store",
        ):
            self.assertNotIn(raw_option, wrapper)
        self.assertIn("--base-sha", wrapper)
        self.assertIn("derive_git_evidence", wrapper)

        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True,
        ).strip()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            inputs = {
                "mission.json": mission("Tier 2"),
                "policy.json": policy(),
                "declarations.json": [declaration()],
                "exceptions.json": [],
                "claims.json": [exception()],
                "evidence.json": git_evidence(),
            }
            for name, value in inputs.items():
                (root / name).write_text(json.dumps(value), encoding="utf-8")
            command = [
                str(wrapper_path), "--mission", str(root / "mission.json"),
                "--policy", str(root / "policy.json"), "--declarations",
                str(root / "declarations.json"), "--exceptions",
                str(root / "exceptions.json"), "--repository", "acme/widgets",
                "--pull-request", "42", "--base-sha", head, "--head-sha", head,
                "--now", "2026-07-15T12:00:00Z", "--action", "write",
            ]
            raw = subprocess.run(
                [*command, "--git-evidence", str(root / "evidence.json")],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
            clean = subprocess.run(
                command, cwd=ROOT, text=True, capture_output=True, check=False,
            )
            claimed = subprocess.run(
                [
                    *command[:command.index(str(root / "exceptions.json"))],
                    str(root / "claims.json"),
                    *command[command.index(str(root / "exceptions.json")) + 1:],
                ],
                cwd=ROOT, text=True, capture_output=True, check=False,
            )
        self.assertNotEqual(raw.returncode, 0)
        self.assertIn("unrecognized arguments: --git-evidence", raw.stderr)
        self.assertEqual(clean.returncode, 0, clean.stderr)
        self.assertEqual(json.loads(clean.stdout)["code"], "FROZEN_PATHS_UNTOUCHED")
        self.assertEqual(claimed.returncode, 1, claimed.stderr)
        self.assertEqual(
            json.loads(claimed.stdout)["code"], "FROZEN_CLI_UNAUTHENTICATED_CLAIMS",
        )

    def test_malformed_glob_class_is_a_stable_declaration_denial(self):
        malformed = declaration()
        malformed["paths"] = ["src/[z-a]/**"]
        result = validate_frozen_changes(
            mission("Tier 2"), policy(), ["src/engine/model.py"], [malformed], [],
            repository="acme/widgets", pull_request=42, head_sha=HEAD,
            now="2026-07-15T12:00:00Z", action="write",
            git_evidence=git_evidence(), verified_envelopes=[],
            release_records=[], durable_reservations=[],
            consumption_store="",
        )
        self.assertEqual(result.code, "FROZEN_DECLARATION_INVALID")

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
        self.assertEqual(decide([outsider]).code, "FROZEN_EXCEPTION_ISSUER_DENIED")
        self.assertEqual(decide([exception()], verified_envelopes=[]).code, "FROZEN_EXCEPTION_SOURCE_UNAUTHENTICATED")

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
        self.assertEqual(decide([exception()], release_records=[]).code, "FROZEN_RELEASE_CONDITION_UNMET")
        self.assertEqual(decide([exception()], durable_reservations=[]).code, "FROZEN_EXCEPTION_RESERVATION_REQUIRED")
        incomplete_reservation = reservation(); incomplete_reservation.pop("expires_at")
        self.assertEqual(decide([exception()], durable_reservations=[incomplete_reservation]).code, "FROZEN_EXCEPTION_RESERVATION_REQUIRED")
        self.assertEqual(decide(
            [exception()], verified_envelopes=[exception()["source"]],
        ).code, "FROZEN_INPUT_INVALID")
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
            ), verified_envelopes=[], release_records=[],
            durable_reservations=[], consumption_store="",
        )
        self.assertEqual((result.allowed, result.code), (True, "FROZEN_PATHS_UNTOUCHED"))
        malformed = copy.deepcopy(declaration()); malformed["paths"] = ["../escape"]
        denied = validate_frozen_changes(
            mission("Tier 1"), policy(), ["src/other.py"], [malformed], [],
            repository="acme/widgets", pull_request=42, head_sha=HEAD,
            now="2026-07-15T12:00:00Z", action="write",
            git_evidence=git_evidence(), verified_envelopes=[], release_records=[],
            durable_reservations=[], consumption_store="",
        )
        self.assertEqual(denied.code, "FROZEN_DECLARATION_INVALID")
        incomplete = copy.deepcopy(declaration()); incomplete.pop("schema_version")
        denied = validate_frozen_changes(
            mission("Tier 1"), policy(), ["src/other.py"], [incomplete], [],
            repository="acme/widgets", pull_request=42, head_sha=HEAD,
            now="2026-07-15T12:00:00Z", action="write",
            git_evidence=git_evidence(), verified_envelopes=[], release_records=[],
            durable_reservations=[], consumption_store="",
        )
        self.assertEqual(denied.code, "FROZEN_DECLARATION_INVALID")

    def test_malformed_structures_boolean_pr_and_unknown_action_fail_stably(self):
        base = dict(
            repository="acme/widgets", head_sha=HEAD, now="2026-07-15T12:00:00Z",
            git_evidence=git_evidence(), verified_envelopes=[], release_records=[],
            durable_reservations=[], consumption_store="",
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
        self.assertEqual(decide([exception()], release_records=malformed_release).code, "FROZEN_INPUT_INVALID")
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
        self.assertIn("local Git object database", text)
        self.assertIn("no caller-selected ledger", text)


if __name__ == "__main__":
    unittest.main()
