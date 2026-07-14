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
- Current branch adds a low-cost audit baseline: one Session Manager KMS key, CloudWatch Logs retention, CloudTrail S3 log storage, and two EventBridge schedules with an SQS DLQ.
- Current model: `docs/cost-model.md`.

## Gaps

- Stop/start schedule is proposed but not deployed.
- No cost dashboard or cost report in repo.
- Manual budget is not imported into Terraform.

## Next Work

- Accept or revise the default 08:00-16:00 Monday-Friday schedule before first apply.
- Document budget import only if requested.
