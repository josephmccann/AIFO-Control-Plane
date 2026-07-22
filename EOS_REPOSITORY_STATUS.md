# EOS Repository Status

**Status:** current · **Source-of-truth commit:** the merge that adds this document · **Audience:** anyone resuming this repository.

> Git identities and authenticated event hashes are authoritative; this narrative is a point-in-time snapshot. For the machine-readable pre-authorization checkpoint see `outputs/eos-activation-readiness/activation-readiness-snapshot.json` and its validator `scripts/engineering-os/validate-activation-readiness`.

---

## Part A — Repository guide (where things live, where not to edit)

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
- The Engineering Constitution (`docs/engineering-os/ENGINEERING_CONSTITUTION.md`) — its exact bytes are pinned by every mission.
- Authenticated event comments on mission issues — never edit; history is append-only.
- Anything outside your mission's `allowed_paths`.

### Top-level EOS documentation
- `EOS_VERSION_1_FINAL_REPORT.md` — overview, governance history, roadmap, lessons.
- `EOS_ARCHITECTURE.md` — components and flows (Mermaid).
- `EOS_ENGINEERING_GUIDE.md` — engineer + AI-agent handbook.
- `EOS_FOUNDER_GUIDE.md` — founder commands.
- `EOS_OPERATIONS_RUNBOOK.md` — activation runbook.
- `EOS_REPOSITORY_STATUS.md` — this document.

---

## Part B — Current status report

### Repository
- **Default branch `main`:** merge commit adding this documentation set (built on the readiness-snapshot merge `ac70fd4cd99de44d26c20a719bd2f678f849631d`).
- **Latest release / tag:** none yet. The `eos-v1.0-governance-complete` tag and GitHub Release are a **founder-controlled post-merge action** (created after this documentation merges).
- **Required checks:** `Validate Terraform` and `GitGuardian Security Checks` (both green on `main`).

### Branch inventory (state, not exhaustive listing)
- **Deleted (fully merged, mine):** `codex/eos-activation-integration` (#34), `codex/eos-compat-chain-merge-parent` (#37), `codex/eos-nonce-retirement` (#39), `codex/eos-activation-readiness-snapshot` (#42).
- **Preserved — open PRs:** `codex/eos-test-integrity-delta-activation` (**PR #24**, historical bootstrap evidence), `codex/eos-postmerge-validation` (PR #20), `claude/company-program-state-consolidation-2026-07` (PR #14), `codex/product-runtime-architecture-decision-package` (PR #13).
- **Preserved — protected:** `codex/engineering-operating-system-v1` (protected worktree).
- **Preserved — other workstreams (not EOS v1):** `agent/*`, `docs/*`, remaining `codex/eos-*` branches with unmerged work, `claude/founder-operating-manual-2026-07`. Left untouched; disposition is out of EOS v1 scope.
- **`codex/eos-test-integrity-canonical-baseline`:** fully merged, no open PR — preserved as pre-program historical evidence (not created by the EOS v1 program).

### Worktree inventory
- `engineering-operating-system` — **protected** (`f5c9dfc`); do not touch.
- `eos-test-integrity-delta-activation` — PR #24; preserve.
- `eos-bootstrap-descendant-hotfix` (branch `codex/eos-postmerge-validation`) — PR #20; preserve.
- `company-program-state-consolidation` — PR #14; preserve.
- `product-runtime-architecture-decision-package` — PR #13; preserve.
- `eos-test-integrity-baseline-activation` — other-workstream, unmerged; preserve.
- The primary checkout is on `main` (its local ref may lag `origin/main`; `origin/main` is authoritative).
- Obsolete EOS v1 worktrees created during this program were removed after each merge.

### Stash inventory
| Stash | Why it exists | Preserve? | Safe to delete when |
|---|---|---|---|
| `stash@{0}` — "WIP before retiring idle EOS Codex session 2026-07-21" | throwaway WIP from a retired session; its branch is merged & deleted | keep unless the founder confirms disposable | after founder confirms it holds nothing needed |
| `stash@{1}` — "WIP before reboot 2026-07-20 12:52:35" | the originally protected stash on the protected branch | **yes — protected** | do not delete |

### Missions
- **Merged (EOS v1):** #35 (PR #34), #36 (PR #37), #38 (PR #39), #40 (PR #42), #41 (this documentation).
- **Governance predecessors:** #26 (baseline), #31 (integration), #32 (classification), and earlier #18–#30 bootstrap missions — authenticated history.
- **Open mission issues** remain visible as the authenticated record; only Ready-bound ones govern change.

### Open historical PRs (do not merge without a founder decision)
- **#24** — historical bootstrap evidence; preserved open. #20, #14, #13 — other workstreams.

### Governance / activation status
- **Mission #26 ledger:** 1 authorized (structurally superseded) · **0 attempted** · **0 consumed**.
- **Retired nonce:** unused, permanently retired, rejected fail-closed (`ACTIVATION_NONCE_RETIRED`). Recorded only by digest identity `db6eaa2a8221f6e4529b85cb3fc80019318e00f491ed04858cc1f81c604f2512` and authorization event hash `b20599a1396bd174d5b4a3ff2cf60d82c34013b4fafd6c2d05d8a1ebeeb91fdb`.
- **Compatibility chain:** `COMPATIBILITY_CHAIN_VALID` on `main`.
- **Test Integrity:** fail-closed at the pre-activation boundary (expected; not a required check; never suppressed).
- **Deployment:** none. Record `5528959623` is `inactive` (accidental API-audit artifact; preserved).

### Remaining engineering work
**None.** EOS Version 1 is engineering-complete (maintenance mode — see `EOS_VERSION_1_FINAL_REPORT.md`).

---

## Part C — Operational sequence (founder-controlled; documented, not executed)

1. `/eos authorize-baseline <FRESH_NONCE>` on issue #26
2. `/eos attempt-baseline <SAME_NONCE>` on issue #26
3. `/eos consume-baseline <SAME_NONCE>` on issue #26
4. Test Integrity activation verification on `main`
5. Deployment (separate gate)

These are **founder-controlled lifecycle events**. See `EOS_OPERATIONS_RUNBOOK.md` for details. No real nonce appears in any document.
