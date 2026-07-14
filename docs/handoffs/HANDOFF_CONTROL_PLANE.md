# AI.FO Control Plane Handoff

## Purpose

This document is the canonical starting context for work on AWS, infrastructure, agent execution, CI/CD, security, and the AI.FO technical control plane.

## Stable Context

- Company: AI.FO
- Primary infrastructure repository: `josephmccann/AIFO-Control-Plane`
- Primary application repository: `josephmccann/AI.FO-Demo`
- AWS region: `us-west-2`
- Human access: IAM Identity Center
- Human administrator permission set: `AIFO-Platform-Admin`
- AWS root account MFA is enabled and root should be emergency-only.
- GitHub Actions will use OIDC and temporary AWS credentials. No long-lived AWS access keys.
- EC2 administration will use AWS Systems Manager Session Manager. No public SSH.
- Infrastructure is managed through Terraform and GitHub pull requests.
- Initial host target: Ubuntu Linux, approximately 8 vCPU and 32 GB RAM.
- Monthly AWS budget currently configured manually at $250.
- The operating philosophy is reproducibility, least privilege, explicit auditability, and human approval for consequential actions.

## Current Architecture Decision

The first control-plane host will use one public subnet in one Availability Zone with a public IPv4 address, but zero inbound security-group rules. This provides outbound access for package installation, GitHub, containers, and model APIs without incurring a managed NAT Gateway. Administrative access remains SSM-only.

The design currently includes:

- VPC with DNS support
- One public subnet
- Internet gateway and outbound route
- EC2 host with no ingress rules
- Required IMDSv2
- Encrypted gp3 root volume
- S3 gateway endpoint where useful
- IAM instance role using `AmazonSSMManagedInstanceCore`
- CloudWatch monitoring
- Optional Terraform-managed budget, default disabled because a manual budget already exists
- Native S3 Terraform state locking using `use_lockfile`
- Separate GitHub OIDC plan and apply roles
- Protected GitHub environments for future plan/apply workflows

## Repository State

Initial scaffold commit:

`4da93f1b674abf108e8c0e1bcb1d97c7a122baed`

The private repository has been pushed to GitHub.

Primary paths:

- `AGENTS.md`
- `README.md`
- `docs/architecture.md`
- `docs/security-model.md`
- `docs/implementation-plan.md`
- `terraform/bootstrap/remote-state/`
- `terraform/bootstrap/github-oidc/`
- `terraform/environments/control-plane/`
- `terraform/modules/`
- `.github/workflows/terraform-validate.yml`
- `.github/workflows/terraform-plan.yml`
- `scripts/`

## Validation Completed

- Terraform formatting passed.
- Terraform initialization with backend disabled passed.
- Terraform validation passed for all roots.
- Shell syntax validation passed.
- GitHub workflow YAML parsed successfully.
- Credential-pattern scan returned no matches.
- `shellcheck` was not installed and remains an optional validation enhancement.
- No AWS resources have been created by Terraform.
- No `terraform apply` or `terraform destroy` has been run.

## Deployment Prerequisites

1. Confirm AWS account ID.
2. Confirm GitHub owner and exact repository name.
3. Select final backend bucket name and state key.
4. Run the approved remote-state bootstrap using an IAM Identity Center session.
5. Run the approved GitHub OIDC bootstrap.
6. Create protected GitHub environments:
   - `terraform-plan`
   - `terraform-apply`
7. Configure GitHub repository variables:
   - `AWS_TERRAFORM_PLAN_ROLE_ARN`
   - `TF_BACKEND_BUCKET`
   - `TF_BACKEND_KEY`
8. Verify CloudTrail status.
9. Confirm EC2 pricing and availability for:
   - `m7i-flex.2xlarge`
   - `m7i.2xlarge`
   - `m7a.2xlarge`
10. Keep `manage_budget = false` until the existing manual budget is deliberately imported or replaced.
11. Add an approval-gated apply workflow only after role permissions and recovery procedures are reviewed.

## Non-Negotiable Guardrails

- Never use AWS root credentials for routine work.
- Never paste AWS credentials or private keys into chat.
- Never commit secrets, state files, plan binaries, or local credentials.
- Never create long-lived AWS access keys for agents or GitHub Actions.
- Never expose SSH or other inbound administrative ports.
- Never run `terraform apply` or destructive AWS actions without explicit human approval.
- Keep plan and apply roles separate.
- Restrict OIDC trust to the exact repository and protected environment.
- Document architecture and security changes through ADRs.

## Immediate Next Work

- Review the bootstrap code and exact OIDC trust policies.
- Determine account-specific values.
- Create a reviewed bootstrap execution checklist.
- Verify instance pricing before selecting the final type.
- Establish the first deployment PR rather than deploying directly from a local working tree.

## Definition of Done for Phase 1

Phase 1 is complete when the state backend and OIDC roles exist, GitHub plan runs successfully, the protected apply boundary is configured, and the initial EC2 control-plane host can be created reproducibly through an approved Terraform workflow.