# Source Material Index

Status: ADOPTED with the Manual on 2026-07-15.

Pinned sources for every document in `docs/governance/`. Doctrine in the
[Founder Operating Manual](FOUNDER_OPERATING_MANUAL.md) traces to these
sources; the [reconciliation crosswalk](PR180_RECONCILIATION.md) cites them
by item ID. Cross-repository links are pinned to commit SHAs so the
reviewed evidence stays reproducible even as branches move. AI.FO-Demo is a
private repository; its links resolve only for authorized readers.

Evidence rule reminder: repository evidence overrides earlier prose, merged
beats unmerged, and pinned drafts are source material, not authority.

## 1. AI.FO-Demo draft PR #180 (primary source material, unmerged)

PR: <https://github.com/josephmccann/AI.FO-Demo/pull/180>
Branch: `docs/founder-aifo-context`
Reviewed head: `5d058ee31f60d2e4f84c652a92c9fd310bb20d2c`
Self-declared status: working drafts, not canonical, no behavior change.

| Source | Pinned link |
|--------|-------------|
| Constitution directory README | <https://github.com/josephmccann/AI.FO-Demo/blob/5d058ee31f60d2e4f84c652a92c9fd310bb20d2c/docs/constitution/README.md> |
| Founder context working draft | <https://github.com/josephmccann/AI.FO-Demo/blob/5d058ee31f60d2e4f84c652a92c9fd310bb20d2c/docs/constitution/FOUNDER_CONTEXT_WORKING_DRAFT.md> |
| Constitution working draft | <https://github.com/josephmccann/AI.FO-Demo/blob/5d058ee31f60d2e4f84c652a92c9fd310bb20d2c/docs/constitution/AIFO_CONSTITUTION_WORKING_DRAFT.md> |
| Reasoning archive | <https://github.com/josephmccann/AI.FO-Demo/blob/5d058ee31f60d2e4f84c652a92c9fd310bb20d2c/docs/constitution/REASONING_ARCHIVE.md> |
| Current company state (2026-07-10) | <https://github.com/josephmccann/AI.FO-Demo/blob/5d058ee31f60d2e4f84c652a92c9fd310bb20d2c/docs/context/CURRENT_COMPANY_STATE.md> |

The PR also contains eight files outside this scope (`.aifo/*.yaml`,
`docs/operating-system/`, `docs/research/founder-finance-discovery/`); see
decision D-5 in the reconciliation.

## 2. AIFO-Control-Plane (this repository, merged main)

| Source | Used for |
|--------|----------|
| [AGENTS.md](../../AGENTS.md) | Agent rules, guardrails, safe commands (Manual 9, 10) |
| [SECURITY.md](../../SECURITY.md) | Non-negotiable security controls (Manual 9) |
| [CONTRIBUTING.md](../../CONTRIBUTING.md) | Material-decision definition, PR standards, primary-source research rule (Manual 5, 7) |
| [docs/principle-traceability-matrix.md](../principle-traceability-matrix.md) | The twenty-four founder principles and their compliance mapping (Manual appendix) |
| [docs/adr/0000-adr-template.md](../adr/0000-adr-template.md) | Decision-record standard, solo-founder recoverability section (Manual 5.2, 18) |
| [docs/adr/README.md](../adr/README.md) | ADR versus runbook roles (Manual 11) |
| [docs/handoffs/HANDOFF_COMPANY.md](../handoffs/HANDOFF_COMPANY.md) | Company operating philosophy distillation, decision discipline (Manual 5, 7, 13) |
| [docs/handoffs/HANDOFF_PRODUCT.md](../handoffs/HANDOFF_PRODUCT.md) | Deterministic-truth boundary, lineage distinctions (Manual 4.1, 8) |
| [docs/product-runtime-inventory.md](../product-runtime-inventory.md) | Engine/AI ownership statement (Manual 4.1) |
| [docs/runbooks/disaster-recovery.md](../runbooks/disaster-recovery.md), [rollback.md](../runbooks/rollback.md), [emergency-access.md](../runbooks/emergency-access.md), [new-engineer-onboarding.md](../runbooks/new-engineer-onboarding.md) | Recoverability doctrine, emergency boundaries (Manual 9, 18) |
| [docs/execution-plan.md](../execution-plan.md) | Decision gates requiring human approval (Manual 5.3, 10.3) |
| [docs/cost-model.md](../cost-model.md), [docs/ec2-instance-recommendation.md](../ec2-instance-recommendation.md) | Cost philosophy, dated primary-source pricing practice (Manual 15) |
| [memory/open-decisions.md](../../memory/open-decisions.md) | Open-decision ledger pattern (Manual 5.5) |
| [docs/session-handoffs/HANDOFF_CONTROL_PLANE_2026-07-15.md](../session-handoffs/HANDOFF_CONTROL_PLANE_2026-07-15.md) | Stop conditions for agents (Manual 10.3, 10.4) |

## 3. AIFO-Control-Plane draft PR #14 (company digest, unmerged)

PR: <https://github.com/josephmccann/AIFO-Control-Plane/pull/14>
Branch: `claude/company-program-state-consolidation-2026-07`
Reviewed head: `83c5bcd0bcae9e586a3b33c643b079d54789d046`

| Source | Pinned link | Used for |
|--------|-------------|----------|
| Source-of-truth hierarchy | <https://github.com/josephmccann/AIFO-Control-Plane/blob/83c5bcd0bcae9e586a3b33c643b079d54789d046/docs/company/SOURCE_OF_TRUTH_HIERARCHY.md> | Authority hierarchy, precedence rules, one home per truth, the "no canonical home for founder doctrine" finding (Manual 1, 11.4) |
| Digest README | <https://github.com/josephmccann/AIFO-Control-Plane/blob/83c5bcd0bcae9e586a3b33c643b079d54789d046/docs/company/README.md> | Statement classification tags, digest-never-overrides rule (Manual 11.6, hierarchy rank 9) |
| Program status | <https://github.com/josephmccann/AIFO-Control-Plane/blob/83c5bcd0bcae9e586a3b33c643b079d54789d046/docs/company/PROGRAM_STATUS.md> | Current-state evidence only; nothing imported as doctrine |
| Active workstreams | <https://github.com/josephmccann/AIFO-Control-Plane/blob/83c5bcd0bcae9e586a3b33c643b079d54789d046/docs/company/ACTIVE_WORKSTREAMS.md> | Recorded-disposition rule for workstreams (Manual 12) |

## 4. AIFO-Control-Plane draft PR #13 (product runtime architecture package, unmerged)

PR: <https://github.com/josephmccann/AIFO-Control-Plane/pull/13>
Branch: `codex/product-runtime-architecture-decision-package`
Reviewed head: `73caaddf401717250121276ca3ef7afb5321e5ee`

| Source | Pinned link | Used for |
|--------|-------------|----------|
| Founder decision packet | <https://github.com/josephmccann/AIFO-Control-Plane/blob/73caaddf401717250121276ca3ef7afb5321e5ee/docs/decision-packets/PRODUCT_RUNTIME_ARCHITECTURE_FOUNDER_DECISION.md> | Decision-packet pattern, approval tiers, latest-safe-decision-date framing, stop conditions (Manual 5.3) |
| Options analysis | <https://github.com/josephmccann/AIFO-Control-Plane/blob/73caaddf401717250121276ca3ef7afb5321e5ee/docs/product-runtime-options-analysis.md> | Weighted-scoring practice; trust and recovery outrank nominal hosting cost (Manual 15) |
| Migration readiness | <https://github.com/josephmccann/AIFO-Control-Plane/blob/73caaddf401717250121276ca3ef7afb5321e5ee/docs/product-runtime-migration-readiness.md> | "Configured without a tested result is not a pass"; readiness-gate pattern (Manual 5.4, 12) |
| Reference architecture | <https://github.com/josephmccann/AIFO-Control-Plane/blob/73caaddf401717250121276ca3ef7afb5321e5ee/docs/product-runtime-reference-architecture.md> | Founder-recoverability drill requirement, deferral-until-evidence discipline (Manual 8, 18) |
| Threat model | <https://github.com/josephmccann/AIFO-Control-Plane/blob/73caaddf401717250121276ca3ef7afb5321e5ee/docs/security/product-runtime-threat-model.md> | Residual-risk-belongs-to-founder rule, provider data-training blocker (Manual 9) |

## 5. AI.FO-Demo (product repository, merged master)

Reviewed head of `master` for this reconciliation:
`fb7bf77e10848e4572ebc680c2151b45536466ce` (2026-07-15). Links are pinned to
that commit so the reconciled evidence stays reproducible. The living
documents on `master` remain canonical for their domains; if a pinned copy
and current `master` differ, current `master` governs the domain and this
index records only what was reviewed.

| Source | Used for |
|--------|----------|
| <https://github.com/josephmccann/AI.FO-Demo/blob/fb7bf77e10848e4572ebc680c2151b45536466ce/AGENTS.md> | Agent integrity rules, tests as source of truth, signal-provenance triplet, derived-numbers rule, reproducibility P0 (Manual 7, 10) |
| <https://github.com/josephmccann/AI.FO-Demo/blob/fb7bf77e10848e4572ebc680c2151b45536466ce/README.md> | "The separation is the product" (Manual 4.1) |
| <https://github.com/josephmccann/AI.FO-Demo/blob/fb7bf77e10848e4572ebc680c2151b45536466ce/docs/ARCHITECTURE.md> | Deterministic math contract, AI boundary negative test, token and data minimization (Manual 4.1, 8, 9) |
| <https://github.com/josephmccann/AI.FO-Demo/blob/fb7bf77e10848e4572ebc680c2151b45536466ce/docs/SIGNAL_METHODOLOGY.md> | Sole methodology authority; "The engine owns the math" (Manual 1.3, 4.1) |
| <https://github.com/josephmccann/AI.FO-Demo/blob/fb7bf77e10848e4572ebc680c2151b45536466ce/docs/scope/SNAPSHOT_ON_CLOSE_V1_SCOPE.md> | Doc-first amendment rule, "the demo is the product", multi-tenant from day one (Manual 4.6, 8) |
| <https://github.com/josephmccann/AI.FO-Demo/blob/fb7bf77e10848e4572ebc680c2151b45536466ce/docs/public-trust-telemetry-APPROACH-2026-06-10.md> | Public-claim integrity: generated never typed, synthetic labeled, round down, staleness flagged (Manual 17) |
| <https://github.com/josephmccann/AI.FO-Demo/blob/fb7bf77e10848e4572ebc680c2151b45536466ce/VISUAL_IDENTITY.md> | Canonical design contract; visual language must not imply autonomous control of financial truth (Manual 1.3, 17) |
| <https://github.com/josephmccann/AI.FO-Demo/blob/fb7bf77e10848e4572ebc680c2151b45536466ce/docs/decisions/2026-07-14-category-and-stage-language.md> | Prohibited positioning terms; founder gate on category change (Manual 17) |
| <https://github.com/josephmccann/AI.FO-Demo/blob/fb7bf77e10848e4572ebc680c2151b45536466ce/docs/decisions/2026-05-18-sealed-snapshot-chronological-order.md> | Refusal of credibility-hole bypasses (Manual 4.6) |
| <https://github.com/josephmccann/AI.FO-Demo/blob/fb7bf77e10848e4572ebc680c2151b45536466ce/docs/audits/aifo_dataflow_redteam_2026-06-15.md> | Adversarial-review habit, "raw can escape by path" method (Manual 9) |

## 6. Superseded or historical inputs

| Source | Status |
|--------|--------|
| AI.FO-Demo PR #190 | Closed unmerged; content folded into PR #180 per the company digest. No independent authority |
| AI-CFO repository founder assets (pitch deck, founding PRD, "Vibe Coding Inputs V1.0") | Historical founder material predating this manual; not inspected for this draft, flagged by the digest as candidate archive material. Any import would be a future amendment with its own evidence |
| Verbal or chat-only founder statements before 2026-07-14 | Captured only insofar as PR #180 recorded them; otherwise not evidence |

## 7. Founder directives

Explicit written founder decisions received during the drafting of this
manual. Each is recorded as an amendment-log row in
[AMENDMENT_AND_TRACEABILITY_PROTOCOL.md](AMENDMENT_AND_TRACEABILITY_PROTOCOL.md),
which is its durable evidence.

| Directive | Recorded |
|-----------|----------|
| 2026-07-15: resequence the three horizons (network intelligence is Horizon 2, the living decision model is Horizon 3; finance remains the trust anchor throughout; confidence qualifier unchanged) | Amendment log version 0.2.0; Manual sections 3 and 19; [PR180_RECONCILIATION.md](PR180_RECONCILIATION.md) revision table |
