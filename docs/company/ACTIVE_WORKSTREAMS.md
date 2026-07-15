# AI.FO Active Workstreams

> **Digest metadata**
> - Audit snapshot: 2026-07-14 · pinned commits: see [README.md](README.md) evidence table
> - Statement classes: **[FACT]** verified current fact · **[PR]** open-PR proposal · **[RUN]** active runtime state · **[REC]** recommendation · **[JOE]** founder decision
> - PR and active-run state is volatile — refresh from the [canonical dynamic sources](README.md#canonical-dynamic-sources-always-fresher-than-this-digest) before acting.

Scope: everything in flight across all AI.FO repositories, with isolation, blockers, and the decision sequence.

Ownership: Joe holds every merge and ratification gate. The "Agent" column names the executing AI session type recorded in repository evidence.

## In flight

| # | Workstream | Class | Where (repo · branch/PR) | Agent | State at audit | Waiting on |
|---|---|---|---|---|---|---|
| 1 | Post-merge demo deployment of product baseline `3329c99` | [FACT] | AI.FO-Demo · `master` (PR #186 **merged** 2026-07-15 02:11 UTC, merge commit `3329c99`) | — | PR #186 is now part of the canonical product baseline; **the live Replit demo has not yet been updated to this SHA**; deployment and telemetry refresh pending | Deployment validation [JOE]; **connector activation remains separately gated** on validation + explicit configuration |
| 2 | Founder context + constitutional principles drafts | [PR] | AI.FO-Demo · PR #180 (`docs/founder-aifo-context`) | Claude Code | Valuable working-draft source material, explicitly non-behavioral | Reconciliation into one canonical Founder Operating Manual, then disposition [JOE] |
| 3 | Session checkpoint (memory/, workqueue/, handoff, CHANGELOG) | [PR] | AI.FO-Demo · PR #195 (`docs/checkpoint-before-shutdown-2026-07-14`) | Claude Code | **July 14 shutdown checkpoint; later activity (PR #186 merge, PR #13, live EDGAR collection) has changed the state it froze** | Decision: refresh, supersede, or close [JOE] — not automatic merge |
| 4 | Product runtime architecture decision package (Replit → AWS, first cohort) | [PR] | AIFO-Control-Plane · **PR #13 (open, draft)**, `codex/product-runtime-architecture-decision-package` | Codex | Package delivered: runtime inventory (17 data flows), requirements, three-option analysis, reference architecture, STRIDE threat model, migration gates MR-01…MR-33, cost model, proposed ADR-0011…0022, founder decision packet. **All proposed, not canonical until reviewed and merged** | Founder review + architecture decisions OD-005…OD-008, OD-012 [JOE] |
| 5 | Study A — EDGAR live collection → scoring → measurement | [RUN] | aifo-signal-validation-study · `master` (runtime on operator machine; prereg frozen at `prereg-v1`, unchanged) | Claude Code ("CC") + adversarial fresh-reader seats | **Authorized full live collection over 8,215 registered companies actively running; ~36% complete at the 2026-07-14 PT checkpoint. Real-company scoring has not occurred.** | Nothing, conditionally: Joe has authorized automatic progression through scoring and measurement **only if all documented technical and methodological gates pass**; Joe re-engages only on a defined stop condition [JOE, standing] |
| 6 | Nightly telemetry + pressure-test operations | [FACT] | AI.FO-Demo · `master` (launchd on Joe's Mac + GitHub Actions deadman) → aifo-telemetry mirror | Automation (`aifo-telemetry-mirror[bot]`) | Steady state; fresh 2026-07-14; integrity fixes #187–#189 recently merged | Nothing — note single-machine dependency and cadence gaps |
| 7 | Company program-state consolidation (this document set) | [REC] | AIFO-Control-Plane · `claude/company-program-state-consolidation-2026-07` (worktree) | Claude Code | Docs under `docs/company/` only; revised per founder feedback | Founder review of the draft PR [JOE] |

## Dormant but live surfaces (no active workstream) — [FACT]

- **getaifo.com marketing site** (GetAIFO-site): deployed and serving; no commits since 2026-06-22; no open PRs. Abandoned April lavender-redesign branches are the only unmerged visual work.
- **Control-plane work queue**: "In Progress: None" — the WQ-001…WQ-037 series is completed **except WQ-023 (product runtime hosting) and WQ-035 (apply workflow automation), which remain Blocked** pending founder decisions (WQ-023 unblocks only after PR #13's review — see the dependency diagram below); the repo is in operational-refinement mode.
- **AWS operator host**: deployed, stopped, scheduler-managed.

## Isolation map (who can collide with whom) — [FACT]

- The two Control-Plane branches touch disjoint files: PR #13 owns the runtime-architecture docs (and supersedes `docs/product-runtime-inventory.md`); this consolidation owns only new files under `docs/company/`. No path overlap.
- AI.FO-Demo's two remaining open PRs (#180, #195) are docs-only and path-disjoint; PR #195's checkpoint content now needs rebasing against the post-#186 baseline as part of its disposition.
- The validation study reads the engine via a **pinned SHA** (`dc6aefc…`) at `/Users/joemccann/Desktop/aifo-demo-app` — product commits cannot silently change the study, but note the Desktop-vs-`~/code` dual-checkout situation (see LEGACY_AND_DEPRECATION_CANDIDATES.md §AI.FO-Demo).

## Decision dependencies

```
[JOE] PR #195 disposition ──► refresh / supersede / close (checkpoint no longer current)
[JOE] PR #180 reconciliation ──► one canonical Founder Operating Manual ──► doctrine home settled
[FACT] PR #186 MERGED (3329c99) ──► [JOE] deployment validation ──► demo on baseline + telemetry refresh
                                                                └──► connector activation (separate gate:
                                                                     validation + explicit configuration)
[JOE] PR #13 review ──► OD-005..OD-008, OD-012 ruled ──► WQ-023 unblocks (runtime migration path)
[RUN] EDGAR collection ──► gates pass? ──yes──► scoring ──► measurement ──► METHODS_AND_RESULTS filled
                                       └──stop condition──► [JOE] re-engaged
                                                             (only then: any public validation claim)
```

## Decision sequence — [REC]; every step is [JOE]

A sequence of decisions to make in order, not a predetermined merge order:

1. **Determine the disposition of PR #195** — refresh to current state, supersede with a new checkpoint, or close. Its content (in-repo memory/workqueue conventions) is worth having in some form; the July-14 snapshot itself is no longer current.
2. **Reconcile PR #180** into one canonical Founder Operating Manual — choose the home (product repo vs control plane vs its own repo), fold in `HANDOFF_COMPANY.md`, then disposition the PR (merge as-is, merge reworked, or close in favor of the manual).
3. **Resolve and validate deployment of product baseline `3329c99`** to the live demo, including the telemetry refresh. Connector activation remains separately gated on deployment validation plus explicit configuration.
4. **Review PR #13** and make the required founder architecture decisions (migration timing, production account, compute/frontend, database, storage, secrets/QBO keys, sessions, domain, AI-provider handling, retention, recovery objectives, budget, deployment approval). Merging #13 records the decisions as ADRs.
5. **Refresh and review this company digest** against the resolved state of steps 1–4 and the EDGAR run's status at that time — per the update protocol in [README.md](README.md) — then merge it.
6. **Begin production-prerequisite hardening** (PRODUCTION_READINESS_PLAN phases: production QBO OAuth, deployment parity, monitoring, real-company datasets, browser E2E, security/privacy review) against the settled baseline.
7. **Begin visual-foundation implementation** after the deployment baseline is settled.
