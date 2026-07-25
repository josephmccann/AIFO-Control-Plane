# Engineering Operating System

The AI.FO Engineering Operating System is a GitHub-native, enforcement-first
control layer for human and agent engineering missions. GitHub Issues and their
authenticated histories are authoritative for mission state. Git and the
base-revision repository policy are authoritative for source and policy.
Airtable is a one-way reporting mirror and grants no authority.

The active contract is EOS version `1.0.0`. Every mission must pin the exact
Engineering Constitution SHA-256:
`a255c0976949d8acae91f7d46e85cc083a15e242ccbd62e587c4e3163b29265e`.

## EOS Version 1 is complete (maintenance mode)

EOS Version 1 governance is complete and the repository is in operational
maintenance. Change it only for operational experience, discovered defects, new
governance requirements, or organizational growth, not to add sophistication.

The operational handoff documentation lives at the repository root:

- [EOS Version 1 Final Report](../../EOS_VERSION_1_FINAL_REPORT.md): overview, governance history, roadmap, lessons.
- [EOS Architecture](../../EOS_ARCHITECTURE.md): components and flows (Mermaid diagrams).
- [EOS Engineering Guide](../../EOS_ENGINEERING_GUIDE.md): engineer and AI-agent handbook.
- [EOS Founder Guide](../../EOS_FOUNDER_GUIDE.md): founder commands and gates.
- [EOS Operations Runbook](../../EOS_OPERATIONS_RUNBOOK.md): founder-controlled activation runbook.
- [EOS Repository Status](../../EOS_REPOSITORY_STATUS.md): current repository, branch, worktree, stash, mission, and activation status.

The founder-controlled activation lifecycle (authorize → attempt → consume →
Test Integrity activation → deployment) is documented but not executed. No real
activation nonce appears in any document.

## Start here

- [Engineering Constitution](ENGINEERING_CONSTITUTION.md)
- [Architecture](ARCHITECTURE.md)
- [Human and agent onboarding](HUMAN_ONBOARDING.md)
- [Definition of Ready](DEFINITION_OF_READY.md)
- [Mission lifecycle](MISSION_LIFECYCLE.md)
- [Definition of Done](DEFINITION_OF_DONE.md)
- [Risk tiers](RISK_TIERS.md)
- [Authority model](AUTHORITY_MODEL.md)
- [Evidence and audit](EVIDENCE_AND_AUDIT.md)
- [Known enforcement gaps](KNOWN_ENFORCEMENT_GAPS.md)
- [Incident and rollback](INCIDENT_AND_ROLLBACK.md)

## Enforcement surface

The dependency-free `engineering_os` Python package implements schema,
mission, state, lease, limit, risk, scope, authority, frozen-artifact,
test-integrity, audit, evidence, approval, merge, incident, metrics, and
reporting decisions. JSON Schemas under `schemas/engineering-os` close the
exchanged records. Shell wrappers under `scripts/engineering-os` expose stable
local commands. Reusable workflows under `.github/workflows` adapt immutable
kernel decisions to authenticated GitHub state.

All decisions deny unknown, missing, malformed, stale, conflicting, or
unverifiable input. Producer validation runs without write authority. A fresh
runner validates the producer artifact boundary against exact base and head
revisions. Merge authorization emits a decision and never calls a merge API.

## Local validation

Run the complete EOS-only offline gate without credentials:

```bash
scripts/engineering-os/validate-all
```

Run the complete repository gate, including Terraform and pinned linters:

```bash
./scripts/install-dev-tools.sh
PATH="$PWD/build/bin:$PATH" ./scripts/validate.sh
```

The complete repository gate executes the developer-tools shell regression in
an isolated child process. Run that regression alone while diagnosing its
contract with:

```bash
PATH="$PWD/build/bin:$PATH" bash tests/install-dev-tools-test.sh
```

No command above deploys infrastructure or mutates AWS.

## Activation boundary

Auto-merge, deployment, cloud mutation, live Airtable writes, orphan recovery
mutation, and EDGAR integration remain disabled. The AI.FO-Demo callers pin a
reviewed Control Plane commit. Exact caller repository, workflow identity,
revision, and provenance checks remain the cross-repository trust boundary.
Required checks and branch protection are external controls and must be
verified before an EOS pull request is eligible for merge authorization.

The Control Plane repository is public. Never place credentials, customer
data, private operational exports, or an activation nonce in repository
content, issue history, pull requests, comments, or workflow logs.

Humans and agents use the same mission declaration, authenticated events,
validation, independent review, evidence, and founder approval gate. No schema,
document, workflow, or external mirror can grant itself authority.
