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
- Current branch proposes CloudTrail management events, encrypted CloudTrail S3 storage, encrypted Session Manager logging, and Scheduler least-privilege controls before first host deployment.

## Gaps

- CloudTrail, Session Manager logging, and Scheduler resources are proposed but not deployed.
- Product secrets architecture not designed.
- Apply role final permissions not designed.

## Next Work

- Review the pre-deployment hardening plan.
- Add least-privilege apply role design after apply boundary is approved.
- Add credential and secret scanning to CI.
