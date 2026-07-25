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
`5d058ee31f60d2e4f84c652a92c9fd310bb20d2c`. That branch is preserved.

Content follows the **item-level dispositions** in
[PR180_RECONCILIATION.md](PR180_RECONCILIATION.md), not a blanket copy. Items
classified there as temporary company state (CCS-01 to CCS-05, CCS-07 to
CCS-10, CCS-12 to CCS-14) are carried forward as written. Two are not:

- **CCS-06**, architectural principles, was reclassified as doctrine with the
  ruling that a current-state file must link rather than restate. It links.
- **CCS-11**, the strategic sequence, had its ordering superseded by the
  founder decision of 2026-07-15 (amendment log 0.2.0). The superseded
  ordering is not reproduced.

A verbatim copy would have reintroduced both defects, one of them contradicting
a founder decision.

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

## Architectural principles

Not restated here. The reconciliation ruled on this directly (CCS-06):
architectural principles are doctrine, and a file that declares itself
non-doctrine must link rather than restate them.

In [FOUNDER_OPERATING_MANUAL.md](FOUNDER_OPERATING_MANUAL.md):

- **4.1** for the deterministic-engine boundary: deterministic systems own
  computation, AI owns interpretation, and the AI layer must not silently
  recalculate or alter authoritative financial outputs.
- **6.1** for the rule that AI.FO reasons while people govern.
- **7** for engineering standards, including traceability and independent
  validation.
- **4.5** and **17** for the constraint that claims stay bounded by tested
  capability: 4.5 prohibits making claims the product has not earned, and 17
  sets the investor and public-claim standards.

## Current product priorities

1. Build and validate the financial reasoning product.
2. Run the first beta/design-partner cohort.
3. Make the first engineering hire; exact title and level remain to be
   determined.
4. Improve data integrations and reduce manual context collection.
5. Establish a proactive delivery cadence for insights and priorities.
6. Continue system validation, including work using public SEC data.

## Position in the strategic sequence

The sequence itself is doctrine and lives in
[FOUNDER_OPERATING_MANUAL.md](FOUNDER_OPERATING_MANUAL.md) section 3: Horizon 1
is continuous financial reasoning, Horizon 2 is privacy-preserving network
intelligence, and Horizon 3 is a living decision model of the company.

Current state is only where AI.FO sits within it: **Horizon 1**, building and
validating financial trust and continuous CFO reasoning. Horizon 2 has not
begun.

The PR #180 draft placed network intelligence last, after broader business
reasoning. That ordering was superseded by the founder decision of 2026-07-15
(amendment log version 0.2.0) and is recorded as superseded at CCS-11 in
[PR180_RECONCILIATION.md](PR180_RECONCILIATION.md). It is not carried forward.

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

Note the gate before you edit. A review that only records a date, or that
restates unchanged content more clearly, is Editorial or Clarifying and
proceeds normally. A review that **changes a recorded fact** currently has no
valid class under
[AMENDMENT_AND_TRACEABILITY_PROTOCOL.md](AMENDMENT_AND_TRACEABILITY_PROTOCOL.md)
section 1 and must stop for a protocol amendment first. See the current-state
section of [README.md](README.md). This is a known gap, not a reason to skip
the review: run it, then escalate what it found.
