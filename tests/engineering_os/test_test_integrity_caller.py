import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
KERNEL_SHA = "fe3a8da3d8eb3c81342cc28205de65abc969e0e2"


class TestIntegrityCallerTests(unittest.TestCase):
    def test_default_branch_caller_is_safe_read_only_and_exactly_pinned(self):
        caller = (ROOT / ".github/workflows/test-integrity.yml").read_text(encoding="utf-8")
        documentation = (ROOT / "docs/engineering-os/TEST_INTEGRITY.md").read_text(encoding="utf-8")
        self.assertIn("pull_request_target:", caller)
        self.assertNotRegex(caller, r"(?m)^\s+pull_request:\s*$")
        self.assertIn("permissions: {}", caller)
        for permission in ("actions: read", "contents: read", "issues: read", "pull-requests: read"):
            self.assertIn(permission, caller)
        self.assertNotIn("write", caller)
        self.assertNotIn("actions/checkout", caller)
        self.assertNotRegex(caller, r"(?m)^\s+run:")
        expected = (
            "uses: josephmccann/AIFO-Control-Plane/.github/workflows/"
            "reusable-test-integrity.yml@" + KERNEL_SHA
        )
        self.assertIn(expected, caller)
        self.assertIn("expected_workflow_sha: " + KERNEL_SHA, caller)
        self.assertIsNotNone(re.fullmatch(r"[0-9a-f]{40}", KERNEL_SHA))
        self.assertIn("bootstrap interval is an explicit enforcement gap", documentation)
