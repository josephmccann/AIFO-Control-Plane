# Control-Plane Host Patching Runbook

## Purpose

Patch the single Ubuntu control-plane host predictably while preserving SSM-only access, audit logging, the approved weekday schedule, and the product-data boundary.

This runbook is not authorization to start, reboot, patch, snapshot, or recover the host. Each maintenance execution requires an approved change record. Documentation validation does not execute any command in this runbook.

## Current Cadence And Scope

- Target window: first Tuesday of each month at 10:00 `America/Los_Angeles`.
- The window sits inside the existing 08:00-16:00 Monday-Friday schedule and adds no planned runtime.
- Evaluate critical out-of-band security updates within one business day and schedule an approved window as soon as practical.
- Patch Ubuntu packages from repositories already configured on the host.
- Do not perform Ubuntu release upgrades, add repositories, update product runtime, or handle customer data.
- AWS Systems Manager Patch Manager automation is deferred by [ADR-0010](../adr/0010-manual-host-patching.md).

## Approval Boundary

The change record must explicitly authorize:

- package index refresh and package installation;
- a guest reboot if `/var/run/reboot-required` exists;
- the expected maintenance start/end time;
- the operator and evidence location.

Separate explicit approval is required for:

- starting the EC2 instance when it is stopped;
- work outside the approved schedule;
- creating an EBS snapshot;
- replacing or restoring the root volume;
- changing Scheduler, IAM, networking, or Terraform;
- package downgrade, removal, repository changes, or Ubuntu release upgrade.

## Preconditions

- IAM Identity Center profile `aifo-admin` is authenticated to account `350480401760`.
- Instance ID is `i-0254a9e2fcbcdebd7` in `us-west-2`.
- No Terraform apply, container build, package operation, or other maintenance is in progress.
- The approved window ends before the 16:00 scheduled stop.
- The operator understands that Session Manager commands and output are retained for 30 days. Never print environment variables, `.env` files, tokens, credentials, product data, or customer data.

## Phase 1: Read-Only Go/No-Go Checks

Confirm identity and instance state:

```bash
aws sts get-caller-identity \
  --profile aifo-admin \
  --query '{Account:Account,Arn:Arn}' \
  --output json
```

```bash
aws ec2 describe-instances \
  --profile aifo-admin \
  --region us-west-2 \
  --instance-ids i-0254a9e2fcbcdebd7 \
  --query 'Reservations[].Instances[].{State:State.Name,LaunchTime:LaunchTime,PrivateIp:PrivateIpAddress,PublicIp:PublicIpAddress}' \
  --output table
```

If the instance is `stopped`, stop the procedure. Starting it requires explicit approval; use [ec2-start-stop.md](ec2-start-stop.md) only after that approval.

Confirm CloudTrail is logging and the scheduled stop remains enabled:

```bash
aws cloudtrail get-trail-status \
  --profile aifo-admin \
  --region us-west-2 \
  --name aifo-control-plane-management-events \
  --query '{IsLogging:IsLogging,LatestDeliveryTime:LatestDeliveryTime,LatestDeliveryError:LatestDeliveryError}' \
  --output table
```

```bash
aws scheduler get-schedule \
  --profile aifo-admin \
  --region us-west-2 \
  --group-name aifo-control-plane-host \
  --name aifo-control-plane-host-stop \
  --query '{State:State,Expression:ScheduleExpression,Timezone:ScheduleExpressionTimezone,Input:Target.Input}' \
  --output table
```

Confirm SSM is online and no conflicting session is active:

```bash
aws ssm describe-instance-information \
  --profile aifo-admin \
  --region us-west-2 \
  --filters Key=InstanceIds,Values=i-0254a9e2fcbcdebd7 \
  --query 'InstanceInformationList[].{PingStatus:PingStatus,AgentVersion:AgentVersion,PlatformName:PlatformName,PlatformVersion:PlatformVersion}' \
  --output table
```

```bash
aws ssm describe-sessions \
  --profile aifo-admin \
  --region us-west-2 \
  --state Active \
  --filters key=Target,value=i-0254a9e2fcbcdebd7 \
  --query 'Sessions[].{SessionId:SessionId,Owner:Owner,StartDate:StartDate}' \
  --output table
```

Go only when CloudTrail is logging, the stop schedule is enabled, SSM is `Online`, there is no conflicting session, and sufficient time remains before 16:00.

## Phase 2: Logged Pre-Change Evidence

Start the only approved administrative session:

```bash
aws ssm start-session \
  --profile aifo-admin \
  --region us-west-2 \
  --target i-0254a9e2fcbcdebd7
```

Inside the session, collect minimal evidence:

```bash
date -u
cat /etc/os-release
uname -a
df -h /
systemctl --failed --no-pager
systemctl is-active amazon-ssm-agent 2>/dev/null || systemctl is-active snap.amazon-ssm-agent.amazon-ssm-agent
sudo dpkg --audit
sudo apt-get check
if [[ -e /var/lib/dpkg/lock-frontend ]]; then echo "APT lock exists"; else echo "No APT lock"; fi
```

Abort if root usage is at or above 85%, `dpkg --audit` or `apt-get check` reports errors, a package lock exists, SSM Agent is unhealthy, or unrelated failed services need investigation.

Review configured repositories and automatic-update state without printing unrelated configuration:

```bash
grep -RhsE '^[[:space:]]*(deb |URIs:|Suites:|Components:)' /etc/apt/sources.list /etc/apt/sources.list.d 2>/dev/null
systemctl is-enabled unattended-upgrades 2>/dev/null || true
systemctl is-active unattended-upgrades 2>/dev/null || true
```

Do not add or change repositories during this procedure.

## Phase 3: Apply Approved Package Updates

The following commands mutate the host and may run only under the approved change record:

```bash
sudo apt-get update
apt list --upgradable 2>/dev/null
sudo DEBIAN_FRONTEND=noninteractive apt-get -y upgrade
```

Do not use `dist-upgrade`, `full-upgrade`, `do-release-upgrade`, package removal, or repository changes in this routine window.

If APT proposes removing packages, changing release sources, or resolving broken dependencies manually, answer no and abort. Record the exact package names and error without printing secrets.

## Phase 4: Post-Change Verification

Inside the same session:

```bash
sudo dpkg --audit
sudo apt-get check
systemctl --failed --no-pager
df -h /
systemctl is-active amazon-ssm-agent 2>/dev/null || systemctl is-active snap.amazon-ssm-agent.amazon-ssm-agent
if [[ -f /var/run/reboot-required ]]; then cat /var/run/reboot-required.pkgs 2>/dev/null || true; fi
```

If no reboot is required, exit the session and continue to closeout.

If a reboot is required but was not pre-approved, stop and request approval. Do not defer silently or enable automatic reboot.

With explicit reboot approval:

```bash
sudo reboot
```

The session will disconnect. From the local workstation, wait for EC2 and SSM recovery:

```bash
aws ec2 wait instance-status-ok \
  --profile aifo-admin \
  --region us-west-2 \
  --instance-ids i-0254a9e2fcbcdebd7
```

```bash
aws ssm describe-instance-information \
  --profile aifo-admin \
  --region us-west-2 \
  --filters Key=InstanceIds,Values=i-0254a9e2fcbcdebd7 \
  --query 'InstanceInformationList[].{PingStatus:PingStatus,AgentVersion:AgentVersion,LastPingDateTime:LastPingDateTime}' \
  --output table
```

Reconnect through Session Manager and repeat `uname -a`, `sudo dpkg --audit`, `sudo apt-get check`, `systemctl --failed --no-pager`, disk, and SSM Agent checks.

## Abort And Recovery

Abort and escalate when:

- SSM does not return `Online` after reboot;
- package integrity checks fail;
- required services fail;
- disk use reaches 85%;
- the 16:00 scheduled stop is approaching;
- recovery would require a snapshot, root-volume replacement, package downgrade/removal, IAM change, public ingress, SSH, or Scheduler change.

Do not disable the scheduled stop, open SSH, force-stop the instance, or improvise a root-volume recovery. Preserve CloudTrail and Session Manager evidence. Root-volume replacement from a snapshot is possible but is a separate AWS mutation and recovery approval, not a routine patch step.

## Closeout

Record:

- approved change identifier and operator;
- start/end timestamps;
- package names and versions changed;
- whether a reboot occurred;
- pre/post kernel version;
- SSM Agent health, package integrity, failed-service, and disk results;
- any follow-up or deferred package.

After leaving the session, confirm the instance state and stop schedule. Do not manually stop a healthy host inside the normal window unless the change approval calls for it; the existing 16:00 schedule remains authoritative.

## Automation Reconsideration Triggers

Revisit Systems Manager Patch Manager when there is more than one managed host, a formal patch-compliance SLA, evidence that manual windows are missed, or an approved need for centralized compliance reporting. That change requires a new Terraform/IAM/cost review and explicit deployment approval.

## References

- Ubuntu package management: https://documentation.ubuntu.com/server/how-to/software/package-management/
- Ubuntu automatic updates and reboot behavior: https://documentation.ubuntu.com/server/how-to/software/automatic-updates/
- AWS Systems Manager Patch Manager: https://docs.aws.amazon.com/systems-manager/latest/userguide/patch-manager.html
- AWS Systems Manager Maintenance Windows: https://docs.aws.amazon.com/systems-manager/latest/userguide/maintenance-windows.html
- EC2 root-volume replacement: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/replace-root.html
