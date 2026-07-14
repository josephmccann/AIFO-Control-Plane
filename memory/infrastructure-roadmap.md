# Infrastructure Roadmap Memory

## Now

- Finish product-gated operating model.
- Validate all Terraform and workflows offline.
- Prepare bootstrap execution steps without running them.
- Open PR for review.

## Next

- Bootstrap remote state after approval.
- Bootstrap GitHub OIDC after approval.
- Configure GitHub protected environments and variables.
- Run first Terraform plan.
- Review cost, no ingress, SSM-only access, and IMDSv2.

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
