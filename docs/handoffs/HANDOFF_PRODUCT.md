# AI.FO Product Handoff

## Purpose

This document is the canonical starting context for product, application architecture, customer value, roadmap, financial reasoning, and design-partner work.

## Stable Context

AI.FO is building a continuous financial decision system for founder-led small and mid-sized organizations, generally below $50 million in annual revenue.

The long-term vision is to become the institutional reasoning layer for founder-led businesses, beginning with finance.

The product is not intended to replace human judgment. It is intended to improve the quality, speed, transparency, and institutional memory of decisions.

## Core Product Thesis

Founder-led companies frequently make consequential decisions using fragmented financial, operational, and behavioral information. They often lack continuous access to experienced CFO judgment and may not know which questions to ask.

AI.FO should:

- ask more questions than a founder initially thinks are necessary;
- identify missing information before relying on inference;
- search connected systems for missing information in parallel;
- tell the founder where unavailable information can be obtained;
- distinguish observed, reported, derived, inferred, and unknown inputs;
- lower confidence explicitly when recommendations depend on inference;
- preserve the information state that existed when a recommendation was made;
- explain the cost of action, delay, and inaction;
- retain human authority over final decisions;
- learn through outcomes and structured reflection.

## Foundational Principles

- Trust is earned, not assumed.
- Silos undermine trust because they remove context.
- The system must explain why different data or scenarios produce different scores or recommendations.
- The system must acknowledge when no clean answer exists and show the likely harms and tradeoffs.
- Human value should be represented without ranking one stakeholder's worth over another.
- Better questions produce better context; better context produces better decisions.
- The product should be probabilistic and company-specific, not a static deterministic decision matrix.
- A great leader is not always the smartest person in the room, but seeks to understand the most.
- The purpose is not merely to produce answers; it is to improve the reasoning process that leads to decisions.

## Product Architecture Direction

### Deterministic financial foundation

Financial calculations, normalization, ratios, trends, and defined models should be deterministic and testable. LLMs reason about validated outputs rather than replacing accounting and financial computation.

### Evidence and knowledge lineage

Material inputs should be classified as:

- Observed
- Reported
- Derived
- Inferred
- Unknown

Every recommendation should expose source lineage, assumptions, confidence, and missing information.

### Decision ledger

For each material decision, preserve:

- context;
- available data;
- missing data;
- assumptions and inferences;
- recommendation;
- confidence;
- alternatives;
- human decision;
- outcome;
- reflection and learning;
- counterfactual result when later information becomes available.

Do not overwrite the historical decision state when better data arrives. Preserve what was known and believed at the time.

### Organizational learning

AI.FO should create a learned financial, operational, and behavioral knowledge base. The value is not only preserving information, but preserving how decisions were reached, what evidence existed, why a decision was made, and what was learned afterward.

## Current Application Repository

Primary product repository:

`josephmccann/AI.FO-Demo`

Known current product work includes:

- deterministic financial engine;
- QuickBooks Online connectivity and recovery;
- operating metric connector architecture, initially including Stripe observations;
- trust evidence surfaces;
- board-package snapshots;
- account and commercial-readiness surfaces;
- source inspection and data health;
- calibration and operating suggestions.

Open product PRs and implementation state should be reviewed directly in GitHub before making new roadmap assumptions.

## Near-Term Commercial Wedge

The immediate value proposition should remain narrow:

> AI.FO is a continuous financial decision system for founder-led businesses.

Avoid marketing the product as a generic enterprise reasoning system. That language creates comparisons with heavily capitalized enterprise platforms and obscures the initial customer and use case.

## Current Priority

Put a useful product into founder hands rapidly while conducting structured discovery. The immediate work is not a 50–70 page philosophical document. Product and fundraising should be informed by real evidence from potential customers.

## Product Discovery Questions

The research should identify:

- how founders make consequential financial decisions today;
- where data is fragmented;
- which financial surprises occur repeatedly;
- who founders rely on for judgment;
- what decisions are delayed by low confidence;
- which decisions are made with false confidence;
- how trust changes when explanations and data lineage are available;
- whether decision history and reflection create practical value;
- which initial use cases are painful and frequent enough to pay for;
- which founders can become design partners.

## Open Product Decisions

- What is the first repeated workflow that creates enough immediate value to drive adoption?
- Is the decision ledger a primary interface, a supporting capability, or both?
- Which proactive insight should the product deliver before a founder asks?
- What level of autonomy is acceptable in the first release?
- How should confidence and uncertainty be communicated without overwhelming users?
- Which connected systems are required for the first design-partner cohort?
- Which customer segment has the highest urgency and lowest adoption friction?

## Definition of Near-Term Success

- 25 standardized founder/finance interviews completed.
- Clear evidence of repeated high-value financial decision pain.
- Five to ten credible design-partner candidates identified.
- Product scope reduced to the smallest workflow that solves a painful recurring problem.
- Design partners use the product with real company data.
- Evidence and customer language strengthen the fundraising narrative.