import copy
import json
import unittest
from pathlib import Path

from engineering_os.authority import validate_authority
from tests.engineering_os.test_risk import mission, policy


ROOT = Path(__file__).resolve().parents[2]
AUTHORITY = ROOT / "tests" / "engineering_os" / "fixtures" / "authority-records"
HEAD = "2222222222222222222222222222222222222222"


def record():
    return json.loads((AUTHORITY / "valid/write.json").read_text(encoding="utf-8"))


def decide(records, **updates):
    context = {
        "action": "write",
        "pull_request": 42,
        "head_sha": HEAD,
        "now": "2026-07-15T12:00:00Z",
        "subject": "producer-a",
    }
    context.update(updates)
    return validate_authority(
        mission("Tier 1"), policy(), ["src/reporting/render.py"], records, **context
    )


class AuthorityTests(unittest.TestCase):
    def test_default_authority_is_read_only(self):
        read = decide([], action="read")
        write = decide([])
        self.assertEqual((read.allowed, read.code), (True, "AUTHORITY_READ_ONLY_DEFAULT"))
        self.assertEqual((write.allowed, write.code), (False, "AUTHORITY_REQUIRED"))

    def test_exact_active_record_authorizes_only_its_bound_action(self):
        self.assertEqual((decide([record()]).allowed, decide([record()]).code), (True, "AUTHORITY_ALLOWED"))
        for field, value, code in (
            ("mission_id", "mission-other", "AUTHORITY_MISSION_MISMATCH"),
            ("pull_request", 43, "AUTHORITY_PR_MISMATCH"),
            ("head_sha", "3" * 40, "AUTHORITY_HEAD_MISMATCH"),
            ("subject", "producer-b", "AUTHORITY_SUBJECT_MISMATCH"),
            ("capabilities", ["merge"], "AUTHORITY_ACTION_MISMATCH"),
        ):
            with self.subTest(field=field):
                candidate = record()
                candidate[field] = value
                self.assertEqual(decide([candidate]).code, code)

    def test_expired_wrong_repository_and_wrong_path_are_denied(self):
        expired = record()
        expired["expires_at"] = "2026-07-15T12:00:00Z"
        wrong_repo = record()
        wrong_repo["repository"] = "acme/other"
        wrong_path = record()
        wrong_path["paths"] = ["src/reporting/other.py"]
        self.assertEqual(decide([expired]).code, "AUTHORITY_EXPIRED")
        self.assertEqual(decide([wrong_repo]).code, "AUTHORITY_REPOSITORY_MISMATCH")
        self.assertEqual(decide([wrong_path]).code, "AUTHORITY_PATH_MISMATCH")

        wrong_base = policy()
        wrong_base["repository"] = "acme/other"
        base_denied = validate_authority(
            mission("Tier 1"), wrong_base, ["src/reporting/render.py"], [record()],
            action="write", pull_request=42, head_sha=HEAD,
            now="2026-07-15T12:00:00Z", subject="producer-a",
        )
        self.assertEqual(base_denied.code, "AUTHORITY_POLICY_REPOSITORY_MISMATCH")

    def test_future_revoked_consumed_or_non_founder_authority_is_denied(self):
        cases = []
        future = record(); future["starts_at"] = "2026-07-15T12:00:01Z"; cases.append((future, "AUTHORITY_NOT_STARTED"))
        revoked = record(); revoked["status"] = "revoked"; cases.append((revoked, "AUTHORITY_INACTIVE"))
        consumed = record(); consumed["status"] = "consumed"; cases.append((consumed, "AUTHORITY_INACTIVE"))
        outsider = record(); outsider["issuer"] = "outsider"; cases.append((outsider, "AUTHORITY_ISSUER_DENIED"))
        for candidate, code in cases:
            with self.subTest(code=code):
                self.assertEqual(decide([candidate]).code, code)

        no_founders = policy()
        no_founders["founder_identities"] = []
        denied = validate_authority(
            mission("Tier 1"), no_founders, ["src/reporting/render.py"], [record()],
            action="write", pull_request=42, head_sha=HEAD,
            now="2026-07-15T12:00:00Z", subject="producer-a",
        )
        self.assertEqual(denied.code, "AUTHORITY_ISSUER_DENIED")

    def test_malformed_timestamps_and_paths_fail_closed(self):
        malformed = record(); malformed["expires_at"] = "tomorrow"
        traversal = record(); traversal["paths"] = ["../escape"]
        incomplete = record(); incomplete.pop("authority_id")
        self.assertEqual(decide([malformed]).code, "AUTHORITY_RECORD_INVALID")
        self.assertEqual(decide([traversal]).code, "AUTHORITY_RECORD_INVALID")
        self.assertEqual(decide([incomplete]).code, "AUTHORITY_RECORD_INVALID")

    def test_authority_cannot_expand_mission_or_disabled_base_policy_capabilities(self):
        deploy = record()
        deploy["capabilities"] = ["deploy"]
        undeclared = decide([deploy], action="deploy")
        self.assertEqual(undeclared.code, "AUTHORITY_MISSION_CAPABILITY_DENIED")

        declared_mission = mission("Tier 2")
        declared_mission["capabilities"].append("deploy")
        base_policy = policy()
        base_policy["deployment_enabled"] = False
        disabled = validate_authority(
            declared_mission, base_policy, ["src/reporting/render.py"], [deploy],
            action="deploy", pull_request=42, head_sha=HEAD,
            now="2026-07-15T12:00:00Z", subject="producer-a",
        )
        self.assertEqual(disabled.code, "AUTHORITY_POLICY_CAPABILITY_DISABLED")

    def test_credential_model_names_real_gap_and_github_app_migration(self):
        text = (ROOT / "docs/engineering-os/CREDENTIAL_MODEL.md").read_text(encoding="utf-8")
        compact = " ".join(text.split())
        self.assertIn("cannot path-scope the Git credential", compact)
        self.assertIn("GitHub App", compact)
        self.assertIn("expiring installation token", compact)
        self.assertIn("does not claim that it enforces path-scoped Git credentials", compact)


if __name__ == "__main__":
    unittest.main()
