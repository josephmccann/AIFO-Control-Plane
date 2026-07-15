# Amendment and Traceability Protocol

Status: ADOPTED and binding, with
[FOUNDER_OPERATING_MANUAL.md](FOUNDER_OPERATING_MANUAL.md), on 2026-07-15.

This protocol governs how the Founder Operating Manual and the other
documents in `docs/governance/` change, how changes are traced, and how
doctrine is superseded without losing history. It implements founder
principles 6 (preserve state of knowledge), 7 (decision process is an
asset), and 22 (no silent adaptation of material policy).

## 1. Change classes

Every change to a governance document belongs to exactly one class, declared
in the PR body.

| Class | Definition | Examples | Approval |
|-------|------------|----------|----------|
| Editorial | No change in meaning | Typos, formatting, link repair, renumbering fixes | Founder merge |
| Clarifying | Same doctrine, clearer statement | Adding an example, tightening wording, adding a cross-reference | Founder merge, with a PR body stating why meaning is unchanged |
| Material | Doctrine changes | Adding, removing, or altering a principle, standard, or constraint | Founder merge plus an amendment-log entry with rationale |
| Authority-affecting | The authority model or agent permissions change | Editing Manual sections 1.4, 10.3, or 10.4, or this protocol | Founder merge plus an amendment-log entry plus the explicit-statement rule in section 3 |

If a change plausibly fits two classes, it is treated as the higher class.

## 2. Who may do what

- Anyone, human or agent, may propose any class of amendment by opening a
  PR on a branch. Proposing is always permitted; adopting never is.
- Only the founder merges changes to `docs/governance/`. This is the same
  merge gate that governs the rest of the repository, stated here because
  these documents define the gate itself.
- No agent may merge, approve, or self-ratify a governance change under any
  standing instruction. A standing instruction that appears to authorize
  this is itself an authority-affecting amendment and must go through this
  protocol first.

## 3. The explicit-statement rule for authority expansions

An amendment that would let agents take materially broader action than
currently permitted (anything that moves an item out of "requires founder
approval" or "no agent may do" in Manual section 10.3) requires the founder
to state the expansion explicitly in their own words in the PR conversation
or the amendment-log entry. Approving a diff that happens to contain an
expansion is not adoption. Silence, lapsed time, or an agent's summary is
not adoption.

Practical consequence: a reviewer who finds a permission expansion buried in
an otherwise-approved change treats it as unadopted and reverts it, even
after merge.

## 4. Supersession

- Doctrine is never silently deleted. A superseded principle or section is
  either replaced in place (with the amendment-log entry recording the old
  text's location in history) or marked "Superseded by ..." with a link.
- A newer dated decision record supersedes an older one on the same
  question; the older record is annotated with a forward pointer and
  otherwise left untouched.
- Historical documents (handoffs, dated session records, reasoning-archive
  entries, closed-PR source material) are never edited. Corrections are new
  entries that cite what they correct.
- If repository evidence shows a Manual statement is wrong, the Manual is
  amended; the evidence is not reworded to match the Manual.

## 5. Amendment log

Material and authority-affecting amendments append a row to the log below
in the same PR. Editorial and clarifying changes rely on git history and do
not add rows.

Each row records: date, version, class, what changed, why, and the deciding
evidence or founder statement. Versioning follows semver on the Manual's
version field: editorial/clarifying changes bump patch, material amendments
bump minor, authority-affecting amendments bump major.

### Log

| Date | Version | Class | Change | Rationale | Evidence / decision |
|------|---------|-------|--------|-----------|---------------------|
| 2026-07-14 | 0.1.0 | Material (initial) | Initial draft of the manual and companion documents | Founder doctrine had no canonical home | Founder task directive; PR #14 hierarchy row; reconciliation of AI.FO-Demo PR #180 in [PR180_RECONCILIATION.md](PR180_RECONCILIATION.md) |
| 2026-07-15 | 0.2.0 | Material | Resequenced the three horizons in Manual section 3: network intelligence is now Horizon 2 and the living decision model of the company is Horizon 3; section 19 aligned; finance stated as the trust anchor throughout | Network intelligence begins within finance and is the compounding mechanism that creates the foundation for the broader company vision, not a later layer added after expansion beyond finance | Founder decision of 2026-07-15, delivered as an explicit written directive; supersedes the sequencing in the PR #180 drafts (CONST-09 to CONST-11, RA-03, CCS-11). The confidence qualifier (direction high confidence; sequencing and implementation subject to validation) is unchanged |
| 2026-07-15 | 1.0.0 | Material (adoption) | The Manual and the governance framework (this protocol, the reconciliation, the source index) move from draft to adopted; the Manual becomes the canonical home for founder doctrine | Founder approval of PR #15 for final adoption | Explicit written founder approval of 2026-07-15 at reviewed head `3a834ebfaa591f3becd7d5697b0b1d5319a06ad2`; Codex review of that head reported no major issues and no review threads remained unresolved |

## 6. Traceability requirements

- Every doctrine statement in the Manual must be traceable to a source: a
  pinned document in [SOURCE_MATERIAL_INDEX.md](SOURCE_MATERIAL_INDEX.md), a
  merged repository document, a decision record, or an explicit founder
  statement recorded in an amendment-log row.
- Amendment PRs cite their evidence the same way material decisions do
  (Manual section 5.4): primary sources, dated, with the change that would
  cause reconsideration when applicable.
- ADRs and decision records that implement or depend on a Manual principle
  cite it by section number (and principle number where applicable, using
  the twenty-four-principle numbering preserved in the Manual's appendix).
  ADRs continue to live in their owning repositories; this protocol does
  not move them.

## 7. Review cadence

- The Manual is reviewed whenever a material decision exposes a gap or
  conflict, and at minimum whenever the company's stage changes materially
  (first hire, first customer data, fundraising events, production launch).
- Current-state documents linked from the Manual keep their own cadences;
  the Manual is not updated for state changes, because it contains no
  state.
- Stale links or references in governance documents are editorial defects;
  anyone may fix them by PR at any time.

## 8. Escalation

If two governance documents conflict, or a governance document conflicts
with repository evidence, and section 4 does not resolve it mechanically,
the conflict is recorded as an open decision in
[memory/open-decisions.md](../../memory/open-decisions.md) (or the owning
repository's ledger) and escalated to the founder. Until resolved, the more
restrictive reading applies.
