# Current State

Date: 2026-07-14

## Repository

- Repository: `josephmccann/AIFO-Control-Plane`
- Baseline commit: `4da93f1b674abf108e8c0e1bcb1d97c7a122baed`
- Operating-model merge commit: `6f8064b9de3aaa0f099013170c3c007e41fd266f`
- Bootstrap-status merge commit: `f96710c44b249976cac66cafd4ca8d60f3f6d598`
- Pre-deployment hardening merge commit: `c4c998bb10289c91dc47013a0069adc0961b461f`
- Current documentation branch: `agent/record-partial-control-plane-apply`
- Pull request #2 was squash-merged into `main`.
- Pull request #3 was squash-merged into `main`.
- PR #1 was closed as superseded.
- Remote-state bootstrap was applied on 2026-07-14 after explicit approval.
- GitHub OIDC bootstrap was applied on 2026-07-14 after explicit approval.
- GitHub planning configuration was completed after PR #3: `terraform-plan` and `terraform-apply` environments exist, repository variables are configured, and the plan workflow succeeded through OIDC.
- GitHub plan role read-only policy update was applied on 2026-07-14 after explicit approval.
- Hardened control-plane apply was attempted on 2026-07-14 after explicit approval and stopped on AWS `PendingVerification` during EC2 launch.
- CloudTrail, Session Manager logging, VPC/network, security group, Scheduler group, Scheduler role, and Scheduler DLQ resources exist.
- No control-plane EC2 host, EBS root volume, Scheduler start/stop schedules, product runtime resources, apply workflow, or apply-role infrastructure permissions have been created.

## Product Context

- Product repository: `/Users/joemccann/code/AI.FO-Demo`
- Product baseline branch: `master`
- Observed baseline commit: `8df211e02f274d0a812771327c69b6d5b6c040d2`
- Current product is a working financial intelligence platform with deterministic financial engine, QBO ingestion, CSV ingestion, PostgreSQL, R2, AI narrative generation, and verifier support.

## Infrastructure Baseline

- Terraform remote state bootstrap root exists and has been applied with local bootstrap state.
- GitHub OIDC bootstrap root exists and has been applied with local bootstrap state.
- Control-plane environment exists.
- Initial network is one public subnet in one Availability Zone.
- Initial host has public IPv4, zero inbound rules, SSM-only administration, IMDSv2, 100 GiB encrypted gp3 root volume, and controlled HTTPS/DNS egress.
- Multi-Region CloudTrail management-events baseline exists with a dedicated encrypted S3 log bucket and 365-day lifecycle expiration.
- Session Manager logging exists with an encrypted CloudWatch Logs log group, 30-day retention, a customer-managed KMS key, and the `SSM-SessionManagerRunShell` preferences document.
- EventBridge Scheduler group, role, and DLQ exist. Start/stop schedules do not exist yet because EC2 creation failed before an instance ID was available.
- Product runtime infrastructure is not yet provisioned.

## Bootstrap Resources Created

Remote state:

- S3 bucket: `aifo-terraform-state-350480401760-us-west-2`
- Public access block for the state bucket.
- Bucket ownership controls with `BucketOwnerEnforced`.
- Bucket versioning enabled.
- Bucket server-side encryption with `AES256`.
- Bucket policy denying insecure transport.

GitHub OIDC:

- OIDC provider: `arn:aws:iam::350480401760:oidc-provider/token.actions.githubusercontent.com`
- Plan role: `arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Plan`
- Apply role: `arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Apply`
- State access policy: `arn:aws:iam::350480401760:policy/AIFO-GitHubActions-Terraform-StateAccess`
- Plan read policy: `arn:aws:iam::350480401760:policy/AIFO-GitHubActions-Terraform-PlanReadAccess`
- Role attachments for plan state access, plan read access, and apply state access.
- Plan read policy default version `v2` includes the approved read-only refresh permissions for the hardened control-plane resources.

Partial hardened control-plane resources:

- CloudTrail: `arn:aws:cloudtrail:us-west-2:350480401760:trail/aifo-control-plane-management-events`
- CloudTrail bucket: `aifo-control-plane-cloudtrail-350480401760-us-west-2`
- VPC: `vpc-0f73b1daaa9fc17ab`
- Public subnet: `subnet-03ce35314c75b8e1f`
- Security group: `sg-0190e01bae800bb1a`
- S3 gateway endpoint: `vpce-058114f11531d5fdd`
- Session Manager log group: `/aifo/control-plane/session-manager`
- Session Manager KMS key: `arn:aws:kms:us-west-2:350480401760:key/e36ac1c5-105c-42c1-92f9-06fcf02cb772`
- Scheduler DLQ: `https://sqs.us-west-2.amazonaws.com/350480401760/aifo-control-plane-scheduler-dlq`

## Bootstrap Verification

- Remote-state apply result: `6 added, 0 changed, 0 destroyed`.
- GitHub OIDC apply result: `8 added, 0 changed, 0 destroyed`.
- Remote-state post-apply plan exit code: `0`, no drift.
- GitHub OIDC post-apply plan exit code: `0`, no drift.
- State bucket versioning, public-access block, encryption, ownership controls, non-public policy status, and TLS-only bucket policy were verified.
- Plan role trust subject verified: `repo:josephmccann/AIFO-Control-Plane:environment:terraform-plan`.
- Apply role trust subject verified: `repo:josephmccann/AIFO-Control-Plane:environment:terraform-apply`.
- OIDC audience verified: `sts.amazonaws.com`.
- Apply role verified with only `AIFO-GitHubActions-Terraform-StateAccess` attached and no inline policies.

## Current Warnings

- `terraform-plan` GitHub environment exists but has no protection rules.
- `terraform-apply` GitHub environment exists, but GitHub required reviewers are unavailable on the current repository plan.
- `terraform-apply` must remain unused and no apply workflow may be created.
- Repository variables for planning are configured.
- AWS returned `PendingVerification` for EC2 `RunInstances` in `us-west-2`; no EC2 instance exists.
- Terraform post-failure plan shows `4 to add, 0 to change, 0 to destroy`.
- Remaining resources are the EC2 instance, Scheduler inline policy, start schedule, and stop schedule.
- No SSM managed node exists and no Session Manager connection test was possible.
- CloudTrail logging is enabled, but latest delivery success is not yet populated immediately after trail creation.
- Bootstrap Terraform state files were generated locally under ignored paths and must not be committed.
- Always-on `m7i-flex.2xlarge` operation exceeds the $250 budget; scheduled operation is required unless a budget exception is approved.

## Current Branch Changes

- Deployment record updated for the partial hardened control-plane apply.
- No further AWS mutation should occur until AWS regional account validation clears and a renewed approval gate is granted.
