# Deployment Readiness Review

Status: Bootstrap complete. Partial control-plane prerequisites deployed. Control-plane host deployment is blocked by AWS account regional validation.

This checklist tracks bootstrap completion and the remaining gates before the first control-plane host deployment. It is not approval to deploy the host or product runtime.

Merged operating-model PR: https://github.com/josephmccann/AIFO-Control-Plane/pull/2
Bootstrap status PR: https://github.com/josephmccann/AIFO-Control-Plane/pull/3
Last successful GitHub plan run before this PR: https://github.com/josephmccann/AIFO-Control-Plane/actions/runs/29371131579
Pre-deployment hardening PR: https://github.com/josephmccann/AIFO-Control-Plane/pull/5

## Completed Preparation

- [x] Product runtime inventory created.
- [x] Control-plane fit assessment created.
- [x] Founder principle traceability matrix created.
- [x] Assumption register created.
- [x] Execution plan created.
- [x] PR #1 handoffs reconciled.
- [x] ADR framework created.
- [x] Bootstrap runbook created.
- [x] Cost model created.
- [x] Session Manager logging design created.
- [x] CloudTrail management-events baseline designed and implemented in Terraform.
- [x] Session Manager logging implemented in Terraform.
- [x] EventBridge Scheduler start/stop automation implemented in Terraform.
- [x] Offline Terraform validation passed.
- [x] GitHub plan workflow configured.
- [x] PR #2 squash-merged to `main`.
- [x] PR #1 closed as superseded.
- [x] GitHub repository variables configured for planning.
- [x] `terraform-plan` environment exists with no protection rules for automated planning.
- [x] `terraform-apply` environment exists, but required reviewers are unavailable on the current GitHub plan.
- [x] First GitHub Actions plan succeeded through OIDC.

## Completed Bootstrap

- [x] AWS account ID confirmed: `350480401760`.
- [x] IAM Identity Center profile `aifo-admin` used for approved bootstrap.
- [x] Remote-state bucket created: `aifo-terraform-state-350480401760-us-west-2`.
- [x] Remote-state apply result: `6 added, 0 changed, 0 destroyed`.
- [x] Remote-state post-apply plan result: no drift.
- [x] GitHub OIDC provider created: `arn:aws:iam::350480401760:oidc-provider/token.actions.githubusercontent.com`.
- [x] Plan role created: `arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Plan`.
- [x] Apply role created: `arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Apply`.
- [x] State access policy created: `arn:aws:iam::350480401760:policy/AIFO-GitHubActions-Terraform-StateAccess`.
- [x] Plan read policy created: `arn:aws:iam::350480401760:policy/AIFO-GitHubActions-Terraform-PlanReadAccess`.
- [x] GitHub OIDC apply result: `8 added, 0 changed, 0 destroyed`.
- [x] GitHub OIDC post-apply plan result: no drift.
- [x] Plan trust subject verified: `repo:josephmccann/AIFO-Control-Plane:environment:terraform-plan`.
- [x] Apply trust subject verified: `repo:josephmccann/AIFO-Control-Plane:environment:terraform-apply`.
- [x] OIDC audience verified: `sts.amazonaws.com`.
- [x] Apply role verified with only Terraform state access and no inline policies.
- [x] GitHub OIDC plan-role read-policy update applied on 2026-07-14.
- [x] Plan-role read-only verification passed.

## Partial Control-Plane Apply

- [x] Refreshed plan matched approval: `33 to add, 0 to change, 0 to destroy`.
- [x] CloudTrail management-events trail created and logging enabled.
- [x] Dedicated CloudTrail S3 log bucket created with public access blocked, versioning, encryption, lifecycle, and TLS-only policy.
- [x] VPC, public subnet, internet gateway, route table, S3 gateway endpoint, and no-ingress security group created.
- [x] Session Manager CloudWatch log group, KMS key, and preferences document created.
- [x] Scheduler group, Scheduler role, and Scheduler DLQ created.
- [ ] EC2 host created.
- [ ] Scheduler inline policy created.
- [ ] Scheduler start schedule created.
- [ ] Scheduler stop schedule created.

Apply stopped when EC2 `RunInstances` returned AWS `PendingVerification` for `us-west-2`. Post-failure plan: `4 to add, 0 to change, 0 to destroy`.

## Not Deployed

- [ ] Control-plane EC2 host.
- [x] Control-plane VPC/network environment.
- [ ] Product runtime infrastructure.
- [x] CloudTrail Terraform resources.
- [x] Session Manager logging Terraform resources.
- [ ] EventBridge Scheduler start/stop schedules.
- [ ] Apply workflow.

## Required Before Resumed Control-Plane Plan

- [x] Remote state exists.
- [x] OIDC plan role exists.
- [x] GitHub repository variables set.
- [x] `terraform-plan` environment exists; no manual approval required for automated planning.
- [x] Read-only CloudTrail inspection completed; no trails were returned in `us-west-2`.
- [x] `manage_budget = false` confirmed unless importing budget.
- [x] No product runtime resources included.
- [x] Bootstrap plan role read-policy update applied; read-only verification passed and apply role was not modified.

## Required Before Resumed Apply

- [x] Confirm no apply workflow exists.
- [x] Confirm `terraform-apply` remains unused because GitHub required reviewers are unavailable on the current repository plan.
- [x] Apply role remains state-access-only.
- [x] Original Terraform plan artifact reviewed.
- [x] Rollback runbook current.
- [x] Emergency access runbook current.
- [x] EC2 start/stop runbook reviewed.
- [x] Default host instance schedule accepted: 08:00-16:00 Monday-Friday in `America/Los_Angeles`.
- [x] Session Manager logging Terraform included.
- [x] CloudTrail management-events Terraform included.
- [x] Scheduler DLQ created.
- [x] Initial cost impact accepted for the approved change window.
- [x] Explicit human approval recorded for the attempted apply.
- [ ] AWS account regional validation cleared for EC2 launch.
- [ ] Residual Terraform plan reviewed and confirmed to contain only the EC2 instance, Scheduler inline policy, and Scheduler start/stop schedules.
- [ ] Renewed explicit human approval recorded before any resumed apply.

## Current Blockers

- GitHub required environment reviewers are unavailable on the current repository plan.
- `terraform-apply` exists but cannot enforce reviewer protection and must remain unused.
- Apply role has no infrastructure mutation permissions by design; future permissions require review.
- Apply workflow intentionally absent.
- Control-plane apply must use an authenticated IAM Identity Center session after an explicit approval packet is reviewed.
- AWS `PendingVerification` currently blocks EC2 launch in `us-west-2`; do not retry apply until validation clears and a renewed approval gate is granted.
