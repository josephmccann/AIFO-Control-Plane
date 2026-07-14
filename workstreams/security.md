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

## Gaps

- CloudTrail status not verified.
- Session Manager logging not configured.
- Product secrets architecture not designed.
- Apply role final permissions not designed.

## Next Work

- Add Session Manager logging ADR.
- Add least-privilege apply role design after apply boundary is approved.
- Add credential and secret scanning to CI.
