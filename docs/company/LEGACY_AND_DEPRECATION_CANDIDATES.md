# AI.FO Legacy and Deprecation Candidates

> **Digest metadata**
> - Audit snapshot: 2026-07-14 · pinned commits: see [README.md](README.md) evidence table
> - Statement classes: **[FACT]** verified current fact · **[PR]** open-PR proposal · **[RUN]** active runtime state · **[REC]** recommendation · **[JOE]** founder decision
> - This entire document is **[REC] — recommendations only. Nothing here has been executed.** No repository has been archived, renamed, deleted, merged, or deployed by this consolidation. Items marked [JOE] require explicit founder sign-off.
> - PR and active-run state is volatile — refresh from the [canonical dynamic sources](README.md#canonical-dynamic-sources-always-fresher-than-this-digest) before acting.

## Repository-level

| Repository | Finding [FACT] | Recommendation [REC] |
|---|---|---|
| **AI-CFO** | Original AI.FO MVP prototype ("VibeInput" / "CFO Reasoning Layer"); dormant since 2026-02-04; contains a hardcoded demo admin credential; holds unique founder assets (AI.FO pitch deck PDFs, founding PRD, Vibe Coding Inputs V1.0 spec, standards-layer/Policy Pack rationale, CrossReference scoring model) | 1) Extract the unique assets to a durable home (a natural fit: the future Founder Operating Manual home, see SOURCE_OF_TRUTH_HIERARCHY.md). 2) Then **archive** the repo with a README pointer to AI.FO-Demo. [JOE] |
| **A2A** | Empty (size 0, no branches, no commits; created 2026-04-30) | **Archive**, or delete only after explicit approval. Nothing to preserve. [JOE] |
| **verifier** | Not AI.FO — verifies receipts for a separate "Axiom" project (polsia.app); zero cross-references either direction | **Leave unchanged**; exclude from AI.FO program documentation. No action. |
| **portfolio-brain / portfolio-brain-total-recall** | Already archived; unrelated hackathon projects | **Leave unchanged.** |
| **aifo-signal-validation-study** | GitHub **default branch is a stale trap**: `study/edgar-validation-build` frozen at 2026-06-23 while all real work (including the `prereg-v1` freeze and the in-flight collection tooling) is on `master`. Open PR #1 wants to merge the abandoned branch and its body describes a superseded state | 1) Switch default branch to `master`. 2) Close PR #1 without merging. 3) Optionally delete the stale branch after re-pointing. [JOE] — the study's audit-trail discipline means branch surgery should be logged in its decision system, and preferably not performed while the live collection run is in flight. |

## Document- and artifact-level

### AI.FO-Demo
- **[FACT] Dual physical checkouts:** CLAUDE.md/AGENTS.md, the nightly launchd job, and the study's engine pin all reference `/Users/joemccann/Desktop/aifo-demo-app`, while a second clone exists at `/Users/joemccann/code/AI.FO-Demo`. Two writable copies of the canonical product repo on one machine is drift risk. [REC] Declare one canonical local path and update the docs/launchd/study-config references — a coordinated change [JOE], since the nightly job and the study pin depend on it; do not touch the study's pin while the collection run is active.
- **[FACT] ~70 stale remote branches** (coverage waves, old fixes, telemetry repairs — most already merged or superseded). [REC] A documented branch-cleanup pass; do not delete `docs/founder-aifo-context` (#180) or `docs/checkpoint-before-shutdown-2026-07-14` (#195) while their PRs are open. `feature/top-five-value-adds-2026-07-10` merged as PR #186 (`3329c99`) and its branch is now an ordinary cleanup candidate.
- **[FACT] Root-level point-in-time review artifacts** (`ENGINE_AUDIT_*`, `HOTFIX_CAPEX_*`, `PR_2b/2c/3/3.1_*`, `WORKSTREAM2_*`, `WS2_*`): historical records living at repo root. [REC] Move to `docs/archive/` (pure `git mv`, no content edits).
- **[FACT] `replit.md` is stale** (says "no Tailwind", "7 screens" vs README's Tailwind + 8 screens). [REC] Update or replace with a pointer to README.md.
- **[FACT] PR #195's checkpoint** lists PR #190 as open; #190 has since been closed unmerged (content folded into #180), and the checkpoint predates PR #13 and the live EDGAR collection. This supports the "refresh, supersede, or close" disposition recorded in ACTIVE_WORKSTREAMS.md — frozen checkpoints are never edited in place.

### AIFO-Control-Plane
- **[FACT] AWS baseline facts duplicated across ~7 documents** (README, memory/current-state, memory/deployment-status, two handoffs, deployment-readiness-review, SECURITY.md). [REC] Elect `memory/current-state.md` + `memory/deployment-status.md` as the only fact-bearing files and reduce the rest to links (per SOURCE_OF_TRUTH_HIERARCHY.md). Docs-only change, but PR #13 comprehensively updates several of these files on its branch — sequence this cleanup **after** PR #13's disposition.
- **[FACT] Cost figures vary by basis** ($279.62 compute-only vs ~$291.27 all-in) without cross-labeling; PR #13 adds a further current/hybrid/AWS cost model. [REC] One cost table in `docs/cost-model.md` with explicit bases, reconciled as part of PR #13's review.
- **[FACT] Dated session handoffs** carry intentionally frozen stale markers ("PARKED — SAFE FOR CODEX CLI UPDATE"; "shellcheck unavailable" since fixed). Correct by convention — no action; readers should know handoffs are historical evidence.
- **[FACT]** `docs/product-runtime-inventory.md` is superseded by PR #13's comprehensive runtime inventory — expected churn, resolved by PR #13's merge decision, not a defect.

### GetAIFO-site
- **[FACT] No README.md, no AGENTS.md** — the only AI.FO repo without either. [REC] Add both (deployment, telemetry-consumption contract, claim-sourcing rules).
- **[FACT] GitHub description says Next.js; the code is Vite + React.** [REC] Fix the description.
- **[FACT]** `attached_assets/` — 11 raw Replit prompt/log dumps committed to the repo. [REC] Delete or move to an archive folder.
- **[FACT] Stale `sitemap.xml` lastmod dates** (April/June) vs code changes through 2026-06-22. [REC] Regenerate.
- **[FACT] `SIGNALS_FALLBACK = 40` literal** (last verified 2026-06-11) — the one remaining hand-typed number. [REC] Retire it or add a verification chore.
- **[FACT]** `pages/privacy.tsx` hardcoded navy/lavender palette — orphan of the abandoned redesign. [REC] Restyle to CSS variables.
- **[FACT]** `.replit` provisions `postgresql-16` but the app uses only Airtable. [REC] Remove the unused module.
- **[FACT]** 8 stale unmerged branches (3 abandoned lavender-redesign, 5 already-landed fix branches). [REC] Cleanup candidates.
- **[FACT]** Two script directories (`script/` used, `scripts/` post-merge hook) — naming confusion. [REC] Document or consolidate.

### aifo-telemetry
- **[FACT]** README's "regenerated after every green nightly" is accurate but easy to misread as "every night"; history shows multi-day gaps (Jun 18–22, Jul 8–9, Jul 11–12). [REC] One clarifying sentence in README.
- **[FACT]** 2026-07-13 anomaly: a second same-day mirror **lowered** counts without advancing `lastRunId`. [REC] A one-line explanation in the mirror job or README — this repo's whole purpose is public auditability.

### aifo-signal-validation-study (doc-level, beyond the default-branch fix)
- **[FACT]** `README.md` on `master` still says "Nothing here touches live scoring yet / pre-registration build in progress" — superseded by the 07-09 freeze, real-data collection, and now the authorized live run. [REC] Update after logging, per the study's discipline.
- **[FACT]** `CC_REPAIR_REPORT.md` and `DECISIONS_WAITING_ON_JOE_2026-07-05.md` state no `prereg-v1` tag exists — true when written, now stale. [REC] Supersede with a dated addendum rather than editing (matches the study's point-in-time discipline).
- **[FACT]** `dpo-deterioration` category divergence (engine source says WORKING_CAPITAL; committed manifest says LEVERAGE) — tracked "honestly red" by design; listed here so it isn't lost.

## Explicitly NOT deprecation candidates

- **aifo-telemetry** (public history is the product's trust record — never rewrite it), **GetAIFO-site** (canonical site, merely dormant), **AI.FO-Demo**, **AIFO-Control-Plane**, and the **study repo** itself: all retained.
- No file in `memory/`, `workqueue/`, existing ADRs, AWS architecture/security docs, Terraform, or product code was modified by this consolidation, and none is recommended for deletion.
