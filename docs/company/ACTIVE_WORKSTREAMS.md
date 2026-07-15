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
| 1 | Commercial account surface + Stripe/external connectors | [PR] | AI.FO-Demo · PR #186 (`feature/top-five-value-adds-2026-07-10`) | Claude Code | Code-complete; PR body self-reports 13,487 aifo / 1,003 api-server tests and 6 Chromium E2E green — **self-reported, not independently re-verified** | Final technical review, then founder merge decision [JOE] |
| 2 | Founder context + constitutional principles drafts | [PR] | AI.FO-Demo · PR #180 (`docs/founder-aifo-context`) | Claude Code | Valuable working-draft source material, explicitly non-behavioral | Reconciliation into one canonical Founder Operating Manual, then disposition [JOE] |
| 3 | Session checkpoint (memory/, workqueue/, handoff, CHANGELOG) | [PR] | AI.FO-Demo · PR #195 (`docs/checkpoint-before-shutdown-2026-07-14`) | Claude Code | **July 14 shutdown checkpoint; later activity (PR #13, live EDGAR collection) has changed the state it froze** | Decision: refresh, supersede, or close [JOE] — not automatic merge |
| 4 | Product runtime architecture decision package (Replit → AWS, first cohort) | [PR] | AIFO-Control-Plane · **PR #13 (open, draft)**, `codex/product-runtime-architecture-decision-package` | Codex | Package delivered: runtime inventory (17 data flows), requirements, three-option analysis, reference architecture, STRIDE threat model, migration gates MR-01…MR-33, cost model, proposed ADR-0011…0022, founder decision packet. **All proposed, not canonical until reviewed and merged** | Founder review + architecture decisions OD-005…OD-008, OD-012 [JOE] |
| 5 | Study A — EDGAR live collection → scoring → measurement | [RUN] | aifo-signal-validation-study · `master` (runtime on operator machine; prereg frozen at `prereg-v1`, unchanged) | Claude Code ("CC") + adversarial fresh-reader seats | **Authorized full live collection over 8,215 registered companies actively running; ~36% complete at latest checkpoint. Real-company scoring has not occurred.** | Nothing, conditionally: Joe has authorized automatic progression through scoring and measurement **only if all documented technical and methodological gates pass**; Joe re-engages only on a defined stop condition [JOE, standing] |
| 6 | Nightly telemetry + pressure-test operations | [FACT] | AI.FO-Demo · `master` (launchd on Joe's Mac + GitHub Actions deadman) → aifo-telemetry mirror | Automation (`aifo-telemetry-mirror[bot]`) | Steady state; fresh 2026-07-14; integrity fixes #187–#189 recently merged | Nothing — note single-machine dependency and cadence gaps |
| 7 | Company program-state consolidation (this document set) | [REC] | AIFO-Control-Plane · `claude/company-program-state-consolidation-2026-07` (worktree) | Claude Code | Docs under `docs/company/` only; revised per founder feedback | Founder review of the draft PR [JOE] |

## Dormant but live surfaces (no active workstream) — [FACT]

- **getaifo.com marketing site** (GetAIFO-site): deployed and serving; no commits since 2026-06-22; no open PRs. Abandoned April lavender-redesign branches are the only unmerged visual work.
- **Control-plane work queue**: "In Progress: None" — WQ-001…WQ-037 completed; the repo is in operational-refinement mode.
- **AWS operator host**: deployed, stopped, scheduler-managed.

## Isolation map (who can collide with whom) — [FACT]

- The two Control-Plane branches touch disjoint files: PR #13 owns the runtime-architecture docs (and supersedes `docs/product-runtime-inventory.md`); this consolidation owns only new files under `docs/company/`. No path overlap.
- AI.FO-Demo's three open PRs are path-disjoint in substance; the only friction is textual (README/docs edits in #186 vs CHANGELOG/docs in #195). The decision sequence handles it.
- The validation study reads the engine via a **pinned SHA** (`dc6aefc…`) at `/Users/joemccann/Desktop/aifo-demo-app` — product commits cannot silently change the study, but note the Desktop-vs-`~/code` dual-checkout situation (see LEGACY_AND_DEPRECATION_CANDIDATES.md §AI.FO-Demo).

## Decision dependencies

```
[JOE] PR #195 disposition ──► refresh / supersede / close (checkpoint no longer current)
[JOE] PR #180 reconciliation ──► one canonical Founder Operating Manual ──► doctrine home settled
[JOE] PR #186 independent technical review ──► founder merge decision ──► commercial surface on master
[JOE] PR #13 review ──► OD-005..OD-008, OD-012 ruled ──► WQ-023 unblocks (runtime migration path)
[RUN] EDGAR collection ──► gates pass? ──yes──► scoring ──► measurement ──► METHODS_AND_RESULTS filled
                                       └──stop condition──► [JOE] re-engaged
                                                             (only then: any public validation claim)
```

## Decision sequence — [REC]; every step is [JOE]

A sequence of decisions to make in order, not a predetermined merge order:

1. **Review PR #195** and decide whether it should be refreshed to current state, superseded by a new checkpoint, or closed. Its content (in-repo memory/workqueue conventions) is worth having in some form; the July-14 snapshot itself is no longer current.
2. **Reconcile PR #180** into one canonical Founder Operating Manual — choose the home (product repo vs control plane vs its own repo), fold in `HANDOFF_COMPANY.md`, then disposition the PR (merge as-is, merge reworked, or close in favor of the manual).
3. **Complete PR #186's technical review** independently of its self-reported test results, then make the merge decision.
4. **Review PR #13** and make the founder architecture decisions (migration timing, production account, compute/frontend, database, storage, secrets/QBO keys, sessions, domain, AI-provider handling, retention, recovery objectives, budget, deployment approval). Merging #13 records the decisions as ADRs.
5. **Then update and merge this company digest** against the resolved state of steps 1–4 and the EDGAR run's status at that time — per the update protocol in [README.md](README.md).
