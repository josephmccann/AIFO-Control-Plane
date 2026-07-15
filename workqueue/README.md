# Work Queue

Session state: ACTIVE - PRODUCT RUNTIME IMPLEMENTATION PARAMETERS PENDING

Status values: `todo`, `in-progress`, `blocked`, `done`.

## Completed

| ID | Work Item | Validation | Notes |
| --- | --- | --- | --- |
| WQ-001 | Inspect current AIFO-Control-Plane repository and branches | Git status and branch review | Done |
| WQ-002 | Inspect local or cloned AI.FO-Demo product repository | Product docs and package review | Done |
| WQ-003 | Produce mandatory pre-work docs | Markdown files added | Done |
| WQ-004 | Review PR #1 handoff documents | `gh pr view`, local branch diff, handoff reads | Done |
| WQ-005 | Establish repository operating model | File existence and docs review | Done |
| WQ-006 | Add ADR framework and initial ADRs | ADR files added | Done |
| WQ-007 | Reconcile PR #1 handoffs | Reconciled handoff docs and reconciliation note | Done |
| WQ-008 | Validate all Terraform and workflows offline | `./scripts/validate.sh`, YAML parse, diff check, Markdown fence check, secret scan | Done |
| WQ-020 | Execute remote-state bootstrap | Applied exactly approved S3 resources; post-apply plan exit code `0` | Done |
| WQ-021 | Execute GitHub OIDC bootstrap | Applied exactly approved OIDC/IAM resources; post-apply plan exit code `0` | Done |
| WQ-026 | Configure GitHub environments and repository variables | Environments and variables configured; OIDC planning works | Done |
| WQ-027 | Align root volume cost model and deployment controls | GitHub plan reviewed in PR #4 | Done |
| WQ-029 | Add pre-deployment audit controls | CloudTrail, Session Manager logging, Scheduler design merged | Done |
| WQ-030 | Apply GitHub OIDC plan-role read-policy updates | Policy default version `v4`; read-only check passed | Done |
| WQ-031 | Complete hardened control-plane baseline | Local and GitHub plans clean; instance stopped | Done |
| WQ-032 | Fix stopped-instance public IPv4 drift | Local stopped/running plans clean | Done |
| WQ-033 | Complete GitHub Terraform plan gate | Main/manual drift fails; PR proposed changes pass | Done |
| WQ-034 | Checkpoint control-plane before Codex CLI update | PR #10 merged | Done |
| WQ-036 | Add durable local `actionlint` and `shellcheck` tooling | Pinned installer, platform tests, full repository validation | Done |
| WQ-037 | Define control-plane host patching and maintenance | ADR-0010, approval-gated runbook, repository-state reconciliation | Done |
| WQ-038 | Define product-runtime requirements | Beta-cohort requirements cover security, recovery, isolation, support, capacity and cost | Done; proposed for founder approval |
| WQ-039 | Complete product-runtime architecture options analysis | Three options, explicit weights, decision matrix and recommendation | Done; proposed for founder approval |
| WQ-040 | Complete product-runtime threat model | STRIDE assets, boundaries, threats, controls, residual risk, owners and evidence | Done; security review pending |
| WQ-041 | Complete product-runtime cost model | Current/hybrid/AWS assumptions, ranges, pricing anchors, thresholds and risks | Done; invoices/founder approval pending |
| WQ-042 | Define product-runtime migration readiness | Objective gates name evidence, owner, approver, status and blocking effect | Done; gates not executed |
| WQ-047 | Refresh architecture package for merged product PR #186 | Product baseline `3329c99`; connector/account delta, threat/gate changes and 10-item prerequisite plan | Done; documentation only |
| WQ-048 | Resolve merged-baseline demo deployment dependency | Live `3329c99`, transactional `0011`, public/auth smoke, disabled connectors, zero connector data, rollback `30a8ed2` retained | Done; destructive schema proposal/startup health findings recorded |

## In Progress

None.

## Blocked

| ID | Work Item | Blocker | Recommendation |
| --- | --- | --- | --- |
| WQ-023 | Product runtime hosting | Requires product migration decision, spending approval, secrets design, database decision, storage decision, and product validation plan | Defer |
| WQ-035 | Apply workflow automation | GitHub required environment reviewers unavailable on current repository plan | Keep apply workflow absent |
| WQ-043 | Obtain founder product-runtime implementation decisions | Strategic migration timing is accepted; ADR-0012 through ADR-0022, exact parameters, connector tenancy/account truth, budget and provider/domain decisions remain Proposed | Review founder decision packet; no deployment approval implied |
| WQ-044 | Future staging deployment | Requires approved architecture/cost/account/IAM, completed product prerequisites, reviewed Terraform plan and explicit resource-creation approval | Do not create staging during architecture mission |
| WQ-045 | Product migration rehearsal | Requires validated staging, source backup/restore approval, synthetic/sanitized data rule and all rehearsal prerequisites | Rehearse only after explicit approval; do not copy customer data |
| WQ-046 | Product production cutover | Requires every migration gate PASS and explicit production/data/DNS/QBO/cutover approval | Keep blocked; no customer data/runtime deployed |

## Next Narrow Workstream

After a separately scoped product-code authorization, implement exactly prerequisite 1 in a dedicated `AI.FO-Demo` worktree: one controlled migration ledger, independent development/production baselines, explicit generated-SQL review, destructive-diff rejection and removal of non-fatal startup DDL. Do not deploy, create AWS runtime infrastructure, enable connectors or use customer data.
