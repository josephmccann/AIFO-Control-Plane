# AI.FO Engineering Operating System v1 Design

**Status:** Approved by the 2026-07-15 founder mission directive
**Owner:** AIFO-Control-Plane
**Initial consumer:** AI.FO-Demo
**Activation posture:** Founder approval for every merge; no deployment or production mutation

## Objective

Build one enforcement-first operating system for agents and humans. GitHub
Issues are the authoritative mission record, GitHub authenticated history is
the append-only event source, repository policy is versioned in Git, and CI
derives evidence. Airtable is a one-way reporting mirror only.

The architecture must be complete in v1 even where a high-risk capability is
disabled by policy. Disabled capabilities retain schemas, interfaces, guards,
and tests so activation is a policy and approval change rather than a redesign.

## Binding context

- The adopted Founder Operating Manual is
  `docs/governance/FOUNDER_OPERATING_MANUAL.md`, version `1.0.0`. The
  Engineering Constitution links to it in one direction and does not restate
  founder doctrine.
- The repository remains the canonical owner of shared EOS policy, schemas,
  reusable workflows, evidence formats, audit formats, and metrics.
- Target repositories own thin callers, local policy, ownership maps, local
  mission issues, PR state, and local ADRs.
- AI.FO-Demo is the initial target. Its deterministic financial engine,
  methodology, production runtime, connectors, credentials, and customer data
  are outside this program's authority.
- The active EDGAR study is architecturally supported by generic frozen
  artifact declarations and is not integrated or modified.

## Options considered

### Option A: GitHub-native event-sourced kernel with repository policy

Use issue declarations plus authenticated issue-comment events, serialized
workflows, a dependency-free Python policy kernel, JSON Schemas, and workflow
artifacts. This preserves GitHub as the sole mission authority, supports local
deterministic tests, and avoids a paid control-plane service.

Trade-offs: GitHub cannot issue path-scoped git credentials, issue comments are
append-only by convention rather than immutable storage, and branch-protection
configuration remains an external enforcement boundary. These limitations are
made explicit and fail closed at the merge authorization check.

### Option B: External mission database and control service

An external service could provide transactional leases, immutable storage, and
fine-grained credentials. It would also become a second mission authority,
introduce production operations and recurring spend, and violate the initial
activation constraints. It remains a migration option if repository scale or
GitHub API behavior becomes a measured bottleneck.

### Option C: Templates and conventions only

Issue templates, PR checklists, and prose would be inexpensive, but would not
enforce readiness, authority, state transitions, scope, evidence integrity, or
approval freshness. This option does not meet the mission.

**Decision:** Option A.

## Layers

### Layer 0: Engineering Constitution

`docs/engineering-os/ENGINEERING_CONSTITUTION.md` is short, versioned, and
hashed with SHA-256 over its exact bytes. Missions pin both the semantic EOS
version and content hash. It defines mission ownership, risk tiers, authority,
founder gates, separation of duties, evidence, stop conditions, and amendment
rules. It references the Founder Operating Manual but does not duplicate it.

### Layer 1: Enforcement Kernel

`engineering_os/` contains focused Python modules with no third-party runtime
dependencies. Executable wrappers in `scripts/engineering-os/` provide stable
command names for humans, agents, and workflows. The kernel reads JSON from
files or standard input, emits deterministic JSON, uses explicit exit codes,
and never mutates GitHub or external systems itself.

GitHub Actions adapters fetch authenticated GitHub state, invoke the pure
kernel, append validated events or comments, and upload evidence. This split
keeps policy testable without credentials and keeps external mutation visible
in workflow permissions.

### Layer 2: Conventions

Issue forms, PR conventions, lifecycle docs, examples, onboarding, incident
guidance, and target-repository instructions describe the same path enforced by
the kernel. Every non-mechanical rule is named in
`KNOWN_ENFORCEMENT_GAPS.md` with owner, risk, current mitigation, and closure
path.

## Canonical records

### Mission declaration

The engineering mission issue body contains exactly one machine-readable JSON
object between EOS markers. The declaration is immutable after Ready unless an
authenticated `mission.amended` event records the old hash, new hash, actor,
reason, computed tier, and any required founder approval. The declaration
contains every required mission field and conforms to
`mission.schema.json`.

The issue and its authenticated history are authoritative. A checked-in
fixture, PR body, Airtable row, workflow artifact, or local cache is never the
mission source of truth.

### Audit events

Every event is a JSON object between audit markers in an issue comment. Events
form a hash chain using `previous_event_hash` and `event_hash`. The kernel
validates sequence numbers, timestamps, mission identity, actor authority,
previous hashes, and transition rules. GitHub supplies authenticated comment
author, creation time, and immutable URL metadata to the normalized event.

Deleting or editing a comment is detectable as a broken sequence or content
hash when a retained audit artifact is compared with current issue history.
GitHub administrator deletion cannot be prevented by repository code and is a
named enforcement gap.

### Evidence manifest

CI generates `evidence.json` from Git, policy evaluation, test adapters,
GitHub state, approval events, audit events, and runtime telemetry. Derived
values are never accepted from a producer-authored PR description. The
manifest is validated, hashed, uploaded as a workflow artifact, and linked in
the PR and mission history by an `evidence.generated` event.

## Mission lifecycle

The transition graph is deny-by-default:

```text
Proposed -> Ready -> Claimed -> In Progress -> Adversarial Review
Adversarial Review -> In Progress              (valid findings/remediation)
Adversarial Review -> Founder Approval -> Merge Authorized -> Merged
Merged -> Verified -> Closed

Proposed|Ready|Claimed|In Progress|Adversarial Review|Founder Approval
  -> Parked|Cancelled
Parked -> Ready                                  (authorized recovery)
Merged|Verified|Closed -> Incident
Incident -> Verified|Closed
```

Each transition has allowed actor roles, required evidence, timeout behavior,
and recovery behavior in versioned policy. An absent rule is a denial. Invalid
transitions create no state event and cause the workflow check to fail.

Ready requires independently testable acceptance criteria, bounded paths,
dependency and founder-decision declarations, budgets, validation, rollback,
producer and adversary assignments, and an EOS pin. A PR fails if its earliest
implementation commit precedes the authenticated Ready and claim events unless
an exact founder-approved readiness exception covers the PR and head SHA.

## Claim, lease, and heartbeat

Mission commands are serialized by workflow concurrency group
`eos-mission-<repository>-<issue>`. Claim evaluation reads the complete event
chain, rejects an unexpired producer lease, and appends one `mission.claimed`
event with owner, start, expiry, and nonce. Heartbeats require the current
lease owner and extend only within the mission wall-clock cap. Release records
an event and returns the mission to Ready.

A scheduled orphan workflow identifies expired leases, emits a dry-run report
by default, and can append `mission.orphaned` and `mission.released` events only
when the repository policy enables recovery mutation. Reclaim requires an
expired or released lease and a fresh serialized claim. Conflicting semantic
ownership remains blocked even after a lease expires until the stale mission
is released, parked, or cancelled.

## Risk, paths, and ownership

Risk is the maximum of declared evidence:

- Tier 0: non-behavioral maintenance explicitly matched by policy.
- Tier 1: bounded behavior within one declared semantic area and with no
  consequential trigger.
- Tier 2: any schema, deployment, cloud, customer-data, methodology, secret,
  destructive, spend, security/privacy, public-claim, cross-module,
  cross-repository, residual-risk, irreversible, or other configured trigger.

The kernel may raise but never lower the declared tier. A declaration below
the computed tier fails closed. A declaration above it is allowed and remains
subject to the higher-tier gates.

Repository policy maps glob paths to semantic domains, minimum tiers, owners,
and conflict groups. Changed paths must be allowed by the mission, outside all
prohibited and frozen declarations, and compatible with active mission leases.
Overlapping paths or conflict groups require a founder-approved coordination
event naming both missions and exact scopes.

## Frozen artifacts

Frozen declarations support path globs, pinned commits, sealed-manifest hashes,
protected engine versions, release conditions, exception authority, exception
expiry, and one-shot markers. A write is denied unless an authenticated,
unexpired exception covers the exact mission, PR, head SHA, path set, and
action. Exceptions never imply deployment, methodology, or customer-data
authority.

No EDGAR repository, workflow, frozen input, study artifact, collection
process, or scoring behavior is referenced by an active target policy in v1.

## Test integrity

The test-integrity adapter evaluates base and head Git trees and emits deltas
for deleted or renamed tests, skips, assertions, sourcing/property assertions,
coverage where present, workflow removal, configuration weakening, and fixture
substitution. It uses deltas and configured patterns, not a permanent absolute
test count. Ambiguous renames and fixture changes are conservative findings.

A reduction override is valid only when it names the mission and behavior
removed, is reviewer-approved, matches the head SHA, and has founder approval
for Tier 2. The evidence manifest records both the raw delta and override.

## Separation of duties and remediation

Producer, adversary, and founder are the only primary roles. Producer and
adversary identities must differ. Policy can require distinct model families;
when a different family is unavailable the evidence records the gap and
founder approval is required before merge authorization.

Adversarial findings are normalized as valid, invalid, duplicate, or founder
decision. Valid findings return the mission to In Progress. Two normal
remediation cycles are allowed by default; a third requires written
justification. Exceeding the configured cap moves the mission to Parked and
generates a decision packet.

## Authority and approvals

Default authority is read-only. Mission authority records name repository,
paths, capabilities, issuer, subject, issue, PR, head SHA, start, expiry, and
revocation state. Unsupported path-scoped git credentials never become
effective write authority: repository policy and merge authorization validate
scope, while the gap register tracks migration to a GitHub App with expiring
installation tokens.

Founder approval is an authenticated event binding mission, action, PR, head
SHA, environment, merge method, expiry, deployment authorization, and cutover
authorization. Merge approval never implies deployment, cutover, cloud
mutation, secrets, customer data, spend, or another artifact.

Merge authorization requires current state, passed status checks, complete
adversarial review, zero unresolved threads, exact unexpired approval, exact
merge method, unchanged head, tier compliance, and valid evidence. The kernel
can emit `manual_merge_authorized`; it can emit `auto_merge_authorized` only
when the repository policy flag is enabled. That flag is false in v1.

## Limits and failure behavior

Mission limits cover estimated model cost/tokens, wall-clock duration,
remediation cycles, concurrent agents, and CI reruns. Repository policy may
tighten them. A crossed limit preserves the event chain and evidence, denies
further execution, and returns a Parked transition recommendation. Workflows
append the transition only through the same serialized command path.

All malformed, missing, stale, conflicting, or unverifiable inputs fail closed.
Diagnostics are machine-readable and identify the violated rule without
printing credentials or sensitive content.

## Incident and rollback

Every mission declares one rollback class: clean revert, forward fix,
point-in-time restore, data migration recovery, or irreversible with explicit
approval. Incident issues link origin mission and PR, preserve evidence, define
kill-switch guidance, record recovery actions, and require recovery
verification. Merge approval never authorizes rollback actions that require
deployment, cloud mutation, customer data, or destructive authority.

## Airtable and metrics

The Airtable adapter transforms GitHub mission projections into a versioned
reporting schema. Dry-run is the default and only initially allowed mode.
Live writes require all of: repository policy activation, exact founder
approval, target identifiers, and an ephemeral secret supplied by the workflow
environment. No code path reads Airtable to drive GitHub, and any requested
writeback direction is rejected.

Metrics derive from audit events and evidence manifests. They include founder
minutes, lifecycle durations, costs, findings, remediation, defects, parked and
orphan counts, false-positive blocks, overrides, rollbacks, incidents, and
throughput. Metrics are operational evidence, never quotas for findings or
people rankings.

## Workflow boundaries

Reusable workflows in AIFO-Control-Plane use least-privilege permissions and
accept explicit policy, mission, PR, base SHA, and head SHA inputs. Target
repositories contain thin pinned callers. No workflow creates AWS resources,
deploys product code, changes branch protection, activates connectors, or
touches customer data.

Reusable workflow references in target repositories pin an immutable commit
SHA. The EOS semantic version and constitution content hash remain separate
mission pins so a workflow implementation change cannot silently alter the
governing constitution.

## Verification strategy

- Unit tests exercise every transition, authority decision, risk trigger,
  path/frozen rule, approval match, limit, evidence field, audit-chain rule,
  incident path, and mirror direction.
- Deterministic repository fixtures exercise base/head test-integrity deltas.
- Black-box CLI tests verify stable exit codes and JSON diagnostics.
- Workflow YAML is parsed and actionlint-checked when the pinned tool is
  available.
- Target integration tests compare the human and agent paths and verify thin
  callers pin immutable workflow revisions.
- The repository's `scripts/validate.sh` remains the single local entrypoint
  and incorporates EOS tests without weakening Terraform checks.

## Rollout and PR boundaries

Implementation is separated into coherent, stackable packages sharing one
schema set:

1. Constitution, architecture, schemas, and state model.
2. Mission lifecycle, claim, lease, heartbeat, limits, and recovery.
3. Tier, path, ownership, and frozen-artifact enforcement.
4. Test-integrity and repository validation controls.
5. Evidence, audit, metrics, and approval model.
6. Merge authorization, incident, and rollback controls.
7. Airtable dry-run reporting mirror.
8. AI.FO-Demo thin integration.
9. Human onboarding and operational documentation.

Each material package receives clean-context adversarial review. Valid findings
are remediated and revalidated before the draft PR series is presented. No PR
is merged by this program.

## Reconsideration triggers

Revisit the GitHub-native design if measured API limits prevent reliable
mission operation, authenticated history cannot meet an adopted audit or
compliance requirement, path-scoped credentials become mandatory before a
GitHub App can provide them, or multi-repository mission volume makes
serialized workflows an observed bottleneck. Any replacement must preserve
GitHub's authoritative mission view or be adopted through a founder-approved
architecture amendment.
