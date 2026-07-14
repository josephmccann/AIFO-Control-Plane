# Changelog

All notable changes to this repository are recorded here.

## Unreleased

- Ignored stopped-state Terraform drift for the EC2 host auto-assigned public IPv4 address to avoid replacing the scheduled SSM-only host after approved stop/start cycles.
- Applied the GitHub OIDC plan-role read-policy update after approval; the apply role remains state-access-only.
- Recorded the partial hardened control-plane apply attempt blocked by AWS `PendingVerification` during EC2 launch.
- Documented the created CloudTrail, Session Manager logging, network, IAM, Scheduler group, and Scheduler DLQ resources, plus remaining unapplied EC2 and Scheduler schedule resources.
- Added Terraform modules for a multi-Region CloudTrail management-events baseline, encrypted Session Manager logging, and EventBridge Scheduler EC2 start/stop automation.
- Added ADR-0008 for the CloudTrail management-events baseline and ADR-0009 for automated EC2 operating schedules.
- Updated runbooks, deployment readiness, memory, roadmap, and handoffs for the hardened first-deployment plan.
- Changed the control-plane default root EBS volume from 200 GiB to 100 GiB.
- Documented 8-hours-per-weekday, 12-hours-per-day, and always-on operating schedules with revised cost estimates.
- Documented that `m7i-flex.2xlarge` is approved only for scheduled operation under the current $250 monthly budget.
- Documented the GitHub required-reviewer limitation and the local IAM Identity Center apply boundary.
- Added EC2 start/stop runbook and proposed EventBridge Scheduler start/stop design.
- Added ADR-0007 for the manual apply boundary while GitHub reviewer protection is unavailable.
- Recorded the approved remote-state and GitHub OIDC bootstrap execution results.
- Documented created bootstrap resources, Terraform outputs, verification results, warnings, and next GitHub setup actions.
- Added product runtime inventory for the existing AI.FO-Demo product.
- Added control-plane fit assessment, principle traceability matrix, assumption register, and execution plan.
- Added repository operating model docs for contribution, security, roadmap, runbooks, memory, workstreams, and workqueue.
- Added ADR framework and initial control-plane decisions.
- Reconciled PR #1 handoff documents against the current product repository, current infrastructure scaffold, and founder principles.
- Documented EC2 instance recommendation and current cost tension against the $250 monthly budget.
- Added initial cost model with always-on, scheduled, and smaller-instance scenarios.
- Narrowed the GitHub Terraform plan role from AWS managed `ReadOnlyAccess` to a custom read policy with explicit extension hook.
- Made EC2 detailed monitoring explicit and disabled by default.
- Reduced example root volume size from 200 GiB to 100 GiB for the initial host.
- Made shell scripts compatible with GitHub `shellcheck`.
- Made the Terraform plan workflow skip until OIDC/backend repository variables are configured.

## 2026-07-14

- Scaffolded initial AWS control-plane repository.
- Added Terraform bootstrap roots for remote state and GitHub OIDC.
- Added control-plane Terraform environment and modules.
- Added local validation script and Terraform validation workflow.
- Pushed private baseline repository.
