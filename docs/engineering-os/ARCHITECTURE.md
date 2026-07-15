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
Actions run, workflow name and path, and allowed invocation event. Recovery is
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
repository-and-issue concurrency key. Scheduled orphan discovery is always
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

## Current limitations

GitHub does not provide path-scoped Git credentials, authenticated comments
can be deleted by administrators, and repository branch protection is an
external control. Later packages must make these named gaps visible and fail
closed at merge authorization. No capability is claimed solely because a
schema exists.
