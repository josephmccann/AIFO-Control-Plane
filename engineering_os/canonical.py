"""Canonical JSON and content hashes."""

import hashlib
import json
from collections.abc import Mapping
from typing import Any


def canonical_json(value: Any) -> str:
    """Return deterministic UTF-8 JSON text without insignificant whitespace."""

    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def content_sha256(value: Any) -> str:
    """Hash exact bytes or a canonical JSON value.

    A root audit ``event_hash`` is derived data and is excluded from its own
    hash. Other fields, including nested fields with the same name, remain in
    the content.
    """

    if isinstance(value, bytes):
        payload = value
    else:
        hash_value = value
        if isinstance(value, Mapping) and "event_hash" in value:
            hash_value = dict(value)
            del hash_value["event_hash"]
        payload = canonical_json(hash_value).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
