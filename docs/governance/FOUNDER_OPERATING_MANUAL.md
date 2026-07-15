# AI.FO Founder Operating Manual

Status: DRAFT, pending founder review and merge approval.
Owner: Joseph McCann (founder).
Version: 0.2.0 (pre-adoption draft).
Created: 2026-07-14.

This document becomes the canonical home for AI.FO founder doctrine when the
founder merges it. Until merge, treat it as proposed text. After merge, it is
amended only through the process in
[AMENDMENT_AND_TRACEABILITY_PROTOCOL.md](AMENDMENT_AND_TRACEABILITY_PROTOCOL.md).

Every statement in this manual is doctrine unless it is explicitly marked as a
link to current state. Volatile facts (budgets, instance identifiers, product
stage, traction) are never stated here; they are linked to their canonical
current-state homes. Sources for every imported principle are pinned in
[SOURCE_MATERIAL_INDEX.md](SOURCE_MATERIAL_INDEX.md).

## Contents

1. [Purpose and authority](#1-purpose-and-authority)
2. [Founder mission and motivation](#2-founder-mission-and-motivation)
3. [Long-term company vision](#3-long-term-company-vision)
4. [Product philosophy](#4-product-philosophy)
5. [Decision framework](#5-decision-framework)
6. [Trust and human-authority model](#6-trust-and-human-authority-model)
7. [Engineering standards](#7-engineering-standards)
8. [Architectural values](#8-architectural-values)
9. [Security and privacy principles](#9-security-and-privacy-principles)
10. [AI-agent operating model](#10-ai-agent-operating-model)
11. [Documentation and memory model](#11-documentation-and-memory-model)
12. [Program-management principles](#12-program-management-principles)
13. [Communication preferences](#13-communication-preferences)
14. [Leadership and organizational style](#14-leadership-and-organizational-style)
15. [Cost and resource-allocation principles](#15-cost-and-resource-allocation-principles)
16. [Customer standards](#16-customer-standards)
17. [Investor and public-claim standards](#17-investor-and-public-claim-standards)
18. [Founder recoverability and succession](#18-founder-recoverability-and-succession)
19. [Network-intelligence vision](#19-network-intelligence-vision)
20. [Amendment, supersession, and traceability](#20-amendment-supersession-and-traceability)

Appendix: [The twenty-four founder principles](#appendix-the-twenty-four-founder-principles)

## 1. Purpose and authority

### 1.1 Why this document exists

Before this manual, AI.FO founder doctrine had no canonical home. The company
digest drafted in AIFO-Control-Plane PR #14 records this explicitly in its
source-of-truth hierarchy: founder doctrine had only working-draft source
material (AI.FO-Demo PR #180) and a company handoff
([docs/handoffs/HANDOFF_COMPANY.md](../handoffs/HANDOFF_COMPANY.md)), and it
recommended reconciling both into one canonical Founder Operating Manual. This
document is that reconciliation. The crosswalk against PR #180 is in
[PR180_RECONCILIATION.md](PR180_RECONCILIATION.md).

### 1.2 What this manual governs

This manual is canonical for:

- founder mission, motivation, and vision;
- the decision framework and approval model;
- the trust and human-authority model;
- durable engineering, architectural, security, and cost doctrine;
- the AI-agent operating model and agent permission tiers;
- the documentation and organizational-memory model;
- customer, investor, and public-claim standards;
- founder recoverability expectations;
- the amendment and traceability process for all of the above.

### 1.3 What this manual does not govern

This manual never becomes a second source of truth for matters that already
have a canonical home. It links instead. In particular:

- Signal methodology: `docs/SIGNAL_METHODOLOGY.md` in AI.FO-Demo. No other
  document, including this one, may claim methodology authority.
- Product metrics (signal, test, and assertion counts): derived telemetry in
  AI.FO-Demo, never typed numbers.
- Visual identity: `VISUAL_IDENTITY.md` in AI.FO-Demo and its token files.
- Infrastructure design and state: this repository's
  [docs/architecture.md](../architecture.md),
  [docs/security-model.md](../security-model.md), ADRs, and
  [memory/](../../memory/current-state.md) files.
- Repository-specific agent rules: each repository's `AGENTS.md`.
- Specific recorded decisions: the ADR or decision record that made them.

### 1.4 Authority hierarchy

The following hierarchy is recommended for adoption with this manual. Each
document class is authoritative for its own domain; the hierarchy resolves
conflicts about doctrine and expectations.

| Rank | Document class | Authoritative for | On conflict |
|------|----------------|-------------------|-------------|
| 1 | Founder Operating Manual (this document) | Founder doctrine, decision framework, authority model, durable principles | Wins on doctrine; defers to domain documents for domain facts |
| 2 | `AGENTS.md` (per repository) | Operational rules for agents working in that repository | Must implement this manual; where it conflicts, the more restrictive rule applies until reconciled by amendment |
| 3 | ADRs and accepted decision records | The specific decisions they record, including context and reversibility | A decision stands until superseded by a newer accepted record |
| 4 | Product methodology documents (for example `docs/SIGNAL_METHODOLOGY.md`) | Domain methodology, formulas, thresholds, benchmarks | Sole authority in their domain |
| 5 | Architecture and security documents | Design intent, threat models, security controls | Sole authority for design; current-state documents report what is actually deployed |
| 6 | Current-state documents (`memory/`, dated state files) | What is true right now | Runtime state beats all documents for what is happening right now |
| 7 | Work queues and workstream documents | What work is planned or in flight | Planning records, not commitments or claims |
| 8 | Session handoffs | What a past session knew and did | Historical evidence; never updated, only superseded by newer dated files |
| 9 | Company digest (`docs/company/`, proposed in PR #14) | Cross-repository orientation | An index, never an override; where it disagrees with an owning repository, the repository wins and the digest is corrected |
| 10 | Marketing and public claims | Nothing | Bound by everything above; never a source of truth |
| 11 | Research findings | Evidence inputs to decisions | Inform doctrine; do not create it |

Precedence rules when sources conflict, adopted from the company digest
(PR #14, `docs/company/SOURCE_OF_TRUTH_HIERARCHY.md`):

1. Merged beats unmerged.
2. Derived beats written.
3. Dated-current beats dated-old.
4. The owning repository beats every other repository.
5. Repository evidence beats repository names, GitHub descriptions, and memory.
6. Runtime state beats all documents for what is happening right now.

Practical consequence: an agent or engineer who finds two documents in
disagreement fixes the lower-ranked one to link to the higher-ranked one, and
records the correction. Nobody argues from an unmerged draft, a repository
name, or a recollection.

### 1.5 Intended readers

Joe, future employees, technical leaders, AI engineering agents, investors
conducting diligence, advisors, and any operator who must assume
responsibility after an interruption. The manual assumes no prior verbal
context; everything needed to act consistently with the founder's judgment is
written here or linked from here.

## 2. Founder mission and motivation

Joseph McCann founded AI.FO after more than twenty years of finance and
operating experience, including CFO and COO roles. He learned to build
AI-native software in order to create AI.FO. Fuller biographical context is
retained in the source material indexed in
[SOURCE_MATERIAL_INDEX.md](SOURCE_MATERIAL_INDEX.md) and is deliberately not
duplicated here.

The motivation is access: high-quality guidance should not be reserved for
people and companies with capital, elite networks, or privileged starting
positions. Joe is motivated by access to better decisions. AI.FO begins by
democratizing access to trustworthy financial judgment; the larger mission is
access to better business decisions.

Success has two components, and both are required:

- Financial success sufficient to provide multigenerational security for his
  family.
- Durable impact: better business decision-making becomes accessible to
  companies that historically could not afford it. Joe would prefer a smaller
  but still generationally significant outcome that materially changes how
  businesses make decisions over a larger outcome that leaves no durable
  impact.

Practical consequence: when growth and trust conflict, trust wins. When a
shortcut increases enterprise value but weakens the credibility of the system,
the shortcut is rejected. This is restated as a non-negotiable constraint in
[Section 4.5](#45-non-negotiable-product-constraints).

## 3. Long-term company vision

The vision proceeds in three horizons. Direction is held with high confidence;
sequencing and implementation remain subject to validation. That confidence
qualifier is doctrine, imported from the reasoning archive in PR #180, and it
must survive into any restatement of the horizons. The ordering of Horizons 2
and 3 below was set by founder decision on 2026-07-15, superseding the
sequence in the PR #180 drafts; the decision is recorded in the amendment log
and in [PR180_RECONCILIATION.md](PR180_RECONCILIATION.md). Finance remains the
trust anchor throughout all three horizons.

### Horizon 1: Continuous financial reasoning

AI.FO begins as a continuous CFO reasoning system for founder-led companies.
It maintains an evolving view of each business, identifies financial signals,
explains what they mean, models possible outcomes, and updates priorities as
new data arrives.

Finance is the proving ground because trust is hardest to earn there. Errors
are consequential, claims must be verifiable, and recommendations require
judgment, lineage, and accountability. By earning trust in the hardest
domain, AI.FO establishes the right to expand. Finance is the proving ground,
not the endpoint.

### Horizon 2: Network intelligence

The next horizon is privacy-preserving network intelligence. Each company
initially reasons only from its own history. Over time, appropriately
anonymized, permissioned, and governed signals across many companies can
create intelligence that no individual company could build alone.

This may include patterns in payment behavior, customer risk, working-capital
cycles, operating performance, and industry-specific decision outcomes. The
experience of one company can help many companies, and the experience of many
companies can help each one.

Network intelligence is not a separate future product layered onto AI.FO
after finance. It is the compounding mechanism that begins within finance and
creates the foundation for the larger company vision.

This horizon carries unresolved requirements involving privacy, consent, data
governance, security, representativeness, and causal inference. Those
requirements are binding design constraints, not implementation details; see
[Section 19](#19-network-intelligence-vision).

### Horizon 3: A living decision model of the company

Once AI.FO has earned trust in financial reasoning and established a governed
network-intelligence foundation, it can expand outward from finance into
commercial, workforce, customer, contractual, and operating information.

The result is a living decision model of the company: a system that
understands how financial and operating decisions interact, preserves the
reasoning and outcomes behind those decisions, and helps leaders make better
choices across the business.

This expansion is not a pivot away from finance. Finance remains the trust
anchor, integration layer, and common language through which broader company
decisions can be evaluated.

Practical consequence: work that strengthens Horizon 1 trust and the
Horizon 2 network foundation outranks speculative expansion into Horizon 3.
No public claim may describe a later horizon as a present capability.

## 4. Product philosophy

### 4.1 The separation is the product

Deterministic systems own computation. AI owns interpretation. The
deterministic engine calculates metrics, ratios, scenarios, constraints, and
signals. The AI layer receives only a server-built computed snapshot and
explains findings, identifies relationships, communicates tradeoffs,
prioritizes issues, and recommends actions. The AI layer must not silently
recalculate or alter authoritative financial outputs. The product repository
states the consequence exactly: "The separation is the product. The engine is
deterministic and auditable. The AI writes the memo ... but cannot change the
numbers."

Practical consequence: any feature, integration, or prompt path that would let
generative output modify, replace, or bypass deterministic financial values is
rejected at design time, and removing such a path is always in scope.

### 4.2 The burden of awareness belongs to AI.FO

A good CFO does not wait for the CEO to open an application and ask the
correct question. AI.FO proactively delivers good news, bad news, status,
emerging risks, immediate needs, changing priorities, and confirmation when
the business remains on plan. Silence is not knowledge; continuous
communication is part of the trust relationship. Login is for depth (scenario
work, board material, evidence investigation), not for the baseline
relationship.

The specific delivery channels and cadence are current-state choices to be
validated with customers, not doctrine. Do not hard-code a channel list into
durable documents.

### 4.3 Build for decisions, not engagement

AI.FO does not optimize for time spent in the application. It optimizes for
useful decision interactions and improved outcomes. Engagement is measured at
the level of delivered insights and recommendations: read, investigated,
shared, accepted, rejected, acted upon, and what happened afterward. The
long-term expression of this is a transparent decision ledger that preserves
recommendations, human decisions, rationale, outcomes, and learning.

### 4.4 Structural customer focus

The target customer is the widest and least-served part of the business
ecosystem: founders, small and midsize businesses, and companies before they
have accumulated large finance teams. This focus is structural, not a
beachhead to abandon. Serving larger companies later should result from the
system scaling upward, not from weakening the product for the customers it
was created to serve. AI.FO is built for this market from first principles;
it is not an enterprise product reaching backward.

The current revenue-band definition of this market is a current-state
parameter, recorded in the product repository's positioning documents, not
here.

### 4.5 Non-negotiable product constraints

AI.FO must not:

1. sacrifice trust for growth;
2. make claims the product has not earned;
3. drift upmarket in a way that abandons founder-led and small businesses;
4. confuse automation with authority;
5. make accountable human decisions on behalf of a company;
6. use AI-generated confidence as a substitute for evidence;
7. become merely a chatbot, dashboard, or engagement destination.

Practical consequence: these seven constraints are decision-terminating. A
proposal that violates one does not proceed to cost-benefit analysis; it is
reframed until it no longer violates the constraint, or it is dropped.

### 4.6 The demo is the product

The demo does not simulate the product. It is the product, running against a
synthetic customer through real API paths. Demo credibility holes are product
defects. This standard was set when a sealed-snapshot ordering bypass was
refused even for admin convenience, because a bypass would reopen a
credibility hole.

## 5. Decision framework

### 5.1 The default reasoning process

For difficult problems, the default process is:

1. Gather comprehensive context.
2. Separate facts, assumptions, and unknowns.
3. Identify the core decision that actually matters.
4. Map the system: dependencies, incentives, second-order effects.
5. Form and test an initial hypothesis.
6. Look for contradictions, weak points, and invalidating evidence.

Context acquisition is not delay; it is a prerequisite for sound judgment.
Recommendations are bounded by the completeness and quality of the available
context, and a recommendation should say so.

### 5.2 What counts as a material decision

A decision is material, and requires a durable record, when it affects trust
boundaries, security controls, IAM or network topology, data lineage or
retention, product methodology, recurring cost, recovery or rollback,
privacy, public claims, or any exception to a non-negotiable constraint.
Material decisions are recorded as ADRs or dated decision records in the
owning repository, following that repository's template. The control-plane
ADR template ([docs/adr/0000-adr-template.md](../adr/0000-adr-template.md)) is
the reference standard: it requires the current product requirement served,
the founder principle implicated, known facts versus assumptions versus
unknowns, solo-founder recoverability, data-lineage impact, reversibility,
and the evidence that would cause reconsideration.

Practical consequence: "we discussed it" is not a decision. If there is no
dated, reviewable record, the decision has not been made.

### 5.3 Decision packets and approval tiers

Consequential decisions are presented to the founder as decision packets, in
the pattern established by the product runtime architecture package (PR #13):

- a recommendation with weighted reasoning, not a menu;
- alternatives considered, with why they lost;
- consequences of each path;
- the latest safe decision date, anchored to a real event, so urgency is
  evidence-based rather than rhetorical.

Approval is tiered, and a higher tier never implies a lower one:

1. Strategic direction (for example: migrate before real customer data).
2. Implementation specifics (sizes, topologies, budgets, names).
3. Deployment approval (permission to create or mutate real resources).
4. Cutover approval (permission to move real customers or real data).

Practical consequence: "approved in principle" authorizes design work only.
No resource is created, no money is committed, and no data moves on a
strategic approval.

### 5.4 Evidence rules

- Merged beats unmerged; derived beats written; dated-current beats
  dated-old.
- "Configured" without a tested result is not a pass for recovery or safety
  controls. A backup that has not been restored is not a backup.
- Proposed documents count as evidence drafts, not approvals.
- Material decisions cite primary sources (official vendor documentation,
  measured data, priced quotes with dates). Blogs may inform options but are
  never the sole basis for a material decision.
- Every decision record names the evidence that would cause reconsideration.

### 5.5 Open decisions are tracked, not remembered

Undecided material questions live in the owning repository's open-decisions
ledger (for example [memory/open-decisions.md](../../memory/open-decisions.md))
with an identifier, owner, needed-by date, and what they block. Resolved
decisions move to a resolved table with the resolution and date. A decision
that is not in the ledger and not in a record is not pending; it is unasked.

## 6. Trust and human-authority model

### 6.1 AI.FO reasons; people govern

The boundary is not recommendation versus execution. The boundary is advice
versus accountable decision authority. AI.FO may be highly opinionated. It
may analyze, model, recommend, prepare execution, and automate analysis,
monitoring, drafting, reporting, scenario preparation, and approved
workflows. It must not assume the authority or accountability of an
executive. Accountable people make the decision on hiring, pricing,
financing, layoffs, major contracts, capital allocation, and other
consequential matters. Automation is not the same as authority.

Illustration: AI.FO may recommend that a company hire an executive, define
the need, develop criteria, and analyze candidates. It does not choose the
human who will hold the role.

### 6.2 Trust must be earned

AI.FO's legitimacy depends on earned trust. Growth, speed, and ambition
cannot compensate for a system that becomes less rigorous, less transparent,
or more willing to overstate certainty. Earned trust requires:

1. claims supported by evidence;
2. facts distinguished from assumptions and uncertainty;
3. recommendations that are traceable and explainable;
4. deterministic outputs validated independently;
5. progress and limitations communicated honestly;
6. improvement through controlled releases rather than waiting for
   perfection or pretending the product is perfect.

### 6.3 Humility is the foundation of good judgment

A credible system explains what it knows, what it assumes, what remains
unknown, and how it intends to improve. Trust is earned, not expected.
Progress should not wait for perfection, but uncertainty must not be hidden.
Unsupported certainty is one of the fastest ways to lose the founder's
trust; it is also the fastest way for the product to lose a customer's.

## 7. Engineering standards

AI.FO is built to world-class engineering standards. Every artifact is
expected to withstand review by experienced engineers, security reviewers,
investors, partners, and future employees. Best-in-class here means clarity,
restraint, maintainability, security, and cost discipline, not novelty.

Durable standards, evidenced across both repositories:

- Tests are the source of truth. If a change breaks them, fix the change, not
  the test. A deliberately failing test may be left in place as the durable
  record of a removal or a known gap.
- Financial logic ships with provenance. Every signal ships in one PR with
  its implementation, a sourcing-citation test naming source, methodology,
  and threshold, and property assertions. If the methodology cannot be cited
  with a specific reference, do not invent one; the signal does not ship.
- Published numbers are derived, never typed. Counts, versions, and metrics
  are generated from the source registry by a single writer; hardcoded copies
  are defects.
- Reproducibility is a requirement. A fresh clone must be able to run the
  test suites and regenerate derived artifacts. If it cannot, that is a P0
  bug.
- Tooling is pinned and verified. Development and lint tools install at
  pinned versions with checksum verification and fail closed on mismatch.
- Work is narrow. Branch per task, one PR per task, no scope creep; document
  follow-ups instead of expanding. Unrelated changes are not combined unless
  they form one coherent decision.
- Every PR body states the problem, the solution, the verification actually
  performed, and the rollback path.
- Validation runs before push, using the owning repository's documented
  entrypoint (here, `scripts/validate.sh`).

Practical consequence: an agent or engineer who cannot cite the verification
they ran has not finished the task.

## 8. Architectural values

- Deterministic truth before generative interpretation (Principle 15). The
  computation and interpretation layers stay architecturally separate, and
  the separation is testable: the product repository ships a negative test
  asserting the removed raw-prompt path stays removed.
- Source systems remain authoritative (Principle 16). AI.FO is a reasoning
  layer above systems of record; it does not become the system of record for
  customers' accounting data.
- Recommendations require lineage (Principle 17). Important outputs are
  traceable, explainable, and independently validated. Distinctions between
  observed, reported, derived, inferred, and unknown are preserved through
  the pipeline.
- Build for the requirement that exists. Infrastructure is gated on a
  documented product requirement. Deferral is a decision with a trigger:
  deferred items name the evidence (measured load, contractual availability,
  compliance, team size, incident) that would cause reconsideration.
- Prefer managed services and boring technology at the current scale. No
  Kubernetes, service mesh, or microservice split without evidence that
  exceeds the current design.
- Design for one operator. Every architectural decision explains how one
  person can recover, roll back, or reason about the system.
- Be honest about reversibility. Do not pretend every change can be rolled
  back in place; where rollback is forward-fix or point-in-time restore, say
  so before the change is approved. Automatic schema convergence is never
  authoritative.
- Isolation lives in the product and data layer, not in assumptions about
  network segmentation. Multi-tenant correctness is tested, not asserted.

## 9. Security and privacy principles

Non-negotiable controls, held company-wide (the control-plane statement is
[SECURITY.md](../../SECURITY.md)):

- No long-lived cloud access keys; short-lived, identity-federated
  credentials only.
- No secrets in repositories, state files, logs, or command output.
- Deny by default for inbound network access; administrative access through
  audited, centralized paths only, never public SSH.
- Separate duties between human, plan, apply, and runtime permissions.
- No production mutation without an explicit, scoped human approval.
- Emergencies do not suspend doctrine. There are documented emergency paths
  and documented disallowed shortcuts; an emergency is never a reason to add
  a bypass. Break-glass use is recorded with reason, time, action, evidence,
  and follow-up.

Privacy doctrine:

- Data minimization toward model providers. Customer and vendor names,
  singleton transaction detail, and raw rows do not reach AI providers
  unless a specific feature requires them and the disclosure is approved.
  Model providers must offer contractual no-training and data-protection
  terms appropriate to financial data; a provider whose terms permit
  training on inputs is a hard blocker for customer data.
- Auditability must not become surveillance (Principle 18). Evidence of
  system behavior is collected to support trust and recovery, not to rank or
  monitor people.
- Adversarial review is a habit, not an event. The product repository's
  red-team audits, cross-model validations (each agent's work audited by a
  different model), and fail-closed verification are the standing pattern:
  assume raw data can escape by path, go look, and record what was found
  with file-and-line evidence.
- Residual risk belongs to the founder. Engineering and agents cannot
  silently accept residual provider, retention, or access risks; acceptance
  is an explicit founder decision.

## 10. AI-agent operating model

### 10.1 Agents are long-running teammates

AI agents (Claude Code, Codex, and successors) are long-running engineering
teammates, not isolated assistants. They read the same canonical documents,
follow the same decision framework, keep the same memory files current, and
are held to the same engineering standards as human engineers. Their work is
reviewed with the same rigor, including review by other models.

Each repository's `AGENTS.md` binds agents working there. Those files
implement this manual; if one conflicts with this manual, the more
restrictive rule applies and the conflict is raised for amendment.

### 10.2 How agents work with the founder

Agents follow the collaboration rules Joe has recorded:

1. Establish context before recommending action.
2. Clearly distinguish facts, assumptions, unknowns, and aspirations.
3. Do not make confident claims without evidence.
4. Challenge the premise of a question when the framing is incomplete or
   false.
5. Avoid forced binaries when the answer is systemic, sequential, or depends
   on company maturity.
6. Surface contradictions and second-order effects.
7. Be willing to disagree, but explain the reasoning.
8. Do not optimize for impressive language over accuracy.
9. Treat words as promises; do not describe capabilities the product has not
   earned.

### 10.3 Permission tiers

What agents may do independently:

- Read anything in the repositories; run documented read-only and validation
  commands.
- Create branches; write code and documentation on branches; open draft PRs.
- Keep memory, work-queue, and current-state files accurate for work they
  performed, in the owning repository.
- Propose ADRs, decision records, and decision packets.
- Refresh point-in-time digests and indexes on documentation-only branches,
  citing pinned commits.

What requires the founder's explicit, scoped approval:

- Merging to a default branch. The founder holds the merge gate.
- Any command that creates, mutates, or destroys cloud resources, including
  `terraform apply` and `terraform destroy`.
- Any new paid or recurring service, and any spend outside an approved
  budget.
- Starting, stopping, patching, or rebooting hosts outside the approved
  schedule; each maintenance execution requires an approved change record.
- Deployments, cutovers, and anything touching real customer data.
- Storing new secrets; changing repository visibility or access.
- Accepting residual security or privacy risk.

What no agent may do under any instruction short of an explicit founder
directive that also amends this manual:

- Alter deterministic financial outputs from the AI layer, or create a path
  that could.
- Create or use long-lived cloud credentials, or commit secrets.
- Weaken an approval gate to work around its inconvenience, including using
  an unenforced apply environment or weakening OIDC trust.
- Force-push, rewrite history, or edit historical handoffs and sealed
  records.
- Bypass documented emergency-access boundaries (for example, adding SSH
  ingress as a workaround).
- Publish claims, numbers, or capabilities not derived from merged, tested
  evidence.
- Silently adapt material policy (Principle 22): changing a rule of this
  manual, an `AGENTS.md`, or a security control without a recorded, approved
  amendment.

### 10.4 Stop conditions

An agent stops and returns a checkpoint, rather than proceeding, when a task
would cross a permission tier, when repository evidence cannot resolve a
material conflict, when the same defect recurs after remediation, or when
scope expands beyond what was authorized. Stopping with a well-formed
question is success, not failure.

## 11. Documentation and memory model

### 11.1 Documentation is code

Documentation changes ship in the same change as the behavior they describe.
A change to security, networking, IAM, cost, methodology, or deployment
behavior that does not update its documentation is incomplete. Documentation
is reviewed, versioned, linted, and validated like code.

### 11.2 Git is the canonical organizational memory

The durable memory of the company is its repositories: decisions in ADRs and
decision records, reasoning in reasoning archives and PR bodies, state in
dated current-state files, history in immutable handoffs and the git log.
Model memory, chat history, and human recollection are conveniences; when
they disagree with the repository, the repository wins. Anything worth
remembering is committed.

Operational side effects that cannot live in git (ledgers of runtime events,
command output evidence) get a named canonical home (for example a designated
ledger), and the repository records where that home is and what it is
authoritative for.

### 11.3 Durable doctrine and current state are separated

Durable beliefs live in doctrine documents like this one. Metrics,
fundraising status, roadmap timing, customer counts, deployment state, and
other time-sensitive facts live in dated current-state documents that are
expected to change. Placing volatile facts in durable documents is a filing
defect; the fix is to move the fact and leave a link.

### 11.4 One home per truth

Every kind of claim has exactly one home; everything else links to that home.
Duplication is how drift happens. If two documents disagree, the canonical
one wins and the other is corrected to a link.

### 11.5 History is preserved, not rewritten

Handoffs and dated session records are historical evidence: never updated,
only superseded by newer dated files. Corrections are recorded as
corrections. The reasoning archive pattern (initial framing, discussion,
correction, current conclusion, confidence) is the preferred way to preserve
how a conclusion was reached, not just its final wording.

### 11.6 Classified statements

Cross-repository summaries and digests tag statements by class: verified
fact, open proposal, volatile runtime state, recommendation, and founder
decision required. Untagged assertions in a digest are treated as
unverified.

## 12. Program-management principles

- Work in flight is visible. Active work lives in work queues and workstream
  documents with owners and status, in the owning repository.
- Nothing stops silently. A workstream leaves the active list only with a
  recorded disposition (done, superseded, parked with a reason, abandoned
  with a reason). A workstream that stops without disposition is flagged
  stale, not deleted.
- Sessions end with handoffs. A working session that will be resumed by
  someone else (human or agent) ends with a dated handoff containing state,
  open items, and exact commands to resume.
- Gates are sequenced and explicit. Multi-step programs name their gates in
  advance (readiness gates with pass criteria, owner, approver, and blocking
  effect), and stage exits are evidence-checked rather than calendar-driven.
- Checkpoints beat heroics. Long-running work commits durable checkpoints so
  that any interruption loses hours, not weeks.

## 13. Communication preferences

- Separate facts, assumptions, hypotheses, and aspirations, always. This is
  the single most load-bearing communication rule in the company.
- Lead with the finding, then the evidence, then the recommendation with its
  confidence and what would change it.
- Direct, operational language. No motivational filler, no hype, no
  superlatives that a diligence reviewer would discount. Transparency,
  humility, and trust outperform hype (Principle 14).
- Bad news travels fastest. Emerging risks, misses, and mistakes are reported
  immediately with what is known, what is assumed, and what happens next.
  Sharing mistakes honestly is how trust is built, not how it is lost.
- Disagreement is expected and must come with reasoning. Performative
  agreement is a defect.
- Questions that expand context are welcome; the founder treats context
  acquisition as work, not overhead.
- Written artifacts follow the owning repository's style rules (the product
  repository, for example, prohibits em-dashes in documentation and commit
  messages); durable documents avoid decorative formatting that ages badly.

## 14. Leadership and organizational style

- Understand first. Great leadership seeks to understand the most
  (Principle 12). When a team member appears wrong, the sequence is: ask how
  they arrived at the conclusion; ask them to defend and test the reasoning;
  identify missing information; explain the leader's own view only after
  understanding theirs.
- Improve the model, do not win the argument (Principle 11). The goal of a
  disagreement is a better shared model of reality, not a victory.
- Complementary teams over uniform teams. Hire for capabilities the team
  lacks. Leaders temporarily cover gaps they can cover themselves; the
  founder can temporarily supply judgment, rigor, and operating context, and
  therefore weights exceptional technical capability heavily in early
  technical hiring, accepting a coaching load in intellectual humility where
  necessary. The specific next hire is a current-state matter.
- People are not rankings. Human value is not a ranking function
  (Principle 9); differences are explained, not flattened (Principle 10), and
  the system helps people discover what they lack (Principle 19).
- Continuous learning includes success and failure (Principle 13). Post-work
  review records both what worked and what did not, with the reasoning
  preserved.

## 15. Cost and resource-allocation principles

- Cost is a first-class design constraint, considered before deployment, not
  after billing. Every recurring cost is justified by a requirement that
  exists.
- Budgets are approval gates. Each environment has an explicit budget target
  recorded in its current-state documents; exceeding it, or adding any paid
  or recurring service, is a founder decision, not an operational detail.
  Current numbers live in the owning repository (for the control plane, see
  [docs/cost-model.md](../cost-model.md) and
  [memory/current-state.md](../../memory/current-state.md)).
- Estimate in ranges with dated primary-source pricing, and set layered
  alerts below the ceiling so the first warning is cheap.
- Cost discipline never outranks trust or correctness. Do not trade away
  tested backups, managed secrets, security logging, or availability that a
  requirement demands merely to meet a budget number. If commercial timing
  and safety conflict, delay the commercial step; do not waive the control.
- Spend where leverage is. A solo-founder company buys managed services and
  avoids operational complexity even at modest premium, because founder time
  is the scarcest resource.

## 16. Customer standards

- The customer is a founder or operator without a deep finance team; the
  product must deliver judgment they could not otherwise afford, in language
  they can act on.
- Honesty about capability is a feature. The product states what it knows,
  what it assumes, and what it cannot yet do. Coverage gaps and warnings are
  explained to users, not hidden.
- The objective is not to replace critical thinking. It is to compound
  founder judgment.
- Customers get the same evidence standard the company applies internally:
  claims are traceable to computed, sourced numbers; "verified" is never
  displayed when verification did not run (verification fails closed).
- No customer's data trains anyone else's model and no customer's private
  detail reaches another tenant. Cross-company learning happens only under
  the explicit conditions of [Section 19](#19-network-intelligence-vision).

## 17. Investor and public-claim standards

Sophisticated customers, investors, and technical peers must find the
company's operating discipline credible under diligence. Therefore:

- Every public number is generated, never typed. One generator writes each
  public artifact from source data; stale artifacts are flagged rather than
  served.
- Synthetic data is labeled synthetic. No phrasing implies customers,
  traction, or outcomes that do not exist. Display values round down.
- Words are promises. No claim describes a capability the product has not
  earned; prohibited framings (for example, positioning as an autonomous
  finance department or claiming network intelligence that does not exist)
  are recorded in the product repository's positioning decisions and bind
  all external communication.
- Research claims stay inside their preregistered bounds, and removals or
  failed legs remain visible in the record rather than being cleaned away.
- Diligence is welcomed, not managed. The repositories are the data room:
  decisions, reasoning, evidence, and failures are inspectable. Nothing said
  externally should be falsifiable by reading them.

## 18. Founder recoverability and succession

AI.FO must survive the founder being unavailable, and the founder must be
able to recover the company alone. Both directions are engineered:

- Every material decision record explains how one operator can recover, roll
  back, or reason about the affected system.
- Runbooks exist for disaster recovery, rollback, emergency access, and
  onboarding, and they order recovery priorities explicitly: repository
  history and decision records first, then state and audit evidence, then
  administrative access, then re-creatable infrastructure.
- Recovery is proven, not configured. Production approval requires a timed,
  observed recovery exercise from a clean workstation. Restore drills are
  scheduled work, and an untested runbook is recorded as a gap.
- Credentials are independently held by the founder; no agent, contractor,
  or vendor is a single point of access failure.
- Handoffs make interruption survivable. Any operator (successor, new
  engineer, or agent) can resume from the newest dated handoff and the
  onboarding runbook alone, without verbal context.
- The company digest, when adopted, is the ten-minute orientation for a cold
  start; this manual is the doctrine they read next.

Succession consequence: if someone must assume responsibility after an
interruption, their authority follows this manual's hierarchy: repository
evidence over recollection, canonical documents over drafts, and the
non-negotiable constraints of Sections 4, 9, and 10 remain binding until a
recorded amendment changes them.

## 19. Network-intelligence vision

The thesis: experience, not merely expertise, is the network asset.
Expertise is what someone knows; experience includes what happened, what was
decided, what worked, what failed, and what followed. AI.FO should allow
anonymized, permissioned, and governed operating histories, decisions,
contexts, and outcomes to give small businesses the pattern recognition that
historically existed only inside large enterprises, experienced executive
teams, boards, and well-connected networks. The experiences of one should
help the many, and the experiences of the many should help each one.

Network intelligence is Horizon 2 of the company vision
([Section 3](#3-long-term-company-vision)): it begins within finance and is
the compounding mechanism that creates the foundation for the broader living
decision model, not a separate future product layered on after expansion
beyond finance.

This horizon is held with high confidence as a thesis, and its preconditions
are explicitly unresolved: privacy architecture, customer consent, data
governance, security, representativeness, and causal inference from
observational operating data. Those are binding design constraints to be
satisfied, not details to be handled later.

Binding constraints until then:

- No cross-company learning on customer data without an approved privacy
  and consent architecture recorded as a decision.
- No public or customer-facing claim of network intelligence as a present
  capability.
- Product and data-model choices should preserve the option (clean lineage,
  per-tenant isolation, well-defined snapshots) without pre-building the
  network itself.

## 20. Amendment, supersession, and traceability

The full process is
[AMENDMENT_AND_TRACEABILITY_PROTOCOL.md](AMENDMENT_AND_TRACEABILITY_PROTOCOL.md).
In summary:

- This manual changes only by pull request merged by the founder.
- Material amendments (doctrine, authority model, agent permissions) require
  a recorded rationale and are logged in the amendment log; agent-permission
  expansions additionally require the founder to state the expansion
  explicitly, not merely approve a diff that contains it.
- Superseded doctrine is marked superseded with a pointer to its
  replacement; it is never silently deleted.
- Anyone, including agents, may propose amendments; nobody but the founder
  adopts them.

## Appendix: The twenty-four founder principles

The twenty-four numbered founder principles predate this manual and are
cited by number throughout the ADRs. The numbering is load-bearing and this
manual preserves it. The canonical compliance mapping (principle to
obligations, gaps, and evidence) is
[docs/principle-traceability-matrix.md](../principle-traceability-matrix.md);
this appendix fixes the canonical statement of each principle.

1. Trust is earned, not assumed.
2. Curiosity before certainty.
3. Better context produces better decisions.
4. Distinguish how the system knows.
5. Missing information is an active workflow.
6. Preserve state of knowledge.
7. Decision process is an asset.
8. Human authority remains central.
9. Human value is not a ranking function.
10. Explain differences, do not flatten them.
11. Improve the model, do not win the argument.
12. Great leadership seeks to understand the most.
13. Continuous learning includes success and failure.
14. Transparency, humility, and trust outperform hype.
15. Deterministic truth before generative interpretation.
16. Source systems remain authoritative.
17. Recommendations require lineage.
18. Auditability must not become surveillance.
19. Help people discover what they lack.
20. Best-in-class work is an operating requirement.
21. Preserve individuality while learning from patterns.
22. No silent adaptation of material policy.
23. Build for decisions, not engagement.
24. Full context is never complete.
