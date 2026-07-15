# Monitoring Workstream

## Objective

Provide enough observability for operations, audit, cost control, and recovery without surveillance or unnecessary paid tooling.

## Current State

- CloudTrail and encrypted Session Manager log resources are deployed; Session Manager connectivity and log delivery were verified.
- EC2 detailed monitoring defaults to false.
- Current sources: CloudTrail, SSM session history, encrypted CloudWatch session logs, GitHub Actions logs, EventBridge Scheduler, and its DLQ.
- AWS Budgets remains manually managed outside Terraform.

## Gaps

- Cost anomaly or budget alerting not imported.
- Product runtime telemetry not mapped to AWS.

## Next Work

- Add periodic checks for stale deployment-status documentation.
- Add lightweight monthly cost evidence.
- Document product telemetry privacy boundaries before AWS runtime.
