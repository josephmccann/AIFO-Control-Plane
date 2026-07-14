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
- Restrict each role trust policy to the exact repository and protected GitHub environment.
- Store role ARN and backend identifiers as GitHub repository variables.
- Configure protected GitHub environments:
  - `terraform-plan`
  - `terraform-apply`
- Confirm the apply environment requires manual approval before any apply workflow exists.

This phase must not use long-lived AWS keys. Use IAM Identity Center credentials or an approved break-glass process.

## Phase 2: First Terraform Plan

- Copy `terraform.tfvars.example` to `terraform.tfvars` locally.
- Confirm `manage_budget = false` while the manually created AWS Budget remains unmanaged by Terraform.
- Review EC2 instance type and expected runtime.
- Decide whether continuous 24/7 operation is approved, because current pricing puts the default 8 vCPU / 32 GiB host above the $250 monthly budget before EBS and public IPv4.
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

- Add a protected apply workflow or perform a supervised local apply.
- Require the `terraform-apply` protected GitHub environment.
- Require manual approval.
- Use OIDC or IAM Identity Center credentials only.
- Capture the reviewed plan artifact.
- Verify Session Manager access after apply.

## Phase 5: Private Subnet Migration

Move the host into private subnets when the operational model justifies the additional cost or complexity.

Candidate migration work:

- Add private subnets.
- Add NAT Gateway or equivalent controlled egress.
- Reintroduce selected interface VPC endpoints for SSM and logs if they are cost-justified.
- Remove public IPv4 from the host.
- Keep zero inbound security-group rules.

## Phase 6: Hardening

- Add CloudWatch log retention and Session Manager logging.
- Add AWS Config or Security Hub baseline if required.
- Add patch management for the Ubuntu host.
- Add CI security checks such as Checkov or tfsec.
- Add least-privilege custom IAM policy for the apply role.
- Add cost model and host stop/start strategy if the 8 vCPU / 32 GiB instance remains the target.

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
