# Manual Host Patching Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Document a secure, approval-gated manual patch window for the single Ubuntu control-plane host and reconcile repository state around that decision.

**Architecture:** A focused runbook owns execution commands, evidence, abort criteria, reboot verification, and escalation. ADR-0010 records why manual patching is current and what triggers reconsideration of Systems Manager Patch Manager automation.

**Tech Stack:** Markdown, AWS CLI, Systems Manager Session Manager, Ubuntu 22.04 APT, existing repository validation tooling.

## Global Constraints

- Do not start, stop, reboot, patch, snapshot, or otherwise mutate the EC2 host while writing or validating this documentation.
- Do not create or modify AWS resources, Terraform, IAM, Scheduler, or GitHub apply automation.
- Preserve SSM-only administration and no public ingress.
- Keep product runtime and customer data out of scope.

---

### Task 1: Manual Patching Runbook

**Files:**
- Create: `docs/runbooks/host-patching.md`

- [x] Document cadence, approvals, preflight, logged SSM access, pre-change evidence, APT commands, post-change checks, reboot handling, abort criteria, rollback escalation, and closeout.
- [x] Separate read-only verification from mutating steps and label every approval boundary.
- [x] Link official Ubuntu package/update guidance and official AWS Patch Manager/Maintenance Windows references.

### Task 2: Decision Record And Canonical State

**Files:**
- Create: `docs/adr/0010-manual-host-patching.md`
- Modify: `docs/adr/README.md`
- Modify: `docs/security-model.md`
- Modify: `ROADMAP.md`
- Modify: `CHANGELOG.md`
- Modify: `memory/open-decisions.md`
- Modify: `memory/infrastructure-roadmap.md`
- Modify: `workqueue/README.md`
- Modify: `workstreams/security.md`
- Modify: `workstreams/control-plane.md`
- Modify: `workstreams/cost-optimization.md`
- Modify: `workstreams/monitoring.md`

- [x] Record manual patching as the current one-host decision and defer automation until scale/compliance justifies new AWS resources.
- [x] Resolve OD-015 and complete a new workqueue item.
- [x] Remove stale workstream claims that the host and Scheduler are undeployed.

### Task 3: Verification And Publication

- [x] Run `PATH="$PWD/build/bin:$PATH" ./scripts/validate.sh`.
- [x] Run `git diff --check` and inspect all changed commands for mutation labels and placeholder instance IDs.
- [x] Confirm the dated pre-update handoff remains historical and unchanged.
- [x] Commit, push, open a documentation-only PR, wait for all checks, and merge under standing authority.
