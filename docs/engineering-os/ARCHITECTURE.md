# Engineering Operating System Architecture

## Purpose

The Engineering Operating System is a GitHub-native, event-sourced policy
layer for humans and agents. It supplies deterministic decisions without
becoming a second source of mission truth or a deployment system.

## Layers and ownership

The Engineering Constitution is the small versioned rule set pinned by every
mission. The dependency-free `engineering_os` Python package implements pure
parsing, validation, projection, and authorization. JSON Schemas under
`schemas/engineering-os` define exchanged records. Repository policy under
`.aifo` binds shared rules to local paths, owners, checks, limits, and disabled
capabilities.

GitHub Issues and authenticated issue history own mission declarations and
events. Git owns source and policy. CI derives evidence from those inputs.
Airtable is a one-way reporting projection only and cannot drive GitHub state
or authority.

An event record is accepted only from a `github-actions[bot]` issue comment.
Human event metadata is derived from an exact, authenticated `/eos` command
comment and rechecked against the mission assignment, repository policy,
transition authority, and full hash chain. A `mission.ready` event binds the
canonical hash of the complete mission declaration, so later issue edits make
the history invalid. System recovery records cannot authenticate themselves:
the kernel requires independently fetched metadata for the exact same-repository
Actions run, a manually dispatched caller path in the versioned
`recovery_workflow_paths` allowlist, and a non-empty caller workflow name. A
`workflow_call` label is not accepted as independent authority. Recovery is
accepted only as a consecutive `mission.orphaned`/`mission.released` pair in one
bot comment that exactly matches a fresh replay of the expired lease. Event JSON
never grants its own actor identity or role.

## State and decision boundary

The state projector folds validated events over a deny-by-default transition
table. Authorization returns a structured decision and never mutates GitHub,
the repository, AWS, product runtime, or another external system. Workflow
adapters added in later packages may propose or append events only after the
pure kernel validates complete authenticated input.

Mission commands and explicit orphan recovery serialize on the same
repository-and-issue concurrency key. Claims additionally serialize on a
repository-wide claim lock. Inside that lock, the adapter re-fetches open and
closed issue and pull-request records plus their complete paginated histories.
Any record with declaration markers or EOS event comments is a mission candidate;
every candidate must retain a complete valid current declaration and authenticated
history. Partial, unmatched, or malformed event markers invalidate the history
instead of truncating it. Active leases are
exposed to conflict evaluation regardless of issue state and remain conflicting
until an authenticated release, park, or cancellation. Malformed candidate
declarations or histories fail the repository snapshot closed; only issues with
neither declaration nor event markers are skipped. Scheduled orphan discovery is always
read-only. Recovery mutation additionally requires a non-dry manual or reusable
workflow invocation and the versioned `orphan_recovery_enabled` policy flag,
which is false by default. Recovery re-fetches the chain, referenced Actions run
metadata, and the current default-branch policy inside that serialized boundary,
then appends `mission.orphaned` plus `mission.released` as one comment.

Command authorization derives cumulative measurements from authenticated
events and compares them with the more restrictive value of mission and
repository caps. Crossed limits preserve the current state and deny further
work while still allowing an explicit park or cancel command. Initial leases
are clamped to the same effective wall-clock cap.

Mission declarations become Ready only with bounded scope, independently
testable acceptance criteria, dependencies and founder decisions, explicit
budgets, validation, rollback, distinct producer and adversary assignments,
and an exact EOS version and Constitution hash.

## Trust boundaries and failure behavior

Repository policy may tighten shared rules. It cannot make an unknown event,
state, role, document, or capability permissive. Derived hashes use canonical
JSON; an audit event's `event_hash` is excluded from its own hash. Closed
records reject undeclared properties.

The product runtime remains outside this package. In particular, the
deterministic financial engine, customer data, credentials, deployment, and
external connectors receive no authority from an engineering mission.

Cross-repository reusable workflows maintain two explicit trust roots. An
immutable enforcement-kernel checkout is selected from the reusable workflow's
own repository and exact workflow SHA. A separate target-repository checkout
is selected from the caller repository at the revision being evaluated. Only
the target checkout supplies source, policy, and declarations. The target
checkout must never supply executable EOS code. Python imports and EOS command wrappers always run
from the immutable kernel. If either repository identity, revision, checkout,
or required policy cannot be established, validation fails closed.

GitHub's personal-account sharing setting is coarse-grained, so every
Demo-only reusable workflow enforces a repository-level caller boundary before
any functional job runs. The caller must be exactly
`josephmccann/AI.FO-Demo` under owner `josephmccann`; the executing workflow
must come from `josephmccann/AIFO-Control-Plane`; `job.workflow_file_path` must
match the expected workflow identity; and `job.workflow_sha` must equal the
40-hex `expected_workflow_sha` supplied by the caller. GitHub associates the
`github` context with the original caller, so `github.workflow_ref`,
`github.workflow_sha`, the triggering event, and the event ref are also
validated. Pull-request composition accepts only
`.github/workflows/eos-pull-request.yml` on a pull-request merge ref. Scheduled
or manual dry runs accept only `.github/workflows/eos-orphan-recovery.yml` or
`.github/workflows/eos-airtable-mirror.yml` on the Demo `master` branch.
Missing, malformed, stale, or contradictory caller evidence terminates the
workflow.

The Control Plane test-integrity caller is a deliberate non-Demo exception: it
may invoke only `reusable-test-integrity.yml`, only from
`.github/workflows/test-integrity.yml`, only for `pull_request_target`, and only
on Control Plane `main`. The orphan workflow separately permits its existing
direct schedule or dispatch only from its own workflow on Control Plane
`main`; it never treats a direct run as an external caller. These exceptions do
not authorize any other private repository exposed by GitHub's account-wide
sharing setting.

## Current limitations

GitHub does not provide path-scoped Git credentials, authenticated comments
can be deleted by administrators, and repository branch protection is an
external control. Later packages must make these named gaps visible and fail
closed at merge authorization. No capability is claimed solely because a
schema exists.
