# Proposed EC2 Start/Stop Scheduler Design

Status: proposed only. Do not deploy this design until it has an approved Terraform plan and apply packet.

## Current Requirement

The initial `m7i-flex.2xlarge` control-plane host is approved only for scheduled operation under the current $250 monthly budget. Manual start/stop is acceptable for first deployment; automation is the next cost-control improvement once the host exists and the operating schedule is confirmed.

## Proposed Design

Use Amazon EventBridge Scheduler with universal targets to call EC2 `StartInstances` and `StopInstances` directly. This avoids a Lambda function and keeps the automation small.

Resources to add in a future Terraform change:

- IAM role assumed by `scheduler.amazonaws.com`.
- IAM policy permitting only `ec2:StartInstances` and `ec2:StopInstances` on the single control-plane instance ARN.
- Optional condition limiting actions to instances tagged `Name=aifo-control-plane-host` and `Environment=control-plane`.
- Schedule group, if useful for naming and future cleanup.
- Start schedule.
- Stop schedule.
- Optional dead-letter queue only if missed invocations become operationally material.

Recommended first schedule:

- Start: `cron(0 9 ? * MON-FRI *)`
- Stop: `cron(0 17 ? * MON-FRI *)`
- Time zone: `America/Los_Angeles`
- Flexible time window: off for predictable operator access, or 5 minutes if operational tolerance permits.

Alternative extended schedule:

- Start: `cron(0 8 * * ? *)`
- Stop: `cron(0 20 * * ? *)`
- Time zone: `America/Los_Angeles`

## Security Controls

- Scheduler execution role must not have `ec2:TerminateInstances`, IAM mutation, SSM session, or Terraform state permissions.
- Scope start/stop to the known instance ARN after the host exists.
- Keep human IAM Identity Center start/stop path as fallback.
- Do not attach this permission to the GitHub apply role.

## Cost Effects

The scheduling resources are expected to have negligible direct cost at this scale compared with EC2 compute. The material cost effect is reduced running hours:

- 8 hours per weekday: estimated $76.30/month.
- 12 hours per day: estimated $149.64/month.
- Always on: estimated $291.27/month and not approved under the current budget.

## Failure Modes

- Start fails and the host remains offline: operator starts manually through IAM Identity Center.
- Stop fails and cost continues: budget alert should prompt manual stop.
- Stop interrupts work: use a schedule only after operator working hours and long-running jobs are understood.
- Public IPv4 changes after restart: use SSM Session Manager rather than address-based access.

## Implementation Gate

Before implementation:

1. Deploy the host through an approved control-plane apply.
2. Confirm the selected schedule.
3. Create a narrow Terraform PR for Scheduler/IAM resources.
4. Review the plan for exactly the expected Scheduler and IAM additions.
5. Apply only after explicit approval.

## References

- EventBridge Scheduler universal targets: https://docs.aws.amazon.com/scheduler/latest/UserGuide/managing-targets-universal.html
- EventBridge Scheduler schedules: https://docs.aws.amazon.com/scheduler/latest/UserGuide/managing-schedule.html
- EC2 `StartInstances`: https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_StartInstances.html
- EC2 `StopInstances`: https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_StopInstances.html
