# EOS Repository Status

**Status:** current · **Scope:** point-in-time narrative refreshed by Mission #50 · **Audience:** anyone resuming this repository.

> Git identities and authenticated event hashes are authoritative; this narrative is a point-in-time snapshot. For the machine-readable pre-authorization checkpoint see `outputs/eos-activation-readiness/activation-readiness-snapshot.json` and its validator `scripts/engineering-os/validate-activation-readiness`.

---

## Part A: Repository guide (where things live, where not to edit)

### Important folders
| Path | Contents |
|---|---|
| `engineering_os/` | The EOS kernel (commands, mission, state, audit, schema, Test Integrity). **Governed; change only under a mission.** |
| `schemas/engineering-os/` | JSON schemas for events, missions, closures, etc. Tier 2; change only under a mission. |
| `scripts/engineering-os/` | Governance/validation scripts (extensionless; classified by shebang). |
| `scripts/validate.sh` | The required-gate entrypoint (runs classification, tests, closure, Terraform). |
| `.github/workflows/mission-command.yml` | The **only** authenticated-event writer. |
| `.github/workflows/terraform-validate.yml` | The required `Validate Terraform` check. |
| `docs/engineering-os/` | Governance documents (constitution, authority model, activation scope, etc.). Start at its `README.md`. |
| `outputs/` | **Committed governed evidence** (mission records, closure records, review/reconciliation logs, the readiness snapshot). |
| `terraform/` | Infrastructure config (validated by CI; deployment is a separate founder gate). |
| `tests/engineering_os/` | The governed test corpus (Test Integrity invariant surface in part). |

### Where NOT to edit
- The **invariant surface** (baseline generator/analyzer): `engineering_os/test_integrity.py`, `engineering_os/test_integrity_cli.py`, `engineering_os/python_imports.py`, `engineering_os/canonical.py`, `scripts/engineering-os/validate-test-integrity`, `docs/engineering-os/TEST_INTEGRITY_CANONICAL_FINDINGS.json`. Changing these breaks the compatibility chain and blocks activation.
- The Engineering Constitution (`docs/engineering-os/ENGINEERING_CONSTITUTION.md`): its exact bytes are pinned by every mission.
- Authenticated event comments on mission issues: never edit; history is append-only.
- Anything outside your mission's `allowed_paths`.

### Top-level EOS documentation
- `EOS_VERSION_1_FINAL_REPORT.md`: overview, governance history, roadmap, lessons.
- `EOS_ARCHITECTURE.md`: components and flows (Mermaid).
- `EOS_ENGINEERING_GUIDE.md`: engineer + AI-agent handbook.
- `EOS_FOUNDER_GUIDE.md`: founder commands.
- `EOS_OPERATIONS_RUNBOOK.md`: activation runbook.
- `EOS_REPOSITORY_STATUS.md`: this document.

---

## Part B: Current status report

### Repository
- **Visibility:** public. Repository content, issues, pull requests, comments, and workflow logs must be treated as public data.
- **Default branch:** `main`; resolve the current commit with `git rev-parse origin/main`.
- **Latest release / tag:** none. Any EOS release or tag remains a separate founder-controlled action.
- **Required checks:** strict `Validate Terraform` and `GitGuardian Security Checks`.
- **Not yet required:** `Test Integrity / Test Integrity`; promotion belongs after the separate baseline-activation gate.

### Branch inventory (state, not exhaustive listing)
- **Open PR:** #24, `codex/eos-test-integrity-delta-activation`, is intentionally preserved as historical bootstrap evidence. It is not merge-ready.
- **Closed as fully subsumed:** #20 has a zero-file diff against current `main`.
- **Closed as stale snapshots:** draft PRs #13 and #14 predate the current EOS and repository state. Their branches remain preserved.
- **Remote branches:** no branch was deleted during this cleanup. A branch's existence is not merge authority.

### Operator-local worktrees and stashes

Worktree paths and stash indices are local, mutable operator state, not
repository truth. Inspect them at the time of use with `git worktree list` and
`git stash list`. Do not remove a worktree, branch, or stash owned by another
session without confirming ownership and recoverability.

### Missions
- **Merged EOS v1 foundation:** #35 (PR #34), #36 (PR #37), #38 (PR #39), #40 (PR #42), and #41 (PR #43).
- **Operational repairs:** #46 (PR #47) aligned every reusable workflow with the reviewed kernel and repaired activation-run provenance collection; #48 (PR #49) made the developer-tools shell regression an isolated mandatory part of complete validation.
- **Current status refresh:** #50 records this public, post-repair operating state.
- **Governance predecessors:** #26 (baseline), #31 (integration), #32 (classification), and earlier #18 to #30 bootstrap missions remain authenticated history.
- **Open mission issues** remain visible as the authenticated record; only Ready-bound ones govern change.

### Open historical PRs (do not merge without a founder decision)
- **#24:** historical bootstrap evidence, preserved open and explicitly not merge-ready.

### Governance / activation status
- **Mission #26 ledger:** 1 authorized (structurally superseded), **0 attempted**, **0 consumed**.
- **Retired nonce:** unused, permanently retired, rejected fail-closed (`ACTIVATION_NONCE_RETIRED`). Recorded only by digest identity `db6eaa2a8221f6e4529b85cb3fc80019318e00f491ed04858cc1f81c604f2512` and authorization event hash `b20599a1396bd174d5b4a3ff2cf60d82c34013b4fafd6c2d05d8a1ebeeb91fdb`.
- **Compatibility chain:** `COMPATIBILITY_CHAIN_VALID` on `main`.
- **Test Integrity:** fail-closed at the pre-activation boundary (expected; not a required check; never suppressed).
- **Orphan monitoring:** a read-only Mission #26 workflow dispatch passed on repaired `main`; two successful scheduled observations remain an operational verification item. Orphan mutation remains disabled.
- **Validation:** the complete gate includes the Engineering OS suite, the isolated developer-tools shell regression, Terraform validation, ShellCheck, and actionlint.
- **Deployment:** none. Record `5528959623` is `inactive` (accidental API-audit artifact; preserved).

### Remaining engineering work

EOS Version 1 remains in maintenance mode. The bounded remaining sequence is:

1. Observe two successful scheduled orphan-recovery dry runs after Mission #46.
2. Obtain a separate founder decision before issuing any baseline-activation command.
3. If activation succeeds, separately promote Test Integrity into branch protection.
4. Monitor the resulting checks and failure notifications; deployment remains independent and unauthorized.

---

## Part C: Operational sequence (founder-controlled; documented, not executed)

1. `/eos authorize-baseline <FRESH_NONCE>` on issue #26
2. `/eos attempt-baseline <SAME_NONCE>` on issue #26
3. `/eos consume-baseline <SAME_NONCE>` on issue #26
4. Test Integrity activation verification on `main`
5. Deployment (separate gate)

These are **founder-controlled lifecycle events**. See `EOS_OPERATIONS_RUNBOOK.md` for details. No real nonce appears in any document.
