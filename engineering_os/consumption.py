"""Durable atomic consumption for single-use authority records."""

from dataclasses import dataclass
import os
import re
import sqlite3
from typing import Sequence


_DIGEST = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class ConsumptionBinding:
    kind: str
    record_id: str
    nonce: str
    binding_digest: str


def consume_once(store_path: str, bindings: Sequence[ConsumptionBinding]) -> bool:
    """Atomically consume all bindings, or consume none on any replay/race."""

    if (
        not isinstance(store_path, str) or not store_path or store_path == ":memory:"
        or store_path.startswith("file:")
        or not isinstance(bindings, (list, tuple)) or not bindings
        or any(
            not isinstance(item, ConsumptionBinding)
            or not item.kind or not item.record_id or not item.nonce
            or _DIGEST.fullmatch(item.binding_digest) is None
            for item in bindings
        )
        or len({item.record_id for item in bindings}) != len(bindings)
        or len({item.nonce for item in bindings}) != len(bindings)
    ):
        return False
    parent = os.path.dirname(os.path.abspath(store_path))
    if not os.path.isdir(parent):
        return False
    connection = None
    try:
        connection = sqlite3.connect(store_path, timeout=10, isolation_level=None)
        connection.execute("PRAGMA busy_timeout = 10000")
        connection.execute("BEGIN IMMEDIATE")
        connection.execute(
            "CREATE TABLE IF NOT EXISTS consumed_records ("
            "kind TEXT NOT NULL, record_id TEXT NOT NULL UNIQUE, "
            "nonce TEXT NOT NULL UNIQUE, binding_digest TEXT NOT NULL)"
        )
        connection.executemany(
            "INSERT INTO consumed_records(kind, record_id, nonce, binding_digest) "
            "VALUES (?, ?, ?, ?)",
            [
                (item.kind, item.record_id, item.nonce, item.binding_digest)
                for item in bindings
            ],
        )
        connection.execute("COMMIT")
        return True
    except (OSError, sqlite3.Error):
        if connection is not None:
            try:
                connection.execute("ROLLBACK")
            except sqlite3.Error:
                pass
        return False
    finally:
        if connection is not None:
            connection.close()
