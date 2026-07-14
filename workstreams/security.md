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
- CloudTrail management events, encrypted CloudTrail S3 storage, encrypted Session Manager logging, and Scheduler prerequisite controls are partially deployed.

## Gaps

- EC2 host and Scheduler start/stop schedules are not deployed because AWS account validation blocked EC2 launch.
- Product secrets architecture not designed.
- Apply role final permissions not designed.

## Next Work

- Re-plan after AWS validation clears and verify residual resources before any renewed apply.
- Add least-privilege apply role design after apply boundary is approved.
- Add credential and secret scanning to CI.
