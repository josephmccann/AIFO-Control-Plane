# EC2 Start/Stop Runbook

This runbook applies only after the control-plane EC2 host has been deployed through an approved Terraform apply. Do not use it to create resources.

## Purpose

The default `m7i-flex.2xlarge` host is cost-approved only for scheduled operation under the current $250 monthly budget. Stopping the host outside the approved work window reduces compute and auto-assigned public IPv4 charges while retaining EBS storage charges.

Terraform defines EventBridge Scheduler automation for the default operating window:

- Start: 08:00 Monday-Friday.
- Stop: 16:00 Monday-Friday.
- Time zone: `America/Los_Angeles`.
- Target: only the Terraform-managed control-plane instance ID.
- Failed invocations: Scheduler retry policy plus SQS dead-letter queue.

## Preconditions

- Control-plane host exists.
- Operator is authenticated with IAM Identity Center profile `aifo-admin`.
- No critical Terraform, package, container, or data movement job is running on the host.
- Any active SSM Session Manager session is closed.
- The instance ID is recorded from Terraform output or discovered by tag.

## Discover The Host

```bash
aws ec2 describe-instances \
  --profile aifo-admin \
  --region us-west-2 \
  --filters \
    Name=tag:Name,Values=aifo-control-plane-host \
    Name=instance-state-name,Values=pending,running,stopping,stopped \
  --query 'Reservations[].Instances[].{InstanceId:InstanceId,State:State.Name,PrivateIp:PrivateIpAddress,PublicIp:PublicIpAddress}' \
  --output table
```

## Start

Use this command as the emergency override to start the instance outside the normal schedule:

```bash
aws ec2 start-instances \
  --profile aifo-admin \
  --region us-west-2 \
  --instance-ids INSTANCE_ID
```

```bash
aws ec2 wait instance-running \
  --profile aifo-admin \
  --region us-west-2 \
  --instance-ids INSTANCE_ID
```

```bash
aws ssm describe-instance-information \
  --profile aifo-admin \
  --region us-west-2 \
  --filters Key=InstanceIds,Values=INSTANCE_ID \
  --query 'InstanceInformationList[].{InstanceId:InstanceId,PingStatus:PingStatus,AgentVersion:AgentVersion,PlatformName:PlatformName}' \
  --output table
```

Use Session Manager after `PingStatus` is `Online`:

```bash
aws ssm start-session \
  --profile aifo-admin \
  --region us-west-2 \
  --target INSTANCE_ID
```

## Stop

Use this command as the emergency override to stop the instance outside the normal schedule.

Before stopping:

```bash
aws ssm start-session \
  --profile aifo-admin \
  --region us-west-2 \
  --target INSTANCE_ID
```

Inside the session, inspect and stop local work gracefully:

```bash
df -h /
docker system df 2>/dev/null || true
git status --short 2>/dev/null || true
```

Exit the SSM session, then stop the instance:

```bash
aws ec2 stop-instances \
  --profile aifo-admin \
  --region us-west-2 \
  --instance-ids INSTANCE_ID
```

```bash
aws ec2 wait instance-stopped \
  --profile aifo-admin \
  --region us-west-2 \
  --instance-ids INSTANCE_ID
```

Do not use forced stop unless the instance is stuck and data-integrity risk has been accepted.

## Manual Override Interaction With The Schedule

Manual starts and stops do not disable EventBridge Scheduler.

- If the host is manually started outside the 08:00-16:00 weekday window, the next scheduled stop still stops it.
- If the host is manually stopped during the weekday operating window, the next scheduled start is the next matching weekday at 08:00.
- If emergency work extends beyond 16:00, expect the scheduled stop to run. Start the instance again manually only if the work remains approved.
- If the schedule must be suspended for incident work, change `ec2_schedule_enabled = false` in Terraform and apply only after explicit approval.
- Because the stop schedule is Monday-Friday, a weekend manual start must be paired with a manual stop when emergency work ends.

## Approved Manual Schedules

| Schedule | Start | Stop | Time zone | Estimated monthly cost |
| --- | --- | --- | --- | ---: |
| 8 hours per weekday | 08:00 Monday-Friday | 16:00 Monday-Friday | America/Los_Angeles | $76.30 |
| 12 hours per day | 08:00 daily | 20:00 daily | America/Los_Angeles | $149.64 |
| Always on | N/A | N/A | N/A | $291.27, not approved under the current budget |

## Initial Deployment State

The host should be created running during the first approved apply so cloud-init and SSM connectivity can be verified immediately. Do not add Terraform-managed permanent stopped state for this host; it conflicts with the operating schedule and would make routine daytime Terraform plans attempt to stop the instance.

To avoid accidental continuous billing:

1. Run the first apply inside the approved weekday operating window when practical.
2. Verify SSM access and Session Manager logging.
3. Confirm EventBridge Scheduler start/stop schedules exist and are enabled.
4. If the apply occurs outside the operating window, stop the instance manually after verification.

## Disk Hygiene

The 100 GiB root volume is sufficient for the initial host only if Docker images, build caches, and model/tooling artifacts are bounded.

Use these checks before requesting a larger volume:

```bash
df -h /
du -h -d 1 /var/lib/docker 2>/dev/null | sort -h || true
docker system df 2>/dev/null || true
```

Prune disposable Docker data only after confirming it is not needed:

```bash
docker system prune
docker builder prune
```

Use `docker system prune -a --volumes` only when container volumes are known to be disposable.

## Recovery

- If the host does not return to SSM `Online`, verify the instance state, IAM instance profile, security-group egress, SSM agent service, and account-level SSM availability.
- If the public IPv4 address changed after restart, use Session Manager instead of relying on the address.
- If disk usage is above 85%, prune disposable caches first. If pressure persists, prepare a reviewed Terraform change to increase `root_volume_size_gb` or add a separate encrypted data volume.

## References

- AWS EC2 stop/start behavior: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/Stop_Start.html
- AWS EC2 `StopInstances`: https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_StopInstances.html
- AWS EC2 `StartInstances`: https://docs.aws.amazon.com/AWSEC2/latest/APIReference/API_StartInstances.html
- Docker pruning: https://docs.docker.com/engine/manage-resources/pruning/
