import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts/engineering-os/validate-activation-closure"
ENTRYPOINT = ROOT / "scripts/validate.sh"


class ValidationClassificationTests(unittest.TestCase):
    def test_extensionless_python_validator_has_python_shebang(self):
        self.assertTrue(VALIDATOR.read_text(encoding="utf-8").splitlines()[0].startswith("#!/usr/bin/env python3"))

    def test_entrypoint_classifies_by_extension_and_audited_shebang(self):
        source = ENTRYPOINT.read_text(encoding="utf-8")
        for marker in ("*.sh", "*.py", "'#!'*bash", "'#!'*/sh", "'#!'*python", "SHELL_FILES", "PYTHON_FILES"):
            self.assertIn(marker, source)
        self.assertIn("Unclassified executable script:", source)
        self.assertNotIn('shellcheck "$ROOT_DIR"/scripts/engineering-os/*', source)

    def test_entrypoint_shell_syntax_is_valid(self):
        result = subprocess.run(["bash", "-n", str(ENTRYPOINT)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_python_validator_compiles_through_python_path(self):
        result = subprocess.run(["python3", "-m", "py_compile", str(VALIDATOR)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
