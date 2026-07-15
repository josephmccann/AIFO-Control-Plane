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

## State and decision boundary

The state projector folds validated events over a deny-by-default transition
table. Authorization returns a structured decision and never mutates GitHub,
the repository, AWS, product runtime, or another external system. Workflow
adapters added in later packages may propose or append events only after the
pure kernel validates complete authenticated input.

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
