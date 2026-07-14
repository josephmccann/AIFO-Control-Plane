# Cost Model

Date: 2026-07-14

Scope: initial control plane in `us-west-2`. This is an estimate for planning, not an AWS bill forecast.

## Budget Constraint

Target monthly budget: $250.

The current 8 vCPU / 32 GiB host target is not compatible with continuous 24/7 On-Demand operation under the $250 budget.

## Pricing Inputs

| Item | Current unit price used | Source |
| --- | ---: | --- |
| `m7i-flex.xlarge` Linux On-Demand | $0.19152/hour | AWS Price List API |
| `m7i-flex.2xlarge` Linux On-Demand | $0.38304/hour | AWS Price List API |
| `m7i.2xlarge` Linux On-Demand | $0.40320/hour | AWS Price List API |
| `m7a.2xlarge` Linux On-Demand | $0.46368/hour | AWS Price List API |
| `m8g.2xlarge` Linux On-Demand | $0.35904/hour | AWS Price List API |
| Public IPv4 | $0.005/hour while assigned | AWS VPC pricing |
| gp3 storage | $0.08/GB-month | AWS EBS pricing |
| S3 Standard storage | $0.0265/GB-month for first 50 TB in us-west-2 | AWS S3 pricing |

Sources:

- AWS Price List API: https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/us-west-2/index.json
- AWS VPC pricing: https://aws.amazon.com/vpc/pricing/
- AWS EBS pricing: https://aws.amazon.com/ebs/pricing/
- AWS S3 pricing: https://aws.amazon.com/s3/pricing/

## Baseline Monthly Scenarios

Assumptions:

- 730 hours/month.
- 100 GiB gp3 root volume.
- One auto-assigned public IPv4 while the instance is running.
- Terraform state S3 storage is less than 1 GiB.
- Data transfer, CloudWatch Logs, snapshots, and taxes are excluded.

| Scenario | Compute | Public IPv4 | EBS | Known monthly subtotal | Budget result |
| --- | ---: | ---: | ---: | ---: | --- |
| `m7i-flex.2xlarge`, always on | $279.62 | $3.65 | $8.00 | $291.27 | Over by $41.27 before other costs |
| `m7i.2xlarge`, always on | $294.34 | $3.65 | $8.00 | $305.99 | Over by $55.99 before other costs |
| `m7a.2xlarge`, always on | $338.49 | $3.65 | $8.00 | $350.14 | Over by $100.14 before other costs |
| `m8g.2xlarge`, always on | $262.10 | $3.65 | $8.00 | $273.75 | Over by $23.75 before other costs and Arm validation |
| `m7i-flex.xlarge`, always on | $139.81 | $3.65 | $8.00 | $151.46 | Under, but below target capacity |
| `m7i-flex.2xlarge`, 12 hours/day | $139.81 | $1.83 | $8.00 | $149.64 | Under, if schedule is acceptable |
| `m7i-flex.2xlarge`, 8 hours/weekday | $67.42 | $0.88 | $8.00 | $76.30 | Under, if operator workflow allows it |

## Interpretation

The requested `m7i-flex.2xlarge` remains the best x86 8 vCPU / 32 GiB candidate by hourly price, but it should not be deployed as an always-on host under the current budget.

The most cost-disciplined initial path is:

1. keep `m7i-flex.2xlarge` as the capacity target;
2. require a stop/start operating model unless continuous operation is explicitly approved;
3. keep the root volume at 100 GiB until actual disk use proves it is insufficient;
4. avoid NAT Gateway and interface endpoints in the initial phase;
5. revisit `m8g.2xlarge` only after Arm compatibility is validated;
6. revisit commitment pricing only after usage is stable.

## Cost Risks

| Risk | Severity | Mitigation |
| --- | --- | --- |
| Continuous 8 vCPU / 32 GiB operation exceeds budget | Critical | Human cost decision before apply |
| Data transfer is excluded | Medium | Review after first plan and before product runtime |
| CloudWatch Logs can grow with session or application logs | Medium | Add retention limits before enabling logs |
| Public IPv4 costs are small but recurring | Low | Remove public IPv4 when private egress is justified |
| EBS snapshots and unattached volumes can accumulate | Medium | Add backup lifecycle policy before snapshots |

## Required Decision Before First Apply

Choose one:

- approve continuous operation above the $250 target;
- approve scheduled operation for `m7i-flex.2xlarge`;
- start smaller with `m7i-flex.xlarge`;
- validate and choose Arm with `m8g.2xlarge`;
- change the budget target.
