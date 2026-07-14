# Control Plane Workstream

## Objective

Build a secure, reproducible AWS control plane for AI.FO infrastructure operations.

## Current Scope

- Terraform bootstrap roots.
- Terraform control-plane environment.
- GitHub OIDC plan/apply boundary.
- SSM-only EC2 operator host.
- Remote state and lockfile design.

## Out Of Scope For Now

- Product runtime hosting.
- Customer data processing.
- Production database.
- Secrets rotation implementation.

## Next Work

- Validate branch changes.
- Prepare first bootstrap PR.
- Execute bootstrap only after approval.
- Run first plan after OIDC and state are available.
