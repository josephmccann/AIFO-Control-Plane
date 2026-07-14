# ADR-0005: EC2 Instance Selection

## Status

Accepted

## Current Product Requirement Supported

The initial host target is Ubuntu with approximately 8 vCPU and 32 GiB RAM for control-plane and agent execution. The host is not yet the AI.FO product runtime.

## Founder Principle Or Constitutional Principle Implicated

Principles 14, 20, and 23: do not overclaim, produce best-in-class disciplined work, and optimize for decisions rather than activity.

## Known Facts

- Official AWS Price List data for us-west-2 on 2026-07-14 lists:
  - `m7i-flex.2xlarge`: 8 vCPU, 32 GiB, $0.38304 per hour.
  - `m7i.2xlarge`: 8 vCPU, 32 GiB, $0.40320 per hour.
  - `m7a.2xlarge`: 8 vCPU, 32 GiB, $0.46368 per hour.
  - `m8g.2xlarge`: 8 vCPU, 32 GiB, $0.35904 per hour.
- At 730 hours per month, compute-only estimates are:
  - `m7i-flex.2xlarge`: $279.62.
  - `m7i.2xlarge`: $294.34.
  - `m7a.2xlarge`: $338.49.
  - `m8g.2xlarge`: $262.10.
- Public IPv4 and EBS add additional monthly cost.
- A 100 GiB gp3 root volume is approximately $8.00 per month in us-west-2 based on the AWS EBS gp3 storage rate shown on the AWS pricing page.

## Assumptions

- x86_64 compatibility is preferred until product and agent tooling are validated on Arm. Confidence: medium.
- The host will not run continuously until budget impact is explicitly accepted. Confidence: medium.

## Unknowns

- Regional capacity at the exact time of deployment.
- Sustained CPU utilization and whether `m7i-flex` burst characteristics are acceptable.
- Whether Arm-based `m8g.2xlarge` is compatible with all required tooling.
- Whether a smaller instance or scheduled stop/start policy is acceptable.

## Information Sources Reviewed

- AWS Price List API offer file for Amazon EC2 in us-west-2: https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/us-west-2/index.json
- AWS M7i and M7i-flex instances: https://aws.amazon.com/ec2/instance-types/m7i/
- AWS M7a instances: https://aws.amazon.com/ec2/instance-types/m7a/
- AWS EC2 instance type specifications: https://docs.aws.amazon.com/ec2/latest/instancetypes/gp.html
- AWS EC2 On-Demand pricing: https://aws.amazon.com/ec2/pricing/on-demand/
- AWS EBS pricing: https://aws.amazon.com/ebs/pricing/
- AWS VPC pricing for public IPv4: https://aws.amazon.com/vpc/pricing/

## Decision

Keep `m7i-flex.2xlarge` as the default candidate among the requested x86 8 vCPU / 32 GiB options because it has the lowest current on-demand hourly price of the three requested x86 candidates. Do not treat it as budget-approved for continuous 24/7 operation.

## Why This Decision Is Appropriate Now

It preserves the stated capacity target while making the budget conflict explicit before deployment.

## Alternatives Considered

- `m7i.2xlarge`
- `m7a.2xlarge`
- `m8g.2xlarge`
- Smaller x86 instance
- Scheduled or on-demand host operation

## Why Alternatives Were Rejected Or Deferred

- `m7i.2xlarge` costs more than `m7i-flex.2xlarge`.
- `m7a.2xlarge` costs more than both Intel candidates in the current us-west-2 price data.
- `m8g.2xlarge` is cheaper but requires Arm compatibility validation.
- Smaller instances may not satisfy the current target.
- Scheduling is likely needed but should be designed after operator usage is known.

## Security Effects

No direct security change. Larger hosts increase the value of the instance if compromised, so least privilege and patching remain required.

## Privacy Effects

No customer data should be placed on the host without a future data-handling decision.

## Reliability Effects

`m7i-flex` is a general-purpose instance suitable for variable workloads, but sustained high CPU may justify `m7i` or another family.

## Cost Effects

Always-on `m7i-flex.2xlarge` compute alone exceeds the $250 monthly budget. With public IPv4 and EBS, continuous operation is materially above budget.

## Operational Burden

No additional operational burden now. Future cost control may require stop/start automation or rightsizing.

## Solo-Founder Recoverability

Configurable instance type allows one operator to downsize, resize, or stop the host after review.

## Product Impact

Provides enough capacity for control-plane and agent workflows while not assuming product runtime hosting.

## Data-Lineage Impact

No direct product lineage effect.

## Auditability Impact

The pricing evidence and caveat are captured before deployment.

## Reversibility

The instance type is a Terraform variable and can be changed before apply or through a reviewed replacement/resize later.

## Rollback Or Migration Path

Change `control_plane_instance_type`, review the plan, schedule downtime if replacing a live host, and apply only after approval.

## Evidence That Would Cause Reconsideration

- Actual utilization is low enough to use a smaller instance.
- Arm compatibility is validated, making `m8g.2xlarge` viable.
- Sustained CPU makes `m7i-flex` inappropriate.
- Budget approval increases or a Savings Plan/Reserved Instance strategy is adopted.
