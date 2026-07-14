# Infrastructure Roadmap Memory

## Now

- Review cost-alignment and deployment-control PR.
- Confirm the revised GitHub Actions plan uses a 100 GiB root volume.
- Keep control-plane apply blocked pending separate approval.

## Next

- Review cost, no ingress, SSM-only access, IMDSv2, and 100 GiB storage in the plan.
- Choose the initial host operating schedule.
- Prepare first control-plane apply approval packet.
- Perform first apply only from an authenticated IAM Identity Center session if approved.

## Later

- Add Session Manager logging and CloudWatch retention.
- Add patch management.
- Add EventBridge Scheduler start/stop automation after the host exists and a schedule is approved.
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
