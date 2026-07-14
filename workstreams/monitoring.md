# Monitoring Workstream

## Objective

Provide enough observability for operations, audit, cost control, and recovery without surveillance or unnecessary paid tooling.

## Current State

- No monitoring resources deployed.
- EC2 detailed monitoring defaults to false.
- Expected future sources: CloudTrail, SSM session history, CloudWatch logs, GitHub Actions logs, AWS Budgets.
- Session Manager logging design recommends CloudWatch Logs with 30-day retention.

## Gaps

- Session logs not streamed to CloudWatch.
- Log retention not defined.
- Cost anomaly or budget alerting not imported.
- Product runtime telemetry not mapped to AWS.

## Next Work

- Implement Session Manager logging after bootstrap approval.
- Define log retention boundaries.
- Document product telemetry privacy boundaries before AWS runtime.
