# Cost Incident Runbook

## Triggers

- Forecasted AWS spend exceeds the $250 monthly budget.
- Unexpected EC2, NAT, EBS, data transfer, public IPv4, CloudWatch, or other recurring charges appear.
- Any unapproved paid service is created.

## Immediate Actions

1. Do not delete evidence.
2. Identify service, region, resource, and owner tag.
3. Stop non-production EC2 instances if cost is active and stopping is safe.
4. Disable workflows that can create or resize resources.
5. Review recent Git commits and CloudTrail events.
6. Record findings in `memory/known-risks.md` and `CHANGELOG.md`.

## Cost Checks

Review:

- AWS Budgets.
- Cost Explorer.
- EC2 running instances.
- Elastic IP and public IPv4 usage.
- NAT Gateways.
- EBS volumes and snapshots.
- CloudWatch logs and metrics.

## Rollback

Use Terraform to remove or downsize resources after approval. For urgent cost containment, stopping an instance is acceptable if it does not destroy data.
