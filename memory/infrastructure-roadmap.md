# Infrastructure Roadmap Memory

Session state: ACTIVE — OPERATIONAL REFINEMENT

## Now

- AWS control-plane baseline is operationally complete for the approved current scope.
- EC2 instance `i-0254a9e2fcbcdebd7` is stopped.
- Local Terraform plan and GitHub Terraform Plan are clean.
- Reproducible local `actionlint` and `shellcheck` installation is available through `scripts/install-dev-tools.sh`.

## Next

- Add periodic documentation checks for stale deployment status.
- Add a cost-review cadence and lightweight monthly cost evidence.

## Later

- Evaluate automated Patch Manager or immutable-host replacement when scale or compliance justifies it.
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
