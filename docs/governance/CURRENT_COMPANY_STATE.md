# AI.FO Current Company State

Status: PROVISIONAL. Content carried forward from 2026-07-10 and not yet
re-verified by the founder. See [Verification required](#verification-required).

Content as of: 2026-07-10
Recorded here: 2026-07-25

This is a dated current-state document, not doctrine. It holds the volatile
facts that [FOUNDER_OPERATING_MANUAL.md](FOUNDER_OPERATING_MANUAL.md)
deliberately excludes under manual section 11.3: stage, market definition,
product framing, priorities, and positioning constraints. Nothing here is
permanent, and nothing here overrides the manual. Where the two appear to
disagree about a durable belief, the manual wins; where they disagree about
what is true right now, this file wins, per the manual's authority hierarchy
(section 1.4, tier 6).

## Why this file exists

The manual states that volatile facts "are linked to their canonical
current-state homes." For AI.FO company state that home did not exist. The
manual's section 4.4 pointed at the product repository's positioning
documents, but `REPO_HYGIENE.md` in AI.FO-Demo excludes planning and
positioning content from that repository, and the drafts that would have held
it were closed unmerged for exactly that reason (AI.FO-Demo PR #190 on
2026-07-15, PR #180 on 2026-07-25).

[PR180_RECONCILIATION.md](PR180_RECONCILIATION.md) classified items CCS-01 to
CCS-05 and CCS-07 to CCS-14 as temporary company state and assumed they would
be covered by AI.FO-Demo PR #195 and by Control Plane PR #14. PR #195 has since
been closed as a stale checkpoint, and PR #14 remains an unmerged draft. This
file closes that gap.

## Provenance

Seeded from `docs/context/CURRENT_COMPANY_STATE.md` in AI.FO-Demo draft PR
#180, branch `docs/founder-aifo-context`, at the pinned head
`5d058ee31f60d2e4f84c652a92c9fd310bb20d2c`. That branch is preserved. Content
is reproduced without revision so that the crosswalk in
[PR180_RECONCILIATION.md](PR180_RECONCILIATION.md) stays item-addressable.

## Verification required

Every fact below is 15 days old at the time of recording and none of it has
been re-confirmed. Treat this file as provisional until the founder reviews it
and replaces this section with a verification date. Items most likely to have
moved: stage and fundraising status, product priorities, and the hiring item.

Open decision D-4 from the reconciliation, whether the revenue band stays a
current-state parameter or is promoted to doctrine, is recorded as unresolved.
The recommendation on file is to keep it here as current state, which is the
placement this document assumes.

## Stage

- Pre-seed
- Solo founder: Joseph McCann
- Current primary market: founder-led businesses and small-to-midsize
  companies, generally below $50M in revenue and before deep internal finance
  infrastructure

## Current product definition

AI.FO is currently being built as a continuous CFO reasoning system. It ingests
financial data, computes deterministic metrics and signals, and uses a separate
AI layer to explain findings, prioritize issues, and recommend actions.

The current product is not yet the full business decision network described in
the long-range vision. The broader business reasoning and network-intelligence
horizons remain directional strategy rather than present-tense product
capability.

## Current architectural principles

- Deterministic engine owns calculations.
- AI layer interprets computed outputs and does not alter the math.
- Important outputs should be traceable, explainable, and independently
  validated.
- Product claims should remain bounded by capabilities that exist and have been
  tested.

These restate, in current-state terms, doctrine held in manual sections 6 and
7. The manual is authoritative for the durable form.

## Current product priorities

1. Build and validate the financial reasoning product.
2. Run the first beta/design-partner cohort.
3. Make the first engineering hire; exact title and level remain to be
   determined.
4. Improve data integrations and reduce manual context collection.
5. Establish a proactive delivery cadence for insights and priorities.
6. Continue system validation, including work using public SEC data.

## Current strategic sequence

- Near term: financial trust and continuous CFO reasoning.
- Next: selected operational data and broader business reasoning.
- Long term: anonymized network intelligence and collective operating
  experience.

## Current positioning constraints

Do not describe AI.FO as:

- accounting software;
- bookkeeping software;
- another dashboard;
- an autonomous finance department;
- a system that currently possesses cross-company network intelligence;
- a system that makes accountable company decisions.

Preferred current framing:

AI.FO is a financial reasoning layer above systems of record. It identifies
financial signals, explains what they mean, and recommends what founders should
consider doing next.

## Relationship to other claim authorities

This file governs positioning and company state. It does not govern engine
numbers. Signal counts, thresholds, formulas, and benchmarks are owned by
AI.FO-Demo's `docs/CANONICAL_CLAIMS.md` and `docs/SIGNAL_METHODOLOGY.md`. Do
not restate an engine figure here; link to those instead.

## Review cadence

Review monthly, or whenever fundraising status, product stage, customer
traction, hiring priorities, or core messaging materially changes. Record the
review date in the header rather than leaving the content silently aging.
