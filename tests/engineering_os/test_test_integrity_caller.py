import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
KERNEL_SHA = "6ec2fc95c8965892f387189e05baf3c4a5c4ed4a"


class TestIntegrityCallerTests(unittest.TestCase):
    def test_default_branch_caller_is_safe_read_only_and_exactly_pinned(self):
        caller = (ROOT / ".github/workflows/test-integrity.yml").read_text(encoding="utf-8")
        documentation = (ROOT / "docs/engineering-os/TEST_INTEGRITY.md").read_text(encoding="utf-8")
        self.assertIn("pull_request_target:", caller)
        self.assertIn("pull_request:", caller)
        self.assertIn("github.event.pull_request.number == 24", caller)
        self.assertIn("github.event.pull_request.head.sha == 'cae9338ba7d4e5147963e7baf198fc56bf6b6cd7'", caller)
        self.assertIn("permissions: {}", caller)
        for permission in ("actions: read", "contents: read", "issues: read", "pull-requests: read"):
            self.assertIn(permission, caller)
        self.assertNotRegex(caller, r"(?m)^\s+[A-Za-z-]+:\s+write\s*$")
        self.assertIn("actions/checkout@v4", caller)
        self.assertIn("run:", caller)
        expected = (
            "uses: josephmccann/AIFO-Control-Plane/.github/workflows/"
            "reusable-test-integrity.yml@" + KERNEL_SHA
        )
        self.assertIn(expected, caller)
        self.assertIn("expected_workflow_sha: " + KERNEL_SHA, caller)
        self.assertIsNotNone(re.fullmatch(r"[0-9a-f]{40}", KERNEL_SHA))
        self.assertIn("bootstrap interval is an explicit enforcement gap", documentation)
