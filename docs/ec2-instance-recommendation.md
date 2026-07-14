# EC2 Instance Recommendation

Date: 2026-07-14

## Recommendation

Use `m7i-flex.2xlarge` as the default x86 8 vCPU / 32 GiB candidate for the initial control-plane host, but approve it only for scheduled operation under the current $250 monthly AWS budget.

The practical recommendation before first apply is:

1. keep `m7i-flex.2xlarge` as the Terraform default candidate;
2. run it on an approved schedule, preferably 8 hours per weekday for the first deployment;
3. validate regional capacity immediately before deployment;
4. revisit Arm-based `m8g.2xlarge` only after toolchain compatibility is tested.

## Current AWS Price Data

Official AWS Price List data for Amazon EC2 On-Demand Linux in `us-west-2` was reviewed on 2026-07-14.

| Instance | vCPU | Memory | Processor | Hourly | 730-hour compute estimate |
| --- | ---: | ---: | --- | ---: | ---: |
| `m7i-flex.2xlarge` | 8 | 32 GiB | Intel Sapphire Rapids | $0.38304 | $279.62 |
| `m7i.2xlarge` | 8 | 32 GiB | Intel Sapphire Rapids | $0.40320 | $294.34 |
| `m7a.2xlarge` | 8 | 32 GiB | AMD EPYC 9R14 | $0.46368 | $338.49 |
| `m8g.2xlarge` | 8 | 32 GiB | AWS Graviton4 | $0.35904 | $262.10 |

Additional recurring costs include EBS, public IPv4, data transfer, and any monitoring/logging additions. With a 100 GiB gp3 root volume and public IPv4, the current modeled totals are $76.30/month for 8 hours per weekday, $149.64/month for 12 hours per day, and $291.27/month always on.

## Interpretation

Among the requested x86 candidates, `m7i-flex.2xlarge` is the least expensive current On-Demand option and matches the target 8 vCPU / 32 GiB profile.

`m7i.2xlarge` may be preferable if sustained CPU or higher EBS/network ceilings are required.

`m7a.2xlarge` is not recommended initially because it is currently more expensive than both requested Intel candidates.

`m8g.2xlarge` is cheaper than the x86 candidates but uses Arm. It should not become the default until Node, pnpm, native dependencies, Docker images, Terraform tooling, browser automation, and any AI/agent tooling are validated on Arm.

## Budget Finding

An always-on `m7i-flex.2xlarge` exceeds the $250 monthly budget after EBS and public IPv4 are counted, before data transfer, logs, snapshots, and taxes. The current budget and host target are therefore in tension.

Options:

- approve an operating schedule;
- approve the higher monthly spend;
- start with a smaller instance;
- test `m8g.2xlarge` compatibility;
- use Savings Plans or Reserved Instances only after usage is stable.

## Sources

- AWS Price List API offer file: https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/us-west-2/index.json
- AWS M7i and M7i-flex: https://aws.amazon.com/ec2/instance-types/m7i/
- AWS M7a: https://aws.amazon.com/ec2/instance-types/m7a/
- EC2 general purpose specs: https://docs.aws.amazon.com/ec2/latest/instancetypes/gp.html
- EC2 On-Demand pricing: https://aws.amazon.com/ec2/pricing/on-demand/
- EBS pricing: https://aws.amazon.com/ebs/pricing/
- VPC public IPv4 pricing: https://aws.amazon.com/vpc/pricing/
