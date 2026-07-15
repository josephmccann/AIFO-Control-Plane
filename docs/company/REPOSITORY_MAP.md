# AI.FO Repository Map

Status: CURRENT — snapshot as of 2026-07-14
Rule: repository evidence overrides repository names and prior assumptions. Every classification below cites what the repository itself says or shows.

## Summary table

| Repository | Visibility | Default branch | Canonicality | Activity (as of 2026-07-14) | Recommended action |
|---|---|---|---|---|---|
| AI.FO-Demo | Private | `master` | **Canonical — product** | Active (nightly automation daily; last feature wave 2026-07-10; 3 open PRs) | Retain |
| AIFO-Control-Plane | Private | `main` | **Canonical — AWS infrastructure** | Active (11 PRs merged 2026-07-14/15; 1 active session worktree) | Retain |
| GetAIFO-site | Private | `main` | **Canonical — public marketing site** | Dormant since 2026-06-22 (~3 weeks) | Retain + document |
| aifo-telemetry | **Public** | `main` | **Canonical — public telemetry artifact** | Active (bot-mirrored; fresh 2026-07-14) | Retain |
| aifo-signal-validation-study | Private | `study/edgar-validation-build` (**stale — real work on `master`**) | **Canonical — research (Study A)** | Active (master commits through 2026-07-14) | Retain + fix default branch (needs approval) |
| AI-CFO | Private | `main` | Legacy (original MVP prototype) | Dormant since 2026-02-04 | Extract unique assets, then archive (needs approval) |
| A2A | Private | `main` (no branches) | Empty | Never populated (created 2026-04-30, size 0) | Archive or delete (needs approval) |
| verifier | Public | `main` | Not AI.FO (separate "Axiom" project) | Dormant since 2026-05-29 | Leave unchanged; exclude from AI.FO docs |
| portfolio-brain / portfolio-brain-total-recall | Private, **archived** | `main` | Not AI.FO (hackathon artifacts) | Archived (2026-03/04) | Leave unchanged |

Other repositories under the account (Prompt-Forge, rocketride-server, Raise-for-Good) contain no AI.FO references and are out of scope.

---

## josephmccann/AI.FO-Demo — the product

- **Purpose** (README.md): "AI.FO is a financial intelligence platform that ingests QuickBooks Online reports or accounting CSV exports into computed financial snapshots and actionable business signals." Deterministic engine computes; a separate AI layer writes narrative memos from a server-built snapshot. "The separation is the product."
- **Default branch:** `master`. Local checkouts: `/Users/joemccann/code/AI.FO-Demo` (audited) — but note the repo's own CLAUDE.md/AGENTS.md and the nightly launchd job reference `/Users/joemccann/Desktop/aifo-demo-app` as the shared physical checkout (see LEGACY_AND_DEPRECATION_CANDIDATES.md).
- **Canonicality:** Canonical product repository. Also the canonical home of signal methodology (`docs/SIGNAL_METHODOLOGY.md`), engine version (`lib/financial-engine/src/version.js`), and the telemetry generator (`generate-telemetry.js`, sole writer of `telemetry.json`).
- **Current activity:** Active. Jul 11–14 commits are nightly telemetry/snapshot automation plus telemetry-integrity fixes (#187–#189); last substantive feature wave merged 2026-07-10 (#179–#184: sealed board package, trust evidence console, QBO self-serve recovery, public trust copy).
- **Latest meaningful work:** Jul-10 feature wave (merged); PR #186 commercial account surface + Stripe connector (open, code-complete, awaiting review).
- **Deployment role:** Deploys the live demo at `https://demo.getaifo.com` via Replit autoscale. Also serves `/api/telemetry`, which the marketing site consumes. Nightly pressure test runs from a launchd job on Joe's Mac (02:00 PT) with a GitHub Actions dead-man monitor.
- **Customer-data role:** Demo/sandbox/synthetic only. Fictional demo companies ("Integra Executive Services", "NovaBridge"); QBO integration is Intuit **sandbox**; nightly runs generate synthetic companies. Recruiting real company datasets is Phase 4 of `docs/PRODUCTION_READINESS_PLAN.md` — unstarted. QBO tokens are AES-256-encrypted at rest; telemetry is denylist-scrubbed.
- **Public/private:** Private.
- **Active PRs:** #186 (feature: account surface + Stripe connectors — the only open code PR), #180 (founder context + constitution docs, working drafts), #195 (session checkpoint docs; body says "do not merge during shutdown unless explicitly requested"). ~70 stale remote branches also exist.
- **Dependencies:** pushes to `aifo-telemetry` via `.github/workflows/mirror-telemetry.yml` (deploy key); Airtable base `appHP0GiJuiNFbdMO` as the nightly-run operational ledger; Cloudflare R2 (`aifo-uploads`) for production storage; GMI Cloud + Anthropic for AI generation; Intuit QBO sandbox. The validation study pins this repo's engine at SHA `dc6aefc…` (read-only, via the Desktop checkout).
- **Recommended action: retain.** This is the company's most important repository.

## josephmccann/AIFO-Control-Plane — AWS infrastructure

- **Purpose** (README.md): "AWS infrastructure control-plane repository for AI.FO. … The approved current-scope AWS control-plane baseline is operationally complete. It does not host the AI.FO product runtime and it does not include an apply workflow."
- **Default branch:** `main`.
- **Canonicality:** Canonical for AWS infrastructure (account `350480401760`, us-west-2), Terraform, deployment status, infrastructure decisions (ADRs), and infrastructure risk/assumption registers. Explicitly *not* canonical for the product — its own docs defer product truth to AI.FO-Demo.
- **Current activity:** Active — the entire repo history is one day (2026-07-14), PRs #2–#12 merged sequentially; one active parallel session worktree (`codex/product-runtime-architecture-decision-package`, docs-only, local, unpushed).
- **Latest meaningful work:** #12 manual host patching runbook; #11 reproducible lint tooling; #9 completed GitHub Terraform plan gate.
- **Deployment role:** Deploys and operates the AWS control plane only: remote state, GitHub OIDC plan/apply roles (apply role deliberately state-access-only), CloudTrail, Session Manager logging, one SSM-only no-ingress EC2 operator host (`i-0254a9e2…`, currently stopped), EventBridge start/stop scheduler. Verified clean (`terraform plan`: 0/0/0). No apply workflow by design; applies are manual, human-approved.
- **Customer-data role:** None. "The current control plane does not host product runtime or customer data" (docs/security-model.md).
- **Public/private:** Private.
- **Active PRs:** None open. PR #1 closed as superseded by #2.
- **Dependencies:** references AI.FO-Demo as the product source of truth; GitHub OIDC; AWS. No references to any other AI.FO repo.
- **Recommended action: retain.**

## josephmccann/GetAIFO-site — public marketing site

- **Purpose** (replit.md): "Production-ready single-page marketing website for AI.FO (domain: getaifo.com)." Despite the GitHub description mentioning Next.js, it is Vite + React 19 + Express 5 (the Next.js reference is a leftover).
- **Default branch:** `main`.
- **Canonicality:** Canonical marketing site for `getaifo.com`, including `/how-we-test` and `/status` public trust pages.
- **Current activity:** Dormant since 2026-06-22 (last commit: #9, hardening `/status` against internal-data leakage). Active clusters: April (v2 marketing migration), June 11–22 (live-telemetry surface, SEO, status hardening).
- **Latest meaningful work:** live-telemetry refactor (PRs #2–#9, June) that replaced hand-typed marketing numbers — which had silently drifted — with runtime fetches.
- **Deployment role:** Deployed on Replit autoscale (`getaifo.com`). Fetches telemetry at runtime from `https://demo.getaifo.com/api/telemetry` (fail-honest: renders "—" on failure) and nightly-run stats from Airtable with an explicit public-projection anonymization boundary.
- **Customer-data role:** Waitlist submissions (name, work email, optional company size/accounting system) written to Airtable, with honeypot + rate limiting. No analytics trackers. Privacy policy present.
- **Public/private:** Private repo; public website.
- **Active PRs:** None. 8 stale unmerged remote branches (including 3 abandoned April "lavender palette" redesign branches).
- **Dependencies:** demo.getaifo.com API (AI.FO-Demo) for telemetry; Airtable base `appHP0GiJuiNFbdMO` for status data and waitlist.
- **Recommended action: retain + document.** It has no README.md or AGENTS.md — add both; clean stale branches and `attached_assets/` dumps (recommendations only; see LEGACY_AND_DEPRECATION_CANDIDATES.md).

## josephmccann/aifo-telemetry — public telemetry artifact

- **Purpose** (README.md + repo description): "Public, machine-generated telemetry for the AI.FO financial engine (regenerated nightly; powers getaifo.com/how-we-test)." Two files only: `README.md` and `telemetry.json`.
- **Default branch:** `main`.
- **Canonicality:** Canonical *published* record of engine/QA metrics and their history. The *generator* is not here — it is `generate-telemetry.js` in AI.FO-Demo; commits are mirrored by `aifo-telemetry-mirror[bot]`.
- **Current activity:** Active and fresh: last mirror 2026-07-14 09:06 UTC (`generatedAt` same day). As of that run: 13,477 engine tests / 987 API tests / 0 failures; 21,851 classified assertions; 40 signals; 13 tracks; 45 nightly runs since 2026-04-28; 900 synthetic companies.
- **Caveats:** cadence is "every green nightly," not every calendar night — the history shows multi-day gaps (Jun 18–22, Jul 8–9, Jul 11–12) and one same-day regenerate (2026-07-13) that lowered counts without advancing the run ledger.
- **Deployment role:** Data backend for `getaifo.com/how-we-test` (via the demo API, which serves this artifact).
- **Customer-data role:** None — aggregate integers about synthetic companies only. Low exposure risk.
- **Public/private:** Public (intentionally — it is the public trust record).
- **Active PRs:** None. No workflows in-repo (push target only).
- **Recommended action: retain.**

## josephmccann/aifo-signal-validation-study — research (Study A)

- **Purpose** (PREREG.md): "an EDGAR retrospective and prospective validation of whether frozen AI.FO financial-engine signals preceded Chapter 11 bankruptcy filings and discriminated failed companies from matched at-risk controls." Explicitly does *not* claim private-market transfer, causality, or superiority to CFOs/auditors.
- **Default branch:** `study/edgar-validation-build` — **stale, frozen at the 2026-06-23 initial build. All real work is on `master` (HEAD `5f84563`, 2026-07-14).** Anyone auditing via the default branch sees a three-week-old snapshot.
- **Canonicality:** Canonical research repository for Study A, on `master`. The preregistration is frozen at tag `prereg-v1` (2026-07-09, commit `4227260`), applied *before* any scored run.
- **Current activity:** Active — post-freeze commits (Jul 9–14) are exclusively SEC-fetch robustness and live-collection-path repairs preparing for the primary run.
- **State:** BUILT (full pipeline + ~23 test files + threshold provenance audit) and PARTIALLY RUN (real universe construction, fire-capability analysis, iXBRL sweeps — all pre-score, all banner-marked `PROVISIONAL-PENDING-CC-RE-VERIFICATION`). The **primary scored discrimination run has NOT been executed** — `docs/METHODS_AND_RESULTS.md` has every result cell TBD. **No empirical validation claim is currently supportable.**
- **Deployment role:** None. No wiring to getaifo.com or aifo-telemetry (deliberately — it is an investor/fundraising credibility artifact, not a marketing feed).
- **Customer-data role:** None — public SEC EDGAR data only.
- **Public/private:** Private.
- **Active PRs:** #1 "Build EDGAR validation prereg pipeline" — stale (updated 2026-06-24); its head is the abandoned default branch and its body describes a superseded state. Recommend closing without merge (needs approval).
- **Dependencies:** hard read-only pin on the AI.FO-Demo engine at SHA `dc6aefc…` via `/Users/joemccann/Desktop/aifo-demo-app`; SEC EDGAR (`data.sec.gov`); Airtable Decision Log as the ruling system of record; two sibling working directories on Joe's Desktop (defs-repair, study-redesign).
- **Recommended action: retain**, plus (needs approval): switch the GitHub default branch to `master` and close PR #1.

## josephmccann/AI-CFO — legacy MVP prototype

- **Purpose** (replit.md): "VibeInput is a financial clarity tool that ingests raw financial data … applies deterministic computations, and generates AI-driven strategic insights" — the PRD names it the "CFO Reasoning Layer." Evidence (AI.FO pitch deck committed in `attached_assets/`) shows this *is* the original AI.FO MVP under earlier working names, not a separate product.
- **Default branch:** `main`.
- **Canonicality:** Legacy. Superseded in practice by AI.FO-Demo (no explicit deprecation note exists in-repo). The "Compute → Explain → Recommend" principle and the deterministic-engine-plus-AI-narrative separation clearly carried forward.
- **Current activity:** Dormant — 21 commits total, all within 2026-01-31 → 2026-02-04.
- **Deployment role:** None active (Replit deploy config exists; no evidence of a live deployment).
- **Customer-data role:** None (seed/sample data only). Contains a hardcoded demo admin credential in `.replit` — dev-grade, but another reason to archive.
- **Public/private:** Private.
- **Active PRs:** None.
- **Unique assets worth extracting before archiving:** the AI.FO pitch deck (`attached_assets/AIFO_Pitch_Deck_….pdf`, Beautiful.ai deck), the founding PRD, the "Vibe Coding Inputs Canonical V1.0" thinking-system spec, the standards-layer/Policy Pack design rationale (GAAP/FASAB/IRC), and the CrossReference citation-scoring model.
- **Recommended action: extract unique assets to a durable home, then archive.** Archiving needs explicit approval; nothing has been done.

## josephmccann/A2A — empty

- **Purpose:** GitHub description says "A2A idea." The repository has size 0, no branches, no commits — created 2026-04-30 and never populated.
- **Recommended action: archive or delete (delete only after explicit approval).** Nothing to preserve.

## Not part of AI.FO (verified, kept for the record)

- **josephmccann/verifier** (public): offline verifier for HMAC execution receipts of "Axiom," a separate agent-platform project hosted at `axiom-ai-19.polsia.app`. Zero AI.FO references in either direction. The words "verifier" (AI.FO's internal LLM-output checker) and "Axiom" (fictional test-fixture company names in AI.FO-Demo) are naming collisions, not links. **Leave unchanged; exclude from AI.FO program documentation.**
- **josephmccann/portfolio-brain** and **portfolio-brain-total-recall** (private, already archived): hackathon projects (Neo4j/RocketRide/GMI Cloud; Dify/HydraDB). Thematically adjacent (financial intelligence) but no AI.FO references. **Leave unchanged.**
