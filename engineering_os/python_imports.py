"""Manifest-bound Python import resolution for test collection semantics."""

import ast
import copy
import hashlib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Mapping, Optional, Sequence, Set, Tuple

from .canonical import canonical_json


_STDLIB_ROOTS = frozenset((
    "__future__", "argparse", "ast", "collections", "concurrent", "copy",
    "dataclasses", "datetime", "hashlib", "io", "json", "keyword", "math",
    "os", "pathlib", "re", "shutil", "sqlite3", "subprocess", "sys",
    "tempfile", "time", "typing", "unittest", "urllib", "zipfile",
))
_FRAMEWORK_ROOTS = frozenset(("pytest",))
_DYNAMIC_NAMES = frozenset((
    "__import__", "eval", "exec", "globals", "locals", "vars", "getattr",
    "setattr", "delattr", "compile",
))
_DYNAMIC_ATTRIBUTES = _DYNAMIC_NAMES | frozenset((
    "import_module", "__dict__", "__globals__", "__getattribute__",
    "f_globals", "f_locals", "modules",
))
_SAFE_BUILTINS = frozenset((
    "Any", "BaseException", "Exception", "False", "None", "NotImplemented",
    "OSError", "OverflowError", "SyntaxError", "True", "TypeError",
    "UnicodeError", "ValueError", "bool", "bytes", "classmethod", "dict",
    "float", "frozenset", "int", "list", "object", "property", "set",
    "staticmethod", "str", "tuple", "type",
))
_SAFE_CALLS = frozenset(("dataclass", "field", "frozenset", "list", "set", "tuple"))
_RUNTIME_DYNAMIC_NAMES = frozenset((
    "__import__", "delattr", "eval", "exec", "globals", "locals", "setattr",
    "vars",
))
_RUNTIME_REFLECTION_ATTRIBUTES = _RUNTIME_DYNAMIC_NAMES | frozenset((
    "__builtins__", "__dict__", "__getattr__", "__globals__", "__getattribute__",
    "f_globals", "f_locals", "import_module", "modules",
))


class PythonImportError(SyntaxError):
    """Stable fail-closed import graph error."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class PythonImportClosure:
    fingerprint: str
    first_party_paths: Tuple[str, ...]
    stdlib_roots: Tuple[str, ...]


def has_dynamic_namespace_mutation(tree: ast.AST) -> bool:
    """Detect runtime namespace mutation while allowing direct benign getattr."""

    parents = {
        id(child): parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }

    def transparent_proxy(call: ast.Call) -> bool:
        if len(call.args) != 2 or call.keywords:
            return False
        parent = parents.get(id(call))
        if not isinstance(parent, ast.Return) or parent.value is not call:
            return False
        function = parents.get(id(parent))
        while function is not None and not isinstance(
            function, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda),
        ):
            function = parents.get(id(function))
        if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return False
        positional = list(function.args.posonlyargs) + list(function.args.args)
        if function.name != "__getattr__" or len(positional) != 2:
            return False
        receiver, attribute = positional
        if (
            not isinstance(call.args[0], ast.Attribute)
            or not isinstance(call.args[1], ast.Name)
            or call.args[1].id != attribute.arg
        ):
            return False
        root = call.args[0]
        while isinstance(root, ast.Attribute):
            root = root.value
        return isinstance(root, ast.Name) and root.id == receiver.arg

    allowed_getattr = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "getattr"
            and len(node.args) in (2, 3)
            and not node.keywords
        ):
            literal_name = (
                isinstance(node.args[1], ast.Constant)
                and isinstance(node.args[1].value, str)
            )
            if literal_name and node.args[1].value in _RUNTIME_REFLECTION_ATTRIBUTES:
                return True
            if literal_name or transparent_proxy(node):
                allowed_getattr.add(id(node.func))
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            if node.id in _RUNTIME_DYNAMIC_NAMES:
                return True
            if node.id == "getattr" and id(node) not in allowed_getattr:
                return True
        if (
            isinstance(node, ast.Attribute)
            and node.attr in _RUNTIME_REFLECTION_ATTRIBUTES | {"getattr"}
        ):
            return True
    return False


class _DefinitionProjector:
    """Project only Python code executed while modules and classes are defined."""

    def __init__(self):
        self.safe_names = set(_SAFE_BUILTINS) | {"__file__", "__name__"}
        self.path_names: Set[str] = set()
        self.frozen_dataclasses: Set[str] = set()

    @staticmethod
    def _main_guard(statement: ast.If) -> bool:
        return (
            isinstance(statement.test, ast.Compare)
            and isinstance(statement.test.left, ast.Name)
            and statement.test.left.id == "__name__"
            and len(statement.test.ops) == 1
            and isinstance(statement.test.ops[0], ast.Eq)
            and len(statement.test.comparators) == 1
            and isinstance(statement.test.comparators[0], ast.Constant)
            and statement.test.comparators[0].value == "__main__"
            and not statement.orelse
        )

    @staticmethod
    def _dotted(value: ast.AST) -> Tuple[str, ...]:
        if isinstance(value, ast.Name):
            return (value.id,)
        if isinstance(value, ast.Attribute):
            parent = _DefinitionProjector._dotted(value.value)
            return parent + (value.attr,) if parent else ()
        return ()

    @staticmethod
    def _bounded(value: ast.AST) -> bool:
        count = 0
        payload = 0
        stack = [(value, 0)]
        while stack:
            node, depth = stack.pop()
            count += 1
            if count > 512 or depth > 24:
                return False
            if isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes)):
                payload += len(node.value.encode("utf-8") if isinstance(node.value, str) else node.value)
                if payload > 16_384:
                    return False
            stack.extend((child, depth + 1) for child in ast.iter_child_nodes(node))
        return True

    def _path_expression(self, value: ast.AST) -> bool:
        if isinstance(value, ast.Name):
            return value.id in self.path_names
        if (
            isinstance(value, ast.Call)
            and not value.keywords
            and len(value.args) == 1
            and isinstance(value.func, ast.Name)
            and value.func.id == "Path"
            and isinstance(value.args[0], ast.Name)
            and value.args[0].id == "__file__"
        ):
            return True
        if (
            isinstance(value, ast.Call)
            and not value.args and not value.keywords
            and isinstance(value.func, ast.Attribute)
            and value.func.attr == "resolve"
        ):
            return self._path_expression(value.func.value)
        if (
            isinstance(value, ast.Subscript)
            and isinstance(value.value, ast.Attribute)
            and value.value.attr == "parents"
            and isinstance(value.slice, ast.Constant)
            and isinstance(value.slice.value, int)
            and 0 <= value.slice.value <= 32
        ):
            return self._path_expression(value.value.value)
        if (
            isinstance(value, ast.Attribute)
            and value.attr == "parent"
        ):
            return self._path_expression(value.value)
        if (
            isinstance(value, ast.BinOp) and isinstance(value.op, ast.Div)
            and isinstance(value.right, ast.Constant)
            and isinstance(value.right.value, str)
            and len(value.right.value.encode("utf-8")) <= 1024
        ):
            return self._path_expression(value.left)
        return False

    def _safe_comprehension(self, value: Any) -> bool:
        generators = getattr(value, "generators", ())
        if len(generators) != 1 or generators[0].is_async or generators[0].ifs:
            return False
        generator = generators[0]
        if not isinstance(generator.target, (ast.Name, ast.Tuple)):
            return False
        target_names = {
            child.id for child in ast.walk(generator.target)
            if isinstance(child, ast.Name)
        }
        if not target_names or any(not name.isidentifier() for name in target_names):
            return False
        if not (
            isinstance(generator.iter, ast.Call)
            and not generator.iter.args and not generator.iter.keywords
            and isinstance(generator.iter.func, ast.Attribute)
            and generator.iter.func.attr == "items"
            and self.safe_expression(generator.iter.func.value)
        ):
            return False
        original = set(self.safe_names)
        self.safe_names.update(target_names)
        try:
            values = [value.elt] if hasattr(value, "elt") else [value.key, value.value]
            return all(self.safe_expression(item) for item in values)
        finally:
            self.safe_names = original

    def safe_expression(self, value: Optional[ast.AST]) -> bool:
        if value is None:
            return True
        if not self._bounded(value):
            return False
        for node in ast.walk(value):
            if isinstance(node, ast.Name) and node.id in _DYNAMIC_NAMES:
                raise PythonImportError("PYTHON_IMPORT_DYNAMIC")
            if (
                isinstance(node, ast.Attribute)
                and node.attr in _DYNAMIC_ATTRIBUTES
                and self._dotted(node) != ("re", "compile")
            ):
                raise PythonImportError("PYTHON_IMPORT_DYNAMIC")
        if isinstance(value, ast.Constant):
            return (
                value.value is None
                or value.value is Ellipsis
                or isinstance(value.value, (bool, int, float, str, bytes))
            )
        if isinstance(value, ast.Name):
            return value.id in self.safe_names
        if isinstance(value, (ast.Tuple, ast.List, ast.Set)):
            return all(self.safe_expression(item) for item in value.elts)
        if isinstance(value, ast.Dict):
            return all(
                key is not None and self.safe_expression(key) and self.safe_expression(item)
                for key, item in zip(value.keys, value.values)
            )
        if isinstance(value, ast.UnaryOp):
            return isinstance(value.op, (ast.UAdd, ast.USub, ast.Not)) and self.safe_expression(value.operand)
        if isinstance(value, ast.BinOp):
            if isinstance(value.op, ast.Div):
                return self._path_expression(value)
            return (
                isinstance(value.op, (ast.Add, ast.Sub, ast.Mult, ast.BitOr))
                and self.safe_expression(value.left) and self.safe_expression(value.right)
            )
        if isinstance(value, ast.Attribute):
            return self.safe_expression(value.value)
        if isinstance(value, ast.Subscript):
            return self.safe_expression(value.value) and self.safe_expression(value.slice)
        if isinstance(value, ast.Call):
            name = self._dotted(value.func)
            if self._path_expression(value):
                return True
            allowed = (
                name in {
                    ("re", "compile"), ("Path",),
                    ("unittest", "skip"), ("unittest", "skipIf"),
                    ("unittest", "skipUnless"),
                    ("pytest", "mark", "parametrize"),
                }
                or (len(name) == 1 and name[0] in _SAFE_CALLS)
                or (len(name) == 1 and name[0] in self.frozen_dataclasses)
            )
            return allowed and all(self.safe_expression(item) for item in value.args) and all(
                item.arg is not None and self.safe_expression(item.value)
                for item in value.keywords
            )
        if isinstance(value, (ast.DictComp, ast.ListComp, ast.SetComp, ast.GeneratorExp)):
            return self._safe_comprehension(value)
        return False

    def _project_function(self, statement: Any) -> ast.AST:
        expressions = list(statement.decorator_list) + list(statement.args.defaults)
        expressions += [item for item in statement.args.kw_defaults if item is not None]
        expressions += [item.annotation for item in (
            list(statement.args.posonlyargs) + list(statement.args.args)
            + list(statement.args.kwonlyargs)
        ) if item.annotation is not None]
        if statement.args.vararg and statement.args.vararg.annotation:
            expressions.append(statement.args.vararg.annotation)
        if statement.args.kwarg and statement.args.kwarg.annotation:
            expressions.append(statement.args.kwarg.annotation)
        if statement.returns is not None:
            expressions.append(statement.returns)
        if not all(self.safe_expression(item) for item in expressions):
            raise PythonImportError("PYTHON_IMPORT_DEFINITION_UNSAFE")
        projected = copy.deepcopy(statement)
        projected.body = [ast.Pass()]
        self.safe_names.add(statement.name)
        return projected

    def _project_class(self, statement: ast.ClassDef) -> ast.ClassDef:
        expressions = list(statement.decorator_list) + list(statement.bases)
        expressions += [item.value for item in statement.keywords]
        if not all(self.safe_expression(item) for item in expressions):
            raise PythonImportError("PYTHON_IMPORT_DEFINITION_UNSAFE")
        projected = copy.deepcopy(statement)
        projected.body = self.project_body(statement.body, class_scope=True)
        if any(
            isinstance(item, ast.Call)
            and self._dotted(item.func) == ("dataclass",)
            and any(
                keyword.arg == "frozen" and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is True
                for keyword in item.keywords
            )
            for item in statement.decorator_list
        ):
            self.frozen_dataclasses.add(statement.name)
        self.safe_names.add(statement.name)
        return projected

    def project_body(self, body: Sequence[ast.stmt], *, class_scope: bool = False) -> list:
        projected = []
        for statement in body:
            if isinstance(statement, (ast.Import, ast.ImportFrom)):
                projected.append(copy.deepcopy(statement))
                for item in statement.names:
                    self.safe_names.add(item.asname or item.name.split(".")[0])
                continue
            if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                projected.append(self._project_function(statement))
                continue
            if isinstance(statement, ast.ClassDef):
                projected.append(self._project_class(statement))
                continue
            if isinstance(statement, ast.Assign):
                if (
                    len(statement.targets) == 1
                    and isinstance(statement.targets[0], ast.Attribute)
                    and statement.targets[0].attr == "__test__"
                    and isinstance(statement.targets[0].value, ast.Name)
                    and statement.targets[0].value.id.startswith("test")
                    and isinstance(statement.value, ast.Constant)
                    and statement.value.value is False
                ):
                    projected.append(copy.deepcopy(statement))
                    continue
                if (
                    len(statement.targets) != 1
                    or not isinstance(statement.targets[0], ast.Name)
                    or not self.safe_expression(statement.value)
                ):
                    raise PythonImportError("PYTHON_IMPORT_EXECUTION_UNSAFE")
                name = statement.targets[0].id
                if self._path_expression(statement.value):
                    self.path_names.add(name)
                self.safe_names.add(name)
                projected.append(copy.deepcopy(statement))
                continue
            if isinstance(statement, ast.AnnAssign):
                if (
                    not isinstance(statement.target, ast.Name)
                    or not self.safe_expression(statement.annotation)
                    or not self.safe_expression(statement.value)
                ):
                    raise PythonImportError("PYTHON_IMPORT_EXECUTION_UNSAFE")
                name = statement.target.id
                if statement.value is not None and self._path_expression(statement.value):
                    self.path_names.add(name)
                self.safe_names.add(name)
                projected.append(copy.deepcopy(statement))
                continue
            if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant):
                projected.append(copy.deepcopy(statement))
                continue
            if isinstance(statement, ast.If) and self._main_guard(statement):
                projected.append(ast.Expr(value=ast.Constant(value="__main__ guard excluded")))
                continue
            if isinstance(statement, ast.Pass):
                projected.append(copy.deepcopy(statement))
                continue
            raise PythonImportError("PYTHON_IMPORT_EXECUTION_UNSAFE")
        return projected

    def project(self, tree: ast.Module) -> str:
        projected = ast.Module(body=self.project_body(tree.body), type_ignores=[])
        return ast.dump(projected, include_attributes=False)


class PythonImportGraph:
    """Resolve and fingerprint a test module's complete import-time closure."""

    def __init__(
        self, root: Any, manifest: Mapping[str, Mapping[str, str]], budget: Any,
        *, support_roots: Sequence[str] = (), support_all: bool = False,
    ):
        self.root = Path(root).resolve(strict=True)
        self.manifest = {str(path): dict(evidence) for path, evidence in manifest.items()}
        for relative in self.manifest:
            parts = PurePosixPath(relative).parts
            if (
                not relative
                or relative.startswith("/")
                or "\\" in relative
                or any(part in ("", ".", "..") for part in parts)
                or PurePosixPath(relative).as_posix() != relative
            ):
                raise PythonImportError("PYTHON_IMPORT_MANIFEST_INVALID")
        self.support_roots = tuple(sorted(set(support_roots)))
        self.support_all = support_all
        for relative in self.support_roots:
            parts = PurePosixPath(relative).parts
            if (
                not relative
                or relative.startswith("/")
                or "\\" in relative
                or any(part in ("", ".", "..") for part in parts)
                or PurePosixPath(relative).as_posix() != relative
            ):
                raise PythonImportError("PYTHON_IMPORT_MANIFEST_INVALID")
        self.budget = budget
        self._loaded: Dict[str, Tuple[ast.Module, str]] = {}
        self._edges: Dict[str, Set[str]] = {}
        self._stdlib: Dict[str, Set[str]] = {}

    def _is_test_support(self, relative: str) -> bool:
        return self.support_all or any(
            relative == root
            or relative == root + ".py"
            or relative.startswith(root + "/")
            for root in self.support_roots
        )

    def _read(self, relative: str) -> Tuple[ast.Module, str]:
        if relative in self._loaded:
            return self._loaded[relative]
        evidence = self.manifest.get(relative)
        if evidence is None:
            raise PythonImportError("PYTHON_IMPORT_MANIFEST_MISSING")
        path = self.root / relative
        if path.is_symlink() or not path.is_file():
            raise PythonImportError("PYTHON_IMPORT_MANIFEST_INVALID")
        self.budget.consume_entry(relative, phase="python-import-graph")
        payload = path.read_bytes()
        self.budget.consume_bytes(len(payload), phase="python-import-graph")
        if hashlib.sha256(payload).hexdigest() != evidence.get("sha256"):
            raise PythonImportError("PYTHON_IMPORT_MANIFEST_STALE")
        try:
            tree = ast.parse(payload.decode("utf-8"), filename=relative)
        except (SyntaxError, UnicodeDecodeError) as error:
            raise PythonImportError("PYTHON_IMPORT_UNPARSABLE") from error
        if self._is_test_support(relative) and has_dynamic_namespace_mutation(tree):
            raise PythonImportError("PYTHON_IMPORT_DYNAMIC")
        projection = _DefinitionProjector().project(tree)
        self._loaded[relative] = (tree, projection)
        return tree, projection

    def _local_candidates(self, module: str) -> Tuple[str, ...]:
        stem = module.replace(".", "/")
        return tuple(
            path for path in (stem + ".py", stem + "/__init__.py")
            if path in self.manifest
        )

    def _package_chain(self, module: str) -> Tuple[str, ...]:
        parts = module.split(".")
        resolved = []
        for size in range(1, len(parts)):
            prefix = ".".join(parts[:size])
            file_candidate = prefix.replace(".", "/") + ".py"
            package_candidate = prefix.replace(".", "/") + "/__init__.py"
            if file_candidate in self.manifest:
                raise PythonImportError("PYTHON_IMPORT_AMBIGUOUS")
            if package_candidate not in self.manifest:
                raise PythonImportError("PYTHON_IMPORT_UNRESOLVED")
            resolved.append(package_candidate)
        candidates = self._local_candidates(module)
        if len(candidates) > 1:
            raise PythonImportError("PYTHON_IMPORT_AMBIGUOUS")
        if not candidates:
            raise PythonImportError("PYTHON_IMPORT_UNRESOLVED")
        resolved.append(candidates[0])
        return tuple(resolved)

    def _absolute_module(self, statement: ast.ImportFrom, caller: str) -> str:
        if statement.level == 0:
            return statement.module or ""
        caller_parts = caller.split("/")[:-1]
        while caller_parts and (
            "/".join(caller_parts) + "/__init__.py"
        ) not in self.manifest:
            caller_parts.pop(0)
        if statement.level > len(caller_parts):
            raise PythonImportError("PYTHON_IMPORT_UNRESOLVED")
        prefix = caller_parts[:len(caller_parts) - statement.level + 1]
        suffix = statement.module.split(".") if statement.module else []
        module = ".".join(prefix + suffix)
        if not module:
            raise PythonImportError("PYTHON_IMPORT_UNRESOLVED")
        return module

    def _resolve(self, module: str) -> Tuple[str, Tuple[str, ...]]:
        if not module or any(not item.isidentifier() for item in module.split(".")):
            raise PythonImportError("PYTHON_IMPORT_UNRESOLVED")
        root = module.split(".")[0]
        local_root = self._local_candidates(root)
        if root in _STDLIB_ROOTS | _FRAMEWORK_ROOTS:
            if local_root:
                raise PythonImportError("PYTHON_IMPORT_SHADOWED")
            return "external", (root,)
        return "first-party", self._package_chain(module)

    @staticmethod
    def _definition_bodies(body: Sequence[ast.stmt]) -> Sequence[ast.stmt]:
        result = []
        for statement in body:
            result.append(statement)
            if isinstance(statement, ast.ClassDef):
                result.extend(PythonImportGraph._definition_bodies(statement.body))
        return result

    def _imports(self, path: str, tree: ast.Module) -> Tuple[Tuple[str, Tuple[str, ...]], ...]:
        resolved = []
        statements = (
            tuple(node for node in ast.walk(tree) if isinstance(node, ast.stmt))
            if self._is_test_support(path)
            else self._definition_bodies(tree.body)
        )
        for statement in statements:
            if isinstance(statement, ast.Import):
                modules = [item.name for item in statement.names]
            elif isinstance(statement, ast.ImportFrom):
                base = self._absolute_module(statement, path)
                modules = [base]
                for item in statement.names:
                    if item.name != "*":
                        optional = base + "." + item.name
                        if self._local_candidates(optional):
                            modules.append(optional)
            else:
                continue
            for module in modules:
                kind, evidence = self._resolve(module)
                resolved.append((kind, evidence))
        return tuple(resolved)

    def closure(self, test_path: str) -> PythonImportClosure:
        if test_path not in self.manifest:
            raise PythonImportError("PYTHON_IMPORT_MANIFEST_MISSING")
        pending = [test_path]
        visited = set()
        first_party = set()
        stdlib = set()
        while pending:
            path = pending.pop()
            if path in visited:
                continue
            visited.add(path)
            tree, _ = self._read(path)
            edges = set()
            external = set()
            for kind, evidence in self._imports(path, tree):
                if kind == "external":
                    external.update(evidence)
                    stdlib.update(evidence)
                    continue
                for imported_path in evidence:
                    edges.add(imported_path)
                    if imported_path != test_path:
                        first_party.add(imported_path)
                    if imported_path not in visited:
                        pending.append(imported_path)
            self._edges[path] = edges
            self._stdlib[path] = external
        nodes = []
        for path in sorted(visited):
            tree, projection = self._loaded[path]
            semantic = (
                ast.dump(tree, include_attributes=False)
                if path != test_path and self._is_test_support(path)
                else projection
            )
            nodes.append({
                "path": "<test-module>" if path == test_path else path,
                "semantic_sha256": hashlib.sha256(semantic.encode("utf-8")).hexdigest(),
                "imports": sorted(self._edges.get(path, ())),
                "stdlib": sorted(self._stdlib.get(path, ())),
            })
        fingerprint = hashlib.sha256(canonical_json(nodes).encode("utf-8")).hexdigest()
        return PythonImportClosure(
            fingerprint,
            tuple(sorted(first_party)),
            tuple(sorted(stdlib)),
        )
