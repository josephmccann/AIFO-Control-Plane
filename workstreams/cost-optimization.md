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
- Current model: `docs/cost-model.md`.

## Gaps

- No stop/start schedule.
- No cost dashboard or cost report in repo.
- Manual budget is not imported into Terraform.

## Next Work

- Decide host runtime schedule or smaller instance before first apply.
- Document budget import only if requested.
