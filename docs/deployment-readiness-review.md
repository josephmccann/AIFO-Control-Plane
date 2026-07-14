# Deployment Readiness Review

Status: Bootstrap complete. Control-plane host deployment is not ready.

This checklist tracks bootstrap completion and the remaining gates before the first control-plane host deployment. It is not approval to deploy the host or product runtime.

Merged operating-model PR: https://github.com/josephmccann/AIFO-Control-Plane/pull/2
Bootstrap status PR: https://github.com/josephmccann/AIFO-Control-Plane/pull/3

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
- [x] Offline Terraform validation passed.
- [x] GitHub plan workflow configured to skip until backend repository variables exist.
- [x] PR #2 squash-merged to `main`.
- [x] PR #1 closed as superseded.

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

## Not Deployed

- [ ] Control-plane EC2 host.
- [ ] Control-plane VPC/network environment.
- [ ] Product runtime infrastructure.
- [ ] Session Manager logging Terraform resources.
- [ ] Apply workflow.
- [ ] GitHub repository variables.
- [ ] `terraform-apply` GitHub environment.

## Required Before First Control-Plane Plan

- [x] Remote state exists.
- [x] OIDC plan role exists.
- [ ] GitHub repository variables set.
- [ ] `terraform-plan` environment protection rules configured.
- [ ] CloudTrail status accepted or remediated; read-only inspection returned no trails in `us-west-2`.
- [ ] `manage_budget = false` confirmed unless importing budget.
- [ ] No product runtime resources included.

## Required Before First Apply

- [ ] Apply workflow design reviewed.
- [ ] `terraform-apply` environment created and requires approval.
- [ ] Apply role infrastructure permissions reviewed before any future apply workflow.
- [ ] Terraform plan artifact reviewed.
- [ ] Rollback runbook current.
- [ ] Emergency access runbook current.
- [ ] Host instance cost decision made; scheduled operation remains recommended for `m7i-flex.2xlarge`.
- [ ] Decide whether Session Manager logging Terraform should be included before first host apply or immediately after.
- [ ] Cost impact accepted.
- [ ] Explicit human approval recorded.

## Current Blockers

- GitHub repository variables not configured.
- `terraform-plan` protection rules not configured.
- `terraform-apply` environment not created or protected.
- Host cost decision unresolved.
- Apply role has no infrastructure mutation permissions by design; future permissions require review.
- Apply workflow intentionally absent.
- Terraform plan workflow will remain skipped until OIDC/backend repository variables exist.
