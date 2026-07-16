import ast
import copy
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from engineering_os.test_integrity import analyze_test_integrity
from tests.engineering_os.test_test_integrity import FIXTURES, codes, policy


ROOT = Path(__file__).resolve().parents[2]


class DetectorEvasionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.base = root / "base"
        self.head = root / "head"
        shutil.copytree(FIXTURES / "base", self.base)
        shutil.copytree(FIXTURES / "head", self.head)

    def tearDown(self):
        self.temp.cleanup()

    def analyze(self, configured=None):
        return analyze_test_integrity(
            self.base, self.head, configured or policy(self.base, self.head),
        )

    def test_preimported_skip_alias_cannot_hide_new_decorator(self):
        base = "from unittest import skip as defer\ndef test_value():\n    assert 1 == 1\n"
        head = "from unittest import skip as defer\n@defer('later')\ndef test_value():\n    assert 1 == 1\n"
        for root, text in ((self.base, base), (self.head, head)):
            (root / "tests/test_service.py").write_text(text, encoding="utf-8")
        self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_assertion_comment_cannot_offset_removed_semantic_assertion(self):
        (self.base / "tests/test_service.py").write_text(
            "def test_value():\n    assert value() == 1\n", encoding="utf-8",
        )
        (self.head / "tests/test_service.py").write_text(
            "def test_value():\n    # assert value() == 1\n    value()\n", encoding="utf-8",
        )
        self.assertIn("TEST_ASSERTION_DECLINE", codes(self.analyze()))

    def test_assertion_added_elsewhere_cannot_offset_case_reduction(self):
        (self.base / "tests/test_service.py").write_text(
            "def test_critical():\n    assert critical() == 1\n\n"
            "def test_other():\n    assert other()\n",
            encoding="utf-8",
        )
        (self.head / "tests/test_service.py").write_text(
            "def test_critical():\n    critical()\n\n"
            "def test_other():\n    assert other()\n    assert extra()\n",
            encoding="utf-8",
        )
        self.assertIn("TEST_CASE_ASSERTION_DECLINE", codes(self.analyze()))

    def test_same_count_python_semantic_change_requires_override(self):
        (self.base / "tests/test_service.py").write_text(
            "def test_value():\n    assert value() == 1\n", encoding="utf-8",
        )
        (self.head / "tests/test_service.py").write_text(
            "def test_value():\n    assert True\n", encoding="utf-8",
        )
        self.assertIn("TEST_CASE_BEHAVIOR_CHANGE_AMBIGUOUS", codes(self.analyze()))

    def test_same_assertion_with_weakened_python_setup_requires_override(self):
        (self.base / "tests/test_service.py").write_text(
            "def test_value():\n    value = authoritative()\n    assert value == 1\n", encoding="utf-8",
        )
        (self.head / "tests/test_service.py").write_text(
            "def test_value():\n    value = 1\n    assert value == 1\n", encoding="utf-8",
        )
        self.assertIn("TEST_CASE_BEHAVIOR_CHANGE_AMBIGUOUS", codes(self.analyze()))

    def test_same_count_javascript_semantic_change_requires_override(self):
        for root, assertion in ((self.base, "expect(value()).toBe(1)"), (self.head, "expect(true).toBe(true)")):
            path = root / "tests/value.test.js"
            path.write_text("test('value', () => { %s; });\n" % assertion, encoding="utf-8")
        self.assertIn("TEST_CASE_BEHAVIOR_CHANGE_AMBIGUOUS", codes(self.analyze()))

    def test_behaviorally_unrelated_same_count_replacement_is_not_a_rename(self):
        original = self.head / "tests/test_service.py"
        original.unlink()
        (self.head / "tests/test_unrelated.py").write_text(
            "def test_sourced_value():\n    assert True\n\n"
            "def test_property_invariant():\n    assert True\n",
            encoding="utf-8",
        )
        self.assertTrue(codes(self.analyze()) & {
            "TEST_RENAME_COVERAGE_REDUCED", "TEST_FILE_DELETED",
        })

    def test_malformed_or_truncated_javascript_fails_closed(self):
        for root in (self.base, self.head):
            path = root / "tests/sample.test.js"
            path.write_text("test('ok', () => { expect(1).toBe(1); });\n", encoding="utf-8")
        (self.head / "tests/sample.test.js").write_text(
            "test('ok', () => { expect(1).toBe(1);\n", encoding="utf-8",
        )
        self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_duplicate_python_runtime_identity_is_denied_but_class_scopes_are_distinct(self):
        duplicate = (
            "class First:\n"
            "    def test_value(self):\n        assert True\n"
            "    def test_value(self):\n        assert True\n"
        )
        (self.head / "tests/test_service.py").write_text(duplicate, encoding="utf-8")
        self.assertIn("TEST_CASE_DUPLICATE", codes(self.analyze()))
        valid = (
            "class First:\n    def test_value(self):\n        assert True\n"
            "class Second:\n    def test_value(self):\n        assert True\n"
        )
        for root in (self.base, self.head):
            (root / "tests/test_service.py").write_text(valid, encoding="utf-8")
        self.assertNotIn("TEST_CASE_DUPLICATE", codes(self.analyze()))

    def test_javascript_suite_scope_duplicates_and_lookalikes_are_tokenized(self):
        valid = (
            "// test('comment', () => { expect(false); });\n"
            "const text = \"test('string', () => {})\";\n"
            "describe('one', () => { test('value', () => { expect(1).toBe(1); }); });\n"
            "describe('two', () => { test('value', () => { expect(2).toBe(2); }); });\n"
        )
        for root in (self.base, self.head):
            (root / "tests/suites.test.js").write_text(valid, encoding="utf-8")
        self.assertNotIn("TEST_CASE_DUPLICATE", codes(self.analyze()))
        (self.head / "tests/suites.test.js").write_text(
            "describe('one', () => { test('value', () => { expect(1); }); test('value', () => { expect(1); }); });\n",
            encoding="utf-8",
        )
        self.assertIn("TEST_CASE_DUPLICATE", codes(self.analyze()))

    def test_enclosing_javascript_skipped_suite_marks_inner_case_skipped(self):
        base = "describe('suite', () => { test('value', () => { expect(1); }); });\n"
        head = "describe.skip('suite', () => { test('value', () => { expect(1); }); });\n"
        for root, text in ((self.base, base), (self.head, head)):
            (root / "tests/suite.test.js").write_text(text, encoding="utf-8")
        self.assertIn("TEST_SKIP_ADDED", codes(self.analyze()))

    def test_python_parametrize_cardinality_decline_changes_collection_semantics(self):
        base = (
            "import pytest\n"
            "@pytest.mark.parametrize('value', [1, 2])\n"
            "def test_value(value):\n    assert value > 0\n"
        )
        head = base.replace("[1, 2]", "[1]")
        for root, text in ((self.base, base), (self.head, head)):
            (root / "tests/test_service.py").write_text(text, encoding="utf-8")
        self.assertIn("TEST_CASE_BEHAVIOR_CHANGE_AMBIGUOUS", codes(self.analyze()))

    def test_python_signature_defaults_decorators_and_async_state_are_semantic(self):
        cases = (
            (
                "def test_value(value=1):\n    assert value\n",
                "def test_value(value=2):\n    assert value\n",
            ),
            (
                "import pytest\n@pytest.mark.parametrize('value', [1])\n"
                "def test_value(value):\n    assert value\n",
                "import pytest\n@pytest.mark.parametrize('value', [2])\n"
                "def test_value(value):\n    assert value\n",
            ),
            (
                "async def test_value():\n    assert True\n",
                "def test_value():\n    assert True\n",
            ),
        )
        for base, head in cases:
            with self.subTest(head=head.splitlines()[0]):
                for root, text in ((self.base, base), (self.head, head)):
                    (root / "tests/test_service.py").write_text(text, encoding="utf-8")
                self.assertIn("TEST_CASE_BEHAVIOR_CHANGE_AMBIGUOUS", codes(self.analyze()))

    def test_python_enclosing_class_skip_and_collection_disable_are_detected(self):
        cases = (
            (
                "import unittest\nclass TestValues(unittest.TestCase):\n"
                "    def test_value(self):\n        self.assertTrue(True)\n",
                "import unittest\n@unittest.skip('disabled')\nclass TestValues(unittest.TestCase):\n"
                "    def test_value(self):\n        self.assertTrue(True)\n",
            ),
            (
                "class TestValues:\n    def test_value(self):\n        assert True\n",
                "class TestValues:\n    __test__ = False\n"
                "    def test_value(self):\n        assert True\n",
            ),
        )
        for base, head in cases:
            with self.subTest(disablement=head.splitlines()[1]):
                for root, text in ((self.base, base), (self.head, head)):
                    (root / "tests/test_service.py").write_text(text, encoding="utf-8")
                self.assertIn("TEST_SKIP_ADDED", codes(self.analyze()))

    def test_python_function_test_flag_and_enclosing_collection_metadata_are_semantic(self):
        cases = (
            (
                "def test_value():\n    assert True\n",
                "def test_value():\n    assert True\ntest_value.__test__ = False\n",
            ),
            (
                "class Base:\n    pass\nclass AlternateBase:\n    pass\n"
                "class TestValues(Base):\n    def test_value(self):\n        assert True\n",
                "class Base:\n    pass\nclass AlternateBase:\n    pass\n"
                "class TestValues(AlternateBase):\n    def test_value(self):\n        assert True\n",
            ),
        )
        for base, head in cases:
            with self.subTest(head=head):
                for root, text in ((self.base, base), (self.head, head)):
                    (root / "tests/test_service.py").write_text(text, encoding="utf-8")
                found = codes(self.analyze())
                self.assertTrue(found & {"TEST_SKIP_ADDED", "TEST_CASE_BEHAVIOR_CHANGE_AMBIGUOUS"})

    def test_python_local_base_class_skip_is_inherited_by_collected_tests(self):
        base = (
            "import unittest\n"
            "class Base(unittest.TestCase):\n    pass\n"
            "class TestThing(Base):\n"
            "    def test_x(self):\n        self.assertTrue(True)\n"
        )
        heads = (
            base.replace(
                "class Base(unittest.TestCase):",
                "@unittest.skip('disabled')\nclass Base(unittest.TestCase):",
            ),
            base.replace(
                "class Base(unittest.TestCase):\n    pass",
                "class Base(unittest.TestCase):\n    __test__ = False",
            ),
        )
        for head in heads:
            with self.subTest(head=head):
                for root, text in ((self.base, base), (self.head, head)):
                    (root / "tests/test_service.py").write_text(text, encoding="utf-8")
                self.assertIn("TEST_SKIP_ADDED", codes(self.analyze()))

    def test_python_transitive_local_base_collection_metadata_is_semantic(self):
        base = (
            "import unittest\n"
            "class Root(unittest.TestCase):\n    pass\n"
            "class Middle(Root):\n    pass\n"
            "class TestThing(Middle):\n"
            "    def test_x(self):\n        self.assertTrue(True)\n"
        )
        head = base.replace(
            "class Root(unittest.TestCase):",
            "@unittest.skip('disabled')\nclass Root(unittest.TestCase):",
        )
        for root, text in ((self.base, base), (self.head, head)):
            (root / "tests/test_service.py").write_text(text, encoding="utf-8")
        self.assertIn("TEST_SKIP_ADDED", codes(self.analyze()))

    def test_python_local_base_alias_preserves_inherited_collection_state(self):
        base = (
            "import unittest\n"
            "class Base(unittest.TestCase):\n    pass\n"
            "Alias = Base\n"
            "class TestThing(Alias):\n"
            "    def test_x(self):\n        self.assertTrue(True)\n"
        )
        head = base.replace(
            "class Base(unittest.TestCase):",
            "@unittest.skip('disabled')\nclass Base(unittest.TestCase):",
        )
        for root, text in ((self.base, base), (self.head, head)):
            (root / "tests/test_service.py").write_text(text, encoding="utf-8")
        self.assertIn("TEST_SKIP_ADDED", codes(self.analyze()))

    def test_python_inherited_unittest_method_uses_subclass_skip_state(self):
        base = (
            "import unittest\n"
            "class Base(unittest.TestCase):\n"
            "    def test_x(self):\n        self.assertTrue(True)\n"
            "class TestThing(Base):\n    pass\n"
        )
        head = base.replace(
            "class TestThing(Base):",
            "@unittest.skip('disabled')\nclass TestThing(Base):",
        )
        for root, text in ((self.base, base), (self.head, head)):
            (root / "tests/test_service.py").write_text(text, encoding="utf-8")
        report = self.analyze()
        self.assertIn("TEST_CASE_SKIP_ADDED", codes(report))
        self.assertEqual(report.deltas["skips"], 1)
        skipped = [
            finding.details["case"] for finding in report.findings
            if finding.code == "TEST_CASE_SKIP_ADDED"
        ]
        self.assertEqual(skipped, ["tests/test_service.py::TestThing.test_x"])

    def test_python_transitive_inherited_methods_project_once_per_runtime_class(self):
        base = (
            "import unittest\n"
            "class Root(unittest.TestCase):\n"
            "    def test_x(self):\n        self.assertTrue(True)\n"
            "class Middle(Root):\n    pass\n"
            "class TestThing(Middle):\n    pass\n"
        )
        head = base.replace(
            "class Root(unittest.TestCase):",
            "@unittest.skip('disabled')\nclass Root(unittest.TestCase):",
        )
        for root, text in ((self.base, base), (self.head, head)):
            (root / "tests/test_service.py").write_text(text, encoding="utf-8")
        report = self.analyze()
        self.assertEqual(report.deltas["skips"], 3)

    def test_python_inherited_method_honors_subclass_and_base_test_flags(self):
        base = (
            "import unittest\n"
            "class Base(unittest.TestCase):\n"
            "    def test_x(self):\n        self.assertTrue(True)\n"
            "class TestThing(Base):\n    pass\n"
        )
        heads = (
            base.replace("class TestThing(Base):\n", "class TestThing(Base):\n    __test__ = False\n"),
            base.replace(
                "class Base(unittest.TestCase):\n",
                "class Base(unittest.TestCase):\n    __test__ = False\n",
            ),
        )
        for index, head in enumerate(heads):
            with self.subTest(index=index):
                for root, text in ((self.base, base), (self.head, head)):
                    (root / "tests/test_service.py").write_text(text, encoding="utf-8")
                report = self.analyze()
                self.assertIn("TEST_SKIP_ADDED", codes(report))
                self.assertEqual(report.deltas["skips"], index + 1)

    def test_python_inherited_method_resolves_ordered_local_alias(self):
        base = (
            "import unittest\n"
            "class Base(unittest.TestCase):\n"
            "    def test_x(self):\n        self.assertTrue(True)\n"
            "Alias = Base\nOther = Alias\n"
            "class TestThing(Other):\n    pass\n"
        )
        head = base.replace(
            "class TestThing(Other):",
            "@unittest.skip('disabled')\nclass TestThing(Other):",
        )
        for root, text in ((self.base, base), (self.head, head)):
            (root / "tests/test_service.py").write_text(text, encoding="utf-8")
        self.assertEqual(self.analyze().deltas["skips"], 1)
        base_skip = base.replace(
            "class Base(unittest.TestCase):",
            "@unittest.skip('disabled')\nclass Base(unittest.TestCase):",
        )
        for root, text in ((self.base, base), (self.head, base_skip)):
            (root / "tests/test_service.py").write_text(text, encoding="utf-8")
        self.assertEqual(self.analyze().deltas["skips"], 2)

    def test_python_inherited_method_body_hash_is_projected_per_subclass(self):
        base = (
            "import unittest\n"
            "class Base(unittest.TestCase):\n"
            "    def test_x(self):\n        self.assertTrue(True)\n"
            "class TestThing(Base):\n    pass\n"
        )
        head = base.replace("self.assertTrue(True)", "self.assertTrue(False)")
        for root, text in ((self.base, base), (self.head, head)):
            (root / "tests/test_service.py").write_text(text, encoding="utf-8")
        changed = [
            finding.details["case"] for finding in self.analyze().findings
            if finding.code == "TEST_CASE_BEHAVIOR_CHANGE_AMBIGUOUS"
        ]
        self.assertEqual(changed, [
            "tests/test_service.py::Base.test_x",
            "tests/test_service.py::TestThing.test_x",
        ])

    def test_python_local_override_suppresses_inherited_runtime_method(self):
        direct_override = (
            "import unittest\n"
            "class Base(unittest.TestCase):\n"
            "    def test_x(self):\n        self.assertTrue(True)\n"
            "class TestThing(Base):\n"
            "    def test_x(self):\n        self.assertTrue(True)\n"
        )
        direct_head = direct_override.replace(
            "    def test_x(self):\n        self.assertTrue(True)\n",
            "    @unittest.skip('base only')\n"
            "    def test_x(self):\n        self.assertTrue(True)\n",
            1,
        )
        for root, text in ((self.base, direct_override), (self.head, direct_head)):
            (root / "tests/test_service.py").write_text(text, encoding="utf-8")
        self.assertEqual(self.analyze().deltas["skips"], 1)

        non_test_override = direct_override.replace(
            "class TestThing(Base):\n"
            "    def test_x(self):\n        self.assertTrue(True)\n",
            "class TestThing(Base):\n    test_x = None\n",
        )
        non_test_head = non_test_override.replace(
            "class TestThing(Base):",
            "@unittest.skip('must not invent a case')\nclass TestThing(Base):",
        )
        for root, text in ((self.base, non_test_override), (self.head, non_test_head)):
            (root / "tests/test_service.py").write_text(text, encoding="utf-8")
        self.assertNotIn("TEST_SKIP_ADDED", codes(self.analyze()))

    def test_python_compound_inherited_method_declaration_fails_closed(self):
        source = (
            "import unittest\n"
            "class Base(unittest.TestCase):\n"
            "    if True:\n"
            "        def test_x(self):\n            self.assertTrue(True)\n"
            "class TestThing(Base):\n    pass\n"
        )
        for root in (self.base, self.head):
            (root / "tests/test_service.py").write_text(source, encoding="utf-8")
        self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_multiple_local_base_method_resolution_fails_closed(self):
        sources = (
            (
                "import unittest\n"
                "class Left(unittest.TestCase):\n"
                "    def test_x(self):\n        self.assertTrue(True)\n"
                "class Right(unittest.TestCase):\n"
                "    def test_x(self):\n        self.assertTrue(True)\n"
                "class TestThing(Left, Right):\n    pass\n"
            ),
            (
                "import unittest\n"
                "class Root(unittest.TestCase):\n"
                "    def test_x(self):\n        self.assertTrue(True)\n"
                "class Left(Root):\n    pass\n"
                "class Right(Root):\n    pass\n"
                "class TestThing(Left, Right):\n    pass\n"
            ),
            (
                "import unittest\n"
                "class Base(unittest.TestCase):\n"
                "    def test_x(self):\n        self.assertTrue(True)\n"
                "class TestThing(Base, unittest.TestCase):\n    pass\n"
            ),
        )
        for source in sources:
            with self.subTest(source=source):
                for root in (self.base, self.head):
                    (root / "tests/test_service.py").write_text(source, encoding="utf-8")
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_rebound_local_base_fails_closed(self):
        base = (
            "import unittest\n"
            "class Base(unittest.TestCase):\n    pass\n"
            "class RuntimeBase(unittest.TestCase):\n    pass\n"
            "Base = RuntimeBase\n"
            "class TestThing(Base):\n"
            "    def test_x(self):\n        self.assertTrue(True)\n"
        )
        head = base.replace(
            "class RuntimeBase(unittest.TestCase):",
            "@unittest.skip('disabled')\nclass RuntimeBase(unittest.TestCase):",
        )
        for root, text in ((self.base, base), (self.head, head)):
            (root / "tests/test_service.py").write_text(text, encoding="utf-8")
        self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_duplicate_or_cyclic_local_base_bindings_fail_closed(self):
        cases = (
            (
                "class Base:\n    pass\nAlias = Base\nclass Base:\n    pass\n"
                "class TestThing(Alias):\n    def test_x(self):\n        assert True\n",
                "class Base:\n    __test__ = False\nAlias = Base\nclass Base:\n    pass\n"
                "class TestThing(Alias):\n    def test_x(self):\n        assert True\n",
            ),
            (
                "class Base:\n    pass\nAlias = Base\nOther = Alias\nAlias = Other\n"
                "class TestThing(Alias):\n    def test_x(self):\n        assert True\n",
                "class Base:\n    __test__ = False\nAlias = Base\nOther = Alias\nAlias = Other\n"
                "class TestThing(Alias):\n    def test_x(self):\n        assert True\n",
            ),
        )
        for base, head in cases:
            with self.subTest(head=head):
                for root, text in ((self.base, base), (self.head, head)):
                    (root / "tests/test_service.py").write_text(text, encoding="utf-8")
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_conditional_and_destructured_local_base_rebinding_fails_closed(self):
        cases = (
            (
                "import unittest\nclass Base(unittest.TestCase):\n    pass\n"
                "class RuntimeBase(unittest.TestCase):\n    pass\n"
                "if True:\n    Base = RuntimeBase\n"
                "class TestThing(Base):\n    def test_x(self):\n        self.assertTrue(True)\n",
                "RuntimeBase",
            ),
            (
                "import unittest\nclass Base(unittest.TestCase):\n    pass\n"
                "Alias, = (Base,)\n"
                "class TestThing(Alias):\n    def test_x(self):\n        self.assertTrue(True)\n",
                "Base",
            ),
        )
        for base, disabled in cases:
            head = base.replace(
                "class %s(unittest.TestCase):" % disabled,
                "@unittest.skip('disabled')\nclass %s(unittest.TestCase):" % disabled,
            )
            with self.subTest(base=base):
                for root, text in ((self.base, base), (self.head, head)):
                    (root / "tests/test_service.py").write_text(text, encoding="utf-8")
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_unsupported_local_base_binding_forms_fail_closed(self):
        bindings = (
            "if flag:\n    Alias = Base\n",
            "for Alias in (Base,):\n    pass\n",
            "Alias: type = Base\n",
            "Alias = Base\nAlias += Base\n",
            "if (Alias := Base):\n    pass\n",
            "from module import value as Alias\n",
            "def Alias():\n    return Base\n",
        )
        for binding in bindings:
            base = (
                "class Base:\n    pass\n" + binding
                + "class TestThing(Alias):\n    def test_x(self):\n        assert True\n"
            )
            head = base.replace("class Base:\n    pass", "class Base:\n    __test__ = False")
            with self.subTest(binding=binding):
                for root, text in ((self.base, base), (self.head, head)):
                    (root / "tests/test_service.py").write_text(text, encoding="utf-8")
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_named_expression_and_unsupported_base_shapes_fail_closed(self):
        base_expressions = (
            "(Alias := Base)",
            "identity(Base)",
            "(Base if enabled else Other)",
            "registry[Base]",
        )
        for expression in base_expressions:
            base = (
                "class Base:\n    pass\n"
                "class TestThing(%s):\n    def test_x(self):\n        assert True\n" % expression
            )
            head = base.replace("class Base:\n    pass", "class Base:\n    __test__ = False")
            with self.subTest(expression=expression):
                for root, text in ((self.base, base), (self.head, head)):
                    (root / "tests/test_service.py").write_text(text, encoding="utf-8")
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_nested_class_collection_structures_fail_closed(self):
        structures = (
            (
                "class TestOuter:\n"
                "    class Base:\n        pass\n"
                "    class TestInner(Base):\n"
                "        def test_x(self):\n            assert True\n",
                "    class Base:\n        __test__ = False",
                "    class Base:\n        pass",
            ),
            (
                "class Container:\n"
                "    class Base:\n        pass\n"
                "    class Middle(Base):\n        pass\n"
                "    class TestInner(Middle):\n"
                "        def test_x(self):\n            assert True\n",
                "    class Base:\n        __test__ = False",
                "    class Base:\n        pass",
            ),
            (
                "class Container:\n"
                "    class TestInner(external.Base):\n"
                "        def test_x(self):\n            assert True\n",
                "external.Base",
                "external.Base",
            ),
        )
        for base, replacement, original in structures:
            head = base.replace(original, replacement)
            with self.subTest(base=base):
                for root, text in ((self.base, base), (self.head, head)):
                    (root / "tests/test_service.py").write_text(text, encoding="utf-8")
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_match_descendant_base_binding_fails_closed(self):
        base = (
            "class Base:\n    pass\n"
            "match 1:\n    case 1:\n        Alias = Base\n"
            "class TestThing(Alias):\n    def test_x(self):\n        assert True\n"
        )
        head = base.replace("class Base:\n    pass", "class Base:\n    __test__ = False")
        for root, text in ((self.base, base), (self.head, head)):
            (root / "tests/test_service.py").write_text(text, encoding="utf-8")
        # Python 3.9 rejects the syntax at parse time; 3.10+ must reject the
        # descendant binding through the generic collector.
        self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_generic_descendant_binding_forms_fail_closed(self):
        bindings = (
            "values = [Base for Alias in (Base,)]\n",
            "values = tuple(Base for Alias in (Base,))\n",
            "maker = lambda Alias: Base\n",
            "try:\n    value = Base\nexcept Exception as Alias:\n    pass\n",
            "with context(Base) as Alias:\n    pass\n",
        )
        if hasattr(ast, "TryStar"):
            bindings += (
                "try:\n    value = Base\nexcept* Exception as Alias:\n    pass\n",
            )
        for binding in bindings:
            base = (
                "class Base:\n    pass\n" + binding
                + "class TestThing(Alias):\n    def test_x(self):\n        assert True\n"
            )
            head = base.replace("class Base:\n    pass", "class Base:\n    __test__ = False")
            with self.subTest(binding=binding):
                for root, text in ((self.base, base), (self.head, head)):
                    (root / "tests/test_service.py").write_text(text, encoding="utf-8")
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_future_compound_descendants_use_generic_binding_detection(self):
        from engineering_os.test_integrity import _descendant_binding_names

        class FutureCompound(ast.stmt):
            _fields = ("children",)

        node = FutureCompound(children=[ast.Assign(
            targets=[ast.Name(id="Alias", ctx=ast.Store())],
            value=ast.Name(id="Base", ctx=ast.Load()),
        )])
        self.assertEqual(_descendant_binding_names(node), ("Alias",))

    def test_python_dynamic_namespace_alias_creation_fails_closed(self):
        bindings = (
            'globals()["Alias"] = Base\n',
            "globals().update(Alias=Base)\n",
            'exec("Alias = Base")\n',
        )
        for binding in bindings:
            base = (
                "class Base:\n    pass\n" + binding
                + "class TestThing(Alias):\n    def test_x(self):\n        assert True\n"
            )
            head = base.replace("class Base:\n    pass", "class Base:\n    __test__ = False")
            with self.subTest(binding=binding):
                for root, text in ((self.base, base), (self.head, head)):
                    (root / "tests/test_service.py").write_text(text, encoding="utf-8")
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_unresolved_name_base_fails_closed(self):
        source = (
            "class TestThing(UnknownBase):\n"
            "    def test_x(self):\n        assert True\n"
        )
        for root in (self.base, self.head):
            (root / "tests/test_service.py").write_text(source, encoding="utf-8")
        self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_dynamic_namespace_replacement_of_local_base_fails_closed(self):
        bindings = (
            'globals()["Base"] = RuntimeBase\n',
            "locals().update(Base=RuntimeBase)\n",
            'exec("Base = RuntimeBase")\n',
        )
        for binding in bindings:
            base = (
                "class Base:\n    pass\n"
                "class RuntimeBase:\n    pass\n"
                + binding
                + "class TestThing(Base):\n    def test_x(self):\n        assert True\n"
            )
            head = base.replace(
                "class RuntimeBase:\n    pass",
                "class RuntimeBase:\n    __test__ = False",
            )
            with self.subTest(binding=binding):
                for root, text in ((self.base, base), (self.head, head)):
                    (root / "tests/test_service.py").write_text(text, encoding="utf-8")
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_supported_explicit_and_local_bases_remain_parseable(self):
        sources = (
            (
                "import unittest\n"
                "class TestThing(unittest.TestCase):\n"
                "    def test_x(self):\n        self.assertTrue(True)\n"
            ),
            (
                "class Base:\n    pass\n"
                "class TestThing(Base):\n"
                "    def test_x(self):\n        assert True\n"
            ),
        )
        for source in sources:
            with self.subTest(source=source):
                for root in (self.base, self.head):
                    (root / "tests/test_service.py").write_text(source, encoding="utf-8")
                self.assertNotIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_arbitrary_qualified_base_fails_closed(self):
        source = (
            "import support\n"
            "class TestThing(support.Base):\n"
            "    def test_x(self):\n        assert True\n"
        )
        for root in (self.base, self.head):
            (root / "tests/test_service.py").write_text(source, encoding="utf-8")
        (self.base / "tests/support.py").write_text(
            "class Base:\n    pass\n", encoding="utf-8",
        )
        (self.head / "tests/support.py").write_text(
            "class Base:\n    __test__ = False\n", encoding="utf-8",
        )
        self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_only_exact_unittest_testcase_qualified_base_is_allowlisted(self):
        sources = (
            (
                "import unittest\n"
                "class TestThing(unittest.TestCase):\n"
                "    def test_x(self):\n        self.assertTrue(True)\n"
            ),
            (
                "import unittest\n"
                "class TestThing(unittest.IsolatedAsyncioTestCase):\n"
                "    async def test_x(self):\n        self.assertTrue(True)\n"
            ),
        )
        expected = (False, True)
        for source, denied in zip(sources, expected):
            with self.subTest(source=source):
                for root in (self.base, self.head):
                    (root / "tests/test_service.py").write_text(source, encoding="utf-8")
                self.assertEqual(
                    "TEST_FILE_UNPARSABLE" in codes(self.analyze()), denied,
                )

    def test_python_unittest_allowlist_rejects_repository_shadow(self):
        source = (
            "import unittest\n"
            "class TestThing(unittest.TestCase):\n"
            "    def test_x(self):\n        self.assertTrue(True)\n"
        )
        for root in (self.base, self.head):
            (root / "tests/test_service.py").write_text(source, encoding="utf-8")
            (root / "unittest.py").write_text(
                "class TestCase:\n    __test__ = False\n", encoding="utf-8",
            )
        self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_namespace_factory_alias_shapes_fail_closed(self):
        mutations = (
            'factory = globals\nfactory()["Base"] = RuntimeBase\n',
            '(namespace,) = (globals(),)\nnamespace["Base"] = RuntimeBase\n',
            'dict.update(globals(), {"Base": RuntimeBase})\n',
        )
        for mutation in mutations:
            source = (
                "class Base:\n    pass\nclass RuntimeBase:\n    pass\n"
                + mutation
                + "class TestThing(Base):\n    def test_x(self):\n        assert True\n"
            )
            with self.subTest(mutation=mutation):
                for root in (self.base, self.head):
                    (root / "tests/test_service.py").write_text(source, encoding="utf-8")
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_imported_and_builtins_namespace_aliases_fail_closed(self):
        mutations = (
            "from builtins import globals as factory\n"
            'factory()["Base"] = RuntimeBase\n',
            "import builtins as runtime\n"
            'runtime.globals()["Base"] = RuntimeBase\n',
            "from builtins import exec as run\n"
            'run("Base = RuntimeBase")\n',
            "import builtins\n"
            'getattr(builtins, "globals")()["Base"] = RuntimeBase\n',
        )
        for mutation in mutations:
            source = (
                "class Base:\n    pass\nclass RuntimeBase:\n    pass\n"
                + mutation
                + "class TestThing(Base):\n    def test_x(self):\n        assert True\n"
            )
            with self.subTest(mutation=mutation):
                for root in (self.base, self.head):
                    (root / "tests/test_service.py").write_text(source, encoding="utf-8")
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_safe_top_level_constructs_remain_parseable(self):
        source = (
            "import unittest\n"
            "LABEL = 'collection metadata'\nENABLED = True\n"
            "def helper(value='collection metadata'):\n    return value\n"
            "class Base(unittest.TestCase):\n    pass\n"
            "Alias = Base\n"
            "class TestThing(Alias):\n"
            "    def test_x(self):\n        self.assertEqual(helper(), LABEL)\n"
        )
        for root in (self.base, self.head):
            (root / "tests/test_service.py").write_text(source, encoding="utf-8")
        self.assertNotIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_init_subclass_execution_is_inherited_semantic_metadata(self):
        base = (
            "import unittest\n"
            "class Base(unittest.TestCase):\n"
            "    def __init_subclass__(cls, **kwargs):\n        pass\n"
            "class TestThing(Base):\n"
            "    def test_x(self):\n        self.assertTrue(True)\n"
        )
        head = base.replace(
            "    def __init_subclass__(cls, **kwargs):\n        pass",
            "    def __init_subclass__(cls, **kwargs):\n"
            "        cls.__unittest_skip__ = True\n"
            "        cls.__unittest_skip_why__ = 'disabled'",
        )
        for root, text in ((self.base, base), (self.head, head)):
            (root / "tests/test_service.py").write_text(text, encoding="utf-8")
        self.assertTrue(codes(self.analyze()) & {
            "TEST_SKIP_ADDED", "TEST_CASE_BEHAVIOR_CHANGE_AMBIGUOUS",
        })

    def test_python_imported_definition_decorators_fail_closed(self):
        sources = (
            (
                "from support import decorate\n"
                "@decorate\nclass TestThing:\n"
                "    def test_x(self):\n        assert True\n"
            ),
            (
                "from support import decorate\n"
                "@decorate\ndef test_x():\n    assert True\n"
            ),
        )
        for source in sources:
            with self.subTest(source=source):
                for root in (self.base, self.head):
                    (root / "tests/test_service.py").write_text(source, encoding="utf-8")
                    (root / "tests/support.py").write_text(
                        "def decorate(value):\n    return value\n", encoding="utf-8",
                    )
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_metaclass_and_class_keyword_execution_fail_closed(self):
        sources = (
            (
                "class Meta:\n    pass\n"
                "class TestThing(metaclass=Meta):\n"
                "    def test_x(self):\n        assert True\n"
            ),
            (
                "class Base:\n"
                "    def __init_subclass__(cls, **kwargs):\n        pass\n"
                "class TestThing(Base, collection=False):\n"
                "    def test_x(self):\n        assert True\n"
            ),
        )
        for source in sources:
            with self.subTest(source=source):
                for root in (self.base, self.head):
                    (root / "tests/test_service.py").write_text(source, encoding="utf-8")
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_dynamic_defaults_and_annotations_fail_closed(self):
        declarations = (
            "def test_x(value=factory()):\n    assert value\n",
            "def test_x(value: factory()):\n    assert value\n",
            "def test_x() -> factory():\n    assert True\n",
            "class TestThing:\n"
            "    def test_x(self, value=factory()):\n        assert value\n",
        )
        for declaration in declarations:
            source = "def factory():\n    return True\n" + declaration
            with self.subTest(declaration=declaration):
                for root in (self.base, self.head):
                    (root / "tests/test_service.py").write_text(source, encoding="utf-8")
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_init_subclass_external_execution_fails_closed(self):
        source = (
            "from support import configure\n"
            "class Base:\n"
            "    def __init_subclass__(cls):\n        configure(cls)\n"
            "class TestThing(Base):\n"
            "    def test_x(self):\n        assert True\n"
        )
        for root in (self.base, self.head):
            (root / "tests/test_service.py").write_text(source, encoding="utf-8")
            (root / "tests/support.py").write_text(
                "def configure(cls):\n    return cls\n", encoding="utf-8",
            )
        self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_class_body_import_execution_fails_closed(self):
        imports = (
            "    import support\n",
            "    import support as helper\n",
            "    from support import VALUE\n",
            "    from support import VALUE as setting\n",
        )
        for imported in imports:
            source = (
                "class TestThing:\n" + imported
                + "    def test_x(self):\n        assert True\n"
            )
            with self.subTest(imported=imported):
                for root in (self.base, self.head):
                    (root / "tests/test_service.py").write_text(source, encoding="utf-8")
                (self.base / "support.py").write_text("VALUE = 1\n", encoding="utf-8")
                (self.head / "support.py").write_text(
                    "raise RuntimeError('collection abort')\n", encoding="utf-8",
                )
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_definition_literal_operators_fail_closed(self):
        defaults = (
            "1 / 0",
            "1 << 1000",
            "2 ** 1000",
            "1 @ 2",
            "~1",
        )
        for default in defaults:
            source = "def test_x(value=%s):\n    assert value\n" % default
            with self.subTest(default=default):
                for root in (self.base, self.head):
                    (root / "tests/test_service.py").write_text(source, encoding="utf-8")
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))
        class_source = (
            "class TestThing:\n    VALUE = 1 / 0\n"
            "    def test_x(self):\n        assert True\n"
        )
        for root in (self.base, self.head):
            (root / "tests/test_service.py").write_text(class_source, encoding="utf-8")
        self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_definition_literals_are_bounded(self):
        values = (
            "[0] * 300",
            "[" + ",".join("0" for _ in range(300)) + "]",
            repr("x" * 20_000),
            "[[[[[[[[[[[[[[[[[0]]]]]]]]]]]]]]]]]",
            "{[]}",
        )
        for value in values:
            source = "def test_x(item=%s):\n    assert item is not None\n" % value
            with self.subTest(value=value[:40]):
                for root in (self.base, self.head):
                    (root / "tests/test_service.py").write_text(source, encoding="utf-8")
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_init_subclass_restricts_receiver_attributes(self):
        attributes = ("__bases__", "collection_mode", "__dict__")
        for attribute in attributes:
            source = (
                "class Base:\n"
                "    def __init_subclass__(cls):\n"
                "        cls.%s = ()\n" % attribute
                + "class TestThing(Base):\n"
                "    def test_x(self):\n        assert True\n"
            )
            with self.subTest(attribute=attribute):
                for root in (self.base, self.head):
                    (root / "tests/test_service.py").write_text(source, encoding="utf-8")
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_parametrize_rejects_unknown_or_ambiguous_options(self):
        decorators = (
            "@pytest.mark.parametrize('value', [1], unknown=True)\n",
            "@pytest.mark.parametrize('value', [1], ['id'])\n",
            "@pytest.mark.parametrize('value', [1], **{'ids': ['id']})\n",
            "@pytest.mark.parametrize('value', [1], scope='worker')\n",
        )
        for decorator in decorators:
            source = "import pytest\n" + decorator + "def test_x(value):\n    assert value\n"
            with self.subTest(decorator=decorator):
                for root in (self.base, self.head):
                    (root / "tests/test_service.py").write_text(source, encoding="utf-8")
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_bounded_literals_and_parametrize_options_remain_parseable(self):
        source = (
            "import pytest\n"
            "@pytest.mark.parametrize(\n"
            "    'value', [(1, {'label': 'one'}), (2, {'label': 'two'})],\n"
            "    indirect=False, ids=['one', 'two'], scope='function',\n"
            ")\n"
            "def test_x(value, metadata={'items': [1, -2, +3, None]}):\n"
            "    assert value is not None\n"
        )
        for root in (self.base, self.head):
            (root / "tests/test_service.py").write_text(source, encoding="utf-8")
        self.assertNotIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_module_support_import_fails_closed(self):
        source = (
            "import support\n"
            "import unittest\n"
            "class TestThing(unittest.TestCase):\n"
            "    def test_x(self):\n        self.assertTrue(True)\n"
        )
        for root in (self.base, self.head):
            (root / "tests/test_service.py").write_text(source, encoding="utf-8")
        (self.base / "support.py").write_text("VALUE = 1\n", encoding="utf-8")
        (self.head / "support.py").write_text(
            "import unittest\n"
            "unittest.TestCase.__unittest_skip__ = True\n",
            encoding="utf-8",
        )
        self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_module_import_forms_are_exactly_allowlisted(self):
        denied = (
            "import support\n",
            "import typing\n",
            "import unittest as unit\n",
            "from unittest import TestCase\n",
            "from pytest import mark\n",
            "import unittest, pytest\n",
            "import pytest as framework\n",
        )
        for imported in denied:
            source = imported + "def test_x():\n    assert True\n"
            with self.subTest(imported=imported):
                for root in (self.base, self.head):
                    (root / "tests/test_service.py").write_text(source, encoding="utf-8")
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))
        source = "import unittest\nimport pytest\ndef test_x():\n    assert True\n"
        for root in (self.base, self.head):
            (root / "tests/test_service.py").write_text(source, encoding="utf-8")
        self.assertNotIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_direct_class_collection_flags_affect_skip_state(self):
        existing_base = (
            "import unittest\nclass TestThing(unittest.TestCase):\n"
            "    def test_x(self):\n        self.assertTrue(True)\n"
        )
        existing_head = existing_base.replace(
            "class TestThing(unittest.TestCase):",
            "class TestThing(unittest.TestCase):\n"
            "    __unittest_skip__ = True\n"
            "    __unittest_skip_why__ = 'disabled'",
        )
        for root, text in ((self.base, existing_base), (self.head, existing_head)):
            (root / "tests/test_service.py").write_text(text, encoding="utf-8")
        self.assertIn("TEST_SKIP_ADDED", codes(self.analyze()))

        for root in (self.base, self.head):
            (root / "tests/test_service.py").write_text(existing_base, encoding="utf-8")
        (self.head / "tests/test_new.py").write_text(
            "import unittest\nclass TestNew(unittest.TestCase):\n"
            "    __unittest_skip__ = True\n"
            "    __unittest_skip_why__ = 'disabled'\n"
            "    def test_new(self):\n        self.assertTrue(True)\n",
            encoding="utf-8",
        )
        self.assertIn("TEST_SKIP_ADDED", codes(self.analyze()))

    def test_python_direct_class_collection_flags_require_exact_types(self):
        assignments = (
            "__unittest_skip__ = 1",
            "__unittest_skip__ = 'yes'",
            "__unittest_skip_why__ = 1",
            "__test__ = 0",
            "__test__ = enabled",
        )
        for assignment in assignments:
            source = (
                "enabled = False\nclass TestThing:\n    " + assignment + "\n"
                "    def test_x(self):\n        assert True\n"
            )
            with self.subTest(assignment=assignment):
                for root in (self.base, self.head):
                    (root / "tests/test_service.py").write_text(source, encoding="utf-8")
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_compound_assignment_targets_fail_closed(self):
        assignments = (
            "LEFT, RIGHT = [1]",
            "LEFT, RIGHT = [1, 2]",
            "(LEFT, (RIGHT,)) = (1, (2,))",
            "LEFT, *RIGHT = [1, 2]",
            "LEFT = RIGHT = 1",
        )
        for assignment in assignments:
            source = assignment + "\ndef test_x():\n    assert True\n"
            with self.subTest(assignment=assignment):
                for root in (self.base, self.head):
                    (root / "tests/test_service.py").write_text(source, encoding="utf-8")
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_parametrize_validates_collection_shape_and_signature(self):
        cases = (
            (
                "@pytest.mark.parametrize('left,right', [1, 2])\n"
                "def test_x(left, right):\n    assert left or right\n"
            ),
            (
                "@pytest.mark.parametrize('left,right', [(1,), (2, 3, 4)])\n"
                "def test_x(left, right):\n    assert left or right\n"
            ),
            (
                "@pytest.mark.parametrize('value', [1, 2], ids=['one'])\n"
                "def test_x(value):\n    assert value\n"
            ),
            (
                "@pytest.mark.parametrize('left,right', [(1, 2)], indirect=['missing'])\n"
                "def test_x(left, right):\n    assert left or right\n"
            ),
            (
                "@pytest.mark.parametrize('value,value', [(1, 2)])\n"
                "def test_x(value):\n    assert value\n"
            ),
            (
                "@pytest.mark.parametrize('not-valid', [1])\n"
                "def test_x(not_valid):\n    assert not_valid\n"
            ),
            (
                "@pytest.mark.parametrize('request', [1])\n"
                "def test_x(request):\n    assert request\n"
            ),
            (
                "@pytest.mark.parametrize('value', [1])\n"
                "def test_x(other):\n    assert other\n"
            ),
            (
                "@pytest.mark.parametrize('value', [1])\n"
                "def test_x(value=1):\n    assert value\n"
            ),
            (
                "@pytest.mark.parametrize('value', [1])\n"
                "def test_x(value, /):\n    assert value\n"
            ),
            (
                "@pytest.mark.parametrize('value', [1])\n"
                "@pytest.mark.parametrize('value', [2])\n"
                "def test_x(value):\n    assert value\n"
            ),
        )
        for decorated in cases:
            source = "import pytest\n" + decorated
            with self.subTest(decorated=decorated):
                for root in (self.base, self.head):
                    (root / "tests/test_service.py").write_text(source, encoding="utf-8")
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_parametrize_safe_single_and_multi_argument_shapes(self):
        sources = (
            (
                "import pytest\n@pytest.mark.parametrize('value', [1, (2, 3)])\n"
                "def test_x(value):\n    assert value\n"
            ),
            (
                "import pytest\n"
                "@pytest.mark.parametrize(\n"
                "    ('left', 'right'), [(1, 2), (3, 4)],\n"
                "    ids=['first', 'second'], indirect=['right'],\n"
                ")\n"
                "def test_x(left, right):\n    assert left or right\n"
            ),
        )
        for source in sources:
            with self.subTest(source=source):
                for root in (self.base, self.head):
                    (root / "tests/test_service.py").write_text(source, encoding="utf-8")
                self.assertNotIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_javascript_only_focus_skips_nonfocused_cases(self):
        base = "test('existing', () => { expect(1); });\n"
        head = base + "test.only('focused', () => { expect(2); });\n"
        for root, text in ((self.base, base), (self.head, head)):
            (root / "tests/focus.test.js").write_text(text, encoding="utf-8")
        self.assertIn("TEST_SKIP_ADDED", codes(self.analyze()))

    def test_javascript_new_only_case_is_never_harmless_addition(self):
        (self.head / "tests/focus.test.js").write_text(
            "test.only('focused', () => { expect(1); });\n", encoding="utf-8",
        )
        self.assertIn("TEST_FOCUS_ADDED", codes(self.analyze()))

    def test_javascript_empty_focused_suite_is_not_harmless(self):
        (self.head / "tests/focus.test.js").write_text(
            "describe.only('focused', () => {});\n", encoding="utf-8",
        )
        self.assertIn("TEST_FOCUS_ADDED", codes(self.analyze()))

    def test_javascript_only_computed_alias_and_suite_forms_inherit_focus(self):
        focused = (
            "it['only']('focused', () => { expect(2); });\n",
            "const focused = test.only; focused('focused', () => { expect(2); });\n",
            "describe.only('focused suite', () => { test('inside', () => { expect(2); }); });\n",
            "suite['only']('focused suite', () => { it('inside', () => { expect(2); }); });\n",
            "const focused = context['only']; focused('focused suite', () => { test('inside', () => { expect(2); }); });\n",
        )
        outside = "test('outside', () => { expect(1); });\n"
        for declaration in focused:
            with self.subTest(declaration=declaration):
                for root, text in ((self.base, outside), (self.head, outside + declaration)):
                    (root / "tests/focus.test.js").write_text(text, encoding="utf-8")
                self.assertIn("TEST_SKIP_ADDED", codes(self.analyze()))

    def test_python_module_test_flag_requires_bool_and_controls_all_cases(self):
        base = "__test__ = True\ndef test_x():\n    assert True\n"
        head = "__test__ = False\ndef test_x():\n    assert True\n"
        for root, text in ((self.base, base), (self.head, head)):
            (root / "tests/test_service.py").write_text(text, encoding="utf-8")
        self.assertIn("TEST_SKIP_ADDED", codes(self.analyze()))
        invalid = ("0", "None", "''", "enabled")
        for value in invalid:
            source = "enabled = False\n__test__ = %s\ndef test_x():\n    assert True\n" % value
            with self.subTest(value=value):
                for root in (self.base, self.head):
                    (root / "tests/test_service.py").write_text(source, encoding="utf-8")
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_module_name_alias_requires_prior_local_class(self):
        denied = (
            "ALIAS = missing\n",
            "unittest = missing\n",
            "Alias = Later\nclass Later:\n    pass\n",
            "class Base:\n    pass\nAlias = Base\nAlias = Base\n",
        )
        for binding in denied:
            source = binding + "def test_x():\n    assert True\n"
            with self.subTest(binding=binding):
                for root in (self.base, self.head):
                    (root / "tests/test_service.py").write_text(source, encoding="utf-8")
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))
        source = (
            "class Base:\n    pass\nAlias = Base\nOther = Alias\n"
            "class TestThing(Other):\n"
            "    def test_x(self):\n        assert True\n"
        )
        for root in (self.base, self.head):
            (root / "tests/test_service.py").write_text(source, encoding="utf-8")
        self.assertNotIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_parametrize_rejects_bound_method_receiver(self):
        receivers = ("self", "instance")
        for receiver in receivers:
            source = (
                "import pytest\nclass TestThing:\n"
                "    @pytest.mark.parametrize('%s', [1])\n" % receiver
                + "    def test_x(%s):\n        assert %s\n" % (receiver, receiver)
            )
            with self.subTest(receiver=receiver):
                for root in (self.base, self.head):
                    (root / "tests/test_service.py").write_text(source, encoding="utf-8")
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))
        no_receiver = (
            "import pytest\nclass TestThing:\n"
            "    @pytest.mark.parametrize('value', [1])\n"
            "    def test_x(*, value):\n        assert value\n"
        )
        for root in (self.base, self.head):
            (root / "tests/test_service.py").write_text(no_receiver, encoding="utf-8")
        self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))
        source = (
            "import pytest\nclass TestThing:\n"
            "    @pytest.mark.parametrize('value', [1, 2])\n"
            "    def test_x(self, value):\n        assert value\n"
        )
        for root in (self.base, self.head):
            (root / "tests/test_service.py").write_text(source, encoding="utf-8")
        self.assertNotIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_init_subclass_chained_flag_assignment_fails_closed(self):
        source = (
            "class Base:\n"
            "    def __init_subclass__(cls):\n"
            "        cls.__test__ = cls.__unittest_skip__ = False\n"
            "class TestThing(Base):\n"
            "    def test_x(self):\n        assert True\n"
        )
        for root in (self.base, self.head):
            (root / "tests/test_service.py").write_text(source, encoding="utf-8")
        self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_python_known_safe_definition_metadata_remains_parseable(self):
        sources = (
            (
                "import unittest\n"
                "@unittest.skip('known disabled')\nclass TestThing(unittest.TestCase):\n"
                "    def test_x(self, value: 'int' = 1) -> 'None':\n"
                "        self.assertEqual(value, 1)\n"
            ),
            (
                "import pytest\n"
                "@pytest.mark.parametrize('value', [1, 2], ids=['one', 'two'])\n"
                "def test_x(value: 'int'):\n    assert value > 0\n"
            ),
        )
        for source in sources:
            with self.subTest(source=source):
                for root in (self.base, self.head):
                    (root / "tests/test_service.py").write_text(source, encoding="utf-8")
                self.assertNotIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_javascript_computed_suite_disablement_is_detected(self):
        base = "describe('suite', () => { test('value', () => { expect(1); }); });\n"
        heads = (
            "describe['skip']('suite', () => { test('value', () => { expect(1); }); });\n",
            "describe[\"s\" + 'kip']('suite', () => { test('value', () => { expect(1); }); });\n",
            "const disabled = describe['skip']; disabled('suite', () => { test('value', () => { expect(1); }); });\n",
            "const suiteAlias = describe; suiteAlias.skip('suite', () => { test('value', () => { expect(1); }); });\n",
            "const suiteAlias = describe; const disabled = suiteAlias['skip']; disabled('suite', () => { test('value', () => { expect(1); }); });\n",
        )
        for head in heads:
            with self.subTest(head=head):
                for root, text in ((self.base, base), (self.head, head)):
                    (root / "tests/suite.test.js").write_text(text, encoding="utf-8")
                self.assertIn("TEST_SKIP_ADDED", codes(self.analyze()))

    def test_javascript_dynamic_collection_indirection_fails_closed(self):
        base = "describe('suite', () => { test('value', () => { expect(1); }); });\n"
        heads = (
            "describe[mode]('suite', () => { test('value', () => { expect(1); }); });\n",
            "const disabled = condition ? describe.skip : describe; disabled('suite', () => { test('value', () => { expect(1); }); });\n",
            "(describe)['skip']('suite', () => { test('value', () => { expect(1); }); });\n",
            "globalThis.describe.skip('suite', () => { test('value', () => { expect(1); }); });\n",
            "const {skip: disabled} = describe; disabled('suite', () => { test('value', () => { expect(1); }); });\n",
            "let disabled; disabled = describe.skip; disabled('suite', () => { test('value', () => { expect(1); }); });\n",
        )
        for head in heads:
            with self.subTest(head=head):
                for root, text in ((self.base, base), (self.head, head)):
                    (root / "tests/suite.test.js").write_text(text, encoding="utf-8")
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_javascript_computed_global_suite_reference_fails_closed(self):
        base = "globalThis['describe']('suite', () => { it('value', () => { expect(1); }); });\n"
        heads = (
            "globalThis['describe']['skip']('suite', () => { it('value', () => { expect(1); }); });\n",
            "globalThis['des' + 'cribe']['skip']('suite', () => { it('value', () => { expect(1); }); });\n",
            "window[`describe`]['skip']('suite', () => { it('value', () => { expect(1); }); });\n",
            "const root = globalThis; root['describe']['skip']('suite', () => { it('value', () => { expect(1); }); });\n",
        )
        for head in heads:
            with self.subTest(head=head):
                for root, text in ((self.base, base), (self.head, head)):
                    (root / "tests/suite.test.js").write_text(text, encoding="utf-8")
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_javascript_dynamic_global_computed_reference_fails_closed(self):
        base = "describe('suite', () => { it('value', () => { expect(1); }); });\n"
        heads = (
            "globalThis[suiteName]('suite', () => { it('value', () => { expect(1); }); });\n",
            "window[suiteName]['skip']('suite', () => { it('value', () => { expect(1); }); });\n",
            "const root = globalThis; root[suiteName]['skip']('suite', () => { it('value', () => { expect(1); }); });\n",
        )
        for head in heads:
            with self.subTest(head=head):
                for root, text in ((self.base, base), (self.head, head)):
                    (root / "tests/suite.test.js").write_text(text, encoding="utf-8")
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_javascript_asi_global_alias_computed_suite_fails_closed(self):
        base = (
            "const root = globalThis\nconst suiteName = 'describe'\n"
            "root[suiteName]('suite', () => { it('value', () => { expect(1); }); });\n"
        )
        heads = (
            base.replace("root[suiteName](", "root[suiteName]['skip']("),
            base.replace("const root = globalThis", "let root = globalThis"),
            base.replace(
                "const root = globalThis",
                "const first = globalThis\nconst root = first",
            ),
        )
        for head in heads:
            with self.subTest(head=head):
                for root, text in ((self.base, base), (self.head, head)):
                    (root / "tests/suite.test.js").write_text(text, encoding="utf-8")
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_javascript_asi_alias_after_prior_statement_fails_closed_generally(self):
        bases = (
            "const suiteName = 'describe'\nconst root = globalThis\n"
            "root[suiteName]('suite', () => { it('value', () => { expect(1); }); });\n",
            "const suiteName = 'describe'\nlet root = (globalThis)\n"
            "root[suiteName]('suite', () => { it('value', () => { expect(1); }); });\n",
            "const suiteName = 'describe'\nvar first = globalThis\nconst root = first\n"
            "root[suiteName]('suite', () => { it('value', () => { expect(1); }); });\n",
        )
        for base in bases:
            head = base.replace("root[suiteName](", "root[suiteName]['skip'](")
            with self.subTest(base=base):
                for root, text in ((self.base, base), (self.head, head)):
                    (root / "tests/suite.test.js").write_text(text, encoding="utf-8")
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_javascript_parenthesized_global_computed_suite_fails_closed(self):
        base = "(globalThis)[suiteName]('suite', () => { it('value', () => { expect(1); }); });\n"
        heads = (
            "(globalThis)[suiteName]['skip']('suite', () => { it('value', () => { expect(1); }); });\n",
            "((globalThis))[suiteName]['skip']('suite', () => { it('value', () => { expect(1); }); });\n",
            "(window)[suiteName]['skip']('suite', () => { it('value', () => { expect(1); }); });\n",
        )
        for head in heads:
            with self.subTest(head=head):
                for root, text in ((self.base, base), (self.head, head)):
                    (root / "tests/suite.test.js").write_text(text, encoding="utf-8")
                self.assertIn("TEST_FILE_UNPARSABLE", codes(self.analyze()))

    def test_package_test_command_change_is_blocked(self):
        for root, command in ((self.base, "vitest"), (self.head, "echo tests-disabled")):
            (root / "package.json").write_text(
                json.dumps({"scripts": {"test": command}}), encoding="utf-8",
            )
        self.assertIn("TEST_CONFIGURATION_WEAKENED", codes(self.analyze()))

    def test_unknown_test_config_or_workflow_change_requires_review(self):
        for root, value in ((self.base, "addopts = -q\n"), (self.head, "addopts = --tb=no\n")):
            (root / "pytest.ini").write_text(value, encoding="utf-8")
        for root, command in ((self.base, "pytest"), (self.head, "echo no-tests")):
            path = root / ".github/workflows/quality.yml"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("steps:\n  - run: %s\n" % command, encoding="utf-8")
        found = codes(self.analyze())
        self.assertIn("TEST_CONFIGURATION_CHANGE_AMBIGUOUS", found)
        self.assertIn("VALIDATION_WORKFLOW_CHANGE_AMBIGUOUS", found)

    def test_nested_package_and_runner_configs_are_protected(self):
        for root, command in ((self.base, "vitest"), (self.head, "echo disabled")):
            package = root / "packages/client/package.json"
            package.parent.mkdir(parents=True, exist_ok=True)
            package.write_text(json.dumps({"scripts": {"test": command}}), encoding="utf-8")
            config = root / "packages/client/vitest.config.yaml"
            config.write_text("include:\n  - tests/**\n" if root == self.base else "include: []\n", encoding="utf-8")
        found = codes(self.analyze())
        self.assertIn("TEST_CONFIGURATION_WEAKENED", found)
        self.assertTrue(found & {"TEST_CONFIGURATION_CHANGE_AMBIGUOUS", "TEST_CONFIGURATION_WEAKENED"})

    def test_nested_yaml_fixture_reduction_is_counted(self):
        for root, cases in ((self.base, 2), (self.head, 1)):
            path = root / "tests/fixtures/cases.yaml"
            path.write_text(
                "suite:\n  cases:\n" + "".join("    - input: %d\n" % index for index in range(cases)),
                encoding="utf-8",
            )
        self.assertIn("TEST_FIXTURE_CASE_DECLINE", codes(self.analyze()))

    def test_same_count_fixture_substitution_fails_closed_as_ambiguous(self):
        for root, value in ((self.base, 1), (self.head, 999)):
            (root / "tests/fixtures/cases.json").write_text(
                json.dumps([{"input": value, "output": 2}]), encoding="utf-8",
            )
        self.assertIn("TEST_FIXTURE_SUBSTITUTION_AMBIGUOUS", codes(self.analyze()))

    def test_deletion_of_configured_quality_yaml_workflow_is_blocked(self):
        for root in (self.base, self.head):
            path = root / ".github/workflows/quality.yaml"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("jobs: {}\n", encoding="utf-8")
        (self.head / ".github/workflows/quality.yaml").unlink()
        self.assertIn("VALIDATION_WORKFLOW_DELETED", codes(self.analyze()))

    def test_stale_or_copied_coverage_evidence_is_denied(self):
        configured = policy(self.base, self.head)
        for root, commit in ((self.base, configured["base_sha"]), (self.head, configured["base_sha"])):
            (root / ".eos").mkdir(exist_ok=True)
            (root / ".eos/coverage.json").write_text(json.dumps({
                "schema_version": "1.0.0", "repository": "acme/widgets",
                "commit_sha": commit, "source_manifest_sha256": "0" * 64,
                "generated_at": "2026-07-14T00:00:00Z",
                "coverage": {"lines_percent": 90.0},
            }), encoding="utf-8")
        configured = policy(self.base, self.head)
        self.assertTrue(codes(self.analyze(configured)) & {
            "TEST_COVERAGE_EVIDENCE_STALE", "TEST_COVERAGE_EVIDENCE_UNBOUND",
            "TEST_COVERAGE_ATTESTATION_UNAVAILABLE",
        })

    def test_coverage_file_requires_closed_authenticated_attestation(self):
        configured = policy(self.base, self.head)
        from tests.engineering_os.test_test_integrity import write_coverage
        write_coverage(self.base, configured, configured["base_sha"], 90.0)
        write_coverage(self.head, configured, configured["head_sha"], 90.0)
        configured = policy(self.base, self.head)
        configured["coverage_attestations"] = None
        self.assertIn("TEST_COVERAGE_ATTESTATION_UNAVAILABLE", codes(self.analyze(configured)))

    def test_aggregate_file_count_total_and_path_caps_fail_closed(self):
        for index in range(5):
            (self.head / ("tests/test_extra_%d.py" % index)).write_text(
                "def test_value_%d():\n    assert True\n" % index, encoding="utf-8",
            )
        configured = policy(self.base, self.head)
        configured["configuration"].update({
            "max_files": 3, "max_total_bytes": 100000,
            "max_path_bytes": 20, "max_git_record_bytes": 128,
            "max_github_pages": 2, "max_github_items": 10,
            "max_github_response_bytes": 1024, "max_coverage_bytes": 1024,
        })
        self.assertIn("TEST_RESOURCE_LIMIT", codes(self.analyze(configured)))

    def test_github_page_item_and_response_caps_are_exact(self):
        from engineering_os.test_integrity_cli import validate_github_pages
        for pages, limits in (
            ([[{}], [{}], [{}]], (2, 10, 1000)),
            ([[{}, {}, {}]], (2, 2, 1000)),
            ([[{"body": "x" * 100}]], (2, 10, 20)),
        ):
            with self.subTest(limits=limits):
                with self.assertRaisesRegex(ValueError, "TEST_GITHUB_RESOURCE_LIMIT"):
                    validate_github_pages(pages, *limits)

    def test_large_file_resource_cap_returns_structured_denial(self):
        path = self.head / "tests/test_large.py"
        path.write_text("def test_large():\n    assert True\n" + ("#x\n" * 100), encoding="utf-8")
        configured = policy(self.base, self.head)
        configured["configuration"]["max_file_bytes"] = 64
        report = self.analyze(configured)
        self.assertIn("TEST_RESOURCE_LIMIT", codes(report))

    def test_shared_budget_counts_scan_and_parse_phases(self):
        configured = policy(self.base, self.head)
        scan_bytes = sum(path.stat().st_size for root in (self.base, self.head) for path in root.rglob("*") if path.is_file())
        configured["configuration"]["max_total_bytes"] = scan_bytes
        self.assertIn("TEST_RESOURCE_LIMIT", codes(self.analyze(configured)))

    def test_checkout_traversal_streams_without_path_rglob_materialization(self):
        configured = policy(self.base, self.head)
        with mock.patch.object(Path, "rglob", side_effect=AssertionError("unbounded rglob")):
            report = self.analyze(configured)
        self.assertNotIn("TEST_CHECKOUT_UNAVAILABLE", codes(report))

    def test_resource_budget_uses_one_exact_aggregate_boundary(self):
        from engineering_os.test_integrity import ResourceBudget
        budget = ResourceBudget({
            **policy(self.base, self.head)["configuration"],
            "max_total_bytes": 10,
        })
        budget.consume_bytes(4, phase="discovery")
        budget.consume_bytes(6, phase="parsing")
        with self.assertRaisesRegex(OverflowError, "TEST_RESOURCE_LIMIT"):
            budget.consume_bytes(1, phase="reporting")

    def test_resource_budget_rejects_many_small_files_across_phases(self):
        from engineering_os.test_integrity import ResourceBudget
        budget = ResourceBudget({
            **policy(self.base, self.head)["configuration"],
            "max_files": 3,
        })
        budget.consume_file("a", phase="discovery")
        budget.consume_file("b", phase="git")
        budget.consume_file("c", phase="parsing")
        with self.assertRaisesRegex(OverflowError, "TEST_RESOURCE_LIMIT"):
            budget.consume_file("d", phase="reporting")

    def test_resource_budget_charges_directory_entries_at_exact_boundary(self):
        from engineering_os.test_integrity import ResourceBudget
        configured = policy(self.base, self.head)["configuration"]
        budget = ResourceBudget({**configured, "max_files": 3})
        budget.consume_entry("one", phase="directory")
        budget.consume_entry("two", phase="directory")
        budget.consume_entry("three", phase="file")
        with self.assertRaisesRegex(OverflowError, "TEST_RESOURCE_LIMIT"):
            budget.consume_entry("four", phase="directory")

    def test_checkout_directory_fanout_depth_and_path_are_bounded(self):
        cases = ("wide", "deep", "long")
        for shape in cases:
            with self.subTest(shape=shape):
                shutil.rmtree(self.head)
                shutil.copytree(FIXTURES / "head", self.head)
                if shape == "wide":
                    for index in range(8):
                        (self.head / ("empty-%02d" % index)).mkdir()
                elif shape == "deep":
                    cursor = self.head
                    for index in range(8):
                        cursor = cursor / ("d%d" % index)
                        cursor.mkdir()
                else:
                    (self.head / ("d" * 80)).mkdir()
                configured = policy(self.base, self.head)
                configured["configuration"]["max_files"] = 2 * (
                    len(configured["base_manifest"]) + len(configured["head_manifest"])
                ) + 5
                if shape == "long":
                    configured["configuration"]["max_path_bytes"] = 64
                self.assertIn("TEST_RESOURCE_LIMIT", codes(self.analyze(configured)))

    def test_report_contains_authenticated_mission_and_pr_truth(self):
        report = self.analyze().to_dict()
        for field in (
            "mission_id", "mission_issue", "pull_request", "declared_tier",
            "computed_tier", "producer_identity", "adversary_identity",
        ):
            self.assertIn(field, report)

    def test_mission_truth_is_derived_from_authenticated_ready_history_and_risk(self):
        from engineering_os.canonical import content_sha256
        from engineering_os.test_integrity import authenticate_integrity_context
        from tests.engineering_os.test_commands import (
            audit_event, event_comment, ready_details, source_comment, valid_context,
        )
        mission, repository_policy = valid_context()
        source = source_comment(8001, "agent-a", "/eos ready")
        event = audit_event(
            "mission.ready", "agent-a", "producer", source["html_url"],
            source["created_at"], 1, None, ready_details(mission, "ready-8001"),
        )
        context = authenticate_integrity_context(
            mission, [source, event_comment(8002, [event])], repository_policy,
            ["engineering_os/test_integrity.py"],
            repository=repository_policy["repository"], mission_issue=101,
            pull_request=42, base_sha="1" * 40, head_sha="2" * 40,
        )
        self.assertEqual(context["mission_sha256"], content_sha256(mission))
        self.assertEqual(context["mission_event_hash"], event["event_hash"])
        self.assertEqual(context["effective_tier"], "Tier 2")
        mission["risk_tier"] = "Tier 1"
        with self.assertRaisesRegex(ValueError, "TEST_MISSION"):
            authenticate_integrity_context(
                mission, [source, event_comment(8002, [event])], repository_policy,
                ["engineering_os/test_integrity.py"],
                repository=repository_policy["repository"], mission_issue=101,
                pull_request=42, base_sha="1" * 40, head_sha="2" * 40,
            )


class CliFailureArtifactTests(unittest.TestCase):
    def test_cli_writes_structured_report_before_checkout_or_parse_failure(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "report.json"
            process = subprocess.run([
                str(ROOT / "scripts/engineering-os/validate-test-integrity"),
                "--base-root", str(Path(temporary) / "missing-base"),
                "--head-root", str(Path(temporary) / "missing-head"),
                "--base-sha", "1" * 40, "--head-sha", "2" * 40,
                "--repository", "acme/widgets", "--base-policy", "missing.json",
                "--pull-request", "42", "--output", str(output),
            ], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertNotEqual(process.returncode, 0)
            self.assertTrue(output.is_file())
            value = json.loads(output.read_text(encoding="utf-8"))
            self.assertFalse(value["allowed"])
            self.assertEqual(value["findings"][0]["code"], "TEST_INTEGRITY_NOT_COMPLETED")

    def test_workflow_initializes_report_before_any_checkout(self):
        workflow = (ROOT / ".github/workflows/reusable-test-integrity.yml").read_text(encoding="utf-8")
        self.assertLess(workflow.index("Initialize fail-closed report"), workflow.index("actions/checkout"))
        self.assertIn("pull-requests: read", workflow)
        self.assertIn("issues: read", workflow)
        self.assertIn("actions: read", workflow)
        self.assertIn("AIFO-EOS-MISSION-ISSUE", workflow)

    def test_public_cli_exposes_no_raw_override_or_identity_inputs(self):
        wrapper = (ROOT / "scripts/engineering-os/validate-test-integrity").read_text(encoding="utf-8")
        adapter = (ROOT / "engineering_os/test_integrity_cli.py").read_text(encoding="utf-8")
        for forbidden in (
            "--override", "--review", "--approval", "--reviewer-identity",
        ):
            self.assertNotIn(forbidden, wrapper)
            self.assertNotIn(forbidden, adapter)

    def test_cli_resource_exhaustion_replaces_sentinel_with_bounded_error(self):
        from engineering_os.test_integrity_cli import main
        from tests.engineering_os.helpers import load_fixture
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / "report.json"
            repository_policy = root / "policy.json"
            repository_policy.write_text(
                json.dumps(load_fixture("policy-control-plane.json")), encoding="utf-8",
            )
            with mock.patch(
                "engineering_os.test_integrity_cli.derive_git_manifests",
                side_effect=OverflowError("TEST_RESOURCE_LIMIT"),
            ):
                status = main([
                    "--base-root", str(root), "--head-root", str(root),
                    "--base-sha", "1" * 40, "--head-sha", "2" * 40,
                    "--repository", "josephmccann/AIFO-Control-Plane",
                    "--base-policy", str(repository_policy), "--pull-request", "42",
                    "--output", str(output),
                ])
            self.assertEqual(status, 1)
            value = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(value["findings"][0]["code"], "TEST_RESOURCE_LIMIT")


class RevisionEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def git(self, path, *args):
        return subprocess.run(
            ["git", "-C", str(path), *args], check=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout.decode("utf-8").strip()

    def repository(self, name, content="def test_value():\n    assert True\n"):
        repo = self.root / name
        repo.mkdir()
        self.git(repo, "init", "-q")
        self.git(repo, "config", "user.name", "EOS Test")
        self.git(repo, "config", "user.email", "eos@example.invalid")
        (repo / "tests").mkdir()
        (repo / "tests/test_value.py").write_text(content + "# repository: " + name + "\n", encoding="utf-8")
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-qm", "base")
        return repo, self.git(repo, "rev-parse", "HEAD")

    def derive(self, base, head, base_sha, head_sha):
        from engineering_os.test_integrity_cli import derive_git_manifests
        return derive_git_manifests(base, head, base_sha, head_sha, 1024 * 1024)

    def test_unrelated_repositories_are_rejected(self):
        base, base_sha = self.repository("base")
        head, head_sha = self.repository("head")
        with self.assertRaisesRegex(ValueError, "TEST_REVISION_UNRELATED"):
            self.derive(base, head, base_sha, head_sha)

    def test_dirty_or_untracked_head_is_rejected(self):
        repo, base_sha = self.repository("repo")
        (repo / "tests/test_value.py").write_text("def test_value():\n    assert 1 == 1\n", encoding="utf-8")
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-qm", "head")
        head_sha = self.git(repo, "rev-parse", "HEAD")
        base = self.root / "base-worktree"
        self.git(repo, "worktree", "add", "-q", "--detach", str(base), base_sha)
        (repo / "tests/test_value.py").write_text("dirty\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "TEST_CHECKOUT_DIRTY"):
            self.derive(base, repo, base_sha, head_sha)
        self.git(repo, "reset", "--hard", "-q", head_sha)
        (repo / "untracked.txt").write_text("untrusted", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "TEST_CHECKOUT_DIRTY"):
            self.derive(base, repo, base_sha, head_sha)

    def test_swapped_revision_direction_is_rejected(self):
        repo, base_sha = self.repository("repo")
        (repo / "tests/test_value.py").write_text("def test_value():\n    assert 1 == 1\n", encoding="utf-8")
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-qm", "head")
        head_sha = self.git(repo, "rev-parse", "HEAD")
        base = self.root / "base-worktree"
        self.git(repo, "worktree", "add", "-q", "--detach", str(base), base_sha)
        with self.assertRaisesRegex(ValueError, "TEST_REVISION_UNRELATED"):
            self.derive(repo, base, head_sha, base_sha)

    def test_git_adapter_consumes_existing_shared_budget(self):
        from engineering_os.test_integrity import ResourceBudget
        from engineering_os.test_integrity_cli import derive_git_manifests
        repo, base_sha = self.repository("repo")
        (repo / "tests/test_value.py").write_text(
            "def test_value():\n    assert 1 == 1\n", encoding="utf-8",
        )
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-qm", "head")
        head_sha = self.git(repo, "rev-parse", "HEAD")
        base = self.root / "base-worktree"
        self.git(repo, "worktree", "add", "-q", "--detach", str(base), base_sha)
        limits = {
            "max_files": 100, "max_total_bytes": 512,
            "max_path_bytes": 128, "max_git_record_bytes": 128,
            "max_github_pages": 2, "max_github_items": 10,
            "max_github_response_bytes": 256, "max_coverage_bytes": 256,
        }
        budget = ResourceBudget(limits)
        budget.consume_bytes(500, phase="prior-github")
        with self.assertRaisesRegex(OverflowError, "TEST_RESOURCE_LIMIT"):
            derive_git_manifests(
                base, repo, base_sha, head_sha, 1024 * 1024, limits,
                resource_budget=budget,
            )

    def test_git_adapter_reconciliation_charges_empty_directory_fanout(self):
        from engineering_os.test_integrity import ResourceBudget
        from engineering_os.test_integrity_cli import derive_git_manifests
        repo, base_sha = self.repository("repo")
        (repo / "tests/test_value.py").write_text(
            "def test_value():\n    assert 1 == 1\n", encoding="utf-8",
        )
        self.git(repo, "add", ".")
        self.git(repo, "commit", "-qm", "head")
        head_sha = self.git(repo, "rev-parse", "HEAD")
        base = self.root / "base-worktree"
        self.git(repo, "worktree", "add", "-q", "--detach", str(base), base_sha)
        for index in range(5):
            (repo / ("empty-%d" % index)).mkdir()
        limits = {
            "max_files": 8, "max_total_bytes": 65536,
            "max_path_bytes": 128, "max_git_record_bytes": 256,
            "max_github_pages": 2, "max_github_items": 10,
            "max_github_response_bytes": 1024, "max_coverage_bytes": 1024,
        }
        with self.assertRaisesRegex(OverflowError, "TEST_RESOURCE_LIMIT"):
            derive_git_manifests(
                base, repo, base_sha, head_sha, 1024 * 1024, limits,
                resource_budget=ResourceBudget(limits),
            )


class SharedTransportBudgetTests(unittest.TestCase):
    def test_github_transport_uses_prior_phase_budget_without_reset(self):
        from engineering_os.test_integrity import ResourceBudget
        from engineering_os.test_integrity_cli import _gh
        limits = {
            "max_files": 100, "max_total_bytes": 12,
            "max_path_bytes": 128, "max_git_record_bytes": 128,
            "max_github_pages": 2, "max_github_items": 10,
            "max_github_response_bytes": 12, "max_coverage_bytes": 12,
        }
        budget = ResourceBudget(limits)
        budget.consume_bytes(11, phase="git")
        with mock.patch(
            "engineering_os.test_integrity_cli._command_bytes", return_value=b"{}",
        ):
            with self.assertRaisesRegex(OverflowError, "TEST_RESOURCE_LIMIT"):
                _gh("repos/acme/widgets", max_response_bytes=12, resource_budget=budget)

    def test_policy_input_uses_prior_phase_budget_without_unbounded_read(self):
        from engineering_os.test_integrity import ResourceBudget
        from engineering_os.test_integrity_cli import _bounded_file_bytes
        limits = {
            "max_files": 100, "max_total_bytes": 12,
            "max_path_bytes": 128, "max_git_record_bytes": 128,
            "max_github_pages": 2, "max_github_items": 10,
            "max_github_response_bytes": 12, "max_coverage_bytes": 12,
        }
        budget = ResourceBudget(limits)
        budget.consume_bytes(9, phase="prior")
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "policy.json"
            path.write_bytes(b"1234")
            with self.assertRaisesRegex(OverflowError, "TEST_RESOURCE_LIMIT"):
                _bounded_file_bytes(path, budget, phase="policy-input")
