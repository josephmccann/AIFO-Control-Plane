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
- Deployed EC2 host `i-0254a9e2fcbcdebd7`, currently stopped.
- Deployed EventBridge Scheduler group, role, DLQ, and enabled start/stop schedules.
- Approval-gated manual host patching procedure.

## Out Of Scope For Now

- Product runtime hosting.
- Customer data processing.
- Production database.
- Secrets rotation implementation.

## Next Work

- Keep Terraform and GitHub plans clean.
- Run approved host maintenance inside the existing schedule.
- Add periodic deployment-status documentation checks.
