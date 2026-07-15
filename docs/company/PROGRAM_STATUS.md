# AI.FO Program Status

> **Digest metadata**
> - Audit snapshot: 2026-07-14 · pinned commits: see [README.md](README.md) evidence table
> - Statement classes: **[FACT]** verified current fact · **[PR]** open-PR proposal · **[RUN]** active runtime state · **[REC]** recommendation · **[JOE]** founder decision
> - PR and active-run state is volatile — refresh from the [canonical dynamic sources](README.md#canonical-dynamic-sources-always-fresher-than-this-digest) before acting.

Sources: repository evidence only (commits, PRs, and each repo's own docs), plus explicitly-marked runtime state reported at the 2026-07-14 PT checkpoint.

---

## 1. Product (AI.FO-Demo)

### What works (merged on `master`) — all [FACT]
- Deterministic financial engine with a registry-backed catalog of **40 signals** across **13 industry tracks**; signal methodology centralized in `docs/SIGNAL_METHODOLOGY.md`.
- Seven report parsers (P&L, Balance Sheet, AR, AP, Sales, Bank, Transaction Detail) and CSV upload ingestion.
- QuickBooks Online **sandbox** OAuth sync with field-level provenance.
- Server-owned AI narrative layer: `POST /api/ai/generate` builds the snapshot server-side; the AI writes the memo but "cannot change the numbers." The legacy raw-prompt route was removed and is test-guarded.
- Eight demo screens, admin panel, invite-code auth, sealed board package (#184), trust evidence console (#183), QBO self-serve recovery (#182), centralized public trust copy (#181).
- **Merged 2026-07-15 02:11 UTC (PR #186, merge commit `3329c99` — the current canonical product baseline):** commercial account surface, feature-flagged external-connectors framework with a Stripe billing adapter, DB migration `0011_external_connectors.sql`. **Connector functionality remains disabled pending deployment validation and explicit configuration** — merged into the baseline, not yet active anywhere.
- Public telemetry pipeline: `generate-telemetry.js` (refuses on dirty tree or red suite) → `telemetry.json` → mirrored to the public `aifo-telemetry` repo → served at `/api/telemetry` → consumed by getaifo.com.
- Quality signal as of 2026-07-14 telemetry: 13,477 engine tests + 987 API tests, 0 failures; 21,851 classified assertions (note the mix: 19,648 snapshot vs 1,780 property vs 30 sourcing); 45 nightly pressure-test runs over 900 synthetic companies since 2026-04-28.

### What is deployed — [FACT]
- `https://demo.getaifo.com` on Replit autoscale. Production storage on Cloudflare R2. Nightly pressure test runs via launchd on Joe's Mac (02:00 PT) with a GitHub Actions dead-man monitor.
- **The live demo has not yet been updated to baseline `3329c99`** (it predates the PR #186 merge); deployment and telemetry refresh are pending, and the **post-merge demo deployment workstream is active**. Connector activation is separately gated behind deployment validation and explicit configuration.

### Customer-data position — [FACT]
The product has functioning QBO **sandbox** and CSV ingestion. It does **not currently host or process production customer financial data**: demo companies are fictional, QBO runs against the Intuit sandbox, and nightly runs use synthetic companies. Existing protections: QBO tokens AES-256-encrypted at rest; telemetry denylist-scrubbed of tokens, IDs, names, and accounting values.

### What remains in open PRs (not on master) — all [PR]; refresh state before deciding
- **PR #180** — constitution, founder-context, and operating-system docs plus machine-readable `.aifo/*.yaml` context. **Valuable working-draft source material**, explicitly non-behavioral. [REC] Reconcile into one canonical Founder Operating Manual before or as part of its final disposition (see SOURCE_OF_TRUTH_HIERARCHY.md). Disposition is [JOE].
- **PR #195** — session-checkpoint docs (`memory/`, `workqueue/`, session handoff, CHANGELOG). **A July 14 shutdown checkpoint that may now require refresh, supersession, or closure**: activity since it was written (the PR #186 merge, Control-Plane PR #13, the live EDGAR collection) has changed the state it froze. Not recommended for automatic merge. Disposition is [JOE].
- (PR #186 no longer belongs in this list — it merged 2026-07-15 02:11 UTC as `3329c99`; see "What works" above.)

### Beta-ready vs not production-ready
- **[FACT] Beta-ready today:** the demo/sandbox validation path — engine, QBO sandbox sync, AI memo generation, trust surfaces — is green and demoable end to end.
- **[FACT] Not production-ready.** `docs/PRODUCTION_READINESS_PLAN.md` defines seven phases: (1) production QBO OAuth, (2) deployment parity, (3) operational monitoring, (4) real-company datasets (recruit 3–5 consenting companies), (5) browser E2E, (6) security/privacy review, (7) commercial account surface — the merged PR #186 is a down payment on phase 7 (code in the baseline, connectors still gated off); phases 1–6 remain unstarted.
- **[FACT]** Known product-data gap: QBO sandbox fires 11 of 40 signals (28 evaluated); full 40-signal sandbox coverage needs companion seed data — an open workstream.

## 2. Infrastructure (AIFO-Control-Plane)

### Deployed (verified in AWS account `350480401760`, us-west-2) — all [FACT]
- Terraform remote state (encrypted, versioned, locked), GitHub OIDC provider with separate plan/apply roles — the apply role is deliberately state-access-only (no mutation policy), and there is **no apply workflow**; applies are manual and human-approved.
- Multi-region CloudTrail management events; encrypted Session Manager logging (customer-managed KMS, 30-day retention).
- One SSM-only, zero-ingress EC2 operator host (`i-0254a9e2fcbcdebd7`, m7i-flex.2xlarge, currently **stopped**) with EventBridge Scheduler start/stop automation.
- State verified clean: local and CI `terraform plan` report 0 to add/change/destroy.

### Proposed (open PR #13 — not canonical until reviewed and merged) — [PR]
**PR #13 "docs: propose product runtime architecture decision package"** (draft) delivers: current runtime inventory with 17 principal data flows, beta-cohort requirements, weighted three-option analysis, proposed reference architecture (dedicated production AWS member account; CloudFront/WAF + private S3 frontend; two ECS Fargate API tasks behind an ALB; RDS PostgreSQL Multi-AZ; S3 product objects; PostgreSQL sessions; Secrets Manager/task roles; minimal CloudWatch/CloudTrail/GuardDuty), STRIDE threat model, migration gates MR-01…MR-33, current/hybrid/AWS cost model, proposed ADR-0011…ADR-0022, and a founder decision packet. Its recommendation — complete a gated AWS-managed migration **before** accepting real first-cohort customer data, with the Replit runtime remaining synthetic demo/rehearsal only — is **a proposal awaiting review** [JOE].

### Planned only (not deployed) — [FACT]
- Product runtime hosting, product database, product secrets management, R2→S3 storage migration, domain/TLS/QBO callback migration, apply-workflow automation. All explicitly deferred pending founder decisions OD-005…OD-008 and OD-012 [JOE] — now with PR #13's packet as the proposed decision input.
- A manual $250/month AWS budget exists outside Terraform (module present but disabled).

### What hosts the product today — [FACT]
- **Replit**, not AWS: `demo.getaifo.com` (product demo) and `getaifo.com` (marketing site) are both Replit autoscale deployments. The control plane's own docs are explicit: "Treat AWS product hosting as a future migration, not current fact."
- Nightly operations run from Joe's Mac (launchd) — a single-machine dependency worth knowing about.

### What remains undecided — [JOE]
- OD-005 whether/when the product runtime moves to AWS; OD-006 product database architecture; OD-007 Cloudflare R2 vs S3; OD-008 product secrets manager/rotation; OD-012 GitHub plan upgrade vs alternative apply-approval boundary. All marked blocking. PR #13 proposes answers to most of these; none is decided until Joe rules and the PR merges.

## 3. Research and validation (aifo-signal-validation-study)

### Built — [FACT]
- Full EDGAR validation pipeline (Study A): universe construction, matching, fire rules, stats, event study, negative controls, threshold-attack robustness arm; ~23 test files; threshold-provenance audit of all 236 firing thresholds (zero calibrated on study-window companies; 180 remain unattributed inline — flagged, not hidden).
- Preregistration **frozen and tagged `prereg-v1` on 2026-07-09, before any scored run, and unchanged since**. Primary endpoint: 12-month matched case-vs-control fire-rate gap, success = bootstrap 95% CI lower bound ≥ 0.10, on a three-leg ex-going-concern union (Chapter 11 + strict distress delisting + Item 2.04 actual default), cadence-safe base-signals-only headline.

### Run so far
- **[FACT] Pre-score analyses on real EDGAR data:** universe construction (burned-pilot exclusion verified); fire-capability coverage runs; 48-filing iXBRL parsing sweep. All artifacts banner-marked `PROVISIONAL-PENDING-CC-RE-VERIFICATION`.
- **[RUN] Active now** (reported at the 2026-07-14 PT checkpoint; runtime state, not in the repo — re-verify before acting): the **authorized full live collection over 8,215 registered companies is running, approximately 36% complete** at the latest checkpoint.
- **[FACT] Governance note for diligence:** an entire outcome leg (distressed take-privates) was built, then **pulled** after an 8-seat adversarial cold re-verification refuted 51.9% of its companies — with a deliberately-red QA test left as the record of the removal.

### Not yet occurred — [FACT]
- **Real-company scoring has not occurred.** `docs/METHODS_AND_RESULTS.md` is a locked shell with every result cell TBD.

### Authorization state — [JOE, standing]
- Joe has **conditionally authorized** the run to proceed automatically through scoring and measurement **only if all documented technical and methodological gates pass**. Joe is required again **only if a defined stop condition occurs**. The preregistration remains frozen; any method change would require a logged amendment.

### Claims currently supported
- **[FACT] None empirical.** What exists is methodology, preregistration discipline, provenance, feasibility analysis, and an in-flight collection. Feasibility has a flagged sensitivity: under the strictest cadence-safe reading without the OCF-YTD admission, fire-capable N = 0 — the headline's feasibility depends on that contested ruling.
- [REC] Anything public that implies "validated against real bankruptcies" would be an overclaim today. Nothing on getaifo.com currently makes that claim — keep it that way until scoring and measurement complete under the preregistered gates.

## 4. Marketing and public trust

### Canonical surfaces — [FACT]
- **Site:** GetAIFO-site → `getaifo.com` (Replit). Dormant since 2026-06-22 but functioning.
- **Public telemetry:** `aifo-telemetry` (public GitHub) → served through `demo.getaifo.com/api/telemetry` → rendered on `/how-we-test` and the System·Proof panel. Fresh as of 2026-07-14. Numbers are fetched at runtime, never hand-typed (a June refactor exists specifically because hand-typed numbers had drifted); on fetch failure the site renders "—" rather than stale values.
- **Status page:** `/status` reads the Airtable nightly ledger through an anonymizing public-projection boundary (hardened 2026-06-22 against internal-data leakage).

### Claims requiring reconciliation — [FACT] findings, [REC] dispositions
1. "The product works" / "The product is built" (site) sits next to "We're onboarding our first cohort of real organizations now" — accurate only with the demo/synthetic caveat the site itself provides; keep the pairing intact in any copy edits.
2. "Regenerated after every green nightly run" — true as worded, but the public commit history shows multi-day gaps; a red or skipped night silently pauses the record. The 2026-07-13 double-commit (counts went *down* without the run ledger advancing) is a small integrity wobble worth explaining or fixing in the mirror job.
3. One hardcoded fallback remains on the site (`SIGNALS_FALLBACK = 40`, last verified 2026-06-11) — the exact pattern the live-telemetry refactor was built to eliminate.
4. No validation-study claims exist publicly yet — correct, and must remain so until Study A's scoring and measurement complete under the preregistered gates.

### Visual and messaging work — [FACT]
- None active. The April "light lavender" redesign was explored on three branches and abandoned (main keeps the dark theme; `privacy.tsx` still carries orphaned hardcoded palette colors). Inline "coming next" roadmap on the site: cohort onboarding, board-packet Excel export, Plaid, multi-company portfolio view.

## 5. Company operations

### Active workstreams (detail in [ACTIVE_WORKSTREAMS.md](ACTIVE_WORKSTREAMS.md))
1. [FACT] Post-merge demo deployment — deploy and validate product baseline `3329c99` on the live Replit demo; telemetry refresh pending; connector activation separately gated.
2. [PR] Founder/constitution working drafts — PR #180 (AI.FO-Demo), pending reconciliation into a Founder Operating Manual.
3. [PR] Product runtime architecture decision package — PR #13 (AIFO-Control-Plane, draft), pending founder review.
4. [RUN] Study A live collection — running (~36% at checkpoint), conditionally authorized through scoring/measurement gates.
5. [FACT] Nightly telemetry operations — launchd + deadman; steady state, recent integrity fixes (#187–#189).
6. [FACT] Control-plane operational refinement — workqueue empty ("In Progress: None"); blocked items WQ-023 (product runtime hosting) and WQ-035 (apply automation) await founder decisions.
7. This consolidation — Control-Plane worktree `claude/company-program-state-consolidation-2026-07`, new files under `docs/company/` only.

### Ownership — [FACT]
- All gates route to **Joe** (sole founder; first engineering hire not yet made). Executing agents: Claude Code and Codex sessions, plus independent adversarial "fresh reader" agents in the study. Airtable is the operational ledger (nightly runs) and the study's decision log.

### Branch and worktree isolation — [FACT]
- Control-Plane: worktrees under `.worktrees/` per session; branch prefixes `agent/*`, `docs/*`, `codex/*`, `claude/*`. Two active worktrees: the runtime-architecture session (now PR #13) and this consolidation — their file sets do not overlap.
- AI.FO-Demo: branch-per-workstream convention (~70 remote branches, most stale); prescribed physical checkout for concurrency is `Desktop/aifo-demo-app`.
- Study: real work on `master`; default branch abandoned (needs re-pointing [JOE]).

### Decision sequence — [REC]; each step is [JOE]
This is a sequence of decisions, not a predetermined merge order:
1. **PR #195:** determine its disposition — refresh, supersede, or close; its July-14 checkpoint no longer matches current state (PR #186 merged, PR #13 open, EDGAR collection running).
2. **PR #180:** reconcile the working drafts into one canonical Founder Operating Manual (home and format are Joe's call), then disposition the PR accordingly.
3. **Product baseline `3329c99`:** resolve and validate its deployment to the live demo (including telemetry refresh); connector activation remains separately gated on validation plus explicit configuration.
4. **PR #13:** review the runtime decision packet and make the required founder architecture decisions (OD-005…OD-008, OD-012); merging the PR records them.
5. **This digest:** refresh and review against the resolved state of 1–4 (and the study run's status at that time), then merge.
6. **Production-prerequisite hardening:** begin the PRODUCTION_READINESS_PLAN phases (production QBO OAuth, monitoring, real-company datasets, security/privacy review) against the settled baseline.
7. **Visual-foundation implementation:** begin after the deployment baseline is settled.
