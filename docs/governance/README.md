# Governance

Canonical founder and company governance documents for AI.FO.

Status: ADOPTED by the founder on 2026-07-15. These documents are the
canonical home for AI.FO founder doctrine; their provenance is recorded in
[SOURCE_MATERIAL_INDEX.md](SOURCE_MATERIAL_INDEX.md), and they change only
through
[AMENDMENT_AND_TRACEABILITY_PROTOCOL.md](AMENDMENT_AND_TRACEABILITY_PROTOCOL.md).

## Documents

| Document | Role |
|----------|------|
| [FOUNDER_OPERATING_MANUAL.md](FOUNDER_OPERATING_MANUAL.md) | The canonical Founder Operating Manual: mission, vision, decision framework, trust and authority model, engineering and architectural doctrine, security and privacy principles, AI-agent operating model, documentation and memory model, cost philosophy, customer and investor standards, recoverability, and the network-intelligence vision |
| [AMENDMENT_AND_TRACEABILITY_PROTOCOL.md](AMENDMENT_AND_TRACEABILITY_PROTOCOL.md) | How governance documents change: change classes, approval rules, the explicit-statement rule for agent-permission expansions, supersession rules, and the amendment log |
| [PR180_RECONCILIATION.md](PR180_RECONCILIATION.md) | Item-level crosswalk of AI.FO-Demo draft PR #180 (constitution and founder-context working drafts) into the manual, with a recommended disposition for that PR |
| [SOURCE_MATERIAL_INDEX.md](SOURCE_MATERIAL_INDEX.md) | Pinned sources for every doctrine statement, including commit-pinned links to unmerged draft material |

## Current-state documents

The status above applies to the adopted doctrine set only. The documents in
this section are **not doctrine**, are **not** covered by the 2026-07-15
adoption, and change on their own cadence rather than through the amendment
protocol. They record what is true right now and are expected to go out of
date. Where a current-state document and the manual appear to disagree about a
durable belief, the manual wins.

| Document | Role | Status |
|----------|------|--------|
| [CURRENT_COMPANY_STATE.md](CURRENT_COMPANY_STATE.md) | Stage, market band, product framing, priorities, and positioning constraints: the canonical home for the volatile facts the manual excludes under section 11.3 | PROVISIONAL, content dated 2026-07-10 and not yet founder-verified |

## Reading order

1. New to AI.FO: read the manual front to back; it assumes no verbal
   context.
2. Working as an agent or engineer: read the manual's sections 1, 5, 10,
   and 11, then the `AGENTS.md` of the repository you are working in.
3. Reviewing the doctrine's provenance: read the reconciliation and the
   source index.
4. Proposing a change to any of these documents: read the amendment
   protocol first.

## Boundaries

These documents are canonical for doctrine only. They contain no volatile
facts: company state lives in dated current-state documents, infrastructure
truth lives in [memory/](../../memory/current-state.md) and the architecture
and security documents, product methodology lives in AI.FO-Demo, and this
directory never overrides any of them. See manual section 1.3 and 1.4 for
the full authority hierarchy.
