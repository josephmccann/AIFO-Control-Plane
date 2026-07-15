# AI.FO Legacy and Deprecation Candidates

Status: RECOMMENDATIONS ONLY — compiled 2026-07-14. **Nothing here has been executed.** No repository has been archived, renamed, deleted, merged, or deployed by this consolidation. Items marked "needs approval" require Joe's explicit sign-off.

## Repository-level

| Repository | Finding | Recommendation |
|---|---|---|
| **AI-CFO** | Original AI.FO MVP prototype ("VibeInput" / "CFO Reasoning Layer"); dormant since 2026-02-04; contains a hardcoded demo admin credential; holds unique founder assets (AI.FO pitch deck PDFs, founding PRD, Vibe Coding Inputs V1.0 spec, standards-layer/Policy Pack rationale, CrossReference scoring model) | 1) Extract the unique assets to a durable home (suggest: AI.FO-Demo `docs/heritage/` or the doctrine home chosen via PR #180). 2) Then **archive** the repo with a README pointer to AI.FO-Demo. Needs approval. |
| **A2A** | Empty (size 0, no branches, no commits; created 2026-04-30) | **Archive**, or delete only after explicit approval. Nothing to preserve. |
| **verifier** | Not AI.FO — verifies receipts for a separate "Axiom" project (polsia.app); zero cross-references either direction | **Leave unchanged**; exclude from AI.FO program documentation. No action. |
| **portfolio-brain / portfolio-brain-total-recall** | Already archived; unrelated hackathon projects | **Leave unchanged.** |
| **aifo-signal-validation-study** | GitHub **default branch is a stale trap**: `study/edgar-validation-build` frozen at 2026-06-23 while all real work (including the `prereg-v1` freeze) is on `master`. Open PR #1 wants to merge the abandoned branch and its body describes a superseded state | 1) Switch default branch to `master`. 2) Close PR #1 without merging. 3) Optionally delete the stale branch after re-pointing. Needs approval — the study's audit-trail discipline means branch surgery should be logged in its decision system. |

## Document- and artifact-level

### AI.FO-Demo
- **Dual physical checkouts:** CLAUDE.md/AGENTS.md, the nightly launchd job, and the study's engine pin all reference `/Users/joemccann/Desktop/aifo-demo-app`, while a second clone exists at `/Users/joemccann/code/AI.FO-Demo`. Two writable copies of the canonical product repo on one machine is drift risk. Recommend declaring one canonical local path and updating the docs/launchd/study-config references (coordinated change — needs approval since the nightly job and study pin depend on it).
- **~70 stale remote branches** (coverage waves, old fixes, telemetry repairs — most already merged or superseded). Recommend a documented branch-cleanup pass; do not delete `feature/top-five-value-adds-2026-07-10` (PR #186), `docs/founder-aifo-context` (#180), or `docs/checkpoint-before-shutdown-2026-07-14` (#195).
- **Root-level point-in-time review artifacts** (`ENGINE_AUDIT_*`, `HOTFIX_CAPEX_*`, `PR_2b/2c/3/3.1_*`, `WORKSTREAM2_*`, `WS2_*`): historical records living at repo root. Recommend moving to `docs/archive/` (pure `git mv`, no content edits).
- **`replit.md` is stale** (says "no Tailwind", "7 screens" vs README's Tailwind + 8 screens). Recommend updating or replacing with a pointer to README.md.
- **PR #195's checkpoint** lists PR #190 as open; #190 has since been closed unmerged (content folded into #180). Frozen checkpoint — do not edit; note here suffices.

### AIFO-Control-Plane
- **AWS baseline facts duplicated across ~7 documents** (README, memory/current-state, memory/deployment-status, two handoffs, deployment-readiness-review, SECURITY.md). Recommend electing `memory/current-state.md` + `memory/deployment-status.md` as the only fact-bearing files and reducing the rest to links (per SOURCE_OF_TRUTH_HIERARCHY.md). Docs-only change, but touches files the runtime session may read — sequence after that session merges.
- **Cost figures vary by basis** ($279.62 compute-only vs ~$291.27 all-in) without cross-labeling. Recommend one cost table in `docs/cost-model.md` with explicit bases.
- **Dated session handoffs** carry intentionally frozen stale markers ("PARKED — SAFE FOR CODEX CLI UPDATE"; "shellcheck unavailable" since fixed). Correct by convention — no action; readers should know handoffs are historical evidence.
- `docs/product-runtime-inventory.md` is slated to be superseded by the active runtime-architecture session — expected churn, not a defect.

### GetAIFO-site
- **No README.md, no AGENTS.md** — the only AI.FO repo without either. Recommend adding both (deployment, telemetry-consumption contract, claim-sourcing rules).
- **GitHub description says Next.js; the code is Vite + React.** Recommend fixing the description.
- `attached_assets/` — 11 raw Replit prompt/log dumps committed to the repo. Recommend deleting or moving to an archive folder.
- **Stale `sitemap.xml` lastmod dates** (April/June) vs code changes through 2026-06-22.
- **`SIGNALS_FALLBACK = 40` literal** (last verified 2026-06-11) — the one remaining hand-typed number; retire it or add a verification chore.
- `pages/privacy.tsx` hardcoded navy/lavender palette — orphan of the abandoned redesign; restyle to CSS variables.
- `.replit` provisions `postgresql-16` but the app uses only Airtable — unused module.
- 8 stale unmerged branches (3 abandoned lavender-redesign, 5 already-landed fix branches) — cleanup candidates.
- Two script directories (`script/` used, `scripts/` post-merge hook) — naming confusion; document or consolidate.

### aifo-telemetry
- README's "regenerated after every green nightly" is accurate but easy to misread as "every night"; history shows multi-day gaps (Jun 18–22, Jul 8–9, Jul 11–12). Recommend one clarifying sentence in README.
- 2026-07-13 anomaly: a second same-day mirror **lowered** counts without advancing `lastRunId` — worth a one-line explanation in the mirror job or README, since this repo's whole purpose is public auditability.

### aifo-signal-validation-study (doc-level, beyond the default-branch fix)
- `README.md` on `master` still says "Nothing here touches live scoring yet / pre-registration build in progress" — superseded by the 07-09 freeze and real-data collection. Update after logging.
- `CC_REPAIR_REPORT.md` and `DECISIONS_WAITING_ON_JOE_2026-07-05.md` state no `prereg-v1` tag exists — true when written, now stale; supersede with a dated addendum rather than editing (matches the study's point-in-time discipline).
- `dpo-deterioration` category divergence (engine source says WORKING_CAPITAL; committed manifest says LEVERAGE) — tracked "honestly red" by design; listed here so it isn't lost.

## Explicitly NOT deprecation candidates

- **aifo-telemetry** (public history is the product's trust record — never rewrite it), **GetAIFO-site** (canonical site, merely dormant), **AI.FO-Demo**, **AIFO-Control-Plane**, and the **study repo** itself: all retained.
- No file in `memory/`, `workqueue/`, existing ADRs, AWS architecture/security docs, Terraform, or product code was modified by this consolidation, and none is recommended for deletion.
