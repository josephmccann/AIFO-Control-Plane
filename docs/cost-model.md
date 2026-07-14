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
| KMS customer-managed key | $1.00/key-month | AWS KMS pricing |
| EventBridge Scheduler | 14 million invocations/month free tier, then $1.00/million | AWS EventBridge pricing |
| SQS Standard | 1 million requests/month free tier | AWS SQS pricing |

Sources:

- AWS Price List API: https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/us-west-2/index.json
- AWS VPC pricing: https://aws.amazon.com/vpc/pricing/
- AWS EBS pricing: https://aws.amazon.com/ebs/pricing/
- AWS S3 pricing: https://aws.amazon.com/s3/pricing/
- AWS KMS pricing: https://aws.amazon.com/kms/pricing/
- AWS EventBridge pricing: https://aws.amazon.com/eventbridge/pricing/
- AWS SQS pricing: https://aws.amazon.com/sqs/pricing/

## Baseline Monthly Scenarios

Assumptions:

- 730 hours/month.
- 100 GiB gp3 root volume.
- One auto-assigned public IPv4 while the instance is running.
- Terraform state S3 storage is less than 1 GiB.
- Data transfer, CloudWatch Logs, snapshots, and taxes are excluded.
- Stopped-instance months still retain EBS cost. Auto-assigned public IPv4 cost is modeled only for running hours because EC2 releases the auto-assigned public IPv4 address when an instance is stopped and started.

| Scenario | Monthly running hours | Compute | Public IPv4 | 100 GiB gp3 | Known monthly subtotal | Budget result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `m7i-flex.2xlarge`, 8 hours/weekday | 176 | $67.42 | $0.88 | $8.00 | $76.30 | Under, recommended initial operating posture |
| `m7i-flex.2xlarge`, 12 hours/day | 365 | $139.81 | $1.83 | $8.00 | $149.64 | Under, acceptable if daily availability is needed |
| `m7i-flex.2xlarge`, always on | 730 | $279.62 | $3.65 | $8.00 | $291.27 | Over by $41.27 before data transfer, logs, snapshots, and taxes |
| `m7i.2xlarge`, always on | 730 | $294.34 | $3.65 | $8.00 | $305.99 | Over by $55.99 before other costs |
| `m7a.2xlarge`, always on | 730 | $338.49 | $3.65 | $8.00 | $350.14 | Over by $100.14 before other costs |
| `m8g.2xlarge`, always on | 730 | $262.10 | $3.65 | $8.00 | $273.75 | Over by $23.75 before other costs and Arm validation |
| `m7i-flex.xlarge`, always on | 730 | $139.81 | $3.65 | $8.00 | $151.46 | Under, but below target capacity |

## Pre-Deployment Hardening Costs

The audit and operating-control baseline adds small fixed or usage-based costs:

| Item | Monthly estimate | Notes |
| --- | ---: | --- |
| CloudTrail management events | $0.00 for first management-event copy | S3 storage and requests still apply |
| CloudTrail S3 log storage | Less than $1 expected initially | Depends on API volume; 365-day lifecycle limits growth |
| Session Manager KMS key | $1.00 | One customer-managed key for session data and log group encryption |
| Session Manager CloudWatch Logs | Usage-based, expected less than $1 initially | 30-day retention; operator shell output volume drives cost |
| EventBridge Scheduler | $0.00 expected | Two recurring schedules are far below free tier |
| Scheduler SQS DLQ | $0.00 expected | Only failed invocations create messages; free tier expected |

Expected added monthly cost before heavy session logging is approximately `$1-$3`, dominated by the KMS key and small log storage/ingestion.

## Operating Schedules

| Schedule | Start | Stop | Time zone | Use case | Monthly estimate |
| --- | --- | --- | --- | --- | ---: |
| 8 hours per weekday | 09:00 Monday-Friday | 17:00 Monday-Friday | America/Los_Angeles | Default solo-founder operations window | $76.30 |
| 12 hours per day | 08:00 daily | 20:00 daily | America/Los_Angeles | Extended daily work window | $149.64 |
| Always on | N/A | N/A | N/A | Only after explicit budget exception | $291.27 |

Under the current $250 budget, `m7i-flex.2xlarge` is approved only for scheduled operation. Continuous operation requires a separate budget exception or a different host choice.

## Root Volume Fit

The 100 GiB root volume is the smallest current default that fits the expected initial control-plane workload with margin:

- The Terraform host cloud-init currently enables/validates SSM access and does not preinstall Docker images, local model weights, product databases, or product uploads.
- The local AI.FO-Demo checkout measured 55 MiB on 2026-07-14 without dependency caches.
- 100 GiB gp3 is large enough for Ubuntu, Terraform, AWS CLI, Git, Node/pnpm build caches, a product checkout, and a bounded Docker cache.
- Docker cache must be treated as disposable. Use `docker system df`, `docker system prune`, and `docker builder prune` before increasing storage.

100 GiB is not enough for local foundation-model weights, a persistent PostgreSQL product database, retained accounting uploads, long-lived container registries, or unbounded CI/build caches. If those become in-scope, prefer a separate encrypted data volume or the smallest justified root increase after measuring disk pressure. A 150 GiB gp3 root volume is the first reasonable fallback if Docker/model tooling exceeds the 100 GiB envelope without introducing product data.

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
| KMS key adds fixed monthly cost | Low | Use one key and review need before adding more keys |
| Public IPv4 costs are small but recurring | Low | Remove public IPv4 when private egress is justified |
| EBS snapshots and unattached volumes can accumulate | Medium | Add backup lifecycle policy before snapshots |

## Required Decision Before First Apply

Choose one:

- approve the 8-hours-per-weekday schedule for `m7i-flex.2xlarge`;
- approve the 12-hours-per-day schedule for `m7i-flex.2xlarge`;
- approve continuous operation above the $250 target;
- start smaller with `m7i-flex.xlarge`;
- validate and choose Arm with `m8g.2xlarge`;
- change the budget target.
