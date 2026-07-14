# Infrastructure Roadmap Memory

## Now

- Review pre-deployment hardening PR.
- Confirm the revised GitHub Actions plan includes CloudTrail, Session Manager logging, EventBridge Scheduler, a 100 GiB root volume, and no destroys.
- Keep control-plane apply blocked pending separate approval.

## Next

- Review cost, no ingress, SSM-only access, IMDSv2, CloudTrail logging, Session Manager logging, Scheduler controls, and 100 GiB storage in the plan.
- Accept or revise the default 08:00-16:00 Monday-Friday operating schedule.
- Prepare first control-plane apply approval packet.
- Perform first apply only from an authenticated IAM Identity Center session if approved.

## Later

- Add patch management.
- Review whether to add CloudTrail data events after product runtime storage exists.
- Review whether to add S3 Session Manager log duplication after a compliance requirement exists.
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
