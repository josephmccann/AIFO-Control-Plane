# AI.FO Active Workstreams

Status: CURRENT — snapshot as of 2026-07-14
Scope: everything in flight across all AI.FO repositories, with isolation, blockers, and sequencing. Owners: Joe holds every merge/ratification gate; "agent" below names the executing AI session type recorded in repository evidence.

## In flight

| # | Workstream | Where (repo · branch/worktree) | Agent | State | Blocked on |
|---|---|---|---|---|---|
| 1 | Commercial account surface + Stripe/external connectors | AI.FO-Demo · PR #186 (`feature/top-five-value-adds-2026-07-10`) | Claude Code | Code-complete, suites self-reported green; most recently updated of all open PRs | Joe's review/merge decision |
| 2 | Founder context + constitutional principles docs | AI.FO-Demo · PR #180 (`docs/founder-aifo-context`) | Claude Code | Working drafts, explicitly non-behavioral | Founder review; also settles the "doctrine home" question |
| 3 | Session checkpoint (memory/, workqueue/, handoff, CHANGELOG) | AI.FO-Demo · PR #195 (`docs/checkpoint-before-shutdown-2026-07-14`) | Claude Code | Complete; intentionally held ("do not merge during shutdown unless explicitly requested") | The hold itself |
| 4 | Product runtime architecture decision package (Replit → AWS for first cohort) | AIFO-Control-Plane · worktree `.worktrees/product-runtime-architecture-decision-package`, branch `codex/product-runtime-architecture-decision-package` (local, unpushed, docs-only: 1 commit, 2 spec/plan files so far) | Codex | Active session; deliverables (options analysis, reference architecture, threat model, founder decision packet) not yet written | Session completion, then Joe's OD-005…OD-008 rulings |
| 5 | Study A live-run readiness (EDGAR validation) | aifo-signal-validation-study · `master` (post-`prereg-v1` repairs through 2026-07-14) | Claude Code ("CC") + adversarial fresh-reader seats | Pipeline frozen + preregistered; collection-path repairs landing; primary scored run NOT executed | Matched-set re-emission under the 07-09 match-input rulings → sealed-set manifest → Joe's single-shot trigger (Row 7) |
| 6 | Nightly telemetry + pressure-test operations | AI.FO-Demo · `master` (launchd on Joe's Mac + GitHub Actions deadman) → aifo-telemetry mirror | Automation (`aifo-telemetry-mirror[bot]`) | Steady state; fresh 2026-07-14; integrity fixes #187–#189 recently merged | Nothing — but note single-machine dependency and cadence gaps |
| 7 | Company program-state consolidation (this document set) | AIFO-Control-Plane · worktree `.worktrees/company-program-state-consolidation`, branch `claude/company-program-state-consolidation-2026-07` | Claude Code | Docs written under `docs/company/` only | Joe's review; stops before PR per instruction |

## Dormant but live surfaces (no active workstream)

- **getaifo.com marketing site** (GetAIFO-site): deployed and serving; no commits since 2026-06-22; no open PRs. Abandoned April lavender-redesign branches are the only unmerged visual work.
- **Control-plane work queue**: "In Progress: None" — WQ-001…WQ-037 completed; the repo is in operational-refinement mode.
- **AWS operator host**: deployed, stopped, scheduler-managed.

## Isolation map (who can collide with whom)

- The two Control-Plane worktrees touch disjoint files: the runtime session owns `docs/superpowers/plans|specs/2026-07-15-product-runtime-*` (and plans to supersede `docs/product-runtime-inventory.md`); this consolidation owns only new files under `docs/company/`. No overlap.
- AI.FO-Demo's three open PRs are path-disjoint in substance; the only friction is textual (README/docs edits in #186 vs CHANGELOG/docs in #195). Merge order handles it.
- The validation study reads the engine via a **pinned SHA** (`dc6aefc…`) at `/Users/joemccann/Desktop/aifo-demo-app` — product commits cannot silently change the study, but note the Desktop-vs-`~/code` dual-checkout situation (see LEGACY_AND_DEPRECATION_CANDIDATES.md §AI.FO-Demo).

## Decision dependencies

```
Joe: review PR #195 hold ────────────► merge (anytime; independent)
Joe: review PR #180 ─────────────────► doctrine home decided (SOURCE_OF_TRUTH §founder doctrine)
Joe: review PR #186 ─────────────────► commercial surface on master (Production-Readiness Phase 7 down payment)
Codex session finishes packet ───────► Joe rules OD-005..OD-008, OD-012 ──► WQ-023 unblocks (runtime migration)
Study: matched-set re-emission ──────► Joe triggers single-shot scored run ──► METHODS_AND_RESULTS filled
                                                                            └─► only then: any public validation claim
```

## Recommended merge sequence for current work

1. **AI.FO-Demo #195** (checkpoint docs) — zero risk, restores in-repo memory/workqueue; lift the hold explicitly.
2. **AI.FO-Demo #180** (doctrine) — docs-only; merging it resolves the split doctrine home.
3. **AI.FO-Demo #186** (connectors) — after code review; rebase over the two doc PRs to absorb textual overlap.
4. **Control-Plane: this branch** (`docs/company/`) — new files only; no conflict with anything, including the runtime session.
5. **Control-Plane: runtime decision package** — when its session completes; it intends to supersede `docs/product-runtime-inventory.md`, so it should merge *after* this digest (which cites that file as it exists today) and the digest's link can then be refreshed.
