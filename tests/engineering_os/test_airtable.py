import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError

from engineering_os.airtable import project_airtable_record, sync_airtable
from engineering_os.canonical import content_sha256
from tests.engineering_os.fake_github import (
    SealedFakeGitHubTransport,
    transported_record,
)
from tests.engineering_os.test_risk import policy


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "engineering_os" / "fixtures" / "airtable"


def load(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        return json.dumps(self.payload).encode("utf-8")[:size]


class AirtableTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.inputs = load("missions.json")
        self.expected = load("expected-records.json")

    def tearDown(self):
        self.temp.cleanup()

    def records(self):
        return [
            project_airtable_record(
                item["mission"],
                item["projection"],
                head_sha=item["head_sha"],
                projected_at="2026-07-16T12:00:00Z",
            )
            for item in self.inputs
        ]

    def live_context(self, **overrides):
        records = overrides.pop("records", self.records())
        live_policy = policy()
        live_policy["airtable_live_enabled"] = True
        payload = load("approval.json")
        approval_records = sorted(
            records, key=lambda record: record["upsert_key"]
        )
        payload["environment"] = (
            "airtable:appABCDEFGHIJKLMN:tblABCDEFGHIJKLMN:%s"
            % content_sha256(approval_records)
        )
        approval, evidence = transported_record(
            "founder_approval",
            payload,
            created_at=payload["approved_at"],
            head_sha=payload["head_sha"],
        )
        value = {
            "direction": "github_to_airtable",
            "mode": "live",
            "records": records,
            "policy": live_policy,
            "approval": approval,
            "authorization_mission_id": "mission-7",
            "authorization_head_sha": "2" * 40,
            "pull_request": 42,
            "now": "2026-07-16T12:00:00Z",
            "latest_commit_at": "2026-07-16T10:59:00Z",
            "base_id": "appABCDEFGHIJKLMN",
            "table_id": "tblABCDEFGHIJKLMN",
            "credential": "ephemeral-token-value",
            "credential_source": "environment",
            "evidence_verifier": SealedFakeGitHubTransport(evidence),
            "consumption_store": str(
                Path(self.temp.name) / "airtable-approvals.sqlite"
            ),
        }
        value.update(overrides)
        return value

    def test_projection_matches_closed_schema_and_idempotent_upsert_key(self):
        self.assertEqual(self.records(), self.expected)
        self.assertEqual(
            self.records()[0]["upsert_key"], "acme/widgets#mission-7",
        )

    def test_dry_run_is_deterministic_redacted_and_never_opens_network(self):
        with patch(
            "engineering_os.airtable.urllib.request.urlopen",
            side_effect=AssertionError("dry-run attempted network access"),
        ) as opener:
            first = sync_airtable(
                direction="github_to_airtable",
                mode="dry-run",
                records=self.records(),
            )
            second = sync_airtable(
                direction="github_to_airtable",
                mode="dry-run",
                records=list(reversed(self.records())),
            )
        opener.assert_not_called()
        self.assertTrue(first.allowed)
        self.assertEqual(first, second)
        serialized = json.dumps(first.records, sort_keys=True)
        for secret in ("customer ACME", "token-secret", "financial values"):
            self.assertNotIn(secret, serialized)

    def test_airtable_to_github_and_airtable_authority_are_rejected(self):
        decision = sync_airtable(
            direction="airtable_to_github",
            mode="dry-run",
            records=self.records(),
        )
        self.assertEqual(decision.code, "AIRTABLE_DIRECTION_DENIED")
        self.assertFalse(decision.allowed)
        self.assertNotIn("event", self.records()[0])
        self.assertNotIn("approval", self.records()[0])
        self.assertNotIn("capabilities", self.records()[0])

    def test_live_mode_requires_every_gate(self):
        cases = (
            ("policy", policy(), "AIRTABLE_LIVE_POLICY_DISABLED"),
            ("approval", {}, "AIRTABLE_LIVE_APPROVAL_INVALID"),
            ("base_id", "", "AIRTABLE_LIVE_TARGET_INVALID"),
            ("table_id", "", "AIRTABLE_LIVE_TARGET_INVALID"),
            ("credential", "", "AIRTABLE_LIVE_CREDENTIAL_REQUIRED"),
            (
                "credential_source", "argument",
                "AIRTABLE_LIVE_CREDENTIAL_REQUIRED",
            ),
        )
        for field, value, code in cases:
            with self.subTest(field=field):
                decision = sync_airtable(**self.live_context(**{field: value}))
                self.assertEqual(decision.code, code)
                self.assertFalse(decision.allowed)

    def test_live_upsert_is_bounded_exact_and_does_not_return_token(self):
        requests = []

        def opener(request, timeout):
            requests.append((request, timeout))
            body = json.loads(request.data)
            return FakeResponse({
                "records": [
                    {"id": "rec1", "fields": item["fields"]}
                    for item in body["records"]
                ],
                "updatedRecords": ["rec1"],
                "createdRecords": [],
            })

        with patch(
            "engineering_os.airtable.urllib.request.urlopen",
            side_effect=opener,
        ):
            decision = sync_airtable(**self.live_context())
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.code, "AIRTABLE_LIVE_SYNCED")
        self.assertEqual(decision.completed_batches, 1)
        self.assertEqual(len(requests), 1)
        request, timeout = requests[0]
        self.assertEqual(request.get_method(), "PATCH")
        self.assertEqual(timeout, 10)
        body = json.loads(request.data)
        self.assertEqual(
            body["performUpsert"]["fieldsToMergeOn"], ["upsert_key"],
        )
        self.assertNotIn("ephemeral-token-value", repr(decision))
        self.assertNotIn("ephemeral-token-value", json.dumps(body))

    def test_live_approval_is_bound_to_the_exact_projected_record_set(self):
        context = self.live_context()
        changed = copy.deepcopy(context["records"])
        changed[0]["state"] = "Closed"
        context["records"] = changed
        decision = sync_airtable(**context)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.code, "AIRTABLE_LIVE_APPROVAL_INVALID")

    def test_api_errors_retry_safely_then_fail_closed(self):
        calls = []

        def opener(request, timeout):
            calls.append((request.get_method(), timeout))
            raise URLError("temporary outage")

        with patch(
            "engineering_os.airtable.urllib.request.urlopen",
            side_effect=opener,
        ), patch("engineering_os.airtable.time.sleep"):
            decision = sync_airtable(**self.live_context())
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.code, "AIRTABLE_API_FAILURE")
        self.assertEqual(calls, [("PATCH", 10), ("PATCH", 10), ("PATCH", 10)])
        self.assertEqual(decision.completed_batches, 0)

    def test_oversized_api_response_fails_closed(self):
        class OversizedResponse(FakeResponse):
            def read(self, size=-1):
                return b"x" * (size + 1)

        with patch(
            "engineering_os.airtable.urllib.request.urlopen",
            return_value=OversizedResponse({}),
        ):
            decision = sync_airtable(**self.live_context())
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.code, "AIRTABLE_API_FAILURE")
        self.assertEqual(decision.attempted_batches, 1)

    def test_partial_failure_is_nonzero_and_never_reported_as_success(self):
        many_records = []
        for index in range(11):
            record = copy.deepcopy(self.records()[0])
            record["mission_id"] = f"mission-{index}"
            record["upsert_key"] = f"acme/widgets#mission-{index}"
            many_records.append(record)
        calls = []

        def opener(request, timeout):
            calls.append(request)
            if len(calls) == 1:
                body = json.loads(request.data)
                self.assertEqual(len(body["records"]), 10)
                return FakeResponse({
                    "records": [
                        {"id": f"rec{index}", "fields": item["fields"]}
                        for index, item in enumerate(body["records"])
                    ],
                    "updatedRecords": [],
                    "createdRecords": [f"rec{index}" for index in range(10)],
                })
            raise URLError("second batch failed")

        context = self.live_context(records=many_records)
        with patch(
            "engineering_os.airtable.urllib.request.urlopen",
            side_effect=opener,
        ), patch("engineering_os.airtable.time.sleep"):
            decision = sync_airtable(**context)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.code, "AIRTABLE_PARTIAL_FAILURE")
        self.assertEqual(decision.completed_batches, 1)

    def test_cli_and_reusable_workflow_remain_dry_run_first(self):
        wrapper = ROOT / "scripts" / "engineering-os" / "sync-airtable"
        self.assertTrue(os.access(wrapper, os.X_OK))
        output = Path(self.temp.name) / "records.json"
        completed = subprocess.run(
            [
                str(wrapper),
                "--direction", "github_to_airtable",
                "--mode", "dry-run",
                "--missions", str(FIXTURES / "missions.json"),
                "--projected-at", "2026-07-16T12:00:00Z",
                "--output", str(output),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(output.read_text(encoding="utf-8")), self.expected)
        workflow = (
            ROOT / ".github/workflows/reusable-airtable-mirror.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("permissions: {}", workflow)
        self.assertIn("default: dry-run", workflow)
        self.assertNotIn("AIRTABLE_API_KEY", workflow)
        self.assertNotIn("airtable_to_github", workflow)
        generation_step = workflow.split(
            "- name: Generate redacted deterministic mirror", 1
        )[1].split("- name: Retain dry-run reporting artifact", 1)[0]
        self.assertIn('cd "$GITHUB_WORKSPACE/kernel"', generation_step)
        self.assertIn("scripts/engineering-os/sync-airtable", generation_step)
        self.assertNotIn(
            "kernel/scripts/engineering-os/sync-airtable", generation_step
        )


if __name__ == "__main__":
    unittest.main()
