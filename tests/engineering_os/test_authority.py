import copy
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from engineering_os.authority import validate_authority
from engineering_os.consumption import ConsumptionBinding, consume_once
import engineering_os.records as records_kernel
from engineering_os.records import record_comment_body
from tests.engineering_os.fake_github import SealedFakeGitHubTransport, transported_record
from tests.engineering_os.test_risk import mission, policy


ROOT = Path(__file__).resolve().parents[2]
AUTHORITY = ROOT / "tests" / "engineering_os" / "fixtures" / "authority-records"
HEAD = "2222222222222222222222222222222222222222"


def record():
    return json.loads((AUTHORITY / "valid/write.json").read_text(encoding="utf-8"))


def authority_transport():
    payload = record()
    payload.pop("source")
    candidate, evidence = transported_record("authority", payload)
    if candidate != record():
        raise AssertionError("authority fixture is not its canonical transported record")
    return SealedFakeGitHubTransport(evidence)


def decide(records, **updates):
    consumption_store = updates.pop("consumption_store", None)
    if consumption_store is None:
        with tempfile.TemporaryDirectory() as directory:
            return decide(
                records, consumption_store=str(Path(directory) / "consumed.sqlite3"),
                **updates,
            )
    changed_files = updates.pop("changed_files", ["src/reporting/render.py"])
    context = {
        "action": "write",
        "pull_request": 42,
        "head_sha": HEAD,
        "now": "2026-07-15T12:00:00Z",
        "subject": "producer-a",
        "evidence_verifier": authority_transport(),
        "consumption_store": consumption_store,
    }
    context.update(updates)
    return validate_authority(
        mission("Tier 1"), policy(), changed_files, records, **context
    )


class AuthorityTests(unittest.TestCase):
    def test_consumption_store_rejects_malformed_paths_without_creation(self):
        class StringSubclass(str):
            pass

        binding = ConsumptionBinding("authority", "record-1", "nonce-1", "1" * 64)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            malformed = (
                ("path_object", root / "path-object.sqlite3"),
                ("bytes", bytes(str(root / "bytes.sqlite3"), "utf-8")),
                ("integer", 1),
                ("string_subclass", StringSubclass(str(root / "subclass.sqlite3"))),
                ("nul", str(root / "nul.sqlite3") + "\x00"),
                ("high_surrogate", str(root / "surrogate.sqlite3") + "\ud800"),
                ("low_surrogate", str(root / "surrogate.sqlite3") + "\udcff"),
            )
            for name, store in malformed:
                with self.subTest(name=name):
                    before = set(root.iterdir())
                    try:
                        result = consume_once(store, [binding])
                    except Exception as error:
                        self.fail("malformed store path escaped: %r" % error)
                    self.assertFalse(result)
                    self.assertEqual(set(root.iterdir()), before)

            unicode_store = str(root / "ledger-😀.sqlite3")
            self.assertTrue(consume_once(unicode_store, [binding]))
            self.assertTrue(consume_once(unicode_store, [ConsumptionBinding(
                "authority", "record-2", "nonce-2", "2" * 64,
            )]))

    def test_consumption_store_contains_path_and_cleanup_errors(self):
        binding = ConsumptionBinding("authority", "record-1", "nonce-1", "1" * 64)
        failures = (OSError("os"), ValueError("value"), UnicodeError("unicode"), OverflowError("overflow"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for operation in ("abspath", "isdir", "connect"):
                for error in failures:
                    with self.subTest(operation=operation, error=type(error).__name__):
                        store = str(root / ("%s-%s.sqlite3" % (
                            operation, type(error).__name__,
                        )))
                        target = {
                            "abspath": "engineering_os.consumption.os.path.abspath",
                            "isdir": "engineering_os.consumption.os.path.isdir",
                            "connect": "engineering_os.consumption.sqlite3.connect",
                        }[operation]
                        with patch(target, side_effect=error):
                            try:
                                result = consume_once(store, [binding])
                            except Exception as escaped:
                                self.fail("path operation escaped: %r" % escaped)
                        self.assertFalse(result)
                        self.assertFalse(Path(store).exists())

            real_connect = sqlite3.connect

            class CloseFailureConnection:
                def __init__(self, connection, error):
                    self.connection = connection
                    self.error = error

                def __getattr__(self, name):
                    return getattr(self.connection, name)

                def close(self):
                    self.connection.close()
                    raise self.error

            for index, error in enumerate(failures):
                with self.subTest(operation="close", error=type(error).__name__):
                    store = str(root / ("close-%d.sqlite3" % index))
                    proxy = CloseFailureConnection(real_connect(store), error)
                    with patch("engineering_os.consumption.sqlite3.connect", return_value=proxy):
                        try:
                            result = consume_once(store, [binding])
                        except Exception as escaped:
                            self.fail("cleanup escaped: %r" % escaped)
                    self.assertTrue(result)
                    self.assertTrue(consume_once(store, [ConsumptionBinding(
                        "authority", "record-2", "nonce-2", "2" * 64,
                    )]))

    def test_authority_contains_malformed_consumption_store_paths(self):
        class StringSubclass(str):
            pass

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            malformed = (
                StringSubclass(str(root / "subclass.sqlite3")),
                str(root / "nul.sqlite3") + "\x00",
                str(root / "surrogate.sqlite3") + "\ud800",
                str(root / ("x" * 10000)),
            )
            for store in malformed:
                with self.subTest(store_type=type(store).__name__, length=len(store)):
                    try:
                        result = decide([record()], consumption_store=store)
                    except Exception as error:
                        self.fail("authority store path escaped: %r" % error)
                    self.assertEqual(result.code, "AUTHORITY_REPLAYED")
            valid_store = str(root / "valid.sqlite3")
            self.assertTrue(decide([record()], consumption_store=valid_store).allowed)

    def test_transport_evidence_keys_are_exact_before_hash_or_equality(self):
        class StringKeySubclass(str):
            pass

        class HashBomb:
            def __init__(self):
                self.hash_calls = 0
                self.equality_calls = 0

            def __hash__(self):
                self.hash_calls += 1
                raise RuntimeError("unsafe key hash")

            def __eq__(self, other):
                self.equality_calls += 1
                raise RuntimeError("unsafe key equality")

        class EqualityBomb(HashBomb):
            def __hash__(self):
                self.hash_calls += 1
                return hash("repository")

        class EvidenceMapping(Mapping):
            def __init__(self, keys, values, *, iteration_error=False, access_error=False):
                self._keys = list(keys)
                self._values = values
                self._iteration_error = iteration_error
                self._access_error = access_error

            def __iter__(self):
                if self._iteration_error:
                    raise RuntimeError("key iteration failed")
                return iter(self._keys)

            def __len__(self):
                return len(self._keys)

            def __getitem__(self, key):
                if self._access_error:
                    raise RuntimeError("evidence access failed")
                return self._values[key]

        class DirectTransport:
            transport_provenance = SealedFakeGitHubTransport.transport_provenance

            def __init__(self, evidence):
                self.evidence = evidence

            def retrieve_comment(self, *args):
                return self.evidence

        payload = record()
        payload.pop("source")
        candidate, evidence = transported_record("authority", payload)
        keys = list(evidence)
        hash_bomb = HashBomb()
        equality_bomb = EqualityBomb()
        cases = (
            (
                "custom_hash", EvidenceMapping(
                    [hash_bomb if key == "repository" else key for key in keys],
                    evidence,
                ),
            ),
            (
                "custom_equality", EvidenceMapping(
                    [*keys, equality_bomb], evidence,
                ),
            ),
            (
                "string_subclass", EvidenceMapping(
                    [StringKeySubclass(key) if key == "repository" else key for key in keys],
                    evidence,
                ),
            ),
            ("duplicate", EvidenceMapping([*keys, "repository"], evidence)),
            (
                "equivalent_exotic", EvidenceMapping(
                    [*keys, StringKeySubclass("repository")], evidence,
                ),
            ),
            ("integer", EvidenceMapping([1, *keys[1:]], evidence)),
            ("bytes", EvidenceMapping([b"repository", *keys[1:]], evidence)),
            ("unhashable", EvidenceMapping([[], *keys[1:]], evidence)),
            ("iteration_error", EvidenceMapping(keys, evidence, iteration_error=True)),
            ("access_error", EvidenceMapping(keys, evidence, access_error=True)),
        )
        for name, transported_evidence in cases:
            with self.subTest(name=name):
                transport = DirectTransport(transported_evidence)
                try:
                    verified = records_kernel.verify_record_evidence(
                        candidate, "authority", transport,
                        repository="acme/widgets", actor="founder", head_sha=HEAD,
                    )
                except Exception as error:
                    self.fail("malformed evidence key escaped: %r" % error)
                self.assertFalse(verified)
                self.assertEqual(
                    decide([candidate], evidence_verifier=transport).code,
                    "AUTHORITY_SOURCE_UNAUTHENTICATED",
                )
        self.assertEqual(hash_bomb.hash_calls, 0)
        self.assertEqual(hash_bomb.equality_calls, 0)
        self.assertEqual(equality_bomb.hash_calls, 0)
        self.assertEqual(equality_bomb.equality_calls, 0)

    def test_evidence_fields_and_adapter_provenance_require_exact_primitives(self):
        class EqualString(str):
            def __eq__(self, other):
                return True

            def __ne__(self, other):
                return False

            __hash__ = str.__hash__

        class EqualInteger(int):
            def __eq__(self, other):
                return True

            def __ne__(self, other):
                return False

            __hash__ = int.__hash__

        class EqualObject:
            def __eq__(self, other):
                return True

            def __ne__(self, other):
                return False

        class ProxyValue:
            def __eq__(self, other):
                raise RuntimeError("proxy equality must not run")

            def __ne__(self, other):
                raise RuntimeError("proxy inequality must not run")

        payload = record()
        payload.pop("source")
        candidate, original = transported_record("authority", payload)
        string_fields = (
            "repository", "subject_kind", "url", "actor", "created_at",
            "updated_at", "body", "head_sha", "transport_provenance",
        )
        cases = [
            (field, "string_subclass", EqualString(original[field]), None)
            for field in string_fields
        ]
        cases.extend(
            (field, "integer_subclass", EqualInteger(original[field]), None)
            for field in ("subject_number", "comment_id")
        )
        cases.extend(
            (field, "bool", True, None)
            for field in ("subject_number", "comment_id")
        )
        cases.extend(
            (field, "custom_equality", EqualObject(), None)
            for field in string_fields + ("subject_number", "comment_id")
        )
        cases.extend(
            (field, "proxy", ProxyValue(), None)
            for field in string_fields + ("subject_number", "comment_id")
        )
        cases.append((
            "adapter_transport_provenance", "string_subclass", None,
            EqualString(SealedFakeGitHubTransport.transport_provenance),
        ))
        cases.append((
            "adapter_transport_provenance", "custom_equality", None,
            EqualObject(),
        ))
        cases.append((
            "adapter_transport_provenance", "proxy", None, ProxyValue(),
        ))

        for field, value_type, value, adapter_provenance in cases:
            with self.subTest(field=field, value_type=value_type):
                evidence = copy.deepcopy(original)
                if value is not None:
                    evidence[field] = value
                transport = SealedFakeGitHubTransport(evidence)
                if adapter_provenance is not None:
                    transport.transport_provenance = adapter_provenance
                    evidence["transport_provenance"] = adapter_provenance
                    transport._evidence = evidence
                self.assertFalse(records_kernel.verify_record_evidence(
                    candidate, "authority", transport,
                    repository="acme/widgets", actor="founder", head_sha=HEAD,
                ))
                self.assertEqual(
                    decide([candidate], evidence_verifier=transport).code,
                    "AUTHORITY_SOURCE_UNAUTHENTICATED",
                )

    def test_adapter_lookup_call_and_return_failures_are_contained(self):
        payload = record()
        payload.pop("source")
        candidate, evidence = transported_record("authority", payload)

        class RetrievePropertyFailure:
            transport_provenance = SealedFakeGitHubTransport.transport_provenance

            @property
            def retrieve_comment(self):
                raise RuntimeError("retrieve property failed")

        class ProvenancePropertyFailure:
            def retrieve_comment(self, *args):
                return evidence

            @property
            def transport_provenance(self):
                raise RuntimeError("provenance property failed")

        class LookupProxyFailure:
            def __getattr__(self, name):
                raise RuntimeError("proxy lookup failed: %s" % name)

        class ExplodingEvidence(dict):
            def __iter__(self):
                raise RuntimeError("returned evidence iteration failed")

        cases = (
            ("retrieve_property", RetrievePropertyFailure()),
            ("provenance_property", ProvenancePropertyFailure()),
            ("lookup_proxy", LookupProxyFailure()),
            ("call", SealedFakeGitHubTransport(error=RuntimeError("call failed"))),
            ("none_return", SealedFakeGitHubTransport(None)),
            ("list_return", SealedFakeGitHubTransport([])),
            ("malformed_mapping", SealedFakeGitHubTransport(ExplodingEvidence(evidence))),
        )
        for name, verifier in cases:
            with self.subTest(name=name):
                try:
                    result = records_kernel.verify_record_evidence(
                        candidate, "authority", verifier,
                        repository="acme/widgets", actor="founder", head_sha=HEAD,
                    )
                except Exception as error:
                    self.fail("adapter failure escaped: %r" % error)
                self.assertFalse(result)

    def test_kernel_retrieves_and_binds_authenticated_github_transport(self):
        payload = record()
        payload.pop("source")
        candidate, evidence = transported_record("authority", payload)
        transport = SealedFakeGitHubTransport(evidence)
        verify = getattr(
            records_kernel, "verify_record_evidence", lambda *args, **kwargs: False,
        )
        self.assertTrue(verify(
            candidate, "authority", transport,
            repository="acme/widgets", actor="founder", head_sha=HEAD,
        ))
        self.assertEqual(
            transport.requests, [("acme/widgets", "pull_request", 42, 9001)],
        )

        mutations = {
            "author": ("actor", "outsider"),
            "comment_id": ("comment_id", 9002),
            "timestamp": ("created_at", "2026-07-15T00:00:01Z"),
            "repository": ("repository", "acme/other"),
            "head": ("head_sha", "3" * 40),
            "edited": ("updated_at", "2026-07-15T00:01:00Z"),
            "provenance": ("transport_provenance", "caller-asserted"),
            "subject_kind": ("subject_kind", "issue"),
        }
        for name, (field, value) in mutations.items():
            with self.subTest(name=name):
                altered = copy.deepcopy(evidence)
                altered[field] = value
                self.assertFalse(verify(
                    candidate, "authority", SealedFakeGitHubTransport(altered),
                    repository="acme/widgets", actor="founder", head_sha=HEAD,
                ))

        wrong_content = copy.deepcopy(evidence)
        wrong_content["body"] += " "
        wrong_kind = copy.deepcopy(evidence)
        wrong_kind["body"] = record_comment_body("coordination", payload)
        for name, verifier in (
            ("content", SealedFakeGitHubTransport(wrong_content)),
            ("record_kind", SealedFakeGitHubTransport(wrong_kind)),
            ("unavailable", SealedFakeGitHubTransport(None)),
            ("error", SealedFakeGitHubTransport(error=RuntimeError("offline"))),
            ("raw_mapping", {"evidence": evidence}),
        ):
            with self.subTest(name=name):
                self.assertFalse(verify(
                    candidate, "authority", verifier,
                    repository="acme/widgets", actor="founder", head_sha=HEAD,
                ))

        replayed = copy.deepcopy(candidate)
        replayed["paths"] = ["src/reporting/other.py"]
        self.assertFalse(verify(
            replayed, "authority", SealedFakeGitHubTransport(evidence),
            repository="acme/widgets", actor="founder", head_sha=HEAD,
        ))

    def test_consumption_store_initializes_and_attests_exact_schema_idempotently(self):
        with tempfile.TemporaryDirectory() as directory:
            store = str(Path(directory) / "ledger.sqlite3")
            first = ConsumptionBinding("authority", "record-1", "nonce-1", "1" * 64)
            second = ConsumptionBinding("authority", "record-2", "nonce-2", "2" * 64)
            self.assertTrue(consume_once(store, [first]))
            self.assertTrue(consume_once(store, [second]))
            connection = sqlite3.connect(store)
            try:
                self.assertEqual(connection.execute("PRAGMA user_version").fetchone()[0], 1)
                columns = connection.execute(
                    "PRAGMA table_info(consumed_records)"
                ).fetchall()
                self.assertEqual(
                    [(row[1], row[2], row[3], row[5]) for row in columns],
                    [
                        ("kind", "TEXT", 1, 0),
                        ("record_id", "TEXT", 1, 1),
                        ("nonce", "TEXT", 1, 0),
                        ("binding_digest", "TEXT", 1, 0),
                    ],
                )
                indexes = connection.execute(
                    "PRAGMA index_list(consumed_records)"
                ).fetchall()
                self.assertIn(
                    ("consumed_records_nonce_uq", 1, "c", 0),
                    [(row[1], row[2], row[3], row[4]) for row in indexes],
                )
                self.assertIn(
                    ("consumed_records_binding_idx", 0, "c", 0),
                    [(row[1], row[2], row[3], row[4]) for row in indexes],
                )
            finally:
                connection.close()

    def test_consumption_bindings_require_exact_strings_before_open(self):
        class TruthyValue:
            def __bool__(self):
                return True

        valid = {
            "kind": "authority", "record_id": "record-1",
            "nonce": "nonce-1", "binding_digest": "1" * 64,
        }
        malformed_values = (True, 1, b"value", TruthyValue())
        cases = []
        for field in valid:
            for value in malformed_values:
                candidate = dict(valid)
                candidate[field] = value
                cases.append((field, type(value).__name__, ConsumptionBinding(**candidate)))
            candidate = dict(valid)
            candidate[field] = ""
            cases.append((field, "empty", ConsumptionBinding(**candidate)))

        with tempfile.TemporaryDirectory() as directory:
            store = str(Path(directory) / "ledger.sqlite3")
            for field, value_type, binding in cases:
                with self.subTest(field=field, value_type=value_type):
                    with patch(
                        "engineering_os.consumption.sqlite3.connect",
                        side_effect=sqlite3.OperationalError("must not open"),
                    ) as connect:
                        try:
                            result = consume_once(store, [binding])
                        except Exception as error:
                            self.fail("malformed binding raised: %r" % error)
                        self.assertFalse(result)
                        connect.assert_not_called()
                    self.assertFalse(Path(store).exists())

    def test_rejected_bindings_do_not_mutate_and_valid_ledger_remains_usable(self):
        malformed = (
            ConsumptionBinding(True, "bad-record", "bad-nonce", "1" * 64),
            ConsumptionBinding("authority", 1, "bad-nonce", "1" * 64),
            ConsumptionBinding("authority", "bad-record", b"bad-nonce", "1" * 64),
            ConsumptionBinding("authority", "bad-record", "bad-nonce", 1),
        )
        with tempfile.TemporaryDirectory() as directory:
            store = str(Path(directory) / "ledger.sqlite3")
            first = ConsumptionBinding("authority", "record-1", "nonce-1", "1" * 64)
            second = ConsumptionBinding("authority", "record-2", "nonce-2", "2" * 64)
            self.assertTrue(consume_once(store, [first]))
            for binding in malformed:
                with self.subTest(field_values=binding):
                    try:
                        self.assertFalse(consume_once(store, [binding]))
                    except Exception as error:
                        self.fail("malformed binding raised: %r" % error)
            connection = sqlite3.connect(store)
            try:
                self.assertEqual(
                    connection.execute("SELECT COUNT(*) FROM consumed_records").fetchone()[0],
                    1,
                )
            finally:
                connection.close()
            self.assertTrue(consume_once(store, [second]))

    def test_uninitialized_and_raising_bindings_fail_before_database_open(self):
        uninitialized = object.__new__(ConsumptionBinding)
        valid = ConsumptionBinding("authority", "record-1", "nonce-1", "1" * 64)
        with tempfile.TemporaryDirectory() as directory:
            store = str(Path(directory) / "ledger.sqlite3")
            cases = [("uninitialized", uninitialized, None)]
            cases.extend((field, valid, field) for field in (
                "kind", "record_id", "nonce", "binding_digest",
            ))
            for name, binding, raising_field in cases:
                with self.subTest(name=name):
                    descriptor = (
                        patch.object(
                            ConsumptionBinding, raising_field,
                            property(lambda self: (_ for _ in ()).throw(
                                RuntimeError("binding attribute failed")
                            )),
                            create=True,
                        )
                        if raising_field is not None else None
                    )
                    if descriptor is not None:
                        descriptor.start()
                    try:
                        with patch(
                            "engineering_os.consumption.sqlite3.connect",
                            side_effect=sqlite3.OperationalError("must not open"),
                        ) as connect:
                            try:
                                result = consume_once(store, [binding])
                            except Exception as error:
                                self.fail("malformed binding escaped: %r" % error)
                            self.assertFalse(result)
                            connect.assert_not_called()
                    finally:
                        if descriptor is not None:
                            descriptor.stop()
                    self.assertFalse(Path(store).exists())

    def test_malformed_exact_binding_does_not_mutate_existing_ledger(self):
        with tempfile.TemporaryDirectory() as directory:
            store = str(Path(directory) / "ledger.sqlite3")
            first = ConsumptionBinding("authority", "record-1", "nonce-1", "1" * 64)
            second = ConsumptionBinding("authority", "record-2", "nonce-2", "2" * 64)
            self.assertTrue(consume_once(store, [first]))
            self.assertFalse(consume_once(store, [object.__new__(ConsumptionBinding)]))
            connection = sqlite3.connect(store)
            try:
                self.assertEqual(
                    connection.execute("SELECT COUNT(*) FROM consumed_records").fetchone()[0],
                    1,
                )
            finally:
                connection.close()
            self.assertTrue(consume_once(store, [second]))

    def test_consumption_store_refuses_altered_or_duplicate_capable_schemas(self):
        schemas = {
            "missing_constraints": (
                "CREATE TABLE consumed_records (kind TEXT NOT NULL, record_id TEXT NOT NULL, "
                "nonce TEXT NOT NULL, binding_digest TEXT NOT NULL)"
            ),
            "partial": (
                "CREATE TABLE consumed_records (record_id TEXT PRIMARY KEY, nonce TEXT UNIQUE)"
            ),
            "wrong_types": (
                "CREATE TABLE consumed_records (kind BLOB NOT NULL, record_id TEXT PRIMARY KEY, "
                "nonce TEXT UNIQUE, binding_digest TEXT NOT NULL)"
            ),
        }
        for name, statement in schemas.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                store = str(Path(directory) / "ledger.sqlite3")
                connection = sqlite3.connect(store)
                connection.execute(statement)
                connection.execute("PRAGMA user_version = 1")
                if name == "missing_constraints":
                    row = ("authority", "duplicate", "duplicate", "0" * 64)
                    connection.execute("INSERT INTO consumed_records VALUES (?, ?, ?, ?)", row)
                    connection.execute("INSERT INTO consumed_records VALUES (?, ?, ?, ?)", row)
                connection.commit()
                connection.close()
                self.assertFalse(consume_once(store, [ConsumptionBinding(
                    "authority", "record-new", "nonce-new", "a" * 64,
                )]))

    def test_consumption_store_refuses_wrong_version_extra_objects_and_altered_indexes(self):
        for mutation in ("wrong_version", "extra_table", "altered_indexes"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                store = str(Path(directory) / "ledger.sqlite3")
                seed = ConsumptionBinding("authority", "record-1", "nonce-1", "1" * 64)
                self.assertTrue(consume_once(store, [seed]))
                connection = sqlite3.connect(store)
                if mutation == "wrong_version":
                    connection.execute("PRAGMA user_version = 2")
                elif mutation == "extra_table":
                    connection.execute("CREATE TABLE attacker (value TEXT)")
                else:
                    connection.execute("DROP INDEX IF EXISTS consumed_records_nonce_uq")
                    connection.execute(
                        "CREATE INDEX consumed_records_nonce_uq ON consumed_records(nonce)"
                    )
                connection.commit()
                connection.close()
                self.assertFalse(consume_once(store, [ConsumptionBinding(
                    "authority", "record-2", "nonce-2", "2" * 64,
                )]))

    def test_multi_record_consumption_rolls_back_all_rows_on_replay(self):
        with tempfile.TemporaryDirectory() as directory:
            store = str(Path(directory) / "ledger.sqlite3")
            used = ConsumptionBinding("authority", "record-used", "nonce-used", "1" * 64)
            fresh = ConsumptionBinding("authority", "record-fresh", "nonce-fresh", "2" * 64)
            self.assertTrue(consume_once(store, [used]))
            self.assertFalse(consume_once(store, [fresh, used]))
            self.assertTrue(consume_once(store, [fresh]))

    def test_payload_mutation_cannot_reuse_an_old_authenticated_source(self):
        candidate = record()
        candidate["paths"] = ["src/reporting/other.py"]
        decision = validate_authority(
            mission("Tier 1"), policy(), ["src/reporting/other.py"], [candidate],
            action="write", pull_request=42, head_sha=HEAD,
            now="2026-07-15T12:00:00Z", subject="producer-a",
            evidence_verifier=authority_transport(),
            consumption_store=str(Path(tempfile.gettempdir()) / "unused-authority.sqlite3"),
        )
        self.assertEqual(decision.code, "AUTHORITY_SOURCE_UNAUTHENTICATED")

    def test_transport_locator_uses_exact_json_types(self):
        payload = record()
        payload.pop("source")
        candidate, evidence = transported_record("authority", payload)
        candidate["source"]["subject_number"] = True
        self.assertFalse(records_kernel.verify_record_evidence(
            candidate, "authority", SealedFakeGitHubTransport(evidence),
            repository="acme/widgets", actor="founder", head_sha=HEAD,
        ))

    def test_raw_evidence_mapping_is_not_an_authenticator(self):
        payload = record()
        payload.pop("source")
        candidate, evidence = transported_record("authority", payload)
        self.assertFalse(records_kernel.verify_record_evidence(
            candidate, "authority", evidence,
            repository="acme/widgets", actor="founder", head_sha=HEAD,
        ))

    def test_authority_is_consumed_once_sequentially(self):
        with tempfile.TemporaryDirectory() as directory:
            store = str(Path(directory) / "consumed.sqlite3")
            first = decide([record()], consumption_store=store)
            second = decide([record()], consumption_store=store)
        self.assertEqual((first.allowed, second.code), (True, "AUTHORITY_REPLAYED"))

    def test_authority_is_consumed_once_concurrently(self):
        with tempfile.TemporaryDirectory() as directory:
            store = str(Path(directory) / "consumed.sqlite3")
            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(
                    lambda _: decide([record()], consumption_store=store), range(2),
                ))
        self.assertEqual(sum(result.allowed for result in results), 1)
        self.assertEqual(sum(result.code == "AUTHORITY_REPLAYED" for result in results), 1)

    def test_default_authority_is_read_only(self):
        read = decide([], action="read")
        write = decide([])
        self.assertEqual((read.allowed, read.code), (True, "AUTHORITY_READ_ONLY_DEFAULT"))
        self.assertEqual((write.allowed, write.code), (False, "AUTHORITY_REQUIRED"))

    def test_authority_requires_authenticated_source_and_rejects_replay(self):
        candidate = record()
        self.assertEqual(decide([candidate], evidence_verifier=None).code, "AUTHORITY_SOURCE_UNAUTHENTICATED")
        with tempfile.TemporaryDirectory() as directory:
            store = str(Path(directory) / "consumed.sqlite3")
            self.assertTrue(decide([candidate], consumption_store=store).allowed)
            self.assertEqual(decide([candidate], consumption_store=store).code, "AUTHORITY_REPLAYED")

        duplicate = copy.deepcopy(candidate)
        duplicate["authority_id"] = "authority-write-2"
        self.assertEqual(decide([candidate, duplicate]).code, "AUTHORITY_RECORD_DUPLICATE")

    def test_exact_active_record_authorizes_only_its_bound_action(self):
        self.assertEqual((decide([record()]).allowed, decide([record()]).code), (True, "AUTHORITY_ALLOWED"))
        for field, value, code in (
            ("mission_id", "mission-other", "AUTHORITY_MISSION_MISMATCH"),
            ("pull_request", 43, "AUTHORITY_PR_MISMATCH"),
            ("head_sha", "3" * 40, "AUTHORITY_HEAD_MISMATCH"),
            ("subject", "producer-b", "AUTHORITY_SUBJECT_MISMATCH"),
            ("capabilities", ["merge"], "AUTHORITY_ACTION_MISMATCH"),
        ):
            with self.subTest(field=field):
                candidate = record()
                candidate[field] = value
                self.assertEqual(decide([candidate]).code, code)

    def test_expired_wrong_repository_and_wrong_path_are_denied(self):
        expired = record()
        expired["expires_at"] = "2026-07-15T12:00:00Z"
        wrong_repo = record()
        wrong_repo["repository"] = "acme/other"
        wrong_path = record()
        wrong_path["paths"] = ["src/reporting/other.py"]
        self.assertEqual(decide([expired]).code, "AUTHORITY_EXPIRED")
        self.assertEqual(decide([wrong_repo]).code, "AUTHORITY_REPOSITORY_MISMATCH")
        self.assertEqual(decide([wrong_path]).code, "AUTHORITY_PATH_MISMATCH")

        wrong_base = policy()
        wrong_base["repository"] = "acme/other"
        base_denied = validate_authority(
            mission("Tier 1"), wrong_base, ["src/reporting/render.py"], [record()],
            action="write", pull_request=42, head_sha=HEAD,
            now="2026-07-15T12:00:00Z", subject="producer-a",
            evidence_verifier=authority_transport(),
            consumption_store=str(Path(tempfile.gettempdir()) / "wrong-base.sqlite3"),
        )
        self.assertEqual(base_denied.code, "AUTHORITY_POLICY_REPOSITORY_MISMATCH")

    def test_future_revoked_consumed_or_non_founder_authority_is_denied(self):
        cases = []
        future = record(); future["starts_at"] = "2026-07-15T12:00:01Z"; cases.append((future, "AUTHORITY_NOT_STARTED"))
        revoked = record(); revoked["status"] = "revoked"; cases.append((revoked, "AUTHORITY_INACTIVE"))
        consumed = record(); consumed["status"] = "consumed"; cases.append((consumed, "AUTHORITY_INACTIVE"))
        outsider = record(); outsider["issuer"] = "outsider"; cases.append((outsider, "AUTHORITY_ISSUER_DENIED"))
        for candidate, code in cases:
            with self.subTest(code=code):
                self.assertEqual(decide([candidate]).code, code)

        no_founders = policy()
        no_founders["founder_identities"] = []
        denied = validate_authority(
            mission("Tier 1"), no_founders, ["src/reporting/render.py"], [record()],
            action="write", pull_request=42, head_sha=HEAD,
            now="2026-07-15T12:00:00Z", subject="producer-a",
            evidence_verifier=authority_transport(),
            consumption_store=str(Path(tempfile.gettempdir()) / "no-founders.sqlite3"),
        )
        self.assertEqual(denied.code, "AUTHORITY_POLICY_INVALID")

    def test_malformed_timestamps_and_paths_fail_closed(self):
        malformed = record(); malformed["expires_at"] = "tomorrow"
        traversal = record(); traversal["paths"] = ["../escape"]
        incomplete = record(); incomplete.pop("authority_id")
        self.assertEqual(decide([malformed]).code, "AUTHORITY_RECORD_INVALID")
        self.assertEqual(decide([traversal]).code, "AUTHORITY_RECORD_INVALID")
        self.assertEqual(decide([incomplete]).code, "AUTHORITY_RECORD_INVALID")

    def test_authority_cannot_expand_mission_or_disabled_base_policy_capabilities(self):
        deploy = record()
        deploy["capabilities"] = ["deploy"]
        undeclared = decide([deploy], action="deploy")
        self.assertEqual(undeclared.code, "AUTHORITY_MISSION_CAPABILITY_DENIED")

        declared_mission = mission("Tier 2")
        declared_mission["capabilities"].append("deploy")
        base_policy = policy()
        base_policy["deployment_enabled"] = False
        disabled = validate_authority(
            declared_mission, base_policy, ["src/reporting/render.py"], [deploy],
            action="deploy", pull_request=42, head_sha=HEAD,
            now="2026-07-15T12:00:00Z", subject="producer-a",
            evidence_verifier=authority_transport(),
            consumption_store=str(Path(tempfile.gettempdir()) / "disabled.sqlite3"),
        )
        self.assertEqual(disabled.code, "AUTHORITY_POLICY_CAPABILITY_DISABLED")

    def test_malformed_collections_and_boolean_pr_fail_stably(self):
        self.assertEqual(validate_authority(
            mission("Tier 1"), policy(), ["src/reporting/render.py"], None,
            action="write", pull_request=42, head_sha=HEAD, now="2026-07-15T12:00:00Z",
            subject="producer-a", evidence_verifier=None, consumption_store="",
        ).code, "AUTHORITY_INPUT_INVALID")
        self.assertEqual(validate_authority(
            mission("Tier 1"), policy(), ["src/reporting/render.py"], [record()],
            action="write", pull_request=True, head_sha=HEAD, now="2026-07-15T12:00:00Z",
            subject="producer-a", evidence_verifier=authority_transport(),
            consumption_store="",
        ).code, "AUTHORITY_INPUT_INVALID")

    def test_credential_model_names_real_gap_and_github_app_migration(self):
        text = (ROOT / "docs/engineering-os/CREDENTIAL_MODEL.md").read_text(encoding="utf-8")
        compact = " ".join(text.split())
        self.assertIn("cannot path-scope the Git credential", compact)
        self.assertIn("GitHub App", compact)
        self.assertIn("expiring installation token", compact)
        self.assertIn("does not claim that it enforces path-scoped Git credentials", compact)

    def test_authority_document_names_envelope_and_operational_store_boundaries(self):
        text = (ROOT / "docs/engineering-os/AUTHORITY_MODEL.md").read_text(encoding="utf-8")
        self.assertIn("canonical payload SHA-256", text)
        self.assertIn("SQLite", text)
        self.assertIn("raw mappings", text)
        self.assertIn("no operational adapter", text)


if __name__ == "__main__":
    unittest.main()
