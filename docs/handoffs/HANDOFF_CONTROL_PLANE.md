# AI.FO Control Plane Handoff

## Purpose

Canonical starting context for AWS infrastructure, Terraform, GitHub Actions, SSM access, security boundaries, and control-plane operations.

## Stable Context

- Repository: `josephmccann/AIFO-Control-Plane`
- Product repository: `josephmccann/AI.FO-Demo`
- AWS region: `us-west-2`
- Human access: IAM Identity Center
- Human administrator permission set: `AIFO-Platform-Admin`
- Root MFA: enabled
- Monthly budget target: $250, currently created manually outside Terraform
- GitHub Actions AWS access: OIDC only, no static AWS keys
- EC2 administration: Systems Manager Session Manager only
- Public SSH: not allowed
- Initial host target: Ubuntu, approximately 8 vCPU and 32 GiB RAM

## Current Repository State

Baseline commit:

```text
4da93f1b674abf108e8c0e1bcb1d97c7a122baed
```

Current branch:

```text
docs/product-context-operating-model
```

No infrastructure has been deployed from this repository.

## Current Architecture

The initial control-plane environment defines:

- VPC with DNS support.
- One public subnet in one Availability Zone by default.
- Internet Gateway and outbound default route.
- S3 gateway endpoint.
- Ubuntu EC2 control-plane host.
- Public IPv4 address for outbound egress.
- Zero host ingress rules.
- HTTPS and DNS egress only.
- No SSH key.
- SSM instance role using `AmazonSSMManagedInstanceCore`.
- IMDSv2 required.
- Encrypted gp3 root volume.
- Termination protection enabled by default.
- Optional Terraform-managed AWS Budget, default disabled.

## Bootstrap Architecture

Bootstrap roots are separate:

- `terraform/bootstrap/remote-state/`: S3 state bucket with encryption, versioning, Block Public Access, and native lockfile support.
- `terraform/bootstrap/github-oidc/`: GitHub OIDC provider plus separate plan and apply roles.

The plan role is intended for `terraform-plan`. The apply role is reserved for a future `terraform-apply` protected environment. No apply workflow exists.

## Current Cost Finding

Current AWS Price List data for us-west-2 shows `m7i-flex.2xlarge` compute at $0.38304/hour. At 730 hours/month, compute alone is approximately $279.62 before EBS, public IPv4, and data transfer. Continuous operation exceeds the $250 budget target unless size, schedule, commitment pricing, or budget are changed.

## Product Fit Boundary

The control plane does not currently host AI.FO product runtime. Product hosting is deferred because current product requirements include PostgreSQL, R2 or storage migration, secrets, QBO OAuth, AI provider credentials, domain/TLS, and validation flows that need explicit design.

## Deployment Prerequisites

1. Confirm AWS account ID.
2. Confirm backend bucket name and state key.
3. Review and approve remote-state bootstrap plan.
4. Review and approve GitHub OIDC bootstrap plan.
5. Configure GitHub protected environments:
   - `terraform-plan`
   - `terraform-apply`
6. Configure repository variables:
   - `AWS_TERRAFORM_PLAN_ROLE_ARN`
   - `TF_BACKEND_BUCKET`
   - `TF_BACKEND_KEY`
7. Verify CloudTrail status.
8. Decide host size/schedule against the $250 budget.
9. Run first GitHub Actions plan.
10. Add apply workflow only after the approval boundary is accepted.

## Guardrails

- Do not run `terraform apply` without explicit human approval.
- Do not create AWS resources without explicit human approval.
- Do not use long-lived AWS keys.
- Do not open inbound administrative ports.
- Do not use SSH as an emergency bypass.
- Do not deploy product runtime until a product-hosting ADR is approved.
