import copy
import unittest

from engineering_os.commands import validate_activation_ledger


class ActivationLedgerTests(unittest.TestCase):
    def setUp(self):
        self.activation = {
            "repository": "josephmccann/AIFO-Control-Plane",
            "mission_issue": 26,
            "remediation_head": "b3c0a2c7c85fbd45167d61ae29fc1f21dfafad9e",
            "remediation_tree": "9fd7af9c8f231759ebbee851836dd83a097418d6",
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
            "founder_authorization_sequence": 42,
        }

    def auth(self):
        return {"type": "test_integrity.baseline.authorized", "actor_role": "founder",
                "event_hash": "a" * 64, "sequence": 7, "details": copy.deepcopy(self.activation)}

    def consume(self, auth):
        details = copy.deepcopy(self.activation)
        details.update({"authorization_event_hash": auth["event_hash"],
                        "authorization_sequence": auth["sequence"],
                        "consumer_identity": "github-actions[bot]/test-integrity",
                        "consumed_at": "2026-07-17T20:00:00Z",
                        "consumption_result": "activated",
                        "post_consumption_state": "active"})
        return {"type": "test_integrity.baseline.consumed", "actor_role": "system",
                "details": details}

    def attempt(self, auth):
        details = copy.deepcopy(self.activation)
        details.update({"authorization_event_hash": auth["event_hash"],
                        "authorization_sequence": auth["sequence"],
                        "consumer_identity": "github-actions[bot]/test-integrity",
                        "consumed_at": "2026-07-17T20:00:00Z",
                        "consumption_result": "attempted",
                        "post_consumption_state": "locked",
                        "attempt_event_hash": "0" * 64})
        return {"type": "test_integrity.baseline.consumption_attempted", "actor_role": "system",
                "event_hash": "c" * 64, "details": details}

    def test_authorization_is_valid_and_consumption_is_single_use(self):
        auth = self.auth()
        ok, code, details = validate_activation_ledger(
            [auth], self.activation, repository=self.activation["repository"],
            current_commit=self.activation["remediation_head"], current_tree=self.activation["remediation_tree"])
        self.assertEqual((ok, code), (True, "ACTIVATION_AUTHORIZED"))
        self.assertFalse(details["consumed"])
        attempt = self.attempt(auth)
        consumed = self.consume(auth)
        consumed["details"]["attempt_event_hash"] = attempt["event_hash"]
        ok, code, details = validate_activation_ledger(
            [auth, attempt, consumed], self.activation,
            repository=self.activation["repository"])
        self.assertEqual((ok, code), (True, "ACTIVATION_ALREADY_CONSUMED"))
        self.assertTrue(details["consumed"])

    def test_replay_mismatch_and_context_changes_fail_closed(self):
        auth = self.auth()
        for mutation, expected in (({"activation_nonce": "different-nonce-012345678901234567890123"}, "ACTIVATION_TUPLE_MISMATCH"),
                                   ({"remediation_head": "0" * 40}, "ACTIVATION_COMMIT_MISMATCH"),
                                   ({"remediation_tree": "0" * 40}, "ACTIVATION_TREE_MISMATCH")):
            candidate = copy.deepcopy(self.activation)
            candidate.update(mutation)
            args = {"repository": self.activation["repository"]}
            if expected == "ACTIVATION_COMMIT_MISMATCH": args["current_commit"] = self.activation["remediation_head"]
            if expected == "ACTIVATION_TREE_MISMATCH": args["current_tree"] = self.activation["remediation_tree"]
            self.assertEqual(validate_activation_ledger([auth], candidate, **args)[1], expected)
        self.assertEqual(validate_activation_ledger([auth, auth], self.activation,
            repository=self.activation["repository"])[1], "ACTIVATION_AUTHORIZATION_REPLAY")

    def test_consumption_requires_the_authenticated_authorization(self):
        auth = self.auth()
        attempt = self.attempt(auth)
        consumed = self.consume(auth)
        consumed["details"]["attempt_event_hash"] = attempt["event_hash"]
        consumed["details"]["authorization_event_hash"] = "b" * 64
        self.assertEqual(validate_activation_ledger([auth, attempt, consumed], self.activation,
            repository=self.activation["repository"])[1], "ACTIVATION_AUTHORIZATION_REFERENCE_INVALID")
        self.assertEqual(validate_activation_ledger([consumed], self.activation,
            repository=self.activation["repository"])[1], "ACTIVATION_ORPHAN_CONSUMPTION")

    def test_wrong_repository_or_malformed_tuple_fails_closed(self):
        auth = self.auth()
        self.assertEqual(validate_activation_ledger([auth], self.activation,
            repository="attacker/example")[1], "ACTIVATION_TUPLE_INVALID")
        malformed = copy.deepcopy(self.activation)
        malformed["unexpected"] = True
        self.assertEqual(validate_activation_ledger([auth], malformed,
            repository=self.activation["repository"])[1], "ACTIVATION_TUPLE_INVALID")


if __name__ == "__main__":
    unittest.main()
