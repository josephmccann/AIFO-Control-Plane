# Infrastructure Roadmap Memory

## Now

- Record the partial hardened control-plane apply.
- Keep control-plane apply blocked while AWS account regional validation prevents EC2 launch.
- Do not run destroy.

## Next

- Wait for AWS account validation to clear or open AWS Support if it persists.
- Re-run a read-only control-plane plan.
- Expected residual plan is the EC2 instance, Scheduler inline policy, and Scheduler start/stop schedules only.
- Resume apply only after renewed explicit approval.

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
