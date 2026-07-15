# Manual Host Patching Design

## Goal

Define a repeatable security-patching procedure for the single Ubuntu control-plane host without creating AWS resources, changing the operating schedule, or starting the stopped instance during documentation work.

## Decision

Use a manual monthly patch window inside the existing 08:00-16:00 Monday-Friday `America/Los_Angeles` schedule. The target window is the first Tuesday of each month at 10:00. Critical out-of-band updates are evaluated promptly but still require an approved change window.

AWS Systems Manager Patch Manager automation remains deferred. It would require a patch policy or maintenance-window architecture, additional IAM review, Terraform changes, and deployment approval. The manual procedure is proportionate to one host and preserves the current cost and access boundaries.

## Scope

The procedure covers:

- Ubuntu package index refresh and supported package upgrades;
- SSM Agent health before and after patching;
- disk-capacity, package-manager, service, and reboot checks;
- Session Manager-only access and automatically retained session evidence;
- explicit go/no-go, abort, recovery, and closeout steps.

It excludes:

- Ubuntu release upgrades;
- product runtime or customer-data operations;
- Docker image/application upgrades;
- automatic reboots;
- EBS snapshot creation or root-volume replacement without separate approval;
- AWS resource changes or out-of-window instance starts.

## Approval Boundary

The runbook is documentation only. Executing package changes, rebooting the guest, starting the EC2 instance, creating a snapshot, or replacing a root volume requires an approved maintenance/change record. If the host is stopped when the window begins, the operator stops and obtains explicit start approval rather than treating the runbook as authorization.

## Procedure Shape

1. Verify AWS identity, CloudTrail logging, instance state, SSM status, Scheduler configuration, and absence of conflicting work.
2. Open a logged Session Manager session; never print secrets or customer data.
3. Capture a minimal pre-change record: OS/kernel, disk, failed services, SSM Agent state, pending package configuration, and available upgrades.
4. Apply supported Ubuntu package upgrades from configured repositories only.
5. Verify package-manager integrity, failed services, disk, SSM Agent, and reboot requirement.
6. Reboot only when pre-approved; wait for EC2 and SSM recovery and repeat health checks.
7. Stop and escalate instead of improvising package downgrades or AWS recovery mutations.
8. Record completion and confirm the existing Scheduler remains enabled and unchanged.

## Security And Evidence

- Administration remains SSM-only with no SSH or ingress changes.
- Session commands and output are retained in the encrypted 30-day CloudWatch log group.
- Evidence records package names/versions and health results, not environment variables, tokens, `.env` content, product data, or customer data.
- Automatic reboot stays disabled; disruptive recovery paths require explicit approval.

## Success Criteria

- A new operator can execute the approved window without inventing commands or weakening controls.
- Every mutating step has a clear approval prerequisite.
- Verification covers SSM recovery, package integrity, service health, disk capacity, and reboot state.
- The ADR, security model, roadmap, memory, work queue, and workstreams agree on the manual current posture and deferred automation trigger.
