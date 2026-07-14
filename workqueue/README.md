# Work Queue

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
| WQ-008 | Validate all Terraform and workflows offline | `./scripts/validate.sh`, YAML parse, diff check, Markdown fence check, secret scan | Done; `shellcheck` skipped because unavailable |
| WQ-009 | Commit and push branch | Commit `e54e60b`, branch pushed to origin | Done |
| WQ-010 | Open PR | https://github.com/josephmccann/AIFO-Control-Plane/pull/2 | Done |

## In Progress

| ID | Work Item | Dependencies | Rationale | Owner | Validation | Blocking Decisions |
| --- | --- | --- | --- | --- | --- | --- |
| WQ-011 | Build cost model | WQ-009 | Resolve budget tension before apply | Infrastructure | Cost doc | Host size/schedule decision |

## Blocked

| ID | Work Item | Blocker | Recommendation |
| --- | --- | --- | --- |
| WQ-020 | Execute remote-state bootstrap | Requires human approval to create AWS S3 resources | Approve only after PR review |
| WQ-021 | Execute GitHub OIDC bootstrap | Requires human approval to create IAM resources | Approve only after PR review |
| WQ-022 | First control-plane apply | Requires state, OIDC, plan review, cost decision, and human approval | Do not apply yet |
| WQ-023 | Product runtime hosting | Requires product migration decision and spending approval | Defer |

## Next

| ID | Work Item | Dependencies | Rationale | Owner | Validation | Blocking Decisions |
| --- | --- | --- | --- | --- | --- | --- |
| WQ-012 | Design Session Manager logging | WQ-009 | Improve auditability | Infrastructure | ADR/runbook | Cost review |
| WQ-013 | Prepare deployment-readiness review | WQ-011, WQ-012 | Gate first apply | Infrastructure | Checklist | Human approval |
