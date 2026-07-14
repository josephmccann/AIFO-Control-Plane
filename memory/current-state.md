# Current State

Date: 2026-07-14

## Repository

- Repository: `josephmccann/AIFO-Control-Plane`
- Baseline commit: `4da93f1b674abf108e8c0e1bcb1d97c7a122baed`
- Operating-model merge commit: `6f8064b9de3aaa0f099013170c3c007e41fd266f`
- Current documentation branch: `docs/bootstrap-execution-status`
- Pull request #2 was squash-merged into `main`.
- PR #1 was closed as superseded.
- Remote-state bootstrap was applied on 2026-07-14 after explicit approval.
- GitHub OIDC bootstrap was applied on 2026-07-14 after explicit approval.
- No control-plane EC2 host, product runtime resources, GitHub repository variables, GitHub environments, or CloudTrail resources were created or modified in the bootstrap execution.

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
- Initial host has public IPv4, zero inbound rules, SSM-only administration, IMDSv2, encrypted root volume, and controlled HTTPS/DNS egress.
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
- `terraform-apply` GitHub environment has not been created.
- GitHub repository variables have not been created.
- CloudTrail was not changed and read-only inspection returned no trails in `us-west-2`.
- Bootstrap Terraform state files were generated locally under ignored paths and must not be committed.

## Current Branch Changes

- Deployment-status documentation updated with sanitized bootstrap execution results.
