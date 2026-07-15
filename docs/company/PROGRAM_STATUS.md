# AI.FO Program Status

Status: CURRENT — snapshot as of 2026-07-14
Sources: repository evidence only (commits, PRs, and each repo's own docs); see [README.md](README.md) for the exact commits audited.

---

## 1. Product (AI.FO-Demo)

### What works (merged on `master`)
- Deterministic financial engine with a registry-backed catalog of **40 signals** across **13 industry tracks**; signal methodology centralized in `docs/SIGNAL_METHODOLOGY.md`.
- Seven report parsers (P&L, Balance Sheet, AR, AP, Sales, Bank, Transaction Detail) and CSV upload ingestion.
- QuickBooks Online **sandbox** OAuth sync with field-level provenance.
- Server-owned AI narrative layer: `POST /api/ai/generate` builds the snapshot server-side; the AI writes the memo but "cannot change the numbers." The legacy raw-prompt route was removed and is test-guarded.
- Eight demo screens, admin panel, invite-code auth, sealed board package (#184), trust evidence console (#183), QBO self-serve recovery (#182), centralized public trust copy (#181).
- Public telemetry pipeline: `generate-telemetry.js` (refuses on dirty tree or red suite) → `telemetry.json` → mirrored to the public `aifo-telemetry` repo → served at `/api/telemetry` → consumed by getaifo.com.
- Quality signal as of 2026-07-14 telemetry: 13,477 engine tests + 987 API tests, 0 failures; 21,851 classified assertions (note the mix: 19,648 snapshot vs 1,780 property vs 30 sourcing); 45 nightly pressure-test runs over 900 synthetic companies since 2026-04-28.

### What is deployed
- `https://demo.getaifo.com` on Replit autoscale. Production storage on Cloudflare R2. Nightly pressure test runs via launchd on Joe's Mac (02:00 PT) with a GitHub Actions dead-man monitor.
- Open question recorded in the repo: the deployed frontend bundle may lag current `master` (redeploy decision open; telemetry/deadman do not require it).

### What remains in open PRs (not on master)
- **PR #186** — commercial account surface, feature-flagged external-connectors framework with a Stripe billing adapter, DB migration `0011_external_connectors.sql`. The only open *code* PR; self-reports green suites; awaiting review/merge decision.
- **PR #180** — constitution, founder-context, and operating-system docs plus machine-readable `.aifo/*.yaml` context. Explicitly working drafts; awaiting founder review.
- **PR #195** — session-checkpoint docs (`memory/`, `workqueue/`, session handoff, CHANGELOG). Intentionally held ("do not merge during shutdown unless explicitly requested").

### Beta-ready vs not production-ready
- **Beta-ready today:** the demo/sandbox validation path — engine, QBO sandbox sync, AI memo generation, trust surfaces — is green and demoable end to end.
- **Not production-ready.** `docs/PRODUCTION_READINESS_PLAN.md` defines seven phases, all unstarted: (1) production QBO OAuth, (2) deployment parity, (3) operational monitoring, (4) real-company datasets (recruit 3–5 consenting companies), (5) browser E2E, (6) security/privacy review, (7) commercial account surface (PR #186 is a down payment on this). **No real customer financial data is handled anywhere yet.**
- Known product-data gap: QBO sandbox fires 11 of 40 signals (28 evaluated); full 40-signal sandbox coverage needs companion seed data — an open workstream.

## 2. Infrastructure (AIFO-Control-Plane)

### Deployed (verified in AWS account `350480401760`, us-west-2)
- Terraform remote state (encrypted, versioned, locked), GitHub OIDC provider with separate plan/apply roles — the apply role is deliberately state-access-only (no mutation policy), and there is **no apply workflow**; applies are manual and human-approved.
- Multi-region CloudTrail management events; encrypted Session Manager logging (customer-managed KMS, 30-day retention).
- One SSM-only, zero-ingress EC2 operator host (`i-0254a9e2fcbcdebd7`, m7i-flex.2xlarge, currently **stopped**) with EventBridge Scheduler start/stop automation.
- State verified clean: local and CI `terraform plan` report 0 to add/change/destroy.

### Planned only (not deployed)
- Product runtime hosting, product database, product secrets management, R2→S3 storage migration, domain/TLS/QBO callback migration, apply-workflow automation. All explicitly deferred pending founder decisions OD-005…OD-008 and OD-012.
- A manual $250/month AWS budget exists outside Terraform (module present but disabled).

### What hosts the product today
- **Replit**, not AWS: `demo.getaifo.com` (product demo) and `getaifo.com` (marketing site) are both Replit autoscale deployments. The control plane's own docs are explicit: "Treat AWS product hosting as a future migration, not current fact."
- Nightly operations run from Joe's Mac (launchd) — a single-machine dependency worth knowing about.

### What remains undecided
- OD-005: whether/when the product runtime moves to AWS. An active session (branch `codex/product-runtime-architecture-decision-package`, docs-only, local) is preparing the founder decision package; its working recommendation is a gated migration to an AWS-managed runtime *before* accepting real customer financial data, keeping Replit as demo/rehearsal.
- OD-006 product database architecture; OD-007 Cloudflare R2 vs S3; OD-008 product secrets manager/rotation; OD-012 GitHub plan upgrade vs alternative apply-approval boundary. All marked blocking.

## 3. Research and validation (aifo-signal-validation-study)

### Built
- Full EDGAR validation pipeline (Study A): universe construction, matching, fire rules, stats, event study, negative controls, threshold-attack robustness arm; ~23 test files; threshold-provenance audit of all 236 firing thresholds (zero calibrated on study-window companies; 180 remain unattributed inline — flagged, not hidden).
- Preregistration **frozen and tagged `prereg-v1` on 2026-07-09, before any scored run**. Primary endpoint: 12-month matched case-vs-control fire-rate gap, success = bootstrap 95% CI lower bound ≥ 0.10, on a three-leg ex-going-concern union (Chapter 11 + strict distress delisting + Item 2.04 actual default), cadence-safe base-signals-only headline.

### Run (pre-score only)
- Real EDGAR universe constructed (~833-company population; burned-pilot exclusion verified); fire-capability coverage runs over ~166–169 companies; 48-filing iXBRL parsing sweep. All artifacts banner-marked `PROVISIONAL-PENDING-CC-RE-VERIFICATION`.
- Governance worth noting for diligence: an entire outcome leg (distressed take-privates) was built, then **pulled** after an 8-seat adversarial cold re-verification refuted 51.9% of its companies — with a deliberately-red QA test left as the record of the removal.

### Not run
- **The primary scored discrimination run.** `docs/METHODS_AND_RESULTS.md` is a locked shell with every result cell TBD. Post-freeze commits through 2026-07-14 are SEC-fetch/collection-path repairs preparing for it. Blockers: matched-set re-emission under the 07-09 match-input rulings, then Joe's single-shot live-run trigger.

### Claims currently supported
- **None empirical.** What exists is methodology, preregistration discipline, provenance, and feasibility analysis. Feasibility itself has a flagged sensitivity: under the strictest cadence-safe reading without the OCF-YTD admission, fire-capable N = 0 — the headline's feasibility depends on that contested ruling.
- Anything public that implies "validated against real bankruptcies" would be an overclaim today. Nothing on getaifo.com currently makes that claim — keep it that way until the primary run executes.

## 4. Marketing and public trust

### Canonical surfaces
- **Site:** GetAIFO-site → `getaifo.com` (Replit). Dormant since 2026-06-22 but functioning.
- **Public telemetry:** `aifo-telemetry` (public GitHub) → served through `demo.getaifo.com/api/telemetry` → rendered on `/how-we-test` and the System·Proof panel. Fresh as of 2026-07-14. Numbers are fetched at runtime, never hand-typed (a June refactor exists specifically because hand-typed numbers had drifted); on fetch failure the site renders "—" rather than stale values.
- **Status page:** `/status` reads the Airtable nightly ledger through an anonymizing public-projection boundary (hardened 2026-06-22 against internal-data leakage).

### Claims requiring reconciliation
1. "The product works" / "The product is built" (site) sits next to "We're onboarding our first cohort of real organizations now" — accurate only with the demo/synthetic caveat the site itself provides; keep the pairing intact in any copy edits.
2. "Regenerated after every green nightly run" — true as worded, but the public commit history shows multi-day gaps; a red or skipped night silently pauses the record. The 2026-07-13 double-commit (counts went *down* without the run ledger advancing) is a small integrity wobble worth explaining or fixing in the mirror job.
3. One hardcoded fallback remains on the site (`SIGNALS_FALLBACK = 40`, last verified 2026-06-11) — the exact pattern the live-telemetry refactor was built to eliminate.
4. No validation-study claims exist publicly yet — correct, and must remain so until Study A's primary run produces results.

### Visual and messaging work
- None active. The April "light lavender" redesign was explored on three branches and abandoned (main keeps the dark theme; `privacy.tsx` still carries orphaned hardcoded palette colors). Inline "coming next" roadmap on the site: cohort onboarding, board-packet Excel export, Plaid, multi-company portfolio view.

## 5. Company operations

### Active workstreams (detail in [ACTIVE_WORKSTREAMS.md](ACTIVE_WORKSTREAMS.md))
1. Product feature delivery — PR #186 (AI.FO-Demo), awaiting review.
2. Founder/constitution governance docs — PR #180 (AI.FO-Demo), awaiting founder review.
3. Product runtime architecture decision package — Codex session, Control-Plane worktree `codex/product-runtime-architecture-decision-package` (docs-only, local).
4. Study A live-run readiness — validation-study `master`; blocked on matched-set re-emission and Joe's trigger.
5. Nightly telemetry operations — launchd + deadman; steady state, recent integrity fixes (#187–#189).
6. Control-plane operational refinement — workqueue empty ("In Progress: None"); blocked items WQ-023 (product runtime hosting) and WQ-035 (apply automation) await founder decisions.
7. This consolidation — Control-Plane worktree `claude/company-program-state-consolidation-2026-07`, new files under `docs/company/` only.

### Ownership
- All gates route to **Joe** (sole founder; first engineering hire not yet made). Executing agents: Claude Code and Codex sessions, plus independent adversarial "fresh reader" agents in the study. Airtable is the operational ledger (nightly runs) and the study's decision log.

### Branch and worktree isolation
- Control-Plane: worktrees under `.worktrees/` per session; branch prefixes `agent/*`, `docs/*`, `codex/*`, `claude/*`. Two active worktrees: the runtime-architecture session and this consolidation — their file sets do not overlap.
- AI.FO-Demo: branch-per-workstream convention (~70 remote branches, most stale); prescribed physical checkout for concurrency is `Desktop/aifo-demo-app`.
- Study: real work on `master`; default branch abandoned (needs re-pointing).

### Decision dependencies and merge sequencing (current queue)
1. AI.FO-Demo PR #195 (checkpoint docs) — mergeable whenever the hold lifts; disjoint paths from the others.
2. AI.FO-Demo PR #180 (constitution drafts) — founder review; establishes doctrine home.
3. AI.FO-Demo PR #186 (connectors/Stripe) — code review; watch small textual overlap with #195 (README/docs edits).
4. Control-Plane runtime decision package — session completes → founder decision packet → resolves OD-005…OD-008 → unblocks WQ-023 and any product-runtime Terraform.
5. Study A — matched-set re-emission → sealed-set manifest → Joe's single-shot scored run → METHODS_AND_RESULTS filled → only then any public validation claim.
