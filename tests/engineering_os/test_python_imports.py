import hashlib
from pathlib import Path
import tempfile
import unittest

from engineering_os.python_imports import PythonImportError, PythonImportGraph
from engineering_os.test_integrity import ResourceBudget, _test_stats


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


LIMITS = {
    "max_files": 1000,
    "max_total_bytes": 1024 * 1024,
    "max_path_bytes": 1024,
    "max_git_record_bytes": 4096,
    "max_github_pages": 20,
    "max_github_items": 2000,
    "max_github_response_bytes": 1024 * 1024,
    "max_coverage_bytes": 1024 * 1024,
}


def manifest(root):
    result = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            payload = path.read_bytes()
            result[path.relative_to(root).as_posix()] = {
                "sha256": hashlib.sha256(payload).hexdigest(),
                "git_blob_sha": "0" * 40,
            }
    return result


class PythonImportGraphTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "tests").mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def write(self, relative, source):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(source, encoding="utf-8")

    def graph(self, *, limits=None, evidence=None, support_roots=()):
        return PythonImportGraph(
            self.root,
            evidence or manifest(self.root),
            ResourceBudget(limits or LIMITS),
            support_roots=support_roots,
        )

    def test_recursive_cycle_is_resolved_once_and_fingerprinted_deterministically(self):
        self.write("tests/test_service.py", "import support.alpha\ndef test_x():\n    assert True\n")
        self.write("support/__init__.py", "NAME = 'support'\n")
        self.write("support/alpha.py", "import support.beta\nVALUE = 1\n")
        self.write("support/beta.py", "import support.alpha\nVALUE = 2\n")
        first = self.graph().closure("tests/test_service.py")
        second = self.graph().closure("tests/test_service.py")
        self.assertEqual(first.fingerprint, second.fingerprint)
        self.assertEqual(
            first.first_party_paths,
            (
                "support/__init__.py",
                "support/alpha.py",
                "support/beta.py",
            ),
        )

    def test_imported_support_semantic_mutation_changes_closure_fingerprint(self):
        self.write("tests/test_service.py", "from support import VALUE\ndef test_x():\n    assert VALUE\n")
        self.write("support.py", "VALUE = 1\n")
        before = self.graph().closure("tests/test_service.py").fingerprint
        self.write("support.py", "VALUE = 2\n")
        after = self.graph().closure("tests/test_service.py").fingerprint
        self.assertNotEqual(before, after)

    def test_imported_test_support_function_body_mutation_changes_fingerprint(self):
        self.write("tests/test_service.py", "from support import value\ndef test_x():\n    assert value()\n")
        self.write("support.py", "def value():\n    return 1\n")
        before = self.graph(support_roots=("support",)).closure(
            "tests/test_service.py",
        ).fingerprint
        self.write("support.py", "def value():\n    return 2\n")
        after = self.graph(support_roots=("support",)).closure(
            "tests/test_service.py",
        ).fingerprint
        self.assertNotEqual(before, after)

    def test_dynamic_import_inside_test_support_function_fails_closed(self):
        self.write("tests/test_service.py", "from support import value\ndef test_x():\n    assert value()\n")
        self.write("support.py", "def value():\n    return __import__('os')\n")
        with self.assertRaisesRegex(PythonImportError, "PYTHON_IMPORT_DYNAMIC"):
            self.graph(support_roots=("support",)).closure("tests/test_service.py")

    def test_namespace_mutation_inside_test_support_function_fails_closed(self):
        self.write("tests/test_service.py", "from support import value\ndef test_x():\n    assert value()\n")
        self.write(
            "support.py",
            "def value():\n    globals()['collection_flag'] = False\n    return True\n",
        )
        with self.assertRaisesRegex(PythonImportError, "PYTHON_IMPORT_DYNAMIC"):
            self.graph(support_roots=("support",)).closure("tests/test_service.py")

    def test_static_import_inside_test_support_function_is_traversed(self):
        self.write("tests/test_service.py", "from support import value\ndef test_x():\n    assert value()\n")
        self.write(
            "support.py",
            "def value():\n    from helpers.nested import VALUE\n    return VALUE\n",
        )
        self.write("helpers/__init__.py", "NAME = 'helpers'\n")
        self.write("helpers/nested.py", "VALUE = 1\n")
        closure = self.graph(support_roots=("support",)).closure(
            "tests/test_service.py",
        )
        self.assertEqual(
            closure.first_party_paths,
            ("helpers/__init__.py", "helpers/nested.py", "support.py"),
        )

    def test_closed_stdlib_imports_and_path_setup_are_supported(self):
        self.write(
            "tests/test_service.py",
            "import json\nimport unittest\nfrom pathlib import Path\n"
            "ROOT = Path(__file__).resolve().parents[1]\n"
            "FIXTURES = ROOT / 'fixtures'\n"
            "class ServiceTests(unittest.TestCase):\n"
            "    def test_x(self):\n        self.assertTrue(json.loads('true'))\n",
        )
        closure = self.graph().closure("tests/test_service.py")
        self.assertEqual(closure.first_party_paths, ())
        self.assertEqual(closure.stdlib_roots, ("json", "pathlib", "unittest"))

    def test_closed_import_time_setup_supports_regex_types_and_path_parent(self):
        self.write(
            "tests/test_service.py",
            "import re\nfrom dataclasses import dataclass, field\n"
            "from pathlib import Path\nfrom typing import Dict, Tuple\n"
            "PATTERN = re.compile(r'^[a-z]+$')\n"
            "FIXTURES = Path(__file__).resolve().parent / 'fixtures'\n"
            "@dataclass(frozen=True)\nclass Result:\n"
            "    values: Tuple[Dict[str, int], ...] = ()\n"
            "    metadata: Dict[str, int] = field(default_factory=dict)\n",
        )
        closure = self.graph().closure("tests/test_service.py")
        self.assertEqual(
            closure.stdlib_roots,
            ("dataclasses", "pathlib", "re", "typing"),
        )

    def test_relative_first_party_import_is_manifest_bound(self):
        self.write("tests/test_service.py", "import support.package\n")
        self.write("support/__init__.py", "NAME = 'support'\n")
        self.write("support/package/__init__.py", "from .value import VALUE\n")
        self.write("support/package/value.py", "VALUE = 1\n")
        closure = self.graph().closure("tests/test_service.py")
        self.assertEqual(
            closure.first_party_paths,
            (
                "support/__init__.py",
                "support/package/__init__.py",
                "support/package/value.py",
            ),
        )

    def test_stdlib_shadow_fails_closed(self):
        self.write("tests/test_service.py", "import json\ndef test_x():\n    assert True\n")
        self.write("json.py", "VALUE = 'shadow'\n")
        with self.assertRaisesRegex(PythonImportError, "PYTHON_IMPORT_SHADOWED"):
            self.graph().closure("tests/test_service.py")

    def test_unresolved_import_fails_closed(self):
        self.write("tests/test_service.py", "import requests\ndef test_x():\n    assert True\n")
        with self.assertRaisesRegex(PythonImportError, "PYTHON_IMPORT_UNRESOLVED"):
            self.graph().closure("tests/test_service.py")

    def test_contradictory_module_and_package_resolution_fails_closed(self):
        self.write("tests/test_service.py", "import support\ndef test_x():\n    assert True\n")
        self.write("support.py", "VALUE = 1\n")
        self.write("support/__init__.py", "VALUE = 2\n")
        with self.assertRaisesRegex(PythonImportError, "PYTHON_IMPORT_AMBIGUOUS"):
            self.graph().closure("tests/test_service.py")

    def test_dynamic_import_at_collection_time_fails_closed(self):
        self.write("tests/test_service.py", "import support\ndef test_x():\n    assert True\n")
        self.write("support.py", "module = __import__('os')\n")
        with self.assertRaisesRegex(PythonImportError, "PYTHON_IMPORT_DYNAMIC"):
            self.graph().closure("tests/test_service.py")

    def test_stale_manifest_fails_closed(self):
        self.write("tests/test_service.py", "import support\ndef test_x():\n    assert True\n")
        self.write("support.py", "VALUE = 1\n")
        evidence = manifest(self.root)
        self.write("support.py", "VALUE = 2\n")
        with self.assertRaisesRegex(PythonImportError, "PYTHON_IMPORT_MANIFEST_STALE"):
            self.graph(evidence=evidence).closure("tests/test_service.py")

    def test_manifest_path_escape_fails_closed(self):
        evidence = {
            "../outside.py": {"sha256": "0" * 64, "git_blob_sha": "0" * 40},
        }
        with self.assertRaisesRegex(PythonImportError, "PYTHON_IMPORT_MANIFEST_INVALID"):
            self.graph(evidence=evidence)

    def test_manifest_symlink_fails_closed(self):
        self.write("support.py", "VALUE = 1\n")
        (self.root / "tests/test_service.py").symlink_to(self.root / "support.py")
        with self.assertRaisesRegex(PythonImportError, "PYTHON_IMPORT_MANIFEST_INVALID"):
            self.graph().closure("tests/test_service.py")

    def test_import_traversal_consumes_the_shared_aggregate_budget(self):
        self.write("tests/test_service.py", "import support\ndef test_x():\n    assert True\n")
        self.write("support.py", "VALUE = '" + ("x" * 128) + "'\n")
        limits = dict(LIMITS)
        limits["max_total_bytes"] = 64
        with self.assertRaisesRegex(OverflowError, "TEST_RESOURCE_LIMIT"):
            self.graph(limits=limits).closure("tests/test_service.py")

    def test_every_control_plane_python_test_has_a_closed_import_graph(self):
        evidence = {}
        paths = sorted(
            list((REPOSITORY_ROOT / "engineering_os").glob("*.py"))
            + list((REPOSITORY_ROOT / "tests/engineering_os").glob("*.py"))
            + [REPOSITORY_ROOT / "tests/__init__.py"]
        )
        for path in paths:
            payload = path.read_bytes()
            evidence[path.relative_to(REPOSITORY_ROOT).as_posix()] = {
                "sha256": hashlib.sha256(payload).hexdigest(),
                "git_blob_sha": "0" * 40,
            }
        graph = PythonImportGraph(
            REPOSITORY_ROOT,
            evidence,
            ResourceBudget({**LIMITS, "max_total_bytes": 64 * 1024 * 1024}),
        )
        test_paths = sorted(
            path for path in evidence
            if path.startswith("tests/engineering_os/test_")
        )
        self.assertGreaterEqual(len(test_paths), 25)
        for path in test_paths:
            with self.subTest(path=path):
                graph.closure(path)

    def test_every_control_plane_python_test_has_deterministic_case_stats(self):
        evidence = {}
        paths = sorted(
            list((REPOSITORY_ROOT / "engineering_os").glob("*.py"))
            + list((REPOSITORY_ROOT / "tests/engineering_os").glob("*.py"))
            + [REPOSITORY_ROOT / "tests/__init__.py"]
        )
        for path in paths:
            payload = path.read_bytes()
            evidence[path.relative_to(REPOSITORY_ROOT).as_posix()] = {
                "sha256": hashlib.sha256(payload).hexdigest(),
                "git_blob_sha": "0" * 40,
            }
        test_paths = sorted(
            path for path in evidence
            if path.startswith("tests/engineering_os/test_")
        )
        findings = []
        stats = _test_stats(
            REPOSITORY_ROOT,
            test_paths,
            evidence,
            findings,
            {"test_globs": ["tests/**/test_*.py"]},
            ResourceBudget({**LIMITS, "max_total_bytes": 64 * 1024 * 1024}),
        )
        self.assertEqual(findings, [])
        self.assertEqual(set(stats), set(test_paths))


if __name__ == "__main__":
    unittest.main()
