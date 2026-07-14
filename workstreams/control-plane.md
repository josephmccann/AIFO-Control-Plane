# Control Plane Workstream

## Objective

Build a secure, reproducible AWS control plane for AI.FO infrastructure operations.

## Current Scope

- Terraform bootstrap roots.
- Terraform control-plane environment.
- GitHub OIDC plan/apply boundary.
- SSM-only EC2 operator host.
- Remote state and lockfile design.
- Proposed CloudTrail management-events baseline.
- Proposed Session Manager logging.
- Proposed EventBridge Scheduler start/stop automation.

## Out Of Scope For Now

- Product runtime hosting.
- Customer data processing.
- Production database.
- Secrets rotation implementation.

## Next Work

- Validate branch changes.
- Review the hardened first-deployment plan.
- Prepare first control-plane apply approval packet.
- Execute first control-plane apply only after explicit approval.
