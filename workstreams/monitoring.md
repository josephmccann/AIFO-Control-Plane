# Monitoring Workstream

## Objective

Provide enough observability for operations, audit, cost control, and recovery without surveillance or unnecessary paid tooling.

## Current State

- No monitoring resources deployed beyond GitHub Actions history and AWS bootstrap verification.
- EC2 detailed monitoring defaults to false.
- Expected future sources: CloudTrail, SSM session history, CloudWatch logs, GitHub Actions logs, AWS Budgets.
- Current branch proposes CloudTrail management events, Session Manager CloudWatch Logs with 30-day retention, and EventBridge Scheduler DLQ retention before first host deployment.

## Gaps

- Proposed audit and session log resources are not deployed.
- Cost anomaly or budget alerting not imported.
- Product runtime telemetry not mapped to AWS.

## Next Work

- Review and approve or reject the audit/logging/scheduler plan.
- Document product telemetry privacy boundaries before AWS runtime.
