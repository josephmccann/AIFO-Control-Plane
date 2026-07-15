# ADR-0010: Use Approval-Gated Manual Patching For The Single Control-Plane Host

## Status

Accepted for the current single-host control plane

## Context

The deployed Ubuntu control-plane host needs a repeatable security-update procedure. It is one scheduled, SSM-only operator host, not product runtime. Automated patching would add Systems Manager patch-policy or maintenance-window resources, IAM permissions, deployment work, and compliance behavior that the current one-host scope does not yet require.

Ubuntu Server can apply security updates through `unattended-upgrades` and may require a reboot. Automatic reboot is disruptive and is disabled by default. The current cloud-init does not define a repository-owned patch policy.

## Decision

Use a manual monthly patch window on the first Tuesday at 10:00 `America/Los_Angeles`, inside the existing weekday operating schedule. Require an approved change record before package mutation or reboot. Use Session Manager only, capture minimal pre/post evidence, keep automatic reboot disabled, and stop/escalate when recovery requires AWS mutation or expanded access.

Defer Systems Manager Patch Manager automation until scale, compliance, or missed-window evidence justifies the additional architecture.

## Consequences

### Security

- Updates have an explicit cadence, owner, evidence trail, and abort criteria.
- SSM-only administration, zero ingress, CloudTrail, and encrypted Session Manager logging remain unchanged.
- Manual execution creates a risk of missed windows; the work queue and monthly operational review must surface overdue maintenance.

### Reliability

- Reboots are deliberate and verified through EC2 and SSM health checks.
- Package downgrade, root-volume replacement, snapshot recovery, and SSH are excluded from routine patching.
- No automated fleet compliance report exists for the current host.

### Cost

- The target window uses already scheduled runtime and adds no AWS resources or planned recurring cost.
- Snapshots and automated patch-management resources require separate cost and deployment review.

### Operations

- Operators follow [the host patching runbook](../runbooks/host-patching.md).
- Critical updates are evaluated promptly but do not bypass change approval.
- Ubuntu release upgrades and product-runtime updates are separate changes.

## Alternatives Considered

- Systems Manager Patch Manager Quick Setup patch policy.
- Systems Manager Maintenance Window with `AWS-RunPatchBaseline`.
- Unattended upgrades with automatic reboot.
- Replacing the host from a newly patched AMI.
- No defined patch cadence.

## Why Alternatives Are Deferred Or Rejected

- Patch Manager and Maintenance Windows are appropriate automation paths but add resources, IAM, targeting, rollout, and reporting decisions for one host.
- Automatic reboot can interrupt active work and complicate the existing stop schedule.
- Immutable replacement requires image creation, state migration, and recovery design beyond current scope.
- No cadence leaves a known security obligation unmanaged.

## Reversibility

This decision can be replaced by an approved Terraform-managed patch policy or immutable-host design. The manual runbook can remain as an emergency fallback.

## Reconsideration Triggers

- More than one managed EC2 host.
- A formal patch-compliance or evidence SLA.
- Missed manual windows or unacceptable patch latency.
- Product runtime begins using the host (which is not approved).
- An approved immutable-image/replacement strategy.

## Sources

- AWS Systems Manager Patch Manager: https://docs.aws.amazon.com/systems-manager/latest/userguide/patch-manager.html
- AWS Systems Manager Maintenance Windows: https://docs.aws.amazon.com/systems-manager/latest/userguide/maintenance-windows.html
- Ubuntu package management: https://documentation.ubuntu.com/server/how-to/software/package-management/
- Ubuntu automatic updates: https://documentation.ubuntu.com/server/how-to/software/automatic-updates/
