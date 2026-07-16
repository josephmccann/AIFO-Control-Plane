"""Durable atomic consumption for single-use authority records."""

from dataclasses import dataclass
import os
import re
import sqlite3
from typing import Sequence


_DIGEST = re.compile(r"[0-9a-f]{64}")
_SCHEMA_VERSION = 1
_CREATE_TABLE = """CREATE TABLE consumed_records (
    kind TEXT NOT NULL,
    record_id TEXT NOT NULL PRIMARY KEY,
    nonce TEXT NOT NULL,
    binding_digest TEXT NOT NULL
)"""
_CREATE_NONCE_INDEX = (
    "CREATE UNIQUE INDEX consumed_records_nonce_uq ON consumed_records(nonce)"
)
_CREATE_BINDING_INDEX = (
    "CREATE INDEX consumed_records_binding_idx "
    "ON consumed_records(kind, binding_digest)"
)


class _LedgerSchemaError(ValueError):
    pass


@dataclass(frozen=True)
class ConsumptionBinding:
    kind: str
    record_id: str
    nonce: str
    binding_digest: str


def _binding_values(item: object):
    if type(item) is not ConsumptionBinding:
        return None
    try:
        values = (item.kind, item.record_id, item.nonce, item.binding_digest)
    except Exception:
        return None
    kind, record_id, nonce, binding_digest = values
    if (
        type(kind) is not str or not kind
        or type(record_id) is not str or not record_id
        or type(nonce) is not str or not nonce
        or type(binding_digest) is not str
        or _DIGEST.fullmatch(binding_digest) is None
    ):
        return None
    return values


def _compact_sql(value: str) -> str:
    return " ".join(value.split()) if isinstance(value, str) else ""


def _initialize_or_attest(connection: sqlite3.Connection) -> None:
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    objects = connection.execute(
        "SELECT type, name, tbl_name, sql FROM sqlite_master "
        "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
    ).fetchall()
    if version == 0 and not objects:
        connection.execute(_CREATE_TABLE)
        connection.execute(_CREATE_NONCE_INDEX)
        connection.execute(_CREATE_BINDING_INDEX)
        connection.execute("PRAGMA user_version = %d" % _SCHEMA_VERSION)
        version = _SCHEMA_VERSION
        objects = connection.execute(
            "SELECT type, name, tbl_name, sql FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
        ).fetchall()
    if version != _SCHEMA_VERSION:
        raise _LedgerSchemaError("consumption ledger schema version is invalid")

    expected_objects = {
        ("table", "consumed_records", "consumed_records", _compact_sql(_CREATE_TABLE)),
        (
            "index", "consumed_records_nonce_uq", "consumed_records",
            _compact_sql(_CREATE_NONCE_INDEX),
        ),
        (
            "index", "consumed_records_binding_idx", "consumed_records",
            _compact_sql(_CREATE_BINDING_INDEX),
        ),
    }
    actual_objects = {
        (object_type, name, table, _compact_sql(sql))
        for object_type, name, table, sql in objects
    }
    if actual_objects != expected_objects:
        raise _LedgerSchemaError("consumption ledger objects are not exact")

    columns = connection.execute("PRAGMA table_info(consumed_records)").fetchall()
    actual_columns = tuple(
        (row[0], row[1], row[2].upper(), row[3], row[4], row[5])
        for row in columns
    )
    expected_columns = (
        (0, "kind", "TEXT", 1, None, 0),
        (1, "record_id", "TEXT", 1, None, 1),
        (2, "nonce", "TEXT", 1, None, 0),
        (3, "binding_digest", "TEXT", 1, None, 0),
    )
    if actual_columns != expected_columns:
        raise _LedgerSchemaError("consumption ledger columns are not exact")

    indexes = connection.execute("PRAGMA index_list(consumed_records)").fetchall()
    explicit = {
        row[1]: (row[2], row[3], row[4]) for row in indexes if row[3] == "c"
    }
    if explicit != {
        "consumed_records_nonce_uq": (1, "c", 0),
        "consumed_records_binding_idx": (0, "c", 0),
    }:
        raise _LedgerSchemaError("consumption ledger indexes are not exact")
    primary = [row for row in indexes if row[3] == "pk"]
    if len(primary) != 1 or primary[0][2] != 1 or primary[0][4] != 0:
        raise _LedgerSchemaError("consumption ledger primary key index is invalid")

    expected_index_columns = {
        "consumed_records_nonce_uq": ("nonce",),
        "consumed_records_binding_idx": ("kind", "binding_digest"),
        primary[0][1]: ("record_id",),
    }
    for name, expected in expected_index_columns.items():
        actual = tuple(
            row[2] for row in connection.execute("PRAGMA index_info(%s)" % name).fetchall()
        )
        if actual != expected:
            raise _LedgerSchemaError("consumption ledger index columns are invalid")

    check = connection.execute("PRAGMA quick_check").fetchall()
    if check != [("ok",)]:
        raise _LedgerSchemaError("consumption ledger integrity check failed")
    invalid_row = connection.execute(
        "SELECT 1 FROM consumed_records WHERE "
        "typeof(kind) != 'text' OR kind = '' OR "
        "typeof(record_id) != 'text' OR record_id = '' OR "
        "typeof(nonce) != 'text' OR nonce = '' OR "
        "typeof(binding_digest) != 'text' OR length(binding_digest) != 64 OR "
        "binding_digest GLOB '*[^0-9a-f]*' LIMIT 1"
    ).fetchone()
    if invalid_row is not None:
        raise _LedgerSchemaError("consumption ledger contains invalid audit rows")


def consume_once(store_path: str, bindings: Sequence[ConsumptionBinding]) -> bool:
    """Atomically consume all bindings, or consume none on any replay/race."""

    if (
        not isinstance(store_path, str) or not store_path or store_path == ":memory:"
        or store_path.startswith("file:")
        or not isinstance(bindings, (list, tuple)) or not bindings
    ):
        return False
    values = []
    for item in bindings:
        binding = _binding_values(item)
        if binding is None:
            return False
        values.append(binding)
    if (
        len({item[1] for item in values}) != len(values)
        or len({item[2] for item in values}) != len(values)
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
        _initialize_or_attest(connection)
        connection.executemany(
            "INSERT INTO consumed_records(kind, record_id, nonce, binding_digest) "
            "VALUES (?, ?, ?, ?)",
            values,
        )
        connection.execute("COMMIT")
        return True
    except (OSError, sqlite3.Error, _LedgerSchemaError):
        if connection is not None:
            try:
                connection.execute("ROLLBACK")
            except sqlite3.Error:
                pass
        return False
    finally:
        if connection is not None:
            connection.close()
