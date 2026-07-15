# PR #180 Reconciliation

Status: DRAFT, pending founder review.
Subject: AI.FO-Demo draft PR #180, "Document founder context and AI.FO
constitutional principles", branch `docs/founder-aifo-context`, reviewed at
head `5d058ee31f60d2e4f84c652a92c9fd310bb20d2c`.
Reconciled into:
[FOUNDER_OPERATING_MANUAL.md](FOUNDER_OPERATING_MANUAL.md) (cited below as
"Manual" with section numbers).

PR #180 self-describes as working drafts, not canonical doctrine, and the
company digest (AIFO-Control-Plane PR #14) classifies it as "valuable
working-draft source material" awaiting reconciliation into one canonical
Founder Operating Manual. This document is that reconciliation crosswalk. It
does not change or close PR #180; disposition is the founder's decision
([Recommended disposition](#recommended-disposition)).

## Item identifiers

Items are numbered by source file:

- RM: `docs/constitution/README.md`
- FC: `docs/constitution/FOUNDER_CONTEXT_WORKING_DRAFT.md`
- CONST: `docs/constitution/AIFO_CONSTITUTION_WORKING_DRAFT.md`
- RA: `docs/constitution/REASONING_ARCHIVE.md`
- CCS: `docs/context/CURRENT_COMPANY_STATE.md`

Pinned source links for each file are in
[SOURCE_MATERIAL_INDEX.md](SOURCE_MATERIAL_INDEX.md).

## Crosswalk summary

| Disposition | Items |
|-------------|-------|
| Imported into the Manual | FC-04, FC-05, FC-08 to FC-15, FC-17 to FC-27; CONST-01 to CONST-05, CONST-07, CONST-08, CONST-13 to CONST-15, CONST-19 to CONST-21, CONST-24 to CONST-26, CONST-28; RM-01, RM-02, RM-04; RA-00 |
| Imported with revision | CONST-16/17 (merged with product-repo statements), CONST-18 (revised per RA-06), CONST-06, CONST-09 to CONST-11, CONST-29 (horizon sequence revised by founder decision of 2026-07-15), CONST-12 and CONST-22/23 (imported with RA confidence qualifiers), FC-16 (durable logic imported, stage-bound framing split off) |
| Rejected as durable doctrine (reclassified) | CONST-07 channel list; CCS-06 placement |
| Classified as temporary company state | CCS-01 to CCS-05, CCS-07 to CCS-14; CONST-07 channel list; the stage-bound half of FC-16 |
| Retained in reasoning archive only | FC-01 to FC-03, FC-06, FC-07; RA-01 to RA-08; CONST-27 decision-ledger detail |
| Founder decision still required | D-1 to D-6 below |

Nothing in PR #180 was found false or contrary to repository evidence; no
item is rejected outright. "Rejected as durable doctrine" means the item is
true but belongs in current-state documents, not in the Manual.

## Material imported into the Manual

| Item | Content (abbreviated) | Manual home |
|------|----------------------|-------------|
| FC-04, FC-05 | Access motivation; "motivated by access to better decisions" | Section 2 |
| FC-17, FC-18 | Definition of success: durable impact plus family security | Section 2 |
| CONST-01 to CONST-03 | Mission; finance as proving ground, not endpoint | Sections 2 and 3 |
| CONST-04, CONST-05 | Earned-trust axiom and six trust requirements | Section 6.2 |
| FC-08 to FC-11 | Humility doctrine; unsupported certainty loses trust | Section 6.3 |
| FC-12, FC-13 | Six-step decision process; context acquisition is not delay | Section 5.1 |
| FC-14, FC-15 | Coaching sequence; complementary teams | Section 14 |
| FC-19 to FC-27 | Nine AI collaboration rules | Section 10.2 |
| CONST-07, CONST-08 | Burden of awareness; continuous communication (channel list excluded, see below) | Section 4.2 |
| CONST-13 to CONST-15 | Structural customer focus, funnel, first-principles build | Section 4.4 |
| CONST-19 to CONST-21 | Hiring illustration; consequential-decision boundary; automation is not authority (CONST-18 itself is listed under imported with revision) | Section 6.1 |
| CONST-24 | Compound founder judgment, not replace critical thinking | Section 16 |
| CONST-25, CONST-26 | Decisions over engagement; login is for depth | Section 4.3 |
| CONST-28 | Seven non-negotiable constraints | Section 4.5 |
| RM-01, RM-02 | Purpose of a doctrine layer; doctrine/state/reasoning separation | Sections 1 and 11 |
| RM-04 | Placement rule: durable beliefs in doctrine, volatile facts in dated state docs | Section 11.3 |
| RA-00 | Reasoning-archive format (framing, discussion, correction, conclusion, confidence) as a durable process norm | Section 11.5 |

## Material imported with revision

| Item | Revision made | Reason |
|------|---------------|--------|
| CONST-18 | Boundary restated as "advice versus accountable decision authority" rather than recommendation versus execution | RA-06 records this as an explicit correction reached in discussion; the corrected form is sharper and is adopted (Manual 6.1) |
| CONST-06, CONST-09 to CONST-11, CONST-29 (horizon sequence) | Resequenced by founder decision of 2026-07-15: Horizon 1 remains continuous financial reasoning; Horizon 2 is now privacy-preserving network intelligence; Horizon 3 is now the living decision model of the company. Finance is stated as the trust anchor, integration layer, and common language throughout | The PR #180 drafts (CONST-09 to CONST-11, RA-03, CCS-11) presented expansion beyond finance as the second horizon and network intelligence as the third. The founder decided that network intelligence begins within finance and is the compounding mechanism that creates the foundation for the broader vision, not a later layer. This is a founder-approved revision to the draft sequencing, recorded in the amendment log (version 0.2.0) in [AMENDMENT_AND_TRACEABILITY_PROTOCOL.md](AMENDMENT_AND_TRACEABILITY_PROTOCOL.md) (Manual 3, 19) |
| CONST-09 to CONST-11 (horizon confidence) | Imported with the qualifier "direction high confidence; sequencing and implementation subject to validation" | RA-03 attaches this confidence caveat; the constitution draft presented the horizons unqualified. The Manual makes the qualifier part of the doctrine, and the 2026-07-15 resequencing leaves it unchanged (Manual 3) |
| CONST-12, CONST-22, CONST-23 (network intelligence) | Imported with explicitly unresolved preconditions: privacy, consent, data governance, causal inference; plus binding interim constraints | RA-04 records these as unresolved; stating the vision without them would overstate certainty, violating FC-11 (Manual 19) |
| CONST-16/17 | Merged with the product repository's stronger operational statements ("The separation is the product"; negative test on the removed raw-prompt route) | Repository evidence (AI.FO-Demo README, ARCHITECTURE, SIGNAL_METHODOLOGY) is more precise than the draft prose and is canonical (Manual 4.1, 8) |
| FC-16 (early-hire stance) | Durable logic imported (founder can temporarily supply judgment and operating context, not technical depth; weight technical capability, accept coaching load); the "first engineering hire" framing classified as current state | The reasoning is durable; the specific hire is stage-bound (CCS-08) (Manual 14) |

## Material rejected as durable doctrine (reclassified, not discarded)

| Item | Ruling |
|------|--------|
| CONST-07 channel list ("email, Slack, Teams, SMS") | The proactive-delivery principle is doctrine; the named channel list is a current-state design choice that RA-05 itself says should be validated with customers. The Manual imports the principle and explicitly excludes channel lists from doctrine (Manual 4.2) |
| CCS-06 (architectural principles restated in the current-state file) | Content is correct and already doctrine (CONST-16/17, CONST-05, FC-27); its placement in a file that says it must not be treated as doctrine violates RM-04. Ruling: doctrine lives in the Manual; the current-state file should link, not restate |

## Material classified as temporary company state

These items are accurate as of their date (2026-07-10) but must never be
cited as doctrine. Their canonical homes are the dated current-state
documents of the owning repositories (AI.FO-Demo memory and context files,
and the company digest once adopted), not this manual.

| Item | Content |
|------|---------|
| CCS-01, CCS-02 | Pre-seed; solo founder |
| CCS-03 | Market band "generally below $50M revenue" (a parameterization of durable CONST-13) |
| CCS-04, CCS-05 | Current product definition; honest gap between product and constitution horizons |
| CCS-07 to CCS-10 | Current priorities, including first engineering hire and SEC-data validation work |
| CCS-11 | Current strategic sequence (its ordering, network intelligence last, is superseded by the founder's 2026-07-15 horizon resequencing; see the revision table above) |
| CCS-12, CCS-13 | Current positioning constraints and preferred framing (operationalized durable rules; the durable versions are Manual 4.5 and 17, and the product repository's positioning decision records govern the current wording) |
| CCS-14 | Monthly review cadence for the current-state file |
| RM-03 | The July 10, 2026 working-draft status statement |

## Material retained only in the reasoning archive

These items should persist as historical reasoning and biography, linked
from [SOURCE_MATERIAL_INDEX.md](SOURCE_MATERIAL_INDEX.md), not restated in
doctrine:

| Item | Content | Why archive, not doctrine |
|------|---------|---------------------------|
| FC-01 to FC-03 | Biographical detail (career history, upbringing) | The Manual summarizes in two sentences and links; duplicating biography invites drift and adds nothing operational |
| FC-06, FC-07 | Views on the fractional-CFO market | Market beliefs are hypotheses to validate, not doctrine; FC-06 is tagged claim-needing-verification in the source inventory |
| RA-01 to RA-08 | Dated reasoning entries with corrections and confidence levels | This is exactly what a reasoning archive is for; the Manual imports the format (RA-00) and the two corrections (RA-04, RA-06) but the entries themselves remain history |
| CONST-27 decision-ledger detail | Insight-level engagement measurement and a future "transparent decision ledger" | The principle is imported (Manual 4.3); the ledger design is a future product decision, not present doctrine |

## Files in PR #180 outside the five-file scope

PR #180 also adds eight files not covered by the constitution/context scope:
`.aifo/company-context.yaml`, `.aifo/tool-registry.yaml`,
`.aifo/workstreams.yaml`, `docs/operating-system/README.md`,
`docs/operating-system/RUNBOOK.md`, and three
`docs/research/founder-finance-discovery/` files. These were not reconciled
here. Recommendation: treat them as separate proposals to be re-raised as
their own scoped PRs if still wanted (decision D-5).

## Founder decisions still required

| ID | Decision | Recommendation |
|----|----------|----------------|
| D-1 | Adopt this manual as the canonical home for founder doctrine (merges this PR) | Adopt; PR #14's hierarchy row already anticipates it |
| D-2 | Disposition of PR #180 itself | Supersede and close (below) |
| D-3 | Adopt the authority hierarchy in Manual 1.4, which also makes the company digest's precedence rules binding | Adopt |
| D-4 | Whether the market band (currently "below $50M revenue") remains a current-state parameter or is promoted to doctrine | Keep as current-state parameter |
| D-5 | Disposition of the eight out-of-scope PR #180 files | Re-raise separately if wanted; do not merge as a side effect of doctrine work |
| D-6 | Where the durable reasoning-archive practice lives going forward (per repository, or a single company archive) | Single archive alongside this manual's amendment log, decided when the first new entry is written |

## Recommended disposition

Recommendation: supersede and close PR #180, with its content preserved as
pinned history.

Reasoning against the alternatives:

- Narrow and merge selected source material: merging any doctrine text into
  AI.FO-Demo would create a second doctrine home the day this manual is
  adopted, violating one-home-per-truth. The current-state content
  (CCS items) is already better covered by AI.FO-Demo's own memory files
  (PR #195) and the company digest (PR #14), so there is no remainder worth
  merging.
- Revise into a historical-source archive: this buys nothing that the closed
  PR does not already provide. The branch head is pinned in
  [SOURCE_MATERIAL_INDEX.md](SOURCE_MATERIAL_INDEX.md), and this crosswalk
  records every item's disposition. Reworking the draft into an archive
  document would spend effort re-editing text that is already superseded.

Conditions attached to the recommendation:

1. Close PR #180 only after this manual is merged, so doctrine is never
   homeless.
2. Preserve the source: keep the `docs/founder-aifo-context` branch or tag
   its head (`5d058ee31f60d2e4f84c652a92c9fd310bb20d2c`) so the pinned links
   in the source index remain resolvable.
3. Record the closure in the closing comment by linking to this
   reconciliation and the merged manual.
4. Decide D-5 (the eight out-of-scope files) explicitly in the same closing
   comment, so nothing stops silently.

This document does not execute any of the above. PR #180 remains open and
unchanged until the founder decides.
