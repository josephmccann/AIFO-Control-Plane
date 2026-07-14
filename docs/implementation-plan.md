# Implementation Plan

## Phase 0: Repository Foundation

- Create repository instructions and documentation.
- Scaffold Terraform modules and environment configuration.
- Add GitHub Actions validation and plan workflows.
- Add local bootstrap and validation scripts.
- Validate Terraform syntax without a backend or AWS deployment.

## Phase 1: Account Bootstrap

Manual or separately approved bootstrap work:

- Create the S3 remote state bucket with versioning, encryption, and Block Public Access.
- Use native S3 lockfiles with `use_lockfile = true`.
- Create or verify the GitHub Actions OIDC provider.
- Create separate GitHub Actions Terraform plan and apply roles.
- Restrict each role trust policy to the exact repository and GitHub environment subject.
- Store role ARN and backend identifiers as GitHub repository variables.
- Configure GitHub environments:
  - `terraform-plan`
  - `terraform-apply`
- Confirm whether the apply environment can require manual approval before any apply workflow exists.

This phase must not use long-lived AWS keys. Use IAM Identity Center credentials or an approved break-glass process.

Current status: bootstrap is complete, repository variables are configured, and GitHub planning works. GitHub required reviewers are unavailable on the current repository plan, so `terraform-apply` must remain unused and no apply workflow may be created.

## Phase 2: First Terraform Plan

- Copy `terraform.tfvars.example` to `terraform.tfvars` locally.
- Confirm `manage_budget = false` while the manually created AWS Budget remains unmanaged by Terraform.
- Review EC2 instance type and expected runtime.
- Accept or revise the default 08:00-16:00 Monday-Friday operating schedule, because continuous operation puts the default 8 vCPU / 32 GiB host above the $250 monthly budget after 100 GiB EBS and public IPv4 are counted.
- Verify pricing and regional availability for:
  - `m7i-flex.2xlarge`
  - `m7i.2xlarge`
  - `m7a.2xlarge`
- Run the GitHub Actions plan workflow or a local `terraform plan`.
- Review the plan for:
  - One public subnet by default
  - Public IPv4 on the host
  - No host ingress rules
  - SSM instance role only
  - IMDSv2 required
  - Outbound HTTPS and DNS only
  - No interface VPC endpoints
  - S3 gateway endpoint only
  - 100 GiB encrypted gp3 root volume
  - CloudTrail management events with no data event selectors
  - Dedicated CloudTrail S3 log bucket with lifecycle expiration
  - Session Manager logging to encrypted CloudWatch Logs
  - EventBridge Scheduler start and stop schedules scoped to the single EC2 instance

## Phase 3: Budget Import

This is optional and should happen only if the manually created AWS Budget should move under Terraform management.

- Set `manage_budget = true`.
- Match Terraform budget values to the existing budget.
- Import the budget:

```bash
terraform -chdir=terraform/environments/control-plane import \
  'module.budget[0].aws_budgets_budget.monthly' \
  ACCOUNT_ID:BUDGET_NAME
```

- Review the resulting plan before any future apply.

## Phase 4: First Apply

This repository does not perform this phase yet.

When explicitly approved later:

- Perform a supervised local apply with IAM Identity Center while GitHub required reviewers are unavailable.
- Keep the `terraform-apply` GitHub environment unused.
- Require manual approval.
- Use IAM Identity Center credentials only.
- Capture the reviewed plan artifact.
- Verify Session Manager access after apply.
- Verify CloudTrail delivery and log-file validation configuration after apply.
- Verify Scheduler start/stop targets only the Terraform-managed host.
- Stop the instance manually after verification if the apply occurs outside the approved operating window.

## Phase 5: Private Subnet Migration

Move the host into private subnets when the operational model justifies the additional cost or complexity.

Candidate migration work:

- Add private subnets.
- Add NAT Gateway or equivalent controlled egress.
- Reintroduce selected interface VPC endpoints for SSM and logs if they are cost-justified.
- Remove public IPv4 from the host.
- Keep zero inbound security-group rules.

## Phase 6: Hardening

- Add AWS Config or Security Hub baseline if required.
- Add patch management for the Ubuntu host.
- Add CI security checks such as Checkov or tfsec.
- Add least-privilege custom IAM policy for the apply role.
- Review CloudTrail data events only after product runtime AWS data stores exist.

## Phase 7: Operations

- Define backup and restore expectations for state.
- Add runbooks for Session Manager access and incident response.
- Add cost review cadence.
- Add change management expectations for future infrastructure expansion.

## Phase 8: Product Runtime Migration Design

This phase must be product-gated and separately approved.

- Decide PostgreSQL hosting and backup/restore.
- Decide whether R2 remains product upload storage.
- Decide secrets manager and rotation path.
- Decide frontend/API runtime platform.
- Preserve deterministic financial-engine authority and AI narrative boundaries.
- Support the product validation commands listed in `docs/product-runtime-inventory.md`.
