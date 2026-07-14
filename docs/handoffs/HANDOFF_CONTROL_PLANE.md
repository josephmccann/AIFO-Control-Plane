# AI.FO Control Plane Handoff

## Purpose

Canonical starting context for AWS infrastructure, Terraform, GitHub Actions, SSM access, security boundaries, and control-plane operations.

## Stable Context

- Repository: `josephmccann/AIFO-Control-Plane`
- Product repository: `josephmccann/AI.FO-Demo`
- AWS region: `us-west-2`
- Human access: IAM Identity Center
- Human administrator permission set: `AIFO-Platform-Admin`
- Root MFA: enabled
- Monthly budget target: $250, currently created manually outside Terraform
- GitHub Actions AWS access: OIDC only, no static AWS keys
- EC2 administration: Systems Manager Session Manager only
- Public SSH: not allowed
- Initial host target: Ubuntu, approximately 8 vCPU and 32 GiB RAM

## Current Repository State

Baseline commit:

```text
4da93f1b674abf108e8c0e1bcb1d97c7a122baed
```

Operating-model merge commit:

```text
6f8064b9de3aaa0f099013170c3c007e41fd266f
```

Bootstrap infrastructure has been deployed. Pre-deployment audit/logging/network prerequisites were partially deployed during the approved 2026-07-14 change window. The control-plane host and product runtime have not been deployed.

GitHub planning is configured and has succeeded through OIDC. GitHub required reviewers are unavailable on the current repository plan, so `terraform-apply` exists but must remain unused and no apply workflow may be created.

## Current Architecture

The initial control-plane environment defines:

- Multi-Region CloudTrail management-events trail with log-file validation.
- Dedicated encrypted CloudTrail S3 log bucket with public access blocked and lifecycle expiration.
- VPC with DNS support.
- One public subnet in one Availability Zone by default.
- Internet Gateway and outbound default route.
- S3 gateway endpoint.
- Ubuntu EC2 control-plane host.
- Public IPv4 address for outbound egress.
- Zero host ingress rules.
- HTTPS and DNS egress only.
- No SSH key.
- SSM instance role using `AmazonSSMManagedInstanceCore`.
- IMDSv2 required.
- 100 GiB encrypted gp3 root volume.
- Termination protection enabled by default.
- Session Manager logging to encrypted CloudWatch Logs with 30-day retention.
- EventBridge Scheduler start and stop schedules targeting only the Terraform-managed host.
- Scheduler dead-letter queue.
- Optional Terraform-managed AWS Budget, default disabled.

## Bootstrap Architecture

Bootstrap roots are separate:

- `terraform/bootstrap/remote-state/`: applied S3 state bucket with encryption, versioning, Block Public Access, and native lockfile support.
- `terraform/bootstrap/github-oidc/`: applied GitHub OIDC provider plus separate plan and apply roles.

The plan role is used by the `terraform-plan` environment. The apply role is reserved for a future approval boundary and currently has only Terraform state access. No apply workflow exists.

The plan role policy now includes additional read-only actions for CloudTrail, KMS, CloudWatch Logs, EventBridge Scheduler, SQS, SSM, and S3 lifecycle/ownership refresh. The apply role was not modified and still has only Terraform state access.

Bootstrap resources:

- State bucket: `aifo-terraform-state-350480401760-us-west-2`
- OIDC provider: `arn:aws:iam::350480401760:oidc-provider/token.actions.githubusercontent.com`
- Plan role: `arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Plan`
- Apply role: `arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Apply`

Partial control-plane resources created during the approved 2026-07-14 change window:

- CloudTrail: `arn:aws:cloudtrail:us-west-2:350480401760:trail/aifo-control-plane-management-events`
- CloudTrail log bucket: `aifo-control-plane-cloudtrail-350480401760-us-west-2`
- VPC: `vpc-0f73b1daaa9fc17ab`
- Public subnet: `subnet-03ce35314c75b8e1f`
- Security group: `sg-0190e01bae800bb1a`
- S3 gateway endpoint: `vpce-058114f11531d5fdd`
- EC2 role/profile: `aifo-control-plane-ec2-ssm-role`, `aifo-control-plane-ec2-profile`
- Session Manager log group: `/aifo/control-plane/session-manager`
- Session Manager KMS key: `arn:aws:kms:us-west-2:350480401760:key/e36ac1c5-105c-42c1-92f9-06fcf02cb772`
- Scheduler group and role: `aifo-control-plane-host`, `aifo-control-plane-scheduler-role`
- Scheduler DLQ: `https://sqs.us-west-2.amazonaws.com/350480401760/aifo-control-plane-scheduler-dlq`

Blocked resources:

- EC2 instance: not created.
- EBS root volume: not created.
- Scheduler start and stop schedules: not created.
- Scheduler inline policy: not created.

Blocker: AWS returned `PendingVerification` for EC2 `RunInstances` in `us-west-2`. Do not retry apply until account validation clears and a renewed approval gate is granted.

## Current Cost Finding

Current AWS Price List data for us-west-2 shows `m7i-flex.2xlarge` compute at $0.38304/hour. With a 100 GiB gp3 root volume and public IPv4, estimated monthly totals are $76.30 for 8 hours per weekday, $149.64 for 12 hours per day, and $291.27 always on before data transfer, logs, snapshots, taxes, and the low-volume audit baseline. Continuous operation exceeds the $250 budget target unless size, schedule, commitment pricing, or budget are changed.

The pre-deployment audit controls are expected to add about $1-$3/month at low activity, primarily from one customer-managed KMS key plus small S3 and CloudWatch Logs usage.

## Product Fit Boundary

The control plane does not currently host AI.FO product runtime. Product hosting is deferred because current product requirements include PostgreSQL, R2 or storage migration, secrets, QBO OAuth, AI provider credentials, domain/TLS, and validation flows that need explicit design.

## Deployment Prerequisites

1. Wait for AWS account validation to clear or open an AWS Support account-management case.
2. Re-run `terraform plan` for `terraform/environments/control-plane`.
3. Confirm the residual plan contains only the EC2 instance, Scheduler inline policy, and Scheduler start/stop schedules.
4. Apply locally with IAM Identity Center only after a renewed explicit approval packet.
5. After EC2 creation, verify SSM online registration, test one Session Manager session, and manually stop the instance.
6. Do not add an apply workflow unless GitHub reviewer protection or an equivalent approval boundary is available.

## Guardrails

- Do not run `terraform apply` without explicit human approval.
- Do not create AWS resources without explicit human approval.
- Do not use long-lived AWS keys.
- Do not open inbound administrative ports.
- Do not use SSH as an emergency bypass.
- Do not deploy product runtime until a product-hosting ADR is approved.
