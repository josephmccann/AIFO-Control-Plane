# AI.FO Company Digest

Status: CURRENT — snapshot as of 2026-07-14
Scope: Company-wide repository and program state, across all AI.FO-related repositories
Boundary: Documentation only. Nothing in `docs/company/` changes product, infrastructure, or process. Where these documents disagree with a repository's own docs, the repository's docs win and this digest should be corrected.

## Purpose

This directory is the ten-minute orientation for AI.FO. It answers, in one place:

- which repositories exist and what each one is for,
- what is built, merged, deployed, and blocked,
- which documents are authoritative for which kind of truth,
- what is legacy and what should eventually be cleaned up,
- which decisions only Joe can make.

It is written for Joe, a new engineer, an investor diligence reviewer, or an AI agent starting a session cold.

## Reading order

1. [PROGRAM_STATUS.md](PROGRAM_STATUS.md) — what actually works, is deployed, is blocked, across product / infrastructure / research / marketing / operations.
2. [REPOSITORY_MAP.md](REPOSITORY_MAP.md) — every repository, its role, canonicality, and recommended action.
3. [SOURCE_OF_TRUTH_HIERARCHY.md](SOURCE_OF_TRUTH_HIERARCHY.md) — which document wins for each kind of claim.
4. [ACTIVE_WORKSTREAMS.md](ACTIVE_WORKSTREAMS.md) — who/what is working where, isolation, blockers, merge sequencing.
5. [LEGACY_AND_DEPRECATION_CANDIDATES.md](LEGACY_AND_DEPRECATION_CANDIDATES.md) — stale artifacts and cleanup recommendations (recommendations only; nothing has been executed).

## The company in five sentences

AI.FO is a financial intelligence platform ("a financial reasoning layer above systems of record") whose deterministic engine computes signals from QuickBooks Online or CSV data and whose AI layer writes CFO-grade narrative memos without ever touching the math. The product is real and demo-live at `demo.getaifo.com` on Replit, validated only against sandbox and synthetic data — no real customer books yet. The AWS control plane (this repository) is deployed and operationally complete, but deliberately does not host the product; runtime migration to AWS is an open founder decision with an active architecture-decision-package session in flight. An EDGAR signal-validation study is built and preregistered (`prereg-v1`, 2026-07-09) but its primary scored run has not been executed, so no empirical validation claim is currently supportable. Public trust surfaces (getaifo.com, the public `aifo-telemetry` artifact) publish machine-generated test and signal counts that are fresh as of 2026-07-14.

## Evidence basis

Compiled 2026-07-14 (some same-day PR merge timestamps fall on 2026-07-15 UTC) from direct inspection of each repository at these commits:

| Repository | Branch inspected | HEAD |
|---|---|---|
| josephmccann/AI.FO-Demo | master | `8df211e` |
| josephmccann/AIFO-Control-Plane | main | `707e629` |
| josephmccann/aifo-signal-validation-study | master (default branch is stale — see REPOSITORY_MAP) | `5f84563` |
| josephmccann/aifo-telemetry | main | `bf59bc7` |
| josephmccann/GetAIFO-site | main | `8206a81` |
| josephmccann/AI-CFO | main | `8ccfb6b` |
| josephmccann/A2A | — (empty repository) | — |
| josephmccann/verifier | main (assessed: not part of AI.FO) | `15ef668` |

## Maintenance

This digest is a point-in-time reconciliation, not a live dashboard. Regenerate or amend it when: a repository is archived/renamed, the product runtime decision (OD-005) is made, the validation study's primary run executes, or real customer data onboarding begins. Prefer updating links over copying facts — every number here should trace to a repository source listed in [SOURCE_OF_TRUTH_HIERARCHY.md](SOURCE_OF_TRUTH_HIERARCHY.md).
