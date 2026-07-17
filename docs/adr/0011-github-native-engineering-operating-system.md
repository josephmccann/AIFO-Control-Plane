# ADR-0011: Use A GitHub-Native Engineering Operating System

## Status

Accepted by the 2026-07-15 founder mission directive

## Current Product Requirement Supported

AI.FO needs one enforcement-first operating path for human and agent changes
without building product runtime infrastructure or introducing another
mission system of record.

## Founder Principle Or Constitutional Principle Implicated

The decision implements explicit human authority, deterministic evidence,
deny-by-default security, narrow work, reproducibility, auditability, and
single-operator recovery. The adopted Founder Operating Manual remains the
canonical doctrine.

## Known Facts

- GitHub already owns repository source, Issues, PRs, authenticated history,
  and Actions for the initial repositories.
- The current program does not authorize deployment or production mutation.
- Airtable is already an operational reporting dependency in product context,
  but is not a suitable mission authority.
- GitHub cannot provide path-scoped git credentials and administrator comment
  deletion cannot be prevented by repository code.

## Assumptions

- Initial mission volume fits serialized GitHub Actions concurrency.
- Authenticated issue history plus retained hashed evidence is sufficient for
  the current audit requirement.

## Unknowns

- Measured GitHub API and workflow limits at future multi-repository volume.
- Whether a future compliance requirement will require immutable external
  event storage.

## Information Sources Reviewed

- `docs/product-runtime-inventory.md`
- `docs/governance/FOUNDER_OPERATING_MANUAL.md`, sections 5 through 12
- `docs/superpowers/specs/2026-07-15-engineering-operating-system-v1-design.md`

## Decision

Use GitHub Issues and authenticated history as the authoritative mission and
event source, Git as the source of policy, a dependency-free Python kernel for
deterministic decisions, and CI for derived evidence. Airtable is one-way
reporting only. Repository policy activates local paths and controls while all
high-risk capabilities remain disabled unless separately approved.

## Why This Decision Is Appropriate Now

It uses existing infrastructure, preserves one home per truth, keeps the
kernel testable without credentials, and avoids operating a paid control
service before scale or compliance evidence requires one.

## Alternatives Considered

- An external mission database and control service.
- Templates and conventions without an enforcement kernel.

## Why Alternatives Were Rejected Or Deferred

An external service creates a second authority, recurring operations, and
cost. Conventions alone cannot enforce readiness, scope, authority, evidence,
or approval freshness.

## Security Effects

Pure policy decisions fail closed and expose external mutation through narrow
workflow adapters. GitHub credential path scope and administrative deletion
remain explicit gaps rather than claimed controls.

## Privacy Effects

Mission contracts require no customer financial data. Product data,
credentials, and model-provider boundaries remain outside program authority.

## Reliability Effects

Canonical records, schemas, hashes, and deterministic state projection make
missions reproducible. GitHub availability and API behavior remain external
dependencies.

## Cost Effects

The design adds no paid service or approved recurring spend. Workflow usage
must be measured before it becomes a scaling concern.

## Operational Burden

One operator can inspect Issues, git history, workflow evidence, and pure local
test results. Later packages add adapters without changing the canonical data
model.

## Solo-Founder Recoverability

The founder can reconstruct a mission from its issue history, pinned policy,
schemas, code revision, and evidence artifacts, or stop all automation by
leaving activation flags disabled.

## Product Impact

The system can govern future product changes but this decision creates no
product runtime infrastructure and grants no authority over deterministic
financial behavior.

## Data-Lineage Impact

Mission, audit, approval, and evidence schemas preserve origin and hashes.
Derived records never replace authoritative GitHub and Git inputs.

## Auditability Impact

Authenticated history, canonical hashes, exact revisions, and stable
diagnostic codes provide reviewable evidence. Administrator deletion remains
detectable only when compared with retained evidence.

## Reversibility

The pure kernel and schemas can be retired without product data migration.
Historical mission and approval records remain evidence and are not rewritten.

## Rollback Or Migration Path

Disable workflow callers and policy activation, preserve GitHub history, and
export validated records to a replacement event service if adopted.

## Evidence That Would Cause Reconsideration

- Measured API limits prevent reliable mission operation.
- An adopted audit requirement needs immutable storage GitHub cannot supply.
- Path-scoped credentials become mandatory before a GitHub App supplies them.
- Multi-repository volume makes serialized workflows an observed bottleneck.
