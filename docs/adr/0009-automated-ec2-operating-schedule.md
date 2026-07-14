# ADR-0009: Automate The Control-Plane Host Operating Schedule With EventBridge Scheduler

## Status

Accepted for first control-plane deployment

## Current Product Requirement Supported

The default 8 vCPU / 32 GiB host exceeds the current $250 monthly budget if run continuously. The first deployment needs cost control that does not depend only on memory or manual discipline.

## Founder Principle Or Constitutional Principle Implicated

Principles 1, 14, 20, and 23: trustworthy operation, transparent limits, best-in-class discipline, and building for decisions rather than activity.

## Known Facts

- Current cost model estimates `m7i-flex.2xlarge` at $76.30/month for 8 hours per weekday and $291.27/month always on before logs, data transfer, snapshots, and taxes.
- EventBridge Scheduler supports schedule time zones, universal AWS SDK targets, retry policy, and dead-letter queues.
- EC2 stop/start actions can target a specific instance ARN.
- Manual stop/start remains available through IAM Identity Center.

## Assumptions

- 08:00-16:00 Monday-Friday America/Los_Angeles is the first approved operating window. Confidence: medium.
- A direct EventBridge Scheduler target is simpler than Lambda or Instance Scheduler for one host. Confidence: high.
- The instance should be created running for first deployment verification, not immediately stopped by Terraform-managed state. Confidence: medium.

## Unknowns

- Actual operator working hours after first use.
- Whether weekend or evening emergency work will be common.
- Whether a later product runtime requires always-on infrastructure.

## Information Sources Reviewed

- AWS EventBridge Scheduler universal targets: https://docs.aws.amazon.com/scheduler/latest/UserGuide/managing-targets-universal.html
- AWS EventBridge Scheduler retry and DLQ behavior: https://docs.aws.amazon.com/scheduler/latest/UserGuide/managing-schedule.html
- AWS EventBridge Scheduler DLQ configuration: https://docs.aws.amazon.com/scheduler/latest/UserGuide/configuring-schedule-dlq.html
- AWS EC2 stop/start behavior: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Stop_Start.html
- AWS EventBridge pricing: https://aws.amazon.com/eventbridge/pricing/
- Terraform `aws_scheduler_schedule`: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/scheduler_schedule

## Decision

Create EventBridge Scheduler schedules that start only the Terraform-managed control-plane host at 08:00 Monday-Friday and stop only that host at 16:00 Monday-Friday in `America/Los_Angeles`.

Use a dedicated Scheduler execution role scoped to `ec2:StartInstances` and `ec2:StopInstances` for the single instance ARN. Configure retry policy and an encrypted SQS dead-letter queue for failed schedule deliveries.

Do not create a Lambda scheduler and do not schedule unrelated instances.

## Why This Decision Is Appropriate Now

It keeps cost control close to the EC2 resource, avoids recurring Lambda complexity, and provides auditable start/stop API calls.

## Alternatives Considered

- Manual-only start/stop.
- Terraform-managed stopped state using `aws_ec2_instance_state`.
- Lambda plus EventBridge rule.
- AWS Instance Scheduler solution.
- Always-on host.

## Why Alternatives Were Rejected Or Deferred

- Manual-only control is too easy to forget.
- Terraform-managed stopped state would conflict with a schedule and make routine daytime plans try to stop the host.
- Lambda adds code, IAM, logs, and operational surface for two API calls.
- AWS Instance Scheduler is more complex than required for one host.
- Always-on operation is not approved under the current budget.

## Security Effects

The Scheduler role cannot terminate instances and is scoped to the single host ARN.

## Privacy Effects

No product data is introduced.

## Reliability Effects

Retry and DLQ configuration improves visibility into missed start/stop attempts. Manual start/stop remains the fallback.

## Cost Effects

EventBridge Scheduler usage is expected to fall within the AWS free tier at this scale. SQS DLQ usage is expected to fall within the SQS free tier. The material cost effect is reduced EC2 runtime.

## Operational Burden

Low. Operators must understand that manual starts are temporary and the next scheduled stop still applies.

## Solo-Founder Recoverability

Manual override commands are documented. Failed schedule deliveries are retained in the DLQ.

## Product Impact

No product runtime impact.

## Data-Lineage Impact

Start/stop API calls are visible in CloudTrail after the audit baseline is deployed.

## Auditability Impact

Improves cost-control auditability by recording scheduled API activity and failed deliveries.

## Reversibility

Schedules can be disabled or changed through Terraform variables.

## Rollback Or Migration Path

Disable schedules, stop the host manually, or remove Scheduler resources through a reviewed Terraform change. Move to a broader scheduler only if more instances require it.

## Evidence That Would Cause Reconsideration

- The host needs different operating hours.
- Missed starts/stops occur frequently.
- The host becomes product runtime or needs always-on availability.
- A broader resource scheduler becomes justified.
