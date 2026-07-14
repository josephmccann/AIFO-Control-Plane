# Changelog

All notable changes to this repository are recorded here.

## Unreleased

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

## 2026-07-14

- Scaffolded initial AWS control-plane repository.
- Added Terraform bootstrap roots for remote state and GitHub OIDC.
- Added control-plane Terraform environment and modules.
- Added local validation script and Terraform validation workflow.
- Pushed private baseline repository.
