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

The documents in this section are **not doctrine** and are **not** covered by
the 2026-07-15 doctrine adoption. They record what is true right now and are
expected to go out of date. Where a current-state document and the manual
appear to disagree about a durable belief, the manual wins.

**They are still governed.**
[AMENDMENT_AND_TRACEABILITY_PROTOCOL.md](AMENDMENT_AND_TRACEABILITY_PROTOCOL.md)
governs every document in `docs/governance/`. Changes here are classified
under its section 1 like any other change, and only the founder merges them.

**Open question, deliberately not answered here.** The protocol's four classes
are defined against doctrine: Editorial is "no change in meaning", Clarifying
is "same doctrine, clearer statement", and Material is "doctrine changes".
A substantive state refresh, moving from pre-seed to seed or changing the
market band, fits none of them cleanly: it changes meaning, so it is not
Editorial or Clarifying, but it amends no principle, standard, or constraint,
so calling it Material strains the definition. The protocol requires every
change to belong to exactly one class, so this is a real gap rather than a
drafting choice. Resolving it is a founder decision and an amendment to the
protocol, not something this index may settle.

**Until it is resolved, this fails closed.**

- Editorial and Clarifying changes to a current-state document proceed
  normally: typo and link repair, formatting, renumbering, or a clearer
  statement of content whose meaning is unchanged. These have a valid class.
- A **substantive refresh, where a recorded fact changes**, has no valid class
  and **must not proceed**. Stop and escalate for a protocol amendment. Do not
  select a class by analogy, do not stretch Material to fit, and do not rely
  on PR-body reasoning to supply authority the protocol does not grant.

Known immediate consequence: the founder verification this document is waiting
on is itself a substantive refresh, so it hits this gate. The protocol
amendment should therefore land before or together with the first verified
update, not after it.

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

The **adopted doctrine documents** listed above are canonical for doctrine
only, and they contain no volatile facts. Company state lives in the
current-state documents listed above, infrastructure truth lives in
[memory/](../../memory/current-state.md) and the architecture and security
documents, product methodology lives in AI.FO-Demo, and the doctrine set never
overrides any of them. See manual section 1.3 and 1.4 for the full authority
hierarchy.

This boundary is about the doctrine set, not the directory.
`docs/governance/` now also holds a current-state document, which exists
precisely to carry the volatile facts the doctrine documents exclude.
