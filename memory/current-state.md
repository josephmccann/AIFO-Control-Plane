# Current State

Date: 2026-07-14

## Repository

- Repository: `josephmccann/AIFO-Control-Plane`
- Baseline commit: `4da93f1b674abf108e8c0e1bcb1d97c7a122baed`
- Operating-model merge commit: `6f8064b9de3aaa0f099013170c3c007e41fd266f`
- Bootstrap-status merge commit: `f96710c44b249976cac66cafd4ca8d60f3f6d598`
- Current documentation branch: `agent/predeployment-audit-controls`
- Pull request #2 was squash-merged into `main`.
- Pull request #3 was squash-merged into `main`.
- PR #1 was closed as superseded.
- Remote-state bootstrap was applied on 2026-07-14 after explicit approval.
- GitHub OIDC bootstrap was applied on 2026-07-14 after explicit approval.
- GitHub planning configuration was completed after PR #3: `terraform-plan` and `terraform-apply` environments exist, repository variables are configured, and the plan workflow succeeded through OIDC.
- No control-plane EC2 host, product runtime resources, CloudTrail resources, Session Manager logging resources, EventBridge Scheduler resources, apply workflow, or apply-role infrastructure permissions have been created.

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
- Current branch proposes a multi-Region CloudTrail management-events baseline with a dedicated encrypted S3 log bucket and 365-day lifecycle expiration.
- Current branch proposes Session Manager logging to an encrypted CloudWatch Logs log group with 30-day retention and a customer-managed KMS key.
- Current branch proposes EventBridge Scheduler start/stop automation for the single Terraform-managed host, defaulting to 08:00-16:00 Monday-Friday in `America/Los_Angeles`, with a scheduler DLQ.
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
- CloudTrail was not changed and read-only inspection returned no trails in `us-west-2`.
- Read-only inspection returned no existing `SSM-SessionManagerRunShell` account preference document and no existing `/aifo/control-plane/session-manager` log group.
- Bootstrap Terraform state files were generated locally under ignored paths and must not be committed.
- Always-on `m7i-flex.2xlarge` operation exceeds the $250 budget; scheduled operation is required unless a budget exception is approved.

## Current Branch Changes

- Pre-deployment audit controls proposed for the first host deployment.
- Terraform modules added for CloudTrail, Session Manager logging, and EventBridge Scheduler.
- GitHub plan role read policy expanded in code for the new read-only plan surface; it has not been applied and does not change the apply role.
- Control-plane apply remains blocked pending reviewed plan, cost acceptance, and explicit human approval.
