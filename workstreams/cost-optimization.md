# Cost Optimization Workstream

## Objective

Keep the control plane within the $250 monthly AWS budget unless a human explicitly approves an exception.

## Current Findings

- Always-on `m7i-flex.2xlarge` compute alone is estimated at $279.62/month in us-west-2 from current AWS Price List data.
- Public IPv4 and EBS add additional cost.
- Scheduled operation can keep the 8 vCPU / 32 GiB host under budget if operationally acceptable.
- NAT Gateway is intentionally avoided.
- Interface VPC endpoints are deferred.
- Example root volume is 100 GiB gp3.
- Current deployed cost baseline includes one Session Manager KMS key, CloudWatch Logs retention, CloudTrail S3 log storage, and an SQS DLQ. No EC2 instance or public IPv4 cost is currently active.
- Current model: `docs/cost-model.md`.

## Gaps

- Stop/start schedules are not deployed because the EC2 instance was not created.
- No cost dashboard or cost report in repo.
- Manual budget is not imported into Terraform.

## Next Work

- Keep EC2 launch blocked until AWS validation clears and renewed approval is granted.
- Document budget import only if requested.
