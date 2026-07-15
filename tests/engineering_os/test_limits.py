import unittest

from engineering_os.limits import evaluate_limits


CAPS = {
    "model_cost_usd": 25.0,
    "model_tokens": 250000,
    "wall_clock_minutes": 240,
    "remediation_cycles": 2,
    "concurrent_agents": 4,
    "ci_reruns": 3,
}


class LimitTests(unittest.TestCase):
    def test_values_at_caps_are_allowed(self):
        decision = evaluate_limits(dict(CAPS), CAPS, current_state="In Progress")
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.recommended_action, "continue")

    def test_each_crossed_cap_preserves_state_and_recommends_parked(self):
        cases = {
            "model_cost_usd": 25.01,
            "model_tokens": 250001,
            "wall_clock_minutes": 241,
            "remediation_cycles": 3,
            "concurrent_agents": 5,
            "ci_reruns": 4,
        }
        for name, value in cases.items():
            with self.subTest(limit=name):
                measured = {key: 0 for key in CAPS}
                measured[name] = value
                decision = evaluate_limits(measured, CAPS, current_state="In Progress")
                self.assertFalse(decision.allowed)
                self.assertTrue(decision.preserve_state)
                self.assertEqual(decision.recommended_action, "Parked")
                self.assertEqual(decision.breaches[0].name, name)
                self.assertEqual(decision.breaches[0].measured_value, value)
                self.assertEqual(decision.breaches[0].cap, CAPS[name])

    def test_malformed_or_missing_measurements_fail_closed(self):
        decision = evaluate_limits({"model_cost_usd": -1}, CAPS, current_state="Ready")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.code, "LIMIT_INPUT_INVALID")
        self.assertTrue(decision.preserve_state)
        self.assertEqual(decision.current_state, "Ready")


if __name__ == "__main__":
    unittest.main()
