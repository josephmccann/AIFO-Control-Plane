# Security Workstream

## Objective

Keep the control plane aligned with no-static-keys, least privilege, no public ingress, auditability, and customer-data minimization.

## Current Controls

- IAM Identity Center for human access.
- GitHub OIDC for automation.
- Separate plan and apply roles.
- Apply workflow absent.
- SSM-only administration.
- IMDSv2 required.
- Terraform state excluded from Git.
- CloudTrail management events and encrypted CloudTrail S3 storage.
- Encrypted Session Manager logging with 30-day retention.
- EventBridge Scheduler start/stop automation targeting only the control-plane host.
- Approval-gated monthly manual host patching under ADR-0010.

## Gaps

- Product secrets architecture not designed.
- Apply role final permissions not designed.
- Automated patch compliance reporting is deferred for the current single-host scope.

## Next Work

- Run approved monthly patch windows and record evidence.
- Add least-privilege apply role design after apply boundary is approved.
- Add credential and secret scanning to CI.
