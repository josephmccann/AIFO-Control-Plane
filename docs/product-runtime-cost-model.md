# Product Runtime Cost Model

Date: 2026-07-15

Status: Planning estimate, 2026-07-15 public/list pricing; founder approval and current invoices required

All amounts are USD per month, before tax and support plans. This model intentionally uses ranges. It excludes engineering labor, migration labor, customer support labor, and the existing scheduled control-plane host unless stated.

## Workload Assumptions

- Region `us-west-2`, 730 hours/month.
- 10 companies, 20 to 50 users, normal API below 5 rps and bursts below 25 rps.
- Two production API tasks, 0.5 vCPU/1 GiB each; one scheduled/lower-availability staging task.
- RDS PostgreSQL `db.t4g.medium` Multi-AZ production, 50 GiB gp3; smaller single-AZ staging DB.
- 100 GiB customer objects and 50 GiB DB are deliberately conservative beta bounds.
- 20 to 50 GiB/month logs and low CDN/network transfer.
- Two production NAT gateways. Staging uses a tightly controlled public task or scheduled/one-NAT alternative.
- Anthropic workload assumption for range: 3 to 10 million Sonnet 4.6 input tokens and 1 to 4 million output tokens/month. Current list pricing is `$3/MTok` input and `$15/MTok` output in [Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing).
- GMI cost is not estimated as an approved production service because its applicable invoice and processor/model terms are unresolved.

## Pricing Anchors

The AWS Price List API returned these `us-west-2` on-demand rates on 2026-07-15:

| Item | Rate |
| --- | ---: |
| Fargate Linux x86 vCPU | `$0.04048/vCPU-hour` |
| Fargate Linux x86 memory | `$0.004445/GB-hour` |
| Fargate Linux ARM vCPU | `$0.03238/vCPU-hour` |
| Fargate Linux ARM memory | `$0.00356/GB-hour` |
| NAT gateway | `$0.045/hour` plus `$0.045/GB` processed |
| Application Load Balancer | `$0.0225/hour` plus `$0.008/LCU-hour` used |
| RDS PostgreSQL `db.t4g.small` Multi-AZ | `$0.065/hour` |
| RDS PostgreSQL `db.t4g.medium` Multi-AZ | `$0.129/hour` |
| RDS Multi-AZ gp3 | `$0.23/GB-month` |

AWS explains Fargate's requested-vCPU/memory charging in [Fargate pricing](https://aws.amazon.com/fargate/pricing/), ALB hourly/LCU charging in [Elastic Load Balancing pricing](https://aws.amazon.com/elasticloadbalancing/pricing/), and RDS Multi-AZ/storage pricing in [RDS PostgreSQL pricing](https://aws.amazon.com/rds/postgresql/pricing/).

Cloudflare R2 standard storage is currently `$0.015/GB-month`, has a 10 GB monthly free tier, and charges no internet egress, per [R2 pricing](https://developers.cloudflare.com/r2/pricing/). These savings are small at the expected footprint.

## Option A: Harden Current Platform

| Component | Base | Expected beta | Upper bound | Basis/risk |
| --- | ---: | ---: | ---: | --- |
| Replit plan and autoscale deployment | unknown | 50-200 | 350 | Current invoice and compute-unit history required; request-based pricing varies with active CPU/memory |
| Current PostgreSQL | unknown | 25-100 | 200 | Provider/tier/backup/HA are not evidenced in Git |
| R2 storage/operations | 0 | 0-5 | 15 | Small footprint falls near free tier; operations rounded by billing units |
| Logs/monitoring/backup add-ons | 0 | 25-100 | 200 | Safe production likely requires paid capabilities or external services |
| Anthropic | 24 | 24-90 | 180 | Token range; repair/verification retries create variability |
| GMI verifier | unknown | unknown | unknown | Invoice, model price and acceptable production terms required |
| DNS/certificates/security tools | 1 | 5-25 | 75 | Registrar and security service choices unresolved |
| **Modeled total excluding unknown GMI** | **50-100** | **130-520** | **1,020** | Wide range reflects missing invoices and backup/security evidence |

This option appears cheapest only because critical recovery, security and processor costs are unverified. It cannot be approved from the current range.

## Option B: Hybrid

Representative hybrid: AWS API/RDS/secrets, current frontend temporarily retained, R2 retained during transition.

| Component | Expected beta | Upper bound | Notes |
| --- | ---: | ---: | --- |
| Retained platform/frontend | 25-100 | 200 | Current invoice required |
| AWS compute/load balancing/network | 100-180 | 300 | Depends on whether API is fully on AWS and NAT count |
| RDS production/staging | 100-150 | 250 | Multi-AZ production plus staging |
| R2 | 0-5 | 15 | Low direct storage cost |
| Secrets/logs/security/backup | 35-100 | 200 | Split-provider audit/logging can cost more |
| Anthropic/verifier | 25-125 | 250+ | Verifier remains unapproved/unknown |
| Cross-provider transfer/build/DNS | 10-40 | 100 | More paths and duplicate tooling |
| **Modeled total** | **295-700** | **1,315+** | Wide due to split architecture and retained invoices |

Hybrid is not reliably cheaper than the target architecture and creates the most cost-accounting ambiguity.

## Option C: Recommended AWS Architecture

### Production steady state

| Component | Expected | Upper | Assumption |
| --- | ---: | ---: | --- |
| ECS Fargate API | 29 | 65 | Two ARM 0.5-vCPU/1-GiB tasks; upper uses larger/x86 or modest scaling |
| ALB and LCUs | 18-25 | 45 | One ALB, low traffic, no reserved LCU |
| NAT gateways/data | 66-75 | 130 | Two gateways plus modest processing; largest fixed network cost |
| Public IPv4 | 11-15 | 25 | ALB/NAT addresses; exact AWS allocation billing verified at design time |
| RDS PostgreSQL Multi-AZ | 94 | 190 | `db.t4g.medium`; upper allows larger class |
| RDS gp3 | 12 | 30 | 50 GiB Multi-AZ; upper growth |
| DB backup/cross-Region copies | 5-15 | 50 | Free automated-backup allowance and retained/copy growth vary |
| S3 customer/frontend/log storage | 3-10 | 30 | 100 GiB plus requests/versions/logs |
| CloudFront/WAF/data transfer | 10-25 | 75 | Low beta traffic; WAF base/rules dominate |
| Secrets Manager/KMS | 5-10 | 25 | Roughly 10-20 secrets and several keys/API calls |
| CloudWatch logs/metrics/alarms | 15-35 | 90 | Redaction and retention limits are important cost controls |
| ECR/build/artifact storage | 2-8 | 25 | Aggressive old-image lifecycle |
| Route 53/ACM | 1-3 | 10 | ACM public certificate has no direct charge; registrar is separate |
| GuardDuty/security findings | 5-20 | 60 | Usage-sensitive; no Macie baseline |
| **Production subtotal** | **276-394** | **845** | Upper is a stress ceiling, not expected concurrent maximum |

### Staging

| Component | Expected | Upper | Cost control |
| --- | ---: | ---: | --- |
| API/ALB/network | 25-45 | 100 | One task, scheduled when practical, tightly controlled public egress or one NAT |
| Single-AZ RDS/storage/backups | 25-40 | 80 | Small class, no customer data, stop/schedule only if operationally safe |
| Storage/secrets/logs/security | 10-25 | 60 | Shorter retention and synthetic data |
| **Staging subtotal** | **60-110** | **240** | Keep parity of controls, not production availability |

### Third-party services

| Component | Expected | Upper | Notes |
| --- | ---: | ---: | --- |
| Anthropic Sonnet 4.6 | 24-90 | 180 | Example range from token assumptions; provider budget/usage telemetry required |
| Approved verifier | 0-35 | 100 | Must be contract-approved; zero means deterministic-only/fail-closed during beta |
| Intuit | 0 | 0 | API commercial terms/support cost must still be verified |
| Email/status/alert extras | 0-20 | 50 | No provider selected yet |
| **Third-party subtotal** | **24-145** | **330** | Excludes current unknown GMI invoice |

### Recommended budget envelope

- Expected product-runtime beta: **`$400-$550/month`** after staging scheduling and normal low traffic.
- Reasonable operating upper bound: **`$800/month`**. Crossing it requires a founder review before additional recurring commitments.
- Existing scheduled control-plane baseline: approximately `$76/month` before low-volume logs/tax, tracked separately.
- Expected combined AWS/product-provider operating envelope: approximately **`$476-$626/month`**, excluding current platform overlap during migration, support plan, tax and engineering labor.
- Cutover month may temporarily add `$150-$400` because current and new environments overlap and migration/logging usage increases.

## Cost Sensitivities

1. AI output tokens and repeated repair/verification calls can exceed infrastructure cost.
2. NAT gateways are a fixed roughly `$66/month`; unexpected data processing adds `$0.045/GB` before normal transfer charges.
3. CloudWatch high-cardinality custom metrics or verbose logs can grow rapidly.
4. RDS class/storage/backup copies and Extended Support can materially change the baseline.
5. Always-on staging can add `$40-$100/month` over a scheduled posture.
6. S3 versions, access logs and cross-Region copies multiply retained bytes.
7. Current Replit/database costs continue during rehearsal and rollback hold.
8. Security/support subscriptions selected later are outside this estimate.

## Cost Controls And Alerts

- Tag every product resource by `Environment`, `Service`, `Owner`, `DataClass`, and `CostCenter`.
- Separate production-account budget: forecast alert at `$450`, actual alerts at `$500`, `$600`, and `$700`; founder escalation at `$800`.
- Third-party AI soft alert at `$75`, hard operational review at `$150`, and per-request token ceilings.
- Alert on 20% month-over-month growth and AWS Cost Anomaly Detection findings.
- CloudWatch log retention explicit; reject unbounded debug logging and high-cardinality metrics.
- ECR and S3 lifecycle remove superseded artifacts/versions only under approved recovery/retention rules.
- Review NAT bytes, inter-AZ transfer, RDS class/connections/storage, log ingestion and model usage weekly during beta, monthly after stabilization.
- Use on-demand pricing through the validation period. Consider one-year commitments only after three stable months and founder approval.

## Evidence Required Before Cost Approval

1. Current Replit, database, R2, Anthropic and GMI invoices/usage for the last three months, reviewed without committing sensitive invoice data.
2. Measured production-like API memory/CPU, DB size/connections and token use from synthetic staging.
3. AWS Pricing Calculator or Price List API export linked to the final resource plan and date.
4. Exact staging schedule, backup-copy/retention policy, log volume and security-service selection.
5. Founder acceptance of the product-runtime budget as distinct from the existing `$250` control-plane target.
