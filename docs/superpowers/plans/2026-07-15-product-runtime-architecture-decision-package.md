# Product Runtime Architecture Decision Package Execution Plan

Date: 2026-07-15

## Goal

Create, validate, and publish a draft documentation-only pull request containing the complete founder decision package for the AI.FO first-cohort product runtime.

## Execution Sequence

1. Reconstruct exact control-plane and product repository state, including branches, heads, working trees, pull requests, commits, workflows, and live read-only AWS control evidence.
2. Inspect product implementation for topology, state, trust boundaries, integrations, persistence, retries, idempotency, data exposure, deployment behavior, and validation coverage.
3. Verify current provider capabilities, contractual posture, and material pricing using primary sources.
4. Write the current-runtime inventory and beta-cohort requirements.
5. Evaluate the three required hosting strategies and select the highest-scoring safe path.
6. Define the reference architecture, threat model, readiness gates, and cost model.
7. Draft Proposed ADRs and the founder decision packet.
8. Reconcile current state, open decisions, work queue, roadmap, changelog, architecture, security, readiness, ADR index, and handoff documentation.
9. Run the pinned control-plane validation, read-only Terraform plan, product lockfile preflight, type checks, builds, tests, and dependency audit appropriate to the repository.
10. Review the diff for secrets, generated artifacts, internal consistency, broken links, stale identifiers, and accidental infrastructure changes.
11. Commit in coherent documentation groups, push the unique branch, and open a draft pull request. Do not merge.

## Review Checkpoints

- Current-state checkpoint: exact heads and discrepancies recorded before recommendations.
- Architecture checkpoint: recommendation follows product evidence rather than AWS preference.
- Security checkpoint: sensitive-provider handling, cross-tenant controls, token custody, upload integrity, deletion, and founder recovery have blocking gates.
- Cost checkpoint: assumptions and ranges are explicit; third-party usage and unverified invoices are not presented as precise totals.
- Completion checkpoint: fresh validation evidence is captured after all edits.

## Stop Conditions

Stop before any action that creates, modifies, or deletes infrastructure; starts or changes the host; changes IAM, Scheduler, DNS, certificates, callbacks, secrets, production code, customer data, or Git history; creates an apply workflow; changes environment protection; or merges the pull request.
