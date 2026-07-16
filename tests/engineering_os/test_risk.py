import copy
import json
import os
import subprocess
import unittest
from pathlib import Path

from engineering_os.risk import compute_tier


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "engineering_os" / "fixtures" / "changed-files"


def files(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def policy():
    return {
        "repository": "acme/widgets",
        "founder_identities": ["founder"],
        "semantic_domains": [
            {
                "name": "documentation",
                "paths": ["docs/**"],
                "minimum_tier": "Tier 0",
                "owners": ["docs-owner"],
                "conflict_group": "documentation",
            },
            {
                "name": "reporting",
                "paths": ["src/reporting/**", "tests/reporting/**"],
                "minimum_tier": "Tier 1",
                "owners": ["reporting-owner"],
                "conflict_group": "reporting",
            },
            {
                "name": "governance",
                "paths": [".aifo/**", "docs/governance/**", "schemas/**"],
                "minimum_tier": "Tier 2",
                "owners": ["founder"],
                "conflict_group": "governance",
            },
        ],
        "tier_2_paths": [".aifo/**", ".github/**", "schemas/**", "SECURITY.md"],
    }


def mission(tier="Tier 1"):
    return {
        "mission_id": "mission-123",
        "repository": "acme/widgets",
        "risk_tier": tier,
        "capabilities": ["read", "write"],
        "rollback": {"class": "clean_revert", "plan": "revert"},
    }


class RiskTests(unittest.TestCase):
    def test_tier_zero_and_tier_one_classify_in_both_directions(self):
        tier_zero = compute_tier(mission("Tier 0"), policy(), files("tier-0/docs-only.json"))
        tier_one = compute_tier(mission("Tier 1"), policy(), files("tier-1/bounded-code.json"))
        self.assertEqual((tier_zero.computed_tier, tier_zero.allowed), ("Tier 0", True))
        self.assertEqual((tier_one.computed_tier, tier_one.allowed), ("Tier 1", True))

        under = compute_tier(mission("Tier 0"), policy(), files("tier-1/bounded-code.json"))
        over = compute_tier(mission("Tier 1"), policy(), files("tier-0/docs-only.json"))
        self.assertEqual((under.allowed, under.code), (False, "RISK_TIER_UNDER_DECLARED"))
        self.assertEqual((over.allowed, over.effective_tier), (True, "Tier 1"))

    def test_every_consequential_trigger_computes_tier_two(self):
        cases = {
            "schema": ({}, ["schemas/mission.json"]),
            "deployment": ({"capabilities": ["deploy"]}, ["src/reporting/render.py"]),
            "cloud": ({"capabilities": ["cloud_mutation"]}, ["src/reporting/render.py"]),
            "customer-data": ({"capabilities": ["customer_data"]}, ["src/reporting/render.py"]),
            "secret": ({"capabilities": ["secrets"]}, ["src/reporting/render.py"]),
            "spend": ({"capabilities": ["spend"]}, ["src/reporting/render.py"]),
            "cutover": ({"capabilities": ["cutover"]}, ["src/reporting/render.py"]),
            "methodology": ({"risk_signals": ["methodology"]}, ["src/reporting/render.py"]),
            "destructive": ({"risk_signals": ["destructive"]}, ["src/reporting/render.py"]),
            "security": ({"risk_signals": ["security"]}, ["src/reporting/render.py"]),
            "privacy": ({"risk_signals": ["privacy"]}, ["src/reporting/render.py"]),
            "public-claim": ({"risk_signals": ["public_claim"]}, ["src/reporting/render.py"]),
            "cross-module": ({"risk_signals": ["cross_module"]}, ["src/reporting/render.py"]),
            "cross-repository": ({"repository": "acme/other"}, ["src/reporting/render.py"]),
            "residual-risk": ({"risk_signals": ["residual_risk"]}, ["src/reporting/render.py"]),
            "irreversible": ({"rollback": {"class": "irreversible", "plan": "none"}}, ["src/reporting/render.py"]),
            "governance-policy": ({}, files("tier-2/governance.json")),
        }
        for name, (updates, changed) in cases.items():
            with self.subTest(name=name):
                candidate = mission("Tier 2")
                candidate.update(updates)
                decision = compute_tier(candidate, policy(), changed)
                self.assertEqual(decision.computed_tier, "Tier 2")
                self.assertTrue(decision.allowed)
                self.assertTrue(decision.triggers)

    def test_policy_may_raise_but_never_lower_a_tier(self):
        candidate = mission("Tier 1")
        raised_policy = policy()
        raised_policy["tier_2_paths"].append("src/reporting/**")
        raised = compute_tier(candidate, raised_policy, ["src/reporting/render.py"])
        self.assertEqual((raised.computed_tier, raised.allowed), ("Tier 2", False))

        lower_policy = policy()
        lower_policy["semantic_domains"][1]["minimum_tier"] = "Tier 0"
        not_lowered = compute_tier(mission("Tier 2"), lower_policy, ["src/reporting/render.py"])
        self.assertEqual(not_lowered.effective_tier, "Tier 2")

    def test_unknown_or_malformed_evidence_fails_closed_at_tier_two(self):
        candidate = mission("Tier 2")
        candidate["risk_signals"] = ["unrecognized"]
        self.assertEqual(compute_tier(candidate, policy(), ["src/reporting/render.py"]).computed_tier, "Tier 2")
        self.assertEqual(compute_tier(candidate, policy(), ["../escape"]).code, "RISK_INPUT_INVALID")

    def test_tier_wrapper_is_executable_and_emits_a_machine_decision(self):
        wrapper = ROOT / "scripts" / "engineering-os" / "validate-tier"
        self.assertTrue(os.access(wrapper, os.X_OK))
        completed = subprocess.run(
            [str(wrapper), "--mission", str(ROOT / "tests/engineering_os/fixtures/mission-valid.json"),
             "--policy", str(ROOT / "tests/engineering_os/fixtures/policy-control-plane.json"),
             "--changed-files", str(FIXTURES / "tier-2/governance.json")],
            check=False, capture_output=True, text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout)["computed_tier"], "Tier 2")


if __name__ == "__main__":
    unittest.main()
