import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts/engineering-os/validate-activation-closure"
ENTRYPOINT = ROOT / "scripts/validate.sh"


class ValidationClassificationTests(unittest.TestCase):
    def classify(self, name, content, executable=True):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / name
            path.write_text(content, encoding="utf-8")
            path.chmod(0o755 if executable else 0o644)
            return subprocess.run(
                ["bash", "-c", 'source "$1"; classify_script "$2"', "bash", str(ENTRYPOINT), str(path)],
                cwd=ROOT,
                env={**os.environ, "AIFO_VALIDATE_LIBRARY_ONLY": "1"},
                capture_output=True,
                text=True,
            )

    def test_extensionless_python_validator_has_python_shebang(self):
        self.assertTrue(VALIDATOR.read_text(encoding="utf-8").splitlines()[0].startswith("#!/usr/bin/env python3"))

    def test_entrypoint_classifies_by_extension_and_audited_shebang(self):
        source = ENTRYPOINT.read_text(encoding="utf-8")
        for marker in ("*.sh", "*.py", "bash|sh|dash|ksh", "python", "SHELL_FILES", "PYTHON_FILES"):
            self.assertIn(marker, source)
        self.assertIn("Unclassified executable script:", source)
        self.assertNotIn('shellcheck "$ROOT_DIR"/scripts/engineering-os/*', source)

    def test_entrypoint_shell_syntax_is_valid(self):
        result = subprocess.run(["bash", "-n", str(ENTRYPOINT)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_python_validator_compiles_through_python_path(self):
        result = subprocess.run(["python3", "-m", "py_compile", str(VALIDATOR)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_extensionless_python_is_classified_as_python(self):
        result = self.classify("validator", "#!/usr/bin/env python3\nprint('ok')\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "python")

    def test_extensionless_approved_shell_shebangs_are_classified_as_shell(self):
        for interpreter in ("bash", "sh", "dash", "ksh"):
            with self.subTest(interpreter=interpreter):
                result = self.classify("validator", f"#!/usr/bin/env {interpreter}\necho ok\n")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), "shell")

    def test_conflicting_extension_and_shebang_fail_closed(self):
        for name, content in (
            ("validator.sh", "#!/usr/bin/env python3\nprint('ok')\n"),
            ("validator.py", "#!/usr/bin/env bash\necho ok\n"),
        ):
            with self.subTest(name=name):
                result = self.classify(name, content)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Conflicting script classification", result.stderr)

    def test_malformed_ambiguous_and_unknown_executables_fail_closed(self):
        cases = (
            ("malformed", "#!/usr/bin/env\necho ok\n"),
            ("ambiguous", "#!/usr/bin/env python3 bash\nprint('ok')\n"),
            ("unknown", "#!/usr/bin/env ruby\nputs 'ok'\n"),
            ("missing", "echo ok\n"),
        )
        for name, content in cases:
            with self.subTest(name=name):
                result = self.classify(name, content)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("Unclassified executable script", result.stderr)

    def test_non_executable_data_file_is_ignored(self):
        result = self.classify("notes.txt", "not a script\n", executable=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "ignore")

    def test_non_executable_extensionless_script_path_fails_closed(self):
        result = self.classify("payload", "echo bypass\n", executable=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Unclassified script path", result.stderr)

    def test_tests_cannot_leave_tracked_validation_code_modified(self):
        with tempfile.TemporaryDirectory() as directory:
            clone = Path(directory) / "clone"
            subprocess.run(
                ["git", "clone", "--quiet", "--no-local", str(ROOT), str(clone)],
                check=True,
            )
            shutil.copy2(ENTRYPOINT, clone / "scripts/validate.sh")
            validator = clone / "scripts/engineering-os/validate-activation-closure"
            validator.write_text("#!/usr/bin/env python3\n", encoding="utf-8")
            result = subprocess.run(
                [
                    "bash", "-c",
                    'source "$1"; verify_tracked_validation_state',
                    "bash", str(clone / "scripts/validate.sh"),
                ],
                cwd=clone,
                capture_output=True,
                text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("modified tracked repository state", result.stderr)

    def test_symlinked_script_fails_closed_and_discovery_includes_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target.sh"
            target.write_text("#!/usr/bin/env bash\necho ok\n", encoding="utf-8")
            target.chmod(0o755)
            link = Path(directory) / "linked-script"
            link.symlink_to(target)
            result = subprocess.run(
                ["bash", "-c", 'source "$1"; classify_script "$2"', "bash", str(ENTRYPOINT), str(link)],
                cwd=ROOT, capture_output=True, text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Symlinked validation path", result.stderr)
        self.assertIn("-type l", ENTRYPOINT.read_text(encoding="utf-8"))

    def test_partial_discovery_failure_is_propagated_to_the_parent_shell(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "partial.py"
            path.write_text("print('partial')\n", encoding="utf-8")
            command = r'''
source "$1"
partial="$2"
find() { printf '%s\0' "$partial"; return 7; }
exercise() {
  local -a shell_files=()
  local -a python_files=()
  classify_discovered_paths
}
exercise
'''
            result = subprocess.run(
                ["bash", "-c", command, "bash", str(ENTRYPOINT), str(path)],
                cwd=ROOT, capture_output=True, text=True,
            )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Validation file discovery failed with status 7", result.stderr)

    def test_ci_bootstraps_pinned_linters_before_validation(self):
        source = ENTRYPOINT.read_text(encoding="utf-8")
        self.assertIn('if [[ "${CI:-}" == "true" ]]', source)
        self.assertIn('"$ROOT_DIR/scripts/install-dev-tools.sh"', source)
        self.assertIn('PATH="$ROOT_DIR/build/bin:$PATH"', source)

    def test_standard_validation_replays_the_governed_closure(self):
        source = ENTRYPOINT.read_text(encoding="utf-8")
        self.assertIn('validate-activation-closure', source)
        self.assertIn('ACTIVATION_DEPENDENCY_CLOSURE.json', source)
        self.assertIn('materialization_head="$(git rev-parse HEAD)"', source)
        self.assertIn('"$closure_head" "$materialization_head"', source)
        self.assertGreaterEqual(source.count("verify_tracked_validation_state"), 3)


if __name__ == "__main__":
    unittest.main()
