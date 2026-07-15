"""Small dependency-free validator for the repository's closed JSON contracts."""

import json
import math
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .errors import Violation


DOCUMENT_KINDS = (
    "mission",
    "evidence",
    "approval",
    "audit-event",
    "repository-policy",
    "frozen-path",
    "incident",
    "mission-state",
    "finding",
    "authority",
    "metrics",
    "airtable-record",
)

SCHEMA_ROOT = Path(__file__).resolve().parents[1] / "schemas" / "engineering-os"


def _violation(code: str, message: str, path: str, **details: Any) -> Violation:
    return Violation(code=code, message=message, path=path, details=details)


def _type_matches(expected: str, value: Any) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "null":
        return value is None
    return False


def _walk(schema: Dict[str, Any], value: Any, path: str, kind: str) -> Iterable[Violation]:
    if isinstance(value, float) and not math.isfinite(value):
        yield _violation("SCHEMA_NUMBER_NOT_FINITE", "JSON numbers must be finite", path)
        return

    expected = schema.get("type")
    if expected is not None:
        expected_types = [expected] if isinstance(expected, str) else expected
        if not any(_type_matches(item, value) for item in expected_types):
            yield _violation("SCHEMA_TYPE", "value has the wrong JSON type", path, expected=expected)
            return

    if "const" in schema and value != schema["const"]:
        yield _violation("SCHEMA_CONST", "value does not match the required constant", path, expected=schema["const"])
    if "enum" in schema and value not in schema["enum"]:
        yield _violation("SCHEMA_ENUM", "value is outside the explicit enum", path, allowed=schema["enum"])

    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for field in schema.get("required", []):
            if field not in value:
                code = "MISSION_FIELD_REQUIRED" if kind == "mission" and path == "$" else "SCHEMA_FIELD_REQUIRED"
                yield _violation(code, "required field is missing", path, field=field)
        if schema.get("additionalProperties") is False:
            for field in sorted(set(value) - set(properties)):
                yield _violation(
                    "SCHEMA_ADDITIONAL_PROPERTY",
                    "closed record contains an unknown property",
                    "%s.%s" % (path, field),
                    field=field,
                )
        for field, child in properties.items():
            if field in value:
                yield from _walk(child, value[field], "%s.%s" % (path, field), kind)

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            yield _violation("SCHEMA_MIN_ITEMS", "array has too few items", path, minimum=schema["minItems"])
        if schema.get("uniqueItems") and len({json.dumps(item, sort_keys=True) for item in value}) != len(value):
            yield _violation("SCHEMA_UNIQUE_ITEMS", "array items must be unique", path)
        item_schema = schema.get("items")
        if item_schema:
            for index, item in enumerate(value):
                yield from _walk(item_schema, item, "%s[%d]" % (path, index), kind)

    if isinstance(value, str):
        if "minLength" in schema and len(value) < schema["minLength"]:
            yield _violation("SCHEMA_MIN_LENGTH", "string is too short", path, minimum=schema["minLength"])
        if "pattern" in schema and re.fullmatch(schema["pattern"], value) is None:
            yield _violation("SCHEMA_PATTERN", "string does not match the required pattern", path, pattern=schema["pattern"])

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            yield _violation("SCHEMA_MINIMUM", "number is below the minimum", path, minimum=schema["minimum"])


def validate_document(kind: str, value: Any) -> List[Violation]:
    """Validate a supported contract and return all deterministic violations."""

    if kind not in DOCUMENT_KINDS:
        return [_violation("SCHEMA_KIND_UNKNOWN", "document kind is not supported", "$", kind=kind)]
    path = SCHEMA_ROOT / (kind + ".schema.json")
    if not path.is_file():
        return [_violation("SCHEMA_NOT_FOUND", "schema file is absent", "$", kind=kind, schema=str(path))]
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [_violation("SCHEMA_INVALID", "schema file cannot be loaded", "$", kind=kind, error=str(error))]
    return list(_walk(schema, value, "$", kind))
