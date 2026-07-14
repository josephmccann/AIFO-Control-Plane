# Deployment Readiness Review

Status: Not ready for deployment.

This checklist prepares the first AWS bootstrap and control-plane deployment review. It is not approval to deploy.

Review PR: https://github.com/josephmccann/AIFO-Control-Plane/pull/2

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
- [x] GitHub plan workflow configured to skip before OIDC/backend variables exist.

## Required Before Remote-State Bootstrap

- [ ] AWS account ID confirmed.
- [ ] IAM Identity Center session confirmed.
- [ ] Remote-state bucket name chosen.
- [ ] `terraform/bootstrap/remote-state/terraform.tfvars` prepared locally and not committed.
- [ ] `terraform plan` reviewed for remote-state root.
- [ ] Human approval granted for S3 bucket creation.

## Required Before GitHub OIDC Bootstrap

- [ ] GitHub repository confirmed as `josephmccann/AIFO-Control-Plane`.
- [ ] Protected environment names confirmed:
  - `terraform-plan`
  - `terraform-apply`
- [ ] `terraform/bootstrap/github-oidc/terraform.tfvars` prepared locally and not committed.
- [ ] OIDC trust subjects reviewed.
- [ ] Plan role read policy reviewed.
- [ ] Apply role has no broad policies unless approved.
- [ ] Human approval granted for IAM OIDC provider and roles.

## Required Before First Control-Plane Plan

- [ ] Remote state exists.
- [ ] OIDC plan role exists.
- [ ] GitHub repository variables set.
- [ ] CloudTrail status verified.
- [ ] `manage_budget = false` confirmed unless importing budget.
- [ ] Host instance cost decision made.
- [ ] Decide whether Session Manager logging Terraform should be included before first host apply or immediately after.
- [ ] No product runtime resources included.

## Required Before First Apply

- [ ] Apply workflow design reviewed.
- [ ] `terraform-apply` environment requires approval.
- [ ] Apply role permissions reviewed.
- [ ] Terraform plan artifact reviewed.
- [ ] Rollback runbook current.
- [ ] Emergency access runbook current.
- [ ] Cost impact accepted.
- [ ] Explicit human approval recorded.

## Current Blockers

- AWS bootstrap approval not granted.
- GitHub protected environments not configured.
- Host cost decision unresolved.
- Apply workflow intentionally absent.
- PR #2 not reviewed or merged.
- PR #1 supersession decision unresolved.
- Terraform plan workflow will remain skipped until OIDC/backend repository variables exist.
