# AI.FO Company Digest

> **Digest metadata**
> - Audit snapshot: 2026-07-14 (repository evidence collected 2026-07-14 PT; revised 2026-07-14 19:10 PT / 2026-07-15 02:10 UTC)
> - Pinned commits: see the evidence table below. All facts in this digest trace to those commits.
> - Statement classes used throughout: **[FACT]** verified current fact · **[PR]** open-PR proposal (not canonical until merged) · **[RUN]** active runtime state (volatile; re-verify before acting) · **[REC]** recommendation · **[JOE]** founder decision required.
> - **PR state and active-run state are volatile.** Refresh them from the canonical dynamic sources below before making any decision based on this digest.

Boundary: Documentation only. Nothing in `docs/company/` changes product, infrastructure, or process. Where these documents disagree with a repository's own docs, the repository's docs win and this digest should be corrected.

## Purpose

This directory is the ten-minute orientation for AI.FO. It answers, in one place:

- which repositories exist and what each one is for,
- what is built, merged, deployed, running, and blocked,
- which documents are authoritative for which kind of truth,
- what is legacy and what should eventually be cleaned up,
- which decisions only Joe can make.

It is written for Joe, a new engineer, an investor diligence reviewer, or an AI agent starting a session cold.

## Reading order

1. [PROGRAM_STATUS.md](PROGRAM_STATUS.md) — what works, is deployed, is running, is blocked, across product / infrastructure / research / marketing / operations.
2. [REPOSITORY_MAP.md](REPOSITORY_MAP.md) — every repository, its role, canonicality, and recommended action.
3. [SOURCE_OF_TRUTH_HIERARCHY.md](SOURCE_OF_TRUTH_HIERARCHY.md) — which document wins for each kind of claim.
4. [ACTIVE_WORKSTREAMS.md](ACTIVE_WORKSTREAMS.md) — who/what is working where, isolation, blockers, and the decision sequence.
5. [LEGACY_AND_DEPRECATION_CANDIDATES.md](LEGACY_AND_DEPRECATION_CANDIDATES.md) — stale artifacts and cleanup recommendations (recommendations only; nothing has been executed).

## The company in six sentences

**[FACT]** AI.FO is a financial intelligence platform ("a financial reasoning layer above systems of record") whose deterministic engine computes signals from QuickBooks Online or CSV data and whose AI layer writes CFO-grade narrative memos without ever touching the math. **[FACT]** The product is demo-live at `demo.getaifo.com` on Replit with functioning QBO **sandbox** and CSV ingestion; it does not currently host or process production customer financial data. **[FACT]** The AWS control plane is deployed and operationally complete but deliberately does not host the product; **[PR]** an architecture decision package for a gated Replit→AWS runtime migration is now open as Control-Plane PR #13 and remains a proposal until reviewed and merged. **[FACT]** The EDGAR signal-validation study is built and preregistered (tag `prereg-v1`, 2026-07-09, unchanged); **[RUN]** its authorized full live collection over 8,215 registered companies is actively running (~36% complete at the latest checkpoint) with conditional authorization to proceed automatically through scoring and measurement only if all documented gates pass — real-company scoring has not occurred, so no empirical validation claim is currently supportable. **[FACT]** Public trust surfaces (getaifo.com, the public `aifo-telemetry` artifact) publish machine-generated test and signal counts that were fresh as of 2026-07-14. **[JOE]** Everything now funnels into founder gates: PR dispositions (#195, #180, #186, #13), the runtime-architecture decisions, and any study stop condition.

## Evidence basis (pinned commits)

| Repository | Branch inspected | HEAD at audit |
|---|---|---|
| josephmccann/AI.FO-Demo | master | `8df211e` |
| josephmccann/AIFO-Control-Plane | main | `707e629` |
| josephmccann/aifo-signal-validation-study | master (default branch is stale — see REPOSITORY_MAP) | `5f84563` |
| josephmccann/aifo-telemetry | main | `bf59bc7` |
| josephmccann/GetAIFO-site | main | `8206a81` |
| josephmccann/AI-CFO | main | `8ccfb6b` |
| josephmccann/A2A | — (empty repository) | — |
| josephmccann/verifier | main (assessed: not part of AI.FO) | `15ef668` |

## Canonical dynamic sources (always fresher than this digest)

- Open PRs: [AI.FO-Demo](https://github.com/josephmccann/AI.FO-Demo/pulls) · [AIFO-Control-Plane](https://github.com/josephmccann/AIFO-Control-Plane/pulls) · [aifo-signal-validation-study](https://github.com/josephmccann/aifo-signal-validation-study/pulls)
- Study current state: [`master` branch](https://github.com/josephmccann/aifo-signal-validation-study/tree/master) (not the stale default branch) and the study's Airtable Decision Log
- Live metrics: [aifo-telemetry `telemetry.json`](https://github.com/josephmccann/aifo-telemetry/blob/main/telemetry.json) · [getaifo.com/how-we-test](https://getaifo.com/how-we-test) · [getaifo.com/status](https://getaifo.com/status)
- Infrastructure reality: `AIFO-Control-Plane` `memory/current-state.md` and `memory/deployment-status.md` on `main`
- Active EDGAR collection run: runtime state on the operator machine — not mirrored to any repo; confirm with Joe or the study's run artifacts before relying on progress figures

## Update protocol

**When this digest must be refreshed** (any of):
- any of the four open PRs (#195, #180, #186 in AI.FO-Demo; #13 in AIFO-Control-Plane) is merged, closed, or substantially rewritten;
- the EDGAR live collection completes, halts on a stop condition, or produces scored results;
- the product runtime decision (OD-005…OD-008) is made, or real customer data onboarding begins;
- a repository is archived, renamed, created, or re-pointed (e.g., the study default-branch fix);
- more than ~30 days pass without revision.

**Who or what may update it:** any agent session or engineer, on a dedicated `claude/*`, `codex/*`, or `docs/*` branch, documentation-only, citing pinned commits — with Joe holding the merge gate, same as all other Control-Plane changes. Updates supersede by revising these files and updating the metadata blocks; never edit the git history of prior revisions.

**What remains authoritative when this digest is stale:** the per-repository sources in [SOURCE_OF_TRUTH_HIERARCHY.md](SOURCE_OF_TRUTH_HIERARCHY.md). This digest is an index, never an override: merged repository content, derived numbers, and the Airtable ledgers always outrank it.

**How active workstreams close or transition:** a workstream leaves [ACTIVE_WORKSTREAMS.md](ACTIVE_WORKSTREAMS.md) only with a recorded disposition (merged / closed-superseded / transitioned to a named successor) and a link to the evidence (PR, tag, or dated handoff). A workstream that stops without disposition is flagged stale, not silently removed.
