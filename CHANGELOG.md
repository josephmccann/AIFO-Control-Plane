# Changelog

All notable changes to this repository are recorded here.

## Unreleased

- Added a pinned, checksum-verified local installer for `actionlint` v1.7.12 and ShellCheck v0.11.0 across supported macOS/Linux architectures.
- Extended standard validation to lint repository shell scripts, installer tests, and GitHub Actions workflows when the pinned tools are on `PATH`.
- Grouped Terraform Plan step outputs into a single redirect to satisfy the newly enforced workflow shell lint without changing plan-gate behavior.
- Advanced canonical repository state from the pre-update parked checkpoint to active operational refinement; retained the dated session handoff as historical evidence.
- Checkpointed the operationally complete current-scope AWS control-plane baseline before Codex CLI update.
- Added dated session handoff at `docs/session-handoffs/HANDOFF_CONTROL_PLANE_2026-07-15.md`.
- Updated canonical state, readiness, roadmap, security, and workqueue documents to record `PARKED — SAFE FOR CODEX CLI UPDATE`.
- Completed GitHub plan-role read-policy updates through default version `v4`; apply role remains state-access-only.
- Completed the GitHub Terraform Plan drift gate; main/manual runs now fail on detailed exit code `2`, while pull requests may report proposed changes.
- Verified latest GitHub Terraform Plan run `29378532712` as exit code `0`, `0` add / `0` change / `0` destroy, result `clean`.
- Recorded deployed control-plane host `i-0254a9e2fcbcdebd7` as stopped.
- Ignored stopped-state Terraform drift for the EC2 host auto-assigned public IPv4 address to avoid replacing the scheduled SSM-only host after approved stop/start cycles.
- Completed the hardened control-plane baseline with CloudTrail, Session Manager logging, no-ingress EC2, and EventBridge Scheduler.
- Added Terraform modules for a multi-Region CloudTrail management-events baseline, encrypted Session Manager logging, and EventBridge Scheduler EC2 start/stop automation.
- Added ADR-0008 for the CloudTrail management-events baseline and ADR-0009 for automated EC2 operating schedules.
- Changed the control-plane default root EBS volume from 200 GiB to 100 GiB.
- Documented 8-hours-per-weekday, 12-hours-per-day, and always-on operating schedules with revised cost estimates.
- Documented that `m7i-flex.2xlarge` is approved only for scheduled operation under the current $250 monthly budget.
- Documented the GitHub required-reviewer limitation and the local IAM Identity Center apply boundary.
- Added EC2 start/stop runbook and proposed EventBridge Scheduler start/stop design.
- Added ADR-0007 for the manual apply boundary while GitHub reviewer protection is unavailable.
- Recorded the approved remote-state and GitHub OIDC bootstrap execution results.
- Added product runtime inventory for the existing AI.FO-Demo product.
- Added control-plane fit assessment, principle traceability matrix, assumption register, and execution plan.
- Added repository operating model docs for contribution, security, roadmap, runbooks, memory, workstreams, and workqueue.
- Added ADR framework and initial control-plane decisions.
- Reconciled PR #1 handoff documents against the current product repository, current infrastructure scaffold, and founder principles.
- Documented EC2 instance recommendation and current cost tension against the $250 monthly budget.
- Added initial cost model with always-on, scheduled, and smaller-instance scenarios.
- Narrowed the GitHub Terraform plan role from AWS managed `ReadOnlyAccess` to a custom read policy with explicit extension hook.
- Made EC2 detailed monitoring explicit and disabled by default.
- Made shell scripts compatible with GitHub `shellcheck`.
- Made the Terraform plan workflow skip until OIDC/backend repository variables are configured.

## 2026-07-14

- Scaffolded initial AWS control-plane repository.
- Added Terraform bootstrap roots for remote state and GitHub OIDC.
- Added control-plane Terraform environment and modules.
- Added local validation script and Terraform validation workflow.
- Pushed private baseline repository.
