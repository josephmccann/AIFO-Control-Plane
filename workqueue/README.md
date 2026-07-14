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
| WQ-011 | Build cost model | `docs/cost-model.md` | Done |
| WQ-012 | Design Session Manager logging | `docs/session-manager-logging-design.md`, ADR-0006 | Done |
| WQ-013 | Prepare deployment-readiness review | `docs/deployment-readiness-review.md` | Done; bootstrap complete, host deployment blocked by human gates |
| WQ-020 | Execute remote-state bootstrap | Applied exactly approved S3 resources; post-apply plan exit code `0` | Done |
| WQ-021 | Execute GitHub OIDC bootstrap | Applied exactly approved OIDC/IAM resources; post-apply plan exit code `0` | Done |
| WQ-024 | Merge PR #2 | Squash-merged at `6f8064b9de3aaa0f099013170c3c007e41fd266f` | Done |
| WQ-025 | Close or supersede PR #1 | Closed as superseded | Done |
| WQ-026 | Configure GitHub environments and repository variables | Environments and variables configured; first plan succeeded through OIDC | Done; required reviewers unavailable for `terraform-apply` |
| WQ-027 | Align root volume cost model and deployment controls | GitHub plan reviewed in PR #4 | Done |
| WQ-029 | Add pre-deployment audit controls | PR #5 merged at `c4c998bb10289c91dc47013a0069adc0961b461f`; GitHub plan passed | Done |
| WQ-030 | Apply GitHub OIDC plan-role read-policy update | Applied `0 added, 1 changed, 0 destroyed`; read-only check passed | Done |

## In Progress

| ID | Work Item | Validation | Notes |
| --- | --- | --- | --- |
| WQ-031 | Record partial hardened control-plane apply | Documentation PR required | This PR |

## Blocked

| ID | Work Item | Blocker | Recommendation |
| --- | --- | --- | --- |
| WQ-022 | Finish hardened control-plane apply | AWS `PendingVerification` blocked EC2 `RunInstances`; post-failure plan shows `4 to add, 0 to change, 0 to destroy` | Wait for account validation, re-plan, and require renewed approval before any apply |
| WQ-023 | Product runtime hosting | Requires product migration decision and spending approval | Defer |

## Next

- Wait for AWS account regional validation to clear.
- Re-run control-plane plan and confirm the residual resources are only the EC2 host and dependent Scheduler policy/schedules.
- Decide whether to approve a resumed local IAM Identity Center apply.
