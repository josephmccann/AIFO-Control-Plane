from __future__ import annotations

import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RESOLVER = ROOT / "scripts" / "engineering-os" / "resolve-base-policy"


class PolicyBootstrapTests(unittest.TestCase):
    def git(self, repository: Path, *args: str) -> str:
        return subprocess.check_output(
            ["git", "-C", str(repository), *args], text=True, encoding="utf-8"
        ).strip()

    def commit(self, repository: Path, message: str) -> str:
        subprocess.run(
            ["git", "-C", str(repository), "add", "-A"], check=True
        )
        subprocess.run(
            ["git", "-C", str(repository), "commit", "-m", message],
            check=True,
            capture_output=True,
        )
        return self.git(repository, "rev-parse", "HEAD")

    def repository(self, directory: str, base_policy: bytes | None = None):
        repository = Path(directory) / "repository"
        repository.mkdir()
        subprocess.run(["git", "init", "-q", str(repository)], check=True)
        self.git(repository, "config", "user.email", "eos@example.invalid")
        self.git(repository, "config", "user.name", "EOS Test")
        (repository / "README.md").write_text("base\n", encoding="utf-8")
        if base_policy is not None:
            (repository / ".aifo").mkdir()
            (repository / ".aifo" / "engineering-os-policy.json").write_bytes(
                base_policy
            )
        base_sha = self.commit(repository, "base")
        return repository, base_sha

    def resolve(
        self,
        repository: Path,
        base_sha: str,
        head_sha: str,
        output: Path,
        *,
        repository_name: str = "josephmccann/AI.FO-Demo",
        bootstrap_base_sha: str | None = None,
        bootstrap_digest: str,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                str(RESOLVER),
                "--repository",
                repository_name,
                "--base-root",
                str(repository),
                "--head-root",
                str(repository),
                "--base-sha",
                base_sha,
                "--head-sha",
                head_sha,
                "--bootstrap-repository",
                "josephmccann/AI.FO-Demo",
                "--bootstrap-base-sha",
                bootstrap_base_sha or base_sha,
                "--bootstrap-policy-sha256",
                bootstrap_digest,
                "--output",
                str(output),
            ],
            capture_output=True,
            text=True,
        )

    def test_existing_base_policy_is_always_authoritative(self):
        with tempfile.TemporaryDirectory() as directory:
            base_policy = b'{"source":"base"}\n'
            repository, base_sha = self.repository(directory, base_policy)
            policy = repository / ".aifo" / "engineering-os-policy.json"
            policy.write_bytes(b'{"source":"head"}\n')
            head_sha = self.commit(repository, "head")
            output = Path(directory) / "resolved.json"
            result = self.resolve(
                repository,
                base_sha,
                head_sha,
                output,
                repository_name="unexpected/repository",
                bootstrap_base_sha="0" * 40,
                bootstrap_digest="0" * 64,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(base_policy, output.read_bytes())

    def test_exact_bootstrap_evidence_selects_head_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            repository, base_sha = self.repository(directory)
            policy_bytes = b'{"source":"reviewed-bootstrap"}\n'
            (repository / ".aifo").mkdir()
            (repository / ".aifo" / "engineering-os-policy.json").write_bytes(
                policy_bytes
            )
            head_sha = self.commit(repository, "head")
            output = Path(directory) / "resolved.json"
            result = self.resolve(
                repository,
                base_sha,
                head_sha,
                output,
                bootstrap_digest=hashlib.sha256(policy_bytes).hexdigest(),
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(policy_bytes, output.read_bytes())

    def test_bootstrap_mismatch_fails_closed_without_output(self):
        with tempfile.TemporaryDirectory() as directory:
            repository, base_sha = self.repository(directory)
            policy_bytes = b'{"source":"reviewed-bootstrap"}\n'
            (repository / ".aifo").mkdir()
            (repository / ".aifo" / "engineering-os-policy.json").write_bytes(
                policy_bytes
            )
            head_sha = self.commit(repository, "head")
            cases = (
                {"repository_name": "josephmccann/AI-CFO"},
                {"bootstrap_base_sha": "0" * 40},
                {"bootstrap_digest": "0" * 64},
            )
            for index, mutation in enumerate(cases):
                with self.subTest(mutation=mutation):
                    output = Path(directory) / f"rejected-{index}.json"
                    arguments = {
                        "bootstrap_digest": hashlib.sha256(policy_bytes).hexdigest(),
                        **mutation,
                    }
                    result = self.resolve(
                        repository, base_sha, head_sha, output, **arguments
                    )
                    self.assertNotEqual(0, result.returncode)
                    self.assertIn("base policy resolution denied", result.stderr)
                    self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
