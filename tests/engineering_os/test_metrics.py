import unittest

from engineering_os.metrics import project_metrics
from engineering_os.schema import validate_document


class MetricsTests(unittest.TestCase):
    def test_metrics_derive_all_required_operational_counts(self):
        events = [
            {
                "type": "mission.ready", "occurred_at": "2026-07-15T10:00:00Z",
                "details": {},
            },
            {
                "type": "mission.closed", "occurred_at": "2026-07-15T11:00:00Z",
                "details": {"founder_minutes": 12},
            },
            {"type": "finding.valid", "occurred_at": "2026-07-15T10:20:00Z", "details": {}},
            {"type": "finding.invalid", "occurred_at": "2026-07-15T10:21:00Z", "details": {}},
            {"type": "finding.duplicate", "occurred_at": "2026-07-15T10:22:00Z", "details": {}},
            {"type": "finding.founder_decision", "occurred_at": "2026-07-15T10:23:00Z", "details": {}},
            {"type": "mission.parked", "occurred_at": "2026-07-15T10:30:00Z", "details": {}},
            {"type": "mission.orphaned", "occurred_at": "2026-07-15T10:31:00Z", "details": {}},
            {"type": "override.applied", "occurred_at": "2026-07-15T10:32:00Z", "details": {}},
            {"type": "rollback.completed", "occurred_at": "2026-07-15T10:33:00Z", "details": {}},
            {"type": "incident.opened", "occurred_at": "2026-07-15T10:34:00Z", "details": {}},
            {
                "type": "usage.recorded", "occurred_at": "2026-07-15T10:35:00Z",
                "details": {
                    "model_cost_usd": 2.5, "model_tokens": 1000,
                    "defects": 1, "false_positive_blocks": 1,
                },
            },
        ]
        for event in events:
            event["mission_id"] = "mission-7"
        evidence = [{"mission_id": "mission-7", "generated_at": "2026-07-15T11:00:00Z"}]
        metrics = project_metrics(
            events,
            evidence,
            period_start="2026-07-15T00:00:00Z",
            period_end="2026-07-16T00:00:00Z",
        )
        self.assertEqual(metrics["founder_minutes"], 12)
        self.assertEqual(metrics["lifecycle_seconds"]["mission-7"], 3600)
        self.assertEqual(metrics["model_cost_usd"], 2.5)
        self.assertEqual(metrics["model_tokens"], 1000)
        self.assertEqual(metrics["findings"], {
            "valid": 1, "invalid": 1, "duplicate": 1, "founder_decision": 1,
        })
        self.assertEqual(metrics["remediation_cycles"], 1)
        self.assertEqual(metrics["defects"], 1)
        self.assertEqual(metrics["parked"], 1)
        self.assertEqual(metrics["orphaned"], 1)
        self.assertEqual(metrics["false_positive_blocks"], 1)
        self.assertEqual(metrics["overrides"], 1)
        self.assertEqual(metrics["rollbacks"], 1)
        self.assertEqual(metrics["incidents"], 1)
        self.assertEqual(metrics["throughput"], 1)
        self.assertEqual(validate_document("metrics", metrics), [])
        self.assertNotIn("finding_quota", metrics)
        self.assertNotIn("people_ranking", metrics)

    def test_invalid_ranges_numbers_or_unknown_events_fail_closed(self):
        with self.assertRaises(ValueError):
            project_metrics([], [], period_start="bad", period_end="also-bad")
        with self.assertRaises(ValueError):
            project_metrics(
                [{
                    "type": "usage.recorded",
                    "occurred_at": "2026-07-15T10:00:00Z",
                    "details": {"model_cost_usd": -1},
                }],
                [],
                period_start="2026-07-15T00:00:00Z",
                period_end="2026-07-16T00:00:00Z",
            )

    def test_reversed_lifecycle_and_negative_dynamic_schema_values_fail_closed(self):
        events = [
            {
                "mission_id": "mission-7",
                "type": "mission.ready",
                "occurred_at": "2026-07-15T12:00:00Z",
                "details": {},
            },
            {
                "mission_id": "mission-7",
                "type": "mission.closed",
                "occurred_at": "2026-07-15T11:00:00Z",
                "details": {},
            },
        ]
        with self.assertRaises(ValueError):
            project_metrics(
                events,
                [],
                period_start="2026-07-15T00:00:00Z",
                period_end="2026-07-16T00:00:00Z",
            )
        invalid = {
            "schema_version": "1.0.0",
            "period_start": "2026-07-15T00:00:00Z",
            "period_end": "2026-07-16T00:00:00Z",
            "founder_minutes": 0,
            "lifecycle_seconds": {"mission-7": -1},
            "model_cost_usd": 0,
            "model_tokens": 0,
            "findings": {
                "valid": 0, "invalid": 0, "duplicate": 0,
                "founder_decision": 0,
            },
            "remediation_cycles": 0,
            "defects": 0,
            "parked": 0,
            "orphaned": 0,
            "false_positive_blocks": 0,
            "overrides": 0,
            "rollbacks": 0,
            "incidents": 0,
            "throughput": 0,
        }
        self.assertTrue(validate_document("metrics", invalid))
        with self.assertRaises(ValueError):
            project_metrics(
                [{
                    "type": "quota.enforced",
                    "occurred_at": "2026-07-15T10:00:00Z",
                    "details": {},
                }],
                [],
                period_start="2026-07-15T00:00:00Z",
                period_end="2026-07-16T00:00:00Z",
            )


if __name__ == "__main__":
    unittest.main()
