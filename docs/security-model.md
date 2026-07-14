# Security Model

## Security Goals

- Keep AWS administrative access identity-based and auditable.
- Avoid long-lived credentials.
- Remove public inbound paths by default.
- Use Session Manager instead of SSH.
- Keep Terraform state and plans out of source control.
- Make cost and blast radius visible before deployment.
- Capture management-plane audit evidence before the first host is deployed.

## Identity and Access

### Human Access

Human administrator access uses IAM Identity Center with the `AIFO-Platform-Admin` permission set.

Root user usage is limited to account recovery and account-level break-glass operations. Root MFA is enabled.

### Automation Access

GitHub Actions uses OIDC role assumption.

Required controls for GitHub roles:

- Trust only `token.actions.githubusercontent.com`.
- Require audience `sts.amazonaws.com`.
- Restrict the `sub` claim to the exact repository and GitHub environment.
- Use a plan role for `terraform plan`.
- Reserve a separate apply role for a future protected apply workflow, but keep it state-access-only until an approval boundary is available.
- Do not use static AWS access keys.
- Keep the plan role to the minimum read surface required for Terraform refresh and plan. Add read actions only after observed failures and review.

The current plan workflow uses the `terraform-plan` GitHub environment and successfully assumes the plan role through OIDC.

The `terraform-apply` environment exists, but GitHub required environment reviewers are unavailable on the current repository plan. Because it cannot enforce manual reviewer approval, it must remain unused. Do not create an apply workflow. Until GitHub reviewer protection is available or a replacement approval boundary is accepted, control-plane applies must use an authenticated IAM Identity Center session after a reviewed approval packet.

## Network Security

The initial network posture is public egress with no public ingress:

- The host is launched in one public subnet.
- The host receives a public IPv4 address.
- The host security group has no ingress rules.
- No SSH key pair is attached.
- Administration uses SSM over outbound HTTPS.
- Host egress is limited to:
  - TCP 443 to `0.0.0.0/0`
  - TCP/UDP 53 to the VPC CIDR for resolver access

Public addressing is used only to avoid NAT Gateway cost while retaining outbound internet access for package mirrors, GitHub, container registries, SSM, and external APIs. It does not create an inbound path by itself; inbound reachability remains blocked by security-group policy.

## Host Security

The EC2 host baseline includes:

- Ubuntu AMI selected through a public SSM parameter.
- IMDSv2 required.
- Encrypted root EBS volume.
- Termination protection enabled by default.
- SSM managed instance role.
- Session Manager as the administrative access path.
- Cloud-init rewrite of Ubuntu package sources from HTTP to HTTPS where applicable.
- Session Manager session logging to encrypted CloudWatch Logs.
- Instance-role permissions for only the configured Session Manager log group and KMS key.

Implemented pre-deployment hardening adds:

- Multi-Region CloudTrail management events with log-file validation.
- Dedicated encrypted S3 bucket for CloudTrail logs with 365-day lifecycle expiration.
- EventBridge Scheduler start/stop automation scoped to the single host.

Future hardening should add:

- Centralized patch policy.
- CloudWatch agent configuration if host metrics/logs require it.
- Host-level vulnerability scanning.
- EDR or equivalent workload protection if required.

## Secrets

Do not commit:

- AWS access keys
- Terraform state
- Terraform plan files
- `.terraform/`
- `terraform.tfvars`
- Private keys
- Session logs
- Environment files containing secrets

GitHub repository variables can hold non-secret deployment configuration such as role ARNs and backend names. Sensitive values must use an approved secrets manager, not source control.

## Terraform State

Terraform state can contain sensitive infrastructure metadata. The intended backend must use:

- S3 bucket versioning
- Server-side encryption
- Native S3 lockfiles with `use_lockfile = true`
- Least-privilege bucket policies
- Block Public Access on the state bucket

DynamoDB locking is not used in the initial version. Native S3 lockfiles require Terraform `>= 1.10.0`.

State bootstrap is complete and was applied only after explicit approval.

## Logging and Audit

Expected audit sources:

- AWS CloudTrail for IAM, STS, EC2, SSM, and Terraform activity
- GitHub Actions logs for plan workflow execution
- Session Manager session history
- CloudWatch Logs for Session Manager stream output
- EventBridge Scheduler and SQS DLQ state for scheduled start/stop failures

CloudTrail is implemented as an account-level multi-Region trail. An organization trail is deferred until AWS Organizations scope is confirmed.

## Product Data Boundary

The current control plane does not host product runtime or customer data. Future infrastructure that handles accounting data, QBO tokens, uploads, AI prompts, verifier outputs, or decision records requires a product runtime ADR, secrets design, retention model, and privacy review.

## Threat Model

| Threat | Control |
| --- | --- |
| Public SSH scanning | No SSH ingress, no key pair |
| Public IPv4 exposure | Security group has zero inbound rules |
| Stolen CI credentials | OIDC short-lived credentials, no static keys |
| Overbroad CI role | Separate plan role from future apply role |
| Accidental deployment | No apply workflow, `terraform-apply` unused, local apply requires approval packet |
| State exposure | S3 backend with encryption, versioning, and lockfiles |
| Credential leakage | `.gitignore`, no long-lived keys, no committed secrets |
| Unbounded spend | Manual AWS budget already exists; Terraform import path documented |
| Missing activity audit | Multi-Region CloudTrail management events and Session Manager logging |
| Forgotten host runtime | EventBridge Scheduler start/stop plus manual override runbook |

## Pre-Deployment Security Checklist

- Confirm CloudTrail management trail is in the reviewed plan.
- Confirm Session Manager log group, KMS key, and preferences document are in the reviewed plan.
- Confirm EventBridge Scheduler start/stop targets only the control-plane host.
- Confirm remote-state bucket and GitHub OIDC bootstrap verification.
- Confirm `terraform-apply` remains unused while required reviewers are unavailable.
- Confirm `AWS_TERRAFORM_PLAN_ROLE_ARN`, `TF_BACKEND_BUCKET`, and `TF_BACKEND_KEY` repository variables.
- Confirm budget notification email recipients in the manually created budget.
- Confirm the selected EC2 instance type is acceptable under the budget.
- Confirm whether the host is always-on, scheduled, or downsized.
- Confirm no host ingress is introduced.
