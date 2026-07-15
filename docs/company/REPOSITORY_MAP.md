# AI.FO Repository Map

> **Digest metadata**
> - Audit snapshot: 2026-07-14 · pinned commits: see [README.md](README.md) evidence table
> - Statement classes: **[FACT]** verified current fact · **[PR]** open-PR proposal · **[RUN]** active runtime state · **[REC]** recommendation · **[JOE]** founder decision
> - PR and active-run state is volatile — refresh from the [canonical dynamic sources](README.md#canonical-dynamic-sources-always-fresher-than-this-digest) before acting.

Rule: repository evidence overrides repository names and prior assumptions. Every classification below cites what the repository itself says or shows.

## Summary table

| Repository | Visibility | Default branch | Canonicality [FACT] | Activity at audit [FACT] | Recommended action [REC] |
|---|---|---|---|---|---|
| AI.FO-Demo | Private | `master` | **Canonical — product** | Active (nightly automation daily; PR #186 merged 2026-07-15 UTC → baseline `3329c99`; 2 open PRs) | Retain |
| AIFO-Control-Plane | Private | `main` | **Canonical — AWS infrastructure** | Active (11 PRs merged 2026-07-14/15; PR #13 open draft) | Retain |
| GetAIFO-site | Private | `main` | **Canonical — public marketing site** | Dormant since 2026-06-22 (~3 weeks) | Retain + document |
| aifo-telemetry | **Public** | `main` | **Canonical — public telemetry artifact** | Active (bot-mirrored; fresh 2026-07-14) | Retain |
| aifo-signal-validation-study | Private | `study/edgar-validation-build` (**stale — real work on `master`**) | **Canonical — research (Study A)** | Active (master commits through 2026-07-14; live collection run in progress) | Retain + fix default branch [JOE] |
| AI-CFO | Private | `main` | Legacy (original MVP prototype) | Dormant since 2026-02-04 | Extract unique assets, then archive [JOE] |
| A2A | Private | `main` (no branches) | Empty | Never populated (created 2026-04-30, size 0) | Archive or delete [JOE] |
| verifier | Public | `main` | Not AI.FO (separate "Axiom" project) | Dormant since 2026-05-29 | Leave unchanged; exclude from AI.FO docs |
| portfolio-brain / portfolio-brain-total-recall | Private, **archived** | `main` | Not AI.FO (hackathon artifacts) | Archived (2026-03/04) | Leave unchanged |

Other repositories under the account (Prompt-Forge, rocketride-server, Raise-for-Good) contain no AI.FO references and are out of scope.

---

## josephmccann/AI.FO-Demo — the product

- **Purpose [FACT]** (README.md): "AI.FO is a financial intelligence platform that ingests QuickBooks Online reports or accounting CSV exports into computed financial snapshots and actionable business signals." Deterministic engine computes; a separate AI layer writes narrative memos from a server-built snapshot. "The separation is the product."
- **Default branch [FACT]:** `master`. Local checkouts: `/Users/joemccann/code/AI.FO-Demo` (audited) — but note the repo's own CLAUDE.md/AGENTS.md and the nightly launchd job reference `/Users/joemccann/Desktop/aifo-demo-app` as the shared physical checkout (see LEGACY_AND_DEPRECATION_CANDIDATES.md).
- **Canonicality [FACT]:** Canonical product repository. Also the canonical home of signal methodology (`docs/SIGNAL_METHODOLOGY.md`), engine version (`lib/financial-engine/src/version.js`), and the telemetry generator (`generate-telemetry.js`, sole writer of `telemetry.json`).
- **Current activity [FACT]:** Active. **PR #186 merged 2026-07-15 02:11 UTC — the canonical product baseline is now `3329c99`** (commercial account surface, external-connectors framework with Stripe adapter, DB migration `0011_external_connectors.sql`). Jul 11–14 commits were nightly telemetry/snapshot automation plus telemetry-integrity fixes (#187–#189); the prior feature wave merged 2026-07-10 (#179–#184: sealed board package, trust evidence console, QBO self-serve recovery, public trust copy).
- **Deployment role [FACT]:** Deploys the live demo at `https://demo.getaifo.com` via Replit autoscale. **The live demo has not yet been updated to baseline `3329c99`; deployment and telemetry refresh are pending, and this post-merge demo deployment workstream is active. Connector functionality remains disabled pending deployment validation and explicit configuration** (feature-flagged off). Also serves `/api/telemetry`, which the marketing site consumes. Nightly pressure test runs from a launchd job on Joe's Mac (02:00 PT) with a GitHub Actions dead-man monitor.
- **Customer-data role [FACT]:** The product has functioning QBO **sandbox** and CSV ingestion; it does **not currently host or process production customer financial data**. Demo companies are fictional ("Integra Executive Services", "NovaBridge"); QBO integration runs against the Intuit sandbox; nightly runs generate synthetic companies. Recruiting real company datasets is Phase 4 of `docs/PRODUCTION_READINESS_PLAN.md` — unstarted. Data-protection controls already present: QBO tokens AES-256-encrypted at rest; telemetry denylist-scrubbed.
- **Public/private [FACT]:** Private.
- **Open PRs [PR]** (state as of the 2026-07-14 21:15 PT refresh — re-check before deciding):
  - **#180** founder context + constitutional principles docs. Status: **valuable working-draft source material**, explicitly non-behavioral; disposition pending reconciliation into a single canonical Founder Operating Manual (see SOURCE_OF_TRUTH_HIERARCHY.md).
  - **#195** session checkpoint docs (memory/, workqueue/, handoff, CHANGELOG). Status: **July 14 shutdown checkpoint that may now require refresh, supersession, or closure** — later activity (the PR #186 merge, PR #13, the live EDGAR collection) has changed the state it froze. Not recommended for automatic merge.
  - Recently merged: **#186** (2026-07-15 02:11 UTC, merge commit `3329c99`) — now part of the canonical product baseline; see Current activity and Deployment role above.
  - ~70 stale remote branches also exist (see LEGACY_AND_DEPRECATION_CANDIDATES.md).
- **Dependencies [FACT]:** pushes to `aifo-telemetry` via `.github/workflows/mirror-telemetry.yml` (deploy key); Airtable base `appHP0GiJuiNFbdMO` as the nightly-run operational ledger; Cloudflare R2 (`aifo-uploads`) for production storage; GMI Cloud + Anthropic for AI generation; Intuit QBO sandbox. The validation study pins this repo's engine at SHA `dc6aefc…` (read-only, via the Desktop checkout).
- **Recommended action [REC]: retain.** This is the company's most important repository.

## josephmccann/AIFO-Control-Plane — AWS infrastructure

- **Purpose [FACT]** (README.md): "AWS infrastructure control-plane repository for AI.FO. … The approved current-scope AWS control-plane baseline is operationally complete. It does not host the AI.FO product runtime and it does not include an apply workflow."
- **Default branch [FACT]:** `main`.
- **Canonicality [FACT]:** Canonical for AWS infrastructure (account `350480401760`, us-west-2), Terraform, deployment status, infrastructure decisions (ADRs), and infrastructure risk/assumption registers. Explicitly *not* canonical for the product — its own docs defer product truth to AI.FO-Demo.
- **Current activity [FACT]:** Active — the baseline history is one day (2026-07-14), PRs #2–#12 merged sequentially; **PR #13 now open (draft)**.
- **Latest meaningful work:** **[PR] #13 "docs: propose product runtime architecture decision package"** — runtime inventory (17 principal data flows), beta-cohort requirements, weighted three-option analysis, proposed reference architecture (dedicated production account, CloudFront/WAF + private S3 frontend, ECS Fargate behind ALB, RDS PostgreSQL Multi-AZ, Secrets Manager), STRIDE threat model, migration gates MR-01…MR-33, cost model, proposed ADR-0011…ADR-0022, and a founder decision packet. Its recommendation (gated AWS migration before accepting real first-cohort customer data; Replit remains synthetic demo/rehearsal) is **proposed, not canonical, until reviewed and merged**. [FACT] Merged latest: #12 manual host patching runbook; #11 reproducible lint tooling.
- **Deployment role [FACT]:** Deploys and operates the AWS control plane only: remote state, GitHub OIDC plan/apply roles (apply role deliberately state-access-only), CloudTrail, Session Manager logging, one SSM-only no-ingress EC2 operator host (`i-0254a9e2…`, currently stopped), EventBridge start/stop scheduler. Verified clean (`terraform plan`: 0/0/0). No apply workflow by design; applies are manual, human-approved.
- **Customer-data role [FACT]:** None. "The current control plane does not host product runtime or customer data" (docs/security-model.md).
- **Public/private [FACT]:** Private.
- **Open PRs [PR]:** #13 (draft — see above). PR #1 closed as superseded by #2.
- **Dependencies [FACT]:** references AI.FO-Demo as the product source of truth; GitHub OIDC; AWS. No references to any other AI.FO repo.
- **Recommended action [REC]: retain.**

## josephmccann/GetAIFO-site — public marketing site

- **Purpose [FACT]** (replit.md): "Production-ready single-page marketing website for AI.FO (domain: getaifo.com)." Despite the GitHub description mentioning Next.js, it is Vite + React 19 + Express 5 (the Next.js reference is a leftover).
- **Default branch [FACT]:** `main`.
- **Canonicality [FACT]:** Canonical marketing site for `getaifo.com`, including `/how-we-test` and `/status` public trust pages.
- **Current activity [FACT]:** Dormant since 2026-06-22 (last commit: #9, hardening `/status` against internal-data leakage). Active clusters: April (v2 marketing migration), June 11–22 (live-telemetry surface, SEO, status hardening).
- **Latest meaningful work [FACT]:** live-telemetry refactor (PRs #2–#9, June) that replaced hand-typed marketing numbers — which had silently drifted — with runtime fetches.
- **Deployment role [FACT]:** Deployed on Replit autoscale (`getaifo.com`). Fetches telemetry at runtime from `https://demo.getaifo.com/api/telemetry` (fail-honest: renders "—" on failure) and nightly-run stats from Airtable with an explicit public-projection anonymization boundary.
- **Customer-data role [FACT]:** Waitlist submissions (name, work email, optional company size/accounting system) written to Airtable, with honeypot + rate limiting. No analytics trackers. Privacy policy present. No production customer financial data.
- **Public/private [FACT]:** Private repo; public website.
- **Open PRs [FACT]:** None. 8 stale unmerged remote branches (including 3 abandoned April "lavender palette" redesign branches).
- **Dependencies [FACT]:** demo.getaifo.com API (AI.FO-Demo) for telemetry; Airtable base `appHP0GiJuiNFbdMO` for status data and waitlist.
- **Recommended action [REC]: retain + document.** It has no README.md or AGENTS.md — add both; clean stale branches and `attached_assets/` dumps (recommendations only; see LEGACY_AND_DEPRECATION_CANDIDATES.md).

## josephmccann/aifo-telemetry — public telemetry artifact

- **Purpose [FACT]** (README.md + repo description): "Public, machine-generated telemetry for the AI.FO financial engine (regenerated nightly; powers getaifo.com/how-we-test)." Two files only: `README.md` and `telemetry.json`.
- **Default branch [FACT]:** `main`.
- **Canonicality [FACT]:** Canonical *published* record of engine/QA metrics and their history. The *generator* is not here — it is `generate-telemetry.js` in AI.FO-Demo; commits are mirrored by `aifo-telemetry-mirror[bot]`.
- **Current activity [FACT]:** Active and fresh at audit: last mirror 2026-07-14 09:06 UTC (`generatedAt` same day). As of that run: 13,477 engine tests / 987 API tests / 0 failures; 21,851 classified assertions; 40 signals; 13 tracks; 45 nightly runs since 2026-04-28; 900 synthetic companies.
- **Caveats [FACT]:** cadence is "every green nightly," not every calendar night — the history shows multi-day gaps (Jun 18–22, Jul 8–9, Jul 11–12) and one same-day regenerate (2026-07-13) that lowered counts without advancing the run ledger.
- **Deployment role [FACT]:** Data backend for `getaifo.com/how-we-test` (via the demo API, which serves this artifact).
- **Customer-data role [FACT]:** None — aggregate integers about synthetic companies only. Low exposure risk.
- **Public/private [FACT]:** Public (intentionally — it is the public trust record).
- **Open PRs [FACT]:** None. No workflows in-repo (push target only).
- **Recommended action [REC]: retain.**

## josephmccann/aifo-signal-validation-study — research (Study A)

- **Purpose [FACT]** (PREREG.md): "an EDGAR retrospective and prospective validation of whether frozen AI.FO financial-engine signals preceded Chapter 11 bankruptcy filings and discriminated failed companies from matched at-risk controls." Explicitly does *not* claim private-market transfer, causality, or superiority to CFOs/auditors.
- **Default branch [FACT]:** `study/edgar-validation-build` — **stale, frozen at the 2026-06-23 initial build. All real work is on `master` (HEAD `5f84563`, 2026-07-14).** Anyone auditing via the default branch sees a three-week-old snapshot.
- **Canonicality [FACT]:** Canonical research repository for Study A, on `master`. The preregistration is **frozen at tag `prereg-v1` (2026-07-09, commit `4227260`) and remains unchanged**; it was applied before any scored run.
- **Repository state [FACT]:** BUILT (full pipeline + ~23 test files + threshold provenance audit) and pre-score analyses run (universe construction, fire-capability, iXBRL sweeps — all banner-marked `PROVISIONAL-PENDING-CC-RE-VERIFICATION`). Post-freeze commits through 2026-07-14 are SEC-fetch robustness and collection-path repairs.
- **Active runtime state [RUN]** (reported at the 2026-07-14 PT checkpoint; not mirrored to the repo — re-verify before acting): the **authorized full live collection over 8,215 registered companies is actively running, approximately 36% complete** at the latest checkpoint. **Real-company scoring has not occurred.** [JOE→standing authorization] Joe has conditionally authorized the run to proceed automatically through scoring and measurement **only if all documented technical and methodological gates pass**; Joe is required again only if a defined stop condition occurs.
- **Deployment role [FACT]:** None. No wiring to getaifo.com or aifo-telemetry (deliberately — it is an investor/fundraising credibility artifact, not a marketing feed).
- **Customer-data role [FACT]:** None — public SEC EDGAR data only.
- **Public/private [FACT]:** Private.
- **Open PRs [FACT]:** #1 "Build EDGAR validation prereg pipeline" — stale (updated 2026-06-24); its head is the abandoned default branch and its body describes a superseded state. [REC] Close without merge (needs approval [JOE]).
- **Dependencies [FACT]:** hard read-only pin on the AI.FO-Demo engine at SHA `dc6aefc…` via `/Users/joemccann/Desktop/aifo-demo-app`; SEC EDGAR (`data.sec.gov`); Airtable Decision Log as the ruling system of record; two sibling working directories on Joe's Desktop (defs-repair, study-redesign).
- **Recommended action [REC]: retain**, plus (needs approval [JOE]): switch the GitHub default branch to `master` and close PR #1.

## josephmccann/AI-CFO — legacy MVP prototype

- **Purpose [FACT]** (replit.md): "VibeInput is a financial clarity tool that ingests raw financial data … applies deterministic computations, and generates AI-driven strategic insights" — the PRD names it the "CFO Reasoning Layer." Evidence (AI.FO pitch deck committed in `attached_assets/`) shows this *is* the original AI.FO MVP under earlier working names, not a separate product.
- **Default branch [FACT]:** `main`.
- **Canonicality [FACT]:** Legacy. Superseded in practice by AI.FO-Demo (no explicit deprecation note exists in-repo). The "Compute → Explain → Recommend" principle and the deterministic-engine-plus-AI-narrative separation clearly carried forward.
- **Current activity [FACT]:** Dormant — 21 commits total, all within 2026-01-31 → 2026-02-04.
- **Deployment role [FACT]:** None active (Replit deploy config exists; no evidence of a live deployment).
- **Customer-data role [FACT]:** None (seed/sample data only). Contains a hardcoded demo admin credential in `.replit` — dev-grade, but another reason to archive.
- **Public/private [FACT]:** Private.
- **Open PRs [FACT]:** None.
- **Unique assets worth extracting before archiving [FACT]:** the AI.FO pitch deck (`attached_assets/AIFO_Pitch_Deck_….pdf`, Beautiful.ai deck), the founding PRD, the "Vibe Coding Inputs Canonical V1.0" thinking-system spec, the standards-layer/Policy Pack design rationale (GAAP/FASAB/IRC), and the CrossReference citation-scoring model.
- **Recommended action [REC]: extract unique assets to a durable home, then archive.** Archiving needs explicit approval [JOE]; nothing has been done.

## josephmccann/A2A — empty

- **Purpose [FACT]:** GitHub description says "A2A idea." The repository has size 0, no branches, no commits — created 2026-04-30 and never populated.
- **Recommended action [REC]: archive or delete** (delete only after explicit approval [JOE]). Nothing to preserve.

## Not part of AI.FO (verified, kept for the record)

- **josephmccann/verifier** (public) **[FACT]:** offline verifier for HMAC execution receipts of "Axiom," a separate agent-platform project hosted at `axiom-ai-19.polsia.app`. Zero AI.FO references in either direction. The words "verifier" (AI.FO's internal LLM-output checker) and "Axiom" (fictional test-fixture company names in AI.FO-Demo) are naming collisions, not links. [REC] Leave unchanged; exclude from AI.FO program documentation.
- **josephmccann/portfolio-brain** and **portfolio-brain-total-recall** (private, already archived) **[FACT]:** hackathon projects (Neo4j/RocketRide/GMI Cloud; Dify/HydraDB). Thematically adjacent (financial intelligence) but no AI.FO references. [REC] Leave unchanged.
