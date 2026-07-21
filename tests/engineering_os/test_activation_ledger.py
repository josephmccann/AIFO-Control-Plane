import copy
import unittest

from engineering_os.canonical import content_sha256
from engineering_os.commands import (
    _INVARIANT_BASELINE_PATHS, validate_activation_ledger, validate_compatibility_chain,
    validate_event_chain,
)
from engineering_os.schema import validate_document


class ActivationLedgerTests(unittest.TestCase):
    def setUp(self):
        self.activation = {
            "repository": "josephmccann/AIFO-Control-Plane",
            "mission_issue": 26,
            "mission_issue_identity": {
                "repository": "josephmccann/AIFO-Control-Plane", "number": 26,
                "node_id": "I_kwDOmission26", "url": "https://github.com/josephmccann/AIFO-Control-Plane/issues/26",
                "state": "open", "ready_event_hash": "1" * 64, "ready_sequence": 1,
                "ready_declaration_sha256": "2" * 64,
            },
            "authorization_provenance": self.provenance(1, "prepare"),
            "remediation_head": "b3c0a2c7c85fbd45167d61ae29fc1f21dfafad9e",
            "remediation_tree": "9fd7af9c8f231759ebbee851836dd83a097418d6",
            "baseline_generation_commit": "b3c0a2c7c85fbd45167d61ae29fc1f21dfafad9e",
            "baseline_generation_tree": "9fd7af9c8f231759ebbee851836dd83a097418d6",
            "active_execution_commit": "a" * 40,
            "active_execution_tree": "b" * 40,
            "compatibility_proof": self.proof(),
            "baseline_artifact_sha256": "3bd53aa718599ae33a5093b5b5c6e1d416216631e7818acf5472128ea9e38bce",
            "canonical_inventory_sha256": "23211f7a871c8a9a9f15cb5c010fd5167a1f21314bceebe43c2a38d8d1f04c0e",
            "baseline_generator_identity": "engineering_os.test_integrity_cli:initial-baseline-v1",
            "analyzer_identity": "engineering_os.test_integrity_cli:b3c0a2c7",
            "workflow_identity": "reusable-test-integrity@b3142f5bbed547a97a70f29bda33682294948aed",
            "caller_identity": "test-integrity-caller@80256915bdca989edc7580898971dbad1b199170",
            "immutable_kernel_identity": "5a273627a1a4d4addfcf81129dcdbda4dc58c383",
            "manifest_identity": "db1f444bad41ecf1db5057c8cbbae6390ffb7f5f7477e0c7a3bd8ae35a7a6dab",
            "rollback_sha": "77af0e93780134349abb15bd8d8b665c6de939a3",
            "activation_nonce": "n-0123456789abcdef0123456789abcdef0123456789abcdef",
            "activation_type": "initial_test_integrity_baseline",
            "single_use": True,
            "founder_authorization_identity": "founder@example.test",
            "founder_authorization_sequence": 1,
        }

    def invariant_blobs(self):
        return {path: "%040x" % (index + 1) for index, path in enumerate(_INVARIANT_BASELINE_PATHS)}

    def proof(self, **overrides):
        value = {
            "model": "reviewed_compatibility_chain",
            "chain_sha256": "c" * 64,
            "chain_path": "outputs/mission-35-compatibility-chain.json",
            "baseline_commit": "b3c0a2c7c85fbd45167d61ae29fc1f21dfafad9e",
            "baseline_tree": "9fd7af9c8f231759ebbee851836dd83a097418d6",
            "active_commit": "a" * 40,
            "active_tree": "b" * 40,
            "commit_count": 1,
            "invariant_paths": list(_INVARIANT_BASELINE_PATHS),
            "invariant_digest": content_sha256(self.invariant_blobs()),
        }
        value.update(overrides)
        return value

    def compat_chain(self, **overrides):
        blobs = self.invariant_blobs()
        value = {
            "schema_version": "1.0.0", "model": "reviewed_compatibility_chain",
            "repository": "josephmccann/AIFO-Control-Plane",
            "baseline": {"commit": "b3c0a2c7c85fbd45167d61ae29fc1f21dfafad9e",
                         "tree": "9fd7af9c8f231759ebbee851836dd83a097418d6"},
            "active": {"commit": "a" * 40, "tree": "b" * 40},
            "invariant_paths": list(_INVARIANT_BASELINE_PATHS),
            "invariant_blobs": blobs,
            "pre_baseline_parents": [],
            "commits": [{
                "commit": "a" * 40, "tree": "b" * 40,
                "parents": ["b3c0a2c7c85fbd45167d61ae29fc1f21dfafad9e"],
                "invariant_blobs": dict(blobs),
                "governed_changes": ["engineering_os/state.py"],
            }],
        }
        value.update(overrides)
        return value

    def provenance(self, run_id, job):
        sha = "3" * 40
        return {"repository": "josephmccann/AIFO-Control-Plane",
                "workflow_path": ".github/workflows/mission-command.yml",
                "workflow_ref": "josephmccann/AIFO-Control-Plane/.github/workflows/mission-command.yml@%s" % sha,
                "workflow_sha": sha, "run_id": run_id, "run_attempt": 1, "job": job,
                "actor": "github-actions[bot]", "trigger_actor": "josephmccann", "event": "issue_comment",
                "head_sha": sha, "head_tree": "4" * 40}

    def auth(self):
        return {"type": "test_integrity.baseline.authorized", "actor_role": "founder",
                "schema_version": "1.0.0", "mission_id": "mission-26",
                "actor": "founder@example.test", "occurred_at": "2026-07-17T20:00:00Z",
                "source_url": "https://github.com/josephmccann/AIFO-Control-Plane/issues/26#issuecomment-1",
                "previous_event_hash": None, "sequence": 1,
                "details": copy.deepcopy(self.activation), "event_hash": ""}

    def consume(self, auth):
        details = copy.deepcopy(self.activation)
        details.update({"authorization_event_hash": auth["event_hash"],
                        "authorization_sequence": auth["sequence"],
                        "consumer_provenance": self.provenance(2, "append"),
                        "consumer_identity": {"repository": self.activation["repository"],
                                              "workflow_path": ".github/workflows/mission-command.yml",
                                              "job": "append", "actor": "github-actions[bot]"},
                        "consumed_at": "2026-07-17T20:00:00Z",
                        "consumption_result": "activated",
                        "post_consumption_state": "active"})
        return {"type": "test_integrity.baseline.consumed", "actor_role": "system",
                "schema_version": "1.0.0", "mission_id": "mission-26",
                "actor": "system", "occurred_at": "2026-07-17T20:00:00Z",
                "source_url": "https://github.com/josephmccann/AIFO-Control-Plane/actions/runs/1",
                "previous_event_hash": "", "event_hash": "", "sequence": 3, "details": details}

    def attempt(self, auth):
        details = copy.deepcopy(self.activation)
        details.update({"authorization_event_hash": auth["event_hash"],
                        "authorization_sequence": auth["sequence"],
                        "consumer_provenance": self.provenance(2, "append"),
                        "consumer_identity": {"repository": self.activation["repository"],
                                              "workflow_path": ".github/workflows/mission-command.yml",
                                              "job": "append", "actor": "github-actions[bot]"},
                        "consumed_at": "2026-07-17T20:00:00Z",
                        "consumption_result": "attempted",
                        "post_consumption_state": "locked",
                        "attempt_event_hash": ""})
        return {"type": "test_integrity.baseline.consumption_attempted", "actor_role": "system",
                "schema_version": "1.0.0", "mission_id": "mission-26",
                "actor": "system", "occurred_at": "2026-07-17T20:00:00Z",
                "source_url": "https://github.com/josephmccann/AIFO-Control-Plane/actions/runs/1",
                "previous_event_hash": "", "event_hash": "", "sequence": 2, "details": details}

    def chain(self, events):
        previous = None
        for event in events:
            if event["type"] == "test_integrity.baseline.consumed" and previous:
                event["details"]["attempt_event_hash"] = previous
            event["previous_event_hash"] = previous
            event["event_hash"] = content_sha256(event)
            previous = event["event_hash"]
        return events

    def test_authorization_is_valid_and_consumption_is_single_use(self):
        auth = self.chain([self.auth()])[0]
        ok, code, details = validate_activation_ledger(
            [auth], self.activation, repository=self.activation["repository"],
            current_commit=self.activation["active_execution_commit"],
            current_tree=self.activation["active_execution_tree"])
        self.assertEqual((ok, code), (True, "ACTIVATION_AUTHORIZED"))
        # The historical remediation identity is never the live checkout.
        self.assertEqual(
            validate_activation_ledger(
                [auth], self.activation, repository=self.activation["repository"],
                current_commit=self.activation["remediation_head"],
                current_tree=self.activation["remediation_tree"])[1],
            "ACTIVATION_COMMIT_MISMATCH")
        self.assertFalse(details["consumed"])
        attempt = self.attempt(auth)
        consumed = self.consume(auth)
        consumed["details"]["attempt_event_hash"] = attempt["event_hash"]
        self.chain([auth, attempt, consumed])
        ok, code, details = validate_activation_ledger(
            [auth, attempt, consumed], self.activation,
            repository=self.activation["repository"])
        self.assertEqual((ok, code), (True, "ACTIVATION_ALREADY_CONSUMED"))
        self.assertTrue(details["consumed"])

    def test_replay_mismatch_and_context_changes_fail_closed(self):
        auth = self.chain([self.auth()])[0]
        for mutation, expected in (({"activation_nonce": "different-nonce-012345678901234567890123"}, "ACTIVATION_TUPLE_MISMATCH"),
                                   ({"active_execution_commit": "0" * 40,
                                     "compatibility_proof": self.proof(active_commit="0" * 40)}, "ACTIVATION_COMMIT_MISMATCH"),
                                   ({"active_execution_tree": "0" * 40,
                                     "compatibility_proof": self.proof(active_tree="0" * 40)}, "ACTIVATION_TREE_MISMATCH")):
            candidate = copy.deepcopy(self.activation)
            candidate.update(mutation)
            args = {"repository": self.activation["repository"]}
            if expected == "ACTIVATION_COMMIT_MISMATCH": args["current_commit"] = self.activation["active_execution_commit"]
            if expected == "ACTIVATION_TREE_MISMATCH": args["current_tree"] = self.activation["active_execution_tree"]
            self.assertEqual(validate_activation_ledger([auth], candidate, **args)[1], expected)
        self.assertEqual(validate_activation_ledger([auth, auth], self.activation,
            repository=self.activation["repository"])[1], "ACTIVATION_HISTORY_INVALID")

    def test_consumption_requires_the_authenticated_authorization(self):
        auth = self.chain([self.auth()])[0]
        attempt = self.attempt(auth)
        consumed = self.consume(auth)
        consumed["details"]["attempt_event_hash"] = attempt["event_hash"]
        consumed["details"]["authorization_event_hash"] = "b" * 64
        self.assertEqual(validate_activation_ledger([auth, attempt, consumed], self.activation,
            repository=self.activation["repository"])[1], "ACTIVATION_HISTORY_INVALID")
        self.assertEqual(validate_activation_ledger([consumed], self.activation,
            repository=self.activation["repository"])[1], "ACTIVATION_HISTORY_INVALID")

    def test_wrong_repository_or_malformed_tuple_fails_closed(self):
        auth = self.chain([self.auth()])[0]
        self.assertEqual(validate_activation_ledger([auth], self.activation,
            repository="attacker/example")[1], "ACTIVATION_TUPLE_INVALID")
        malformed = copy.deepcopy(self.activation)
        malformed["unexpected"] = True
        self.assertEqual(validate_activation_ledger([auth], malformed,
            repository=self.activation["repository"])[1], "ACTIVATION_TUPLE_INVALID")

    def test_direct_validator_rejects_unauthenticated_or_unknown_activation_history(self):
        auth = self.auth()
        unknown = {"type": "test_integrity.baseline.unknown", "details": {}}
        self.assertEqual(
            validate_activation_ledger([auth, unknown], self.activation,
                                       repository=self.activation["repository"])[1],
            "ACTIVATION_HISTORY_INVALID",
        )

    def test_identity_and_provenance_are_closed_and_canonical(self):
        for field, value in (
            ("mission_issue_identity", {**self.activation["mission_issue_identity"], "number": 27}),
            ("authorization_provenance", {**self.activation["authorization_provenance"], "run_attempt": 0}),
        ):
            candidate = copy.deepcopy(self.activation)
            candidate[field] = value
            self.assertEqual(validate_activation_ledger([], candidate,
                repository=self.activation["repository"])[1], "ACTIVATION_TUPLE_INVALID")
        auth = self.chain([self.auth()])[0]
        attempt = self.attempt(auth)
        attempt["details"]["consumer_identity"]["job"] = "prepare"
        self.chain([auth, attempt])
        self.assertEqual(validate_activation_ledger([auth, attempt], self.activation,
            repository=self.activation["repository"])[1], "ACTIVATION_TUPLE_MISMATCH")
        malformed = copy.deepcopy(auth)
        malformed["sequence"] = 0
        self.assertEqual(
            validate_activation_ledger([malformed], self.activation,
                                       repository=self.activation["repository"])[1],
            "ACTIVATION_HISTORY_INVALID",
        )


class CompatibilityChainTests(ActivationLedgerTests):
    """Adversarial coverage for the Model B compatibility chain.

    Every case here asserts a *rejection*.  The chain exists to prove that the
    reviewed historical baseline artifact still means what it meant when it was
    reviewed; anything that cannot prove that must fail closed.
    """

    REPOSITORY = "josephmccann/AIFO-Control-Plane"

    def check(self, chain, proof=None):
        return validate_compatibility_chain(
            chain, proof or self.proof(), repository=self.REPOSITORY)

    def test_complete_enumerated_range_is_accepted(self):
        self.assertEqual(self.check(self.compat_chain()), (True, "COMPATIBILITY_CHAIN_VALID"))

    def test_ancestry_alone_is_not_a_proof(self):
        chain = self.compat_chain(commits=[])
        self.assertEqual(self.check(chain, self.proof(commit_count=0))[1],
                         "COMPATIBILITY_CHAIN_RANGE_MISSING")

    def test_final_tree_equality_alone_is_not_a_proof(self):
        # The endpoints agree and the final tree matches, but the range between
        # them is not enumerated, so nothing constrains the intermediate commits.
        chain = self.compat_chain(commits=[])
        self.assertFalse(self.check(chain, self.proof(commit_count=0))[0])

    def test_unauthorized_change_reverted_before_the_end_is_still_rejected(self):
        blobs = self.invariant_blobs()
        moved = dict(blobs)
        moved["engineering_os/test_integrity.py"] = "f" * 40
        chain = self.compat_chain(commits=[
            {"commit": "d" * 40, "tree": "e" * 40,
             "parents": ["b3c0a2c7c85fbd45167d61ae29fc1f21dfafad9e"],
             "invariant_blobs": moved, "governed_changes": []},
            {"commit": "a" * 40, "tree": "b" * 40, "parents": ["d" * 40],
             "invariant_blobs": dict(blobs), "governed_changes": []},
        ])
        self.assertEqual(self.check(chain, self.proof(commit_count=2))[1],
                         "COMPATIBILITY_INVARIANT_VIOLATED")

    def test_missing_intermediate_commit_breaks_the_range(self):
        chain = self.compat_chain(commits=[
            {"commit": "a" * 40, "tree": "b" * 40, "parents": ["9" * 40],
             "invariant_blobs": self.invariant_blobs(), "governed_changes": []},
        ])
        self.assertEqual(self.check(chain)[1], "COMPATIBILITY_CHAIN_PARENT_UNDECLARED")

    def test_merge_importing_undeclared_history_is_rejected(self):
        chain = self.compat_chain(commits=[
            {"commit": "a" * 40, "tree": "b" * 40,
             "parents": ["b3c0a2c7c85fbd45167d61ae29fc1f21dfafad9e", "7" * 40],
             "invariant_blobs": self.invariant_blobs(), "governed_changes": []},
        ])
        self.assertEqual(self.check(chain)[1], "COMPATIBILITY_CHAIN_PARENT_UNDECLARED")

    def test_verified_pre_baseline_parent_is_accepted_when_declared(self):
        """A merge parent that predates the reviewed baseline is safe.

        Everything reachable from it is already subsumed by the reviewed
        baseline artifact, which captured the governed inventory at the
        baseline commit.  This is the real merged-topology case that the
        original linear walk rejected.
        """
        chain = self.compat_chain(
            pre_baseline_parents=["7" * 40],
            commits=[{"commit": "a" * 40, "tree": "b" * 40,
                      "parents": ["b3c0a2c7c85fbd45167d61ae29fc1f21dfafad9e", "7" * 40],
                      "invariant_blobs": self.invariant_blobs(), "governed_changes": []}],
        )
        self.assertEqual(self.check(chain), (True, "COMPATIBILITY_CHAIN_VALID"))

    def test_undeclared_merge_parent_is_still_rejected_when_others_are_declared(self):
        chain = self.compat_chain(
            pre_baseline_parents=["7" * 40],
            commits=[{"commit": "a" * 40, "tree": "b" * 40,
                      "parents": ["b3c0a2c7c85fbd45167d61ae29fc1f21dfafad9e", "6" * 40],
                      "invariant_blobs": self.invariant_blobs(), "governed_changes": []}],
        )
        self.assertEqual(self.check(chain)[1], "COMPATIBILITY_CHAIN_PARENT_UNDECLARED")

    def test_commit_cannot_be_both_enumerated_and_pre_baseline(self):
        chain = self.compat_chain(pre_baseline_parents=["a" * 40])
        self.assertEqual(self.check(chain)[1], "COMPATIBILITY_PRE_BASELINE_CONTRADICTORY")

    def test_baseline_cannot_be_declared_pre_baseline(self):
        chain = self.compat_chain(
            pre_baseline_parents=["b3c0a2c7c85fbd45167d61ae29fc1f21dfafad9e"])
        self.assertEqual(self.check(chain)[1], "COMPATIBILITY_PRE_BASELINE_CONTRADICTORY")

    def test_malformed_pre_baseline_declaration_is_rejected(self):
        self.assertEqual(self.check(self.compat_chain(pre_baseline_parents=["nope"]))[1],
                         "COMPATIBILITY_CHAIN_INVALID")
        self.assertEqual(self.check(self.compat_chain(pre_baseline_parents="7" * 40))[1],
                         "COMPATIBILITY_CHAIN_INVALID")

    def test_orphan_record_outside_active_history_is_rejected(self):
        """An enumerated commit unreachable from the active commit is an orphan.

        The linear walk could not detect this; the DAG closure must.
        """
        blobs = self.invariant_blobs()
        chain = self.compat_chain(commits=[
            {"commit": "a" * 40, "tree": "b" * 40,
             "parents": ["b3c0a2c7c85fbd45167d61ae29fc1f21dfafad9e"],
             "invariant_blobs": dict(blobs), "governed_changes": []},
            {"commit": "d" * 40, "tree": "e" * 40,
             "parents": ["b3c0a2c7c85fbd45167d61ae29fc1f21dfafad9e"],
             "invariant_blobs": dict(blobs), "governed_changes": []},
        ])
        self.assertEqual(self.check(chain, self.proof(commit_count=2))[1],
                         "COMPATIBILITY_CHAIN_RANGE_BROKEN")

    def test_cyclic_chain_is_rejected(self):
        """Commit history is acyclic; a cycle is malformed authority.

        Two records naming each other are mutually reachable, so reachability
        alone accepts a history no Git repository could produce.
        """
        blobs = self.invariant_blobs()
        chain = self.compat_chain(commits=[
            {"commit": "a" * 40, "tree": "b" * 40, "parents": ["d" * 40],
             "invariant_blobs": dict(blobs), "governed_changes": []},
            {"commit": "d" * 40, "tree": "e" * 40,
             "parents": ["a" * 40, "b3c0a2c7c85fbd45167d61ae29fc1f21dfafad9e"],
             "invariant_blobs": dict(blobs), "governed_changes": []},
        ])
        self.assertEqual(self.check(chain, self.proof(commit_count=2))[1],
                         "COMPATIBILITY_CHAIN_CYCLIC")

    def test_self_referencing_commit_is_rejected(self):
        blobs = self.invariant_blobs()
        chain = self.compat_chain(commits=[
            {"commit": "a" * 40, "tree": "b" * 40,
             "parents": ["a" * 40, "b3c0a2c7c85fbd45167d61ae29fc1f21dfafad9e"],
             "invariant_blobs": dict(blobs), "governed_changes": []},
        ])
        self.assertEqual(self.check(chain)[1], "COMPATIBILITY_CHAIN_CYCLIC")

    def test_range_detached_from_the_baseline_is_rejected(self):
        """The enumerated range must actually attach to the reviewed baseline."""
        blobs = self.invariant_blobs()
        chain = self.compat_chain(
            pre_baseline_parents=["7" * 40],
            commits=[{"commit": "a" * 40, "tree": "b" * 40, "parents": ["7" * 40],
                      "invariant_blobs": dict(blobs), "governed_changes": []}],
        )
        self.assertEqual(self.check(chain)[1], "COMPATIBILITY_CHAIN_RANGE_BROKEN")

    def test_governed_change_touching_an_invariant_path_is_rejected(self):
        chain = self.compat_chain(commits=[
            {"commit": "a" * 40, "tree": "b" * 40,
             "parents": ["b3c0a2c7c85fbd45167d61ae29fc1f21dfafad9e"],
             "invariant_blobs": self.invariant_blobs(),
             "governed_changes": ["engineering_os/test_integrity_cli.py"]},
        ])
        self.assertEqual(self.check(chain)[1], "COMPATIBILITY_INVARIANT_VIOLATED")

    def test_partial_invariant_coverage_is_rejected(self):
        partial = self.invariant_blobs()
        partial.pop("engineering_os/canonical.py")
        chain = self.compat_chain(invariant_blobs=partial)
        self.assertEqual(self.check(chain)[1], "COMPATIBILITY_INVARIANT_PATHS_INVALID")

    def test_invariant_digest_must_match_the_declared_blobs(self):
        self.assertEqual(self.check(self.compat_chain(), self.proof(invariant_digest="0" * 64))[1],
                         "COMPATIBILITY_INVARIANT_DIGEST_MISMATCH")

    def test_endpoint_substitution_is_rejected(self):
        chain = self.compat_chain(active={"commit": "9" * 40, "tree": "8" * 40})
        self.assertEqual(self.check(chain)[1], "COMPATIBILITY_CHAIN_ENDPOINT_MISMATCH")

    def test_commit_count_must_match_the_enumerated_range(self):
        self.assertEqual(self.check(self.compat_chain(), self.proof(commit_count=9))[1],
                         "COMPATIBILITY_CHAIN_COUNT_MISMATCH")

    def test_duplicate_commit_is_rejected(self):
        record = {"commit": "a" * 40, "tree": "b" * 40,
                  "parents": ["b3c0a2c7c85fbd45167d61ae29fc1f21dfafad9e"],
                  "invariant_blobs": self.invariant_blobs(), "governed_changes": []}
        chain = self.compat_chain(commits=[record, copy.deepcopy(record)])
        self.assertEqual(self.check(chain, self.proof(commit_count=2))[1],
                         "COMPATIBILITY_CHAIN_COMMIT_DUPLICATE")

    def test_wrong_repository_is_rejected(self):
        chain = self.compat_chain(repository="attacker/AIFO-Control-Plane")
        self.assertEqual(self.check(chain)[1], "COMPATIBILITY_CHAIN_REPOSITORY_INVALID")

    def test_range_must_terminate_at_the_active_execution_commit(self):
        chain = self.compat_chain(commits=[
            {"commit": "d" * 40, "tree": "e" * 40,
             "parents": ["b3c0a2c7c85fbd45167d61ae29fc1f21dfafad9e"],
             "invariant_blobs": self.invariant_blobs(), "governed_changes": []},
        ])
        self.assertEqual(self.check(chain)[1], "COMPATIBILITY_CHAIN_RANGE_INCOMPLETE")

    def test_activating_at_the_reviewed_baseline_needs_no_range(self):
        base = {"commit": "b3c0a2c7c85fbd45167d61ae29fc1f21dfafad9e",
                "tree": "9fd7af9c8f231759ebbee851836dd83a097418d6"}
        chain = self.compat_chain(active=dict(base), commits=[])
        proof = self.proof(active_commit=base["commit"], active_tree=base["tree"], commit_count=0)
        self.assertEqual(self.check(chain, proof), (True, "COMPATIBILITY_CHAIN_VALID"))

    def test_unknown_proof_model_is_rejected(self):
        self.assertEqual(self.check(self.compat_chain(), self.proof(model="ancestry"))[1],
                         "COMPATIBILITY_PROOF_INVALID")


class ActivationIdentityRoleTests(ActivationLedgerTests):
    """Identity roles may not be substituted for one another."""

    def ledger(self, activation, **kwargs):
        auth = self.chain([self.auth()])[0]
        auth["details"] = copy.deepcopy(activation)
        auth["event_hash"] = content_sha256(auth)
        return validate_activation_ledger(
            [auth], activation, repository=self.activation["repository"], **kwargs)

    def test_historical_artifact_paired_with_active_commit_without_proof_is_rejected(self):
        # This is the exact defect: the tuple claims the active checkout while
        # the artifact digest still describes the historical tree.
        candidate = copy.deepcopy(self.activation)
        candidate["baseline_generation_commit"] = candidate["active_execution_commit"]
        self.assertEqual(self.ledger(candidate)[1], "ACTIVATION_TUPLE_INVALID")

    def test_proof_must_describe_the_declared_active_execution_identity(self):
        candidate = copy.deepcopy(self.activation)
        candidate["compatibility_proof"] = self.proof(active_commit="9" * 40)
        self.assertEqual(self.ledger(candidate)[1], "ACTIVATION_TUPLE_INVALID")

    def test_missing_compatibility_proof_is_rejected(self):
        candidate = copy.deepcopy(self.activation)
        candidate.pop("compatibility_proof")
        self.assertEqual(self.ledger(candidate)[1], "ACTIVATION_TUPLE_INVALID")

    def test_legacy_authorization_is_terminally_superseded(self):
        legacy = copy.deepcopy(self.activation)
        for field in ("baseline_generation_commit", "baseline_generation_tree",
                      "active_execution_commit", "active_execution_tree",
                      "compatibility_proof"):
            legacy.pop(field)
        ok, code, details = self.ledger(legacy)
        self.assertFalse(ok)
        self.assertEqual(code, "ACTIVATION_AUTHORIZATION_SUPERSEDED")
        self.assertTrue(details["superseded"])
        self.assertFalse(details["consumed"])

    def test_legacy_authorization_stays_schema_valid_and_chain_valid(self):
        """Authenticated history is not rewritten by a later identity model.

        A pre-separation authorization was well-formed when it was written, so
        it must still validate structurally and keep the event chain intact.
        Making the new fields schema-required would reject it during
        ``authenticate_event_history`` before the ledger could report it as
        superseded, bricking every mission command on the issue.
        """
        legacy = copy.deepcopy(self.activation)
        for field in ("baseline_generation_commit", "baseline_generation_tree",
                      "active_execution_commit", "active_execution_tree",
                      "compatibility_proof"):
            legacy.pop(field)
        event = self.chain([self.auth()])[0]
        event["details"] = legacy
        event["event_hash"] = content_sha256(event)
        self.assertEqual(validate_document("audit-event", event), [])
        self.assertEqual(validate_event_chain([copy.deepcopy(event)])[0], True)
        # Structurally valid, yet permanently unusable.
        self.assertEqual(
            validate_activation_ledger([event], legacy,
                                       repository=self.activation["repository"])[1],
            "ACTIVATION_AUTHORIZATION_SUPERSEDED")

    def legacy_details(self):
        legacy = copy.deepcopy(self.activation)
        for field in ("baseline_generation_commit", "baseline_generation_tree",
                      "active_execution_commit", "active_execution_tree",
                      "compatibility_proof"):
            legacy.pop(field)
        return legacy

    def test_superseded_authorization_can_be_replaced(self):
        """A superseded authorization must not strand activation forever.

        It can never be attempted or consumed, so if it also blocked a
        replacement the baseline could never be activated by any means short of
        rewriting authenticated history.
        """
        current = copy.deepcopy(self.activation)
        current["founder_authorization_sequence"] = 2
        legacy = self.auth()
        legacy["details"] = self.legacy_details()
        legacy["sequence"] = 1
        replacement = self.auth()
        replacement["details"] = copy.deepcopy(current)
        replacement["sequence"] = 2
        events = self.chain([legacy, replacement])
        ok, code, _ = validate_activation_ledger(
            events, current, repository=self.activation["repository"])
        self.assertEqual((ok, code), (True, "ACTIVATION_AUTHORIZED"))

    def test_superseded_authorization_is_never_selected_for_consumption(self):
        current = copy.deepcopy(self.activation)
        current["founder_authorization_sequence"] = 2
        legacy = self.auth()
        legacy["details"] = self.legacy_details()
        legacy["sequence"] = 1
        replacement = self.auth()
        replacement["details"] = copy.deepcopy(current)
        replacement["sequence"] = 2
        events = self.chain([legacy, replacement])
        _, _, details = validate_activation_ledger(
            events, current, repository=self.activation["repository"])
        self.assertEqual(details["authorization_event_hash"], events[1]["event_hash"])

    def test_duplicate_current_authorization_still_fails_closed(self):
        first = self.auth()
        second = self.auth()
        second["sequence"] = 1
        self.assertEqual(
            validate_activation_ledger(self.chain([first, second]), self.activation,
                                       repository=self.activation["repository"])[1],
            "ACTIVATION_HISTORY_INVALID")

    def test_default_branch_advance_after_authorization_fails_closed(self):
        self.assertEqual(
            self.ledger(self.activation, current_commit="9" * 40)[1],
            "ACTIVATION_COMMIT_MISMATCH")

    def test_chain_digest_must_match_the_declared_proof(self):
        self.assertEqual(
            self.ledger(self.activation, compatibility_chain=self.compat_chain())[1],
            "ACTIVATION_COMPATIBILITY_CHAIN_DIGEST_MISMATCH")

    def test_ledger_validates_the_supplied_chain(self):
        chain = self.compat_chain(commits=[])
        candidate = copy.deepcopy(self.activation)
        candidate["compatibility_proof"] = self.proof(
            chain_sha256=content_sha256(chain), commit_count=0)
        self.assertEqual(
            self.ledger(candidate, compatibility_chain=chain)[1],
            "COMPATIBILITY_CHAIN_RANGE_MISSING")


if __name__ == "__main__":
    unittest.main()
