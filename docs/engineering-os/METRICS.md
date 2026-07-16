# Engineering OS metrics

Metrics are deterministic projections of audit events and evidence manifests.
They include founder minutes, lifecycle duration, model cost and tokens,
finding dispositions, remediation cycles, defects, parked and orphaned events,
false-positive blocks, overrides, rollbacks, incidents, and throughput.

Metrics describe system behavior. There is no finding quota, rejection quota,
people ranking, model ranking, or target that rewards creating findings.
Invalid and duplicate findings remain visible so review quality and guard
precision can improve without distorting the audit history.

Metric inputs are closed, bounded to an exact UTC period, and nonnegative.
Unknown event types or metric fields fail closed instead of being silently
ignored.
