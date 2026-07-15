# Work Queue

Session state: ACTIVE — OPERATIONAL REFINEMENT

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

## In Progress

None.

## Blocked

| ID | Work Item | Blocker | Recommendation |
| --- | --- | --- | --- |
| WQ-023 | Product runtime hosting | Requires product migration decision, spending approval, secrets design, database decision, storage decision, and product validation plan | Defer |
| WQ-035 | Apply workflow automation | GitHub required environment reviewers unavailable on current repository plan | Keep apply workflow absent |

## Next

- Add periodic deployment-status documentation checks.
- Add lightweight monthly cost evidence.
