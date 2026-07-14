# Control Plane Workstream

## Objective

Build a secure, reproducible AWS control plane for AI.FO infrastructure operations.

## Current Scope

- Terraform bootstrap roots.
- Terraform control-plane environment.
- GitHub OIDC plan/apply boundary.
- SSM-only EC2 operator host.
- Remote state and lockfile design.
- Deployed CloudTrail management-events baseline.
- Deployed Session Manager logging.
- Partially deployed EventBridge Scheduler automation: group, role, and DLQ exist; start/stop schedules wait for the EC2 instance.

## Out Of Scope For Now

- Product runtime hosting.
- Customer data processing.
- Production database.
- Secrets rotation implementation.

## Next Work

- Validate branch changes.
- Record the partial apply.
- Wait for AWS account validation to clear.
- Resume apply only after renewed explicit approval.
