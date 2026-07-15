# AI.FO Control Plane Handoff

Session state: PARKED — SAFE FOR CODEX CLI UPDATE

## Purpose

Canonical starting context for AWS infrastructure, Terraform, GitHub Actions, SSM access, security boundaries, and control-plane operations.

The detailed Codex 5.6 resume handoff is [../session-handoffs/HANDOFF_CONTROL_PLANE_2026-07-15.md](../session-handoffs/HANDOFF_CONTROL_PLANE_2026-07-15.md).

## Stable Context

- Repository: `josephmccann/AIFO-Control-Plane`
- Product repository: `josephmccann/AI.FO-Demo`
- AWS account: `350480401760`
- AWS region: `us-west-2`
- Human access: IAM Identity Center
- Human administrator permission set: `AIFO-Platform-Admin`
- Root MFA: enabled
- Monthly budget target: $250, currently created manually outside Terraform
- GitHub Actions AWS access: OIDC only, no static AWS keys
- EC2 administration: Systems Manager Session Manager only
- Public SSH: not allowed

## Current Repository State

- Latest main commit at checkpoint start: `b9e1b539474efa30086d9031b3118cfe241ffa28`
- Current-scope AWS baseline: operationally complete
- Product runtime infrastructure: not deployed
- Apply workflow: absent
- `terraform-apply` environment: exists but must remain unused

## Current Architecture

The deployed initial control-plane environment includes:

- Multi-Region CloudTrail management-events trail with log-file validation.
- Dedicated encrypted CloudTrail S3 log bucket with public access blocked and lifecycle expiration.
- VPC with DNS support.
- One public subnet in one Availability Zone.
- Internet Gateway and outbound default route.
- S3 gateway endpoint.
- Ubuntu EC2 control-plane host `i-0254a9e2fcbcdebd7`.
- Public IPv4 while running for outbound egress.
- Zero host ingress rules.
- HTTPS and DNS egress only.
- No SSH key.
- SSM instance role using `AmazonSSMManagedInstanceCore`.
- IMDSv2 required.
- 100 GiB encrypted gp3 root volume.
- Termination protection enabled.
- Session Manager logging to encrypted CloudWatch Logs with 30-day retention.
- EventBridge Scheduler start and stop schedules targeting only the Terraform-managed host.
- Scheduler dead-letter queue.
- Optional Terraform-managed AWS Budget, default disabled.

## Bootstrap Architecture

- State bucket: `aifo-terraform-state-350480401760-us-west-2`
- State key: `control-plane/terraform.tfstate`
- OIDC provider: `arn:aws:iam::350480401760:oidc-provider/token.actions.githubusercontent.com`
- Plan role: `arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Plan`
- Apply role: `arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Apply`
- Plan role policy: `arn:aws:iam::350480401760:policy/AIFO-GitHubActions-Terraform-PlanReadAccess`, default version `v4`
- Apply role status: state-access-only, no inline policies

## Verification

- Local Terraform plan: `0 to add, 0 to change, 0 to destroy`
- Latest GitHub Terraform Plan: https://github.com/josephmccann/AIFO-Control-Plane/actions/runs/29378532712
- GitHub plan classification: exit code `0`, `0` add / `0` change / `0` destroy, result `clean`
- EC2 state: `stopped`
- Session Manager connectivity: tested successfully after deployment
- Session Manager logging: reached `/aifo/control-plane/session-manager`
- CloudTrail: deployed and logging management events

## Current Cost Finding

Current modeled totals for `m7i-flex.2xlarge`, 100 GiB gp3, and public IPv4:

- 8 hours per weekday: about `$76.30` monthly before low-volume logs/taxes
- 12 hours per day: about `$149.64` monthly before low-volume logs/taxes
- Always on: about `$291.27` monthly before low-volume logs/taxes

Always-on operation exceeds the $250 budget target. Scheduled operation remains the approved posture.

## Product Fit Boundary

The control plane does not currently host AI.FO product runtime. Product hosting is deferred because current product requirements include PostgreSQL, R2 or storage migration, secrets, QBO OAuth, AI provider credentials, domain/TLS, and validation flows that need explicit design.

## Guardrails

- Do not run `terraform apply` without explicit human approval.
- Do not run `terraform destroy`.
- Do not create, modify, or delete AWS resources without explicit human approval.
- Do not start the EC2 instance unless an approved operating window or emergency override applies.
- Do not create an apply workflow until an enforceable approval boundary exists.
- Do not use long-lived AWS keys.
- Do not open inbound administrative ports.
- Do not use SSH as an emergency bypass.
- Do not deploy product runtime until a product-hosting ADR is approved.
