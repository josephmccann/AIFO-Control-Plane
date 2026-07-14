# Infrastructure Roadmap Memory

## Now

- Review and merge bootstrap execution status documentation.
- Configure GitHub environments and repository variables after approval.
- Run first GitHub Actions plan after repository variables are configured.
- Keep control-plane apply blocked pending separate approval.

## Next

- Configure GitHub protected environments and variables.
- Run first Terraform plan through GitHub Actions.
- Review cost, no ingress, SSM-only access, and IMDSv2.
- Prepare first control-plane apply approval packet.

## Later

- Add Session Manager logging and CloudWatch retention.
- Add patch management.
- Add cost model and stop/start strategy.
- Design product runtime architecture.
- Design PostgreSQL, secrets, storage, and validation pipeline.
- Evaluate private subnet migration.

## Explicitly Deferred

- EKS.
- Service mesh.
- NAT Gateway.
- Multi-AZ production database.
- Paid observability platform.
- Cross-company analytics infrastructure.
