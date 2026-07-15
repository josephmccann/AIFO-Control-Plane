# Infrastructure Roadmap Memory

Session state: PARKED — SAFE FOR CODEX CLI UPDATE

## Now

- AWS control-plane baseline is operationally complete for the approved current scope.
- EC2 instance `i-0254a9e2fcbcdebd7` is stopped.
- Local Terraform plan and GitHub Terraform Plan are clean.
- No new AWS implementation work should begin before the Codex CLI update.

## Next

- Resume with Codex 5.6 using `docs/session-handoffs/HANDOFF_CONTROL_PLANE_2026-07-15.md`.
- Confirm clean repository state, AWS identity, stopped instance state, and clean Terraform plans.
- Then choose one narrow next task:
  - add `actionlint`/`shellcheck` availability to the developer toolchain or CI;
  - create a product-runtime architecture ADR without deploying anything;
  - define host patching and maintenance procedure.

## Later

- Add patch management.
- Review whether to add CloudTrail data events after product runtime storage exists.
- Review whether to add S3 Session Manager log duplication after a compliance requirement exists.
- Design product runtime architecture.
- Design PostgreSQL, secrets, storage, and validation pipeline.
- Evaluate private subnet migration.

## Explicitly Deferred

- Product runtime deployment.
- EKS.
- Service mesh.
- NAT Gateway.
- Multi-AZ production database.
- Paid observability platform.
- Cross-company analytics infrastructure.
