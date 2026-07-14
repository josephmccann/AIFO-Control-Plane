# Monitoring Workstream

## Objective

Provide enough observability for operations, audit, cost control, and recovery without surveillance or unnecessary paid tooling.

## Current State

- CloudTrail and Session Manager log resources are deployed, but no EC2 session logs exist because the host was not created.
- EC2 detailed monitoring defaults to false.
- Expected future sources: CloudTrail, SSM session history, CloudWatch logs, GitHub Actions logs, AWS Budgets.
- EventBridge Scheduler DLQ exists; start and stop schedules do not exist yet because the EC2 instance was not created.

## Gaps

- No SSM managed node or session connectivity has been verified.
- Cost anomaly or budget alerting not imported.
- Product runtime telemetry not mapped to AWS.

## Next Work

- Verify CloudTrail delivery after initial logs arrive.
- Test Session Manager logging after a future approved EC2 launch.
- Document product telemetry privacy boundaries before AWS runtime.
