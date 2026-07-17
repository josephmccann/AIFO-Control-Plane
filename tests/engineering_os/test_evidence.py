import unittest
from pathlib import Path
import json
import os
import subprocess
import tempfile

from engineering_os.audit import normalize_audit_event
from engineering_os.canonical import content_sha256
from engineering_os.evidence import (
    ArtifactInput,
    generate_evidence,
    validate_producer_bundle,
)
from engineering_os.schema import validate_document


ROOT = Path(__file__).resolve().parents[2]


class EvidenceTests(unittest.TestCase):
    def mission(self):
        return {
            "schema_version": "1.0.0",
            "mission_id": "mission-7",
            "repository": "acme/widgets",
            "title": "Evidence",
            "objective": "Generate exact evidence.",
            "acceptance_criteria": ["Manifest validates."],
            "allowed_paths": ["src/**"],
            "prohibited_paths": [],
            "dependencies": [],
            "founder_decisions": [],
            "risk_tier": "Tier 1",
            "capabilities": ["read", "write"],
            "budgets": {
                "model_cost_usd": 1,
                "model_tokens": 100,
                "wall_clock_minutes": 10,
                "remediation_cycles": 2,
                "concurrent_agents": 1,
                "ci_reruns": 1,
            },
            "validation_commands": ["python3 -m unittest"],
            "rollback": {"class": "clean_revert", "plan": "Revert."},
            "assignments": {
                "producer": {"identity": "agent-a", "model_family": "gpt"},
                "adversary": {"identity": "agent-b", "model_family": "claude"},
            },
            "eos": {"version": "1.0.0", "constitution_sha256": "a" * 64},
        }

    def policy(self):
        return {
            "schema_version": "1.0.0",
            "repository": "acme/widgets",
            "eos_version": "1.0.0",
            "constitution_sha256": "a" * 64,
            "founder_identities": ["founder"],
            "semantic_domains": [{
                "name": "source",
                "paths": ["src/**"],
                "minimum_tier": "Tier 1",
                "owners": ["agent-a"],
                "conflict_group": "source",
            }],
            "tier_2_paths": [".github/**"],
            "required_status_checks": ["Engineering OS Validation"],
            "default_limits": {
                "model_cost_usd": 1,
                "model_tokens": 100,
                "wall_clock_minutes": 10,
                "remediation_cycles": 2,
                "concurrent_agents": 1,
                "ci_reruns": 1,
            },
            "transition_roles": {},
            "recovery_workflow_paths": [".github/workflows/recovery.yml"],
            "auto_merge_enabled": False,
            "airtable_live_enabled": False,
            "deployment_enabled": False,
            "edgar_integration_enabled": False,
            "orphan_recovery_enabled": False,
        }

    def audit(self):
        return [
            normalize_audit_event(
                {
                    "schema_version": "1.0.0", "mission_id": "mission-7",
                    "type": "mission.ready", "details": {},
                },
                {
                    "actor": "agent-a", "actor_role": "producer",
                    "occurred_at": "2026-07-15T12:00:00Z",
                    "source_url": "https://github.com/acme/widgets/issues/7#issuecomment-1",
                },
                sequence=1,
                previous_event_hash=None,
            )
        ]

    def generate(self, **overrides):
        values = {
            "mission": self.mission(),
            "policy": self.policy(),
            "audit_events": self.audit(),
            "repository": "acme/widgets",
            "pull_request": 42,
            "base_sha": "1" * 40,
            "head_sha": "2" * 40,
            "generated_at": "2026-07-15T13:00:00Z",
            "status_checks": [
                {"name": "Engineering OS Validation", "conclusion": "success"},
            ],
            "artifacts": [
                ArtifactInput("test-report.json", b'{"ok":true}', "github-actions"),
            ],
            "cleanup_state": "complete",
            "deployment_state": "not_authorized",
        }
        values.update(overrides)
        return generate_evidence(**values)

    def test_manifest_derives_hashes_and_validates_schema(self):
        manifest = self.generate()
        self.assertEqual(manifest["policy_hash"], content_sha256(self.policy()))
        self.assertEqual(manifest["mission_hash"], content_sha256(self.mission()))
        self.assertEqual(manifest["audit_head_hash"], self.audit()[-1]["event_hash"])
        self.assertEqual(
            manifest["artifacts"][0]["sha256"],
            content_sha256(b'{"ok":true}'),
        )
        self.assertEqual(validate_document("evidence", manifest), [])

    def test_missing_failed_or_unknown_machine_inputs_fail_closed(self):
        with self.assertRaises(ValueError):
            self.generate(status_checks=[])
        with self.assertRaises(ValueError):
            self.generate(status_checks=[
                {"name": "Engineering OS Validation", "conclusion": "failure"},
            ])
        with self.assertRaises(ValueError):
            self.generate(status_checks=[
                {
                    "name": "Engineering OS Validation",
                    "conclusion": "success",
                    "producer_policy_hash": "forged",
                },
            ])

    def test_audit_chain_must_belong_to_the_manifest_mission(self):
        mission = self.mission()
        mission["mission_id"] = "different-mission"
        with self.assertRaises(ValueError):
            self.generate(mission=mission)

    def test_artifact_hash_cleanup_and_deployment_state_are_exact(self):
        manifest = self.generate(cleanup_state="pending", deployment_state="not_deployed")
        self.assertEqual(manifest["cleanup_state"], "pending")
        self.assertEqual(manifest["deployment_state"], "not_deployed")
        with self.assertRaises(ValueError):
            self.generate(artifacts=[{"name": "forged", "sha256": "0" * 64}])
        with self.assertRaises(ValueError):
            self.generate(deployment_state="deployed")

    def test_split_privilege_workflow_and_public_entrypoints_are_present(self):
        workflow_path = ROOT / ".github/workflows/reusable-evidence-manifest.yml"
        self.assertTrue(workflow_path.is_file())
        workflow = workflow_path.read_text(encoding="utf-8")
        self.assertIn("permissions: {}", workflow)
        self.assertIn("producer-evidence:", workflow)
        self.assertIn("manifest:", workflow)
        self.assertIn("needs: producer-evidence", workflow)
        self.assertIn("actions/upload-artifact@", workflow)
        self.assertIn("actions/download-artifact@", workflow)
        self.assertIn(
            "kernel/scripts/engineering-os/validate-test-integrity", workflow
        )
        self.assertIn(
            "kernel/scripts/engineering-os/validate-evidence-bundle", workflow
        )
        self.assertIn("path: base", workflow)
        self.assertIn("path: head", workflow)
        trusted = workflow.split(
            "- name: Validate source integrity with immutable kernel", 1
        )[1]
        for field in ("BASE_SHA", "HEAD_SHA", "PULL_REQUEST"):
            self.assertIn(f"{field}:", trusted)
        self.assertIn('--base-sha "$BASE_SHA"', trusted)
        self.assertIn('--head-sha "$HEAD_SHA"', trusted)
        self.assertIn('--pull-request "$PULL_REQUEST"', trusted)
        self.assertNotIn('--base-sha "${{ inputs.base_sha }}"', trusted)
        self.assertNotIn('--head-sha "${{ inputs.head_sha }}"', trusted)
        self.assertNotIn('--pull-request "${{ inputs.pull_request }}"', trusted)
        producer = workflow.split("producer-evidence:", 1)[1].split(
            "\n  manifest:", 1
        )[0]
        self.assertIn("producer_validation_command:", workflow)
        self.assertIn("required: true", workflow.split(
            "producer_validation_command:", 1
        )[1].split("jobs:", 1)[0])
        self.assertIn(
            "PRODUCER_VALIDATION_COMMAND: ${{ inputs.producer_validation_command }}",
            producer,
        )
        self.assertIn(
            'bash -euo pipefail -c "$PRODUCER_VALIDATION_COMMAND"', producer
        )
        head_checkout = producer.split("- name: Check out immutable head", 1)[1].split(
            "- name: Capture unprivileged validation outputs", 1
        )[0]
        self.assertIn("fetch-depth: 0", head_checkout)
        self.assertIn("persist-credentials: false", head_checkout)
        self.assertIn('git cat-file -e "$BASE_SHA^{commit}"', producer)
        self.assertIn(
            'git merge-base --is-ancestor "$BASE_SHA" "$HEAD_SHA"', producer
        )
        self.assertIn(
            'git update-ref refs/remotes/origin/master "$BASE_SHA"', producer
        )
        self.assertLess(
            producer.index('git update-ref refs/remotes/origin/master "$BASE_SHA"'),
            producer.index('bash -euo pipefail -c "$PRODUCER_VALIDATION_COMMAND"'),
        )
        self.assertIn("producer-validation.txt", producer)
        self.assertNotIn("tests/engineering_os", producer)
        self.assertNotIn("${{ inputs.producer_validation_command }}\n", producer.split(
            "run: |", 1
        )[1])
        for permission in ("contents: read", "actions: read"):
            self.assertIn(permission, producer)
        for capability in (
            "issues: write", "pull-requests: write", "id-token: write",
            "deployments: write", "secrets:",
        ):
            self.assertNotIn(capability, producer)
        for name in (
            "validate-approval", "validate-audit", "generate-evidence",
            "generate-metrics",
        ):
            path = ROOT / "scripts/engineering-os" / name
            self.assertTrue(path.is_file())

    def test_fresh_runner_recomputes_bundle_identity_and_artifact_hashes(self):
        content = b"326 tests passed\n"
        bundle = {
            "schema_version": "1.0.0",
            "repository": "acme/widgets",
            "pull_request": 42,
            "base_sha": "1" * 40,
            "head_sha": "2" * 40,
            "artifacts": [{
                "name": "unittest.txt",
                "sha256": content_sha256(content),
                "size_bytes": len(content),
            }],
        }
        validated = validate_producer_bundle(
            bundle,
            {"unittest.txt": content},
            repository="acme/widgets",
            pull_request=42,
            base_sha="1" * 40,
            head_sha="2" * 40,
        )
        self.assertEqual(validated["artifacts"][0]["sha256"], content_sha256(content))
        with self.assertRaises(ValueError):
            validate_producer_bundle(
                bundle,
                {"unittest.txt": content + b"forged"},
                repository="acme/widgets",
                pull_request=42,
                base_sha="1" * 40,
                head_sha="2" * 40,
            )
        with self.assertRaises(ValueError):
            validate_producer_bundle(
                bundle,
                {"unittest.txt": content},
                repository="acme/widgets",
                pull_request=42,
                base_sha="1" * 40,
                head_sha="3" * 40,
            )

    def test_package_five_cli_wrappers_are_executable_and_deterministic(self):
        for name in (
            "validate-audit", "validate-approval", "generate-evidence",
            "generate-metrics", "validate-evidence-bundle",
        ):
            self.assertTrue(os.access(
                ROOT / "scripts/engineering-os" / name, os.X_OK,
            ))
        denied = subprocess.run(
            [str(ROOT / "scripts/engineering-os/validate-approval")],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(denied.returncode, 1)
        self.assertEqual(
            json.loads(denied.stdout)["code"],
            "APPROVAL_AUTHENTICATED_ADAPTER_REQUIRED",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audit_path = root / "audit.json"
            audit_path.write_text(
                json.dumps(self.audit()), encoding="utf-8",
            )
            validated = subprocess.run(
                [
                    str(ROOT / "scripts/engineering-os/validate-audit"),
                    str(audit_path),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(validated.returncode, 0, validated.stderr)
            self.assertEqual(json.loads(validated.stdout)["code"], "AUDIT_CHAIN_VALID")

    def test_package_five_documents_name_trust_and_quota_boundaries(self):
        adversary = (
            ROOT / "docs/engineering-os/PRODUCER_ADVERSARY_MODEL.md"
        ).read_text(encoding="utf-8")
        evidence = (
            ROOT / "docs/engineering-os/EVIDENCE_AND_AUDIT.md"
        ).read_text(encoding="utf-8")
        metrics = (
            ROOT / "docs/engineering-os/METRICS.md"
        ).read_text(encoding="utf-8")
        self.assertIn("different model family", adversary)
        self.assertIn("authenticated GitHub", evidence)
        self.assertIn("fresh runner", evidence)
        self.assertIn("no finding quota", metrics.lower())


if __name__ == "__main__":
    unittest.main()
