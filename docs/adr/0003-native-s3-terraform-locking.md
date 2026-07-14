# ADR-0003: Native S3 Terraform Locking

## Status

Accepted

## Current Product Requirement Supported

AI.FO needs reproducible, auditable infrastructure without avoidable bootstrap complexity.

## Founder Principle Or Constitutional Principle Implicated

Principles 1, 6, 7, 14, and 20: evidence, preserved decision state, decision process, honest limitations, and professional discipline.

## Known Facts

- Terraform S3 backend supports state locking with `use_lockfile = true`.
- Terraform documentation recommends S3 bucket versioning for state recovery.
- The workflows pin Terraform `1.10.5`, which supports native S3 lockfiles.

## Assumptions

- Terraform native S3 lockfiles are sufficient for this repository's initial concurrency risk. Confidence: high.
- DynamoDB locking is not needed unless compatibility or cross-tooling requires it. Confidence: medium.

## Unknowns

- Whether future tooling will require DynamoDB locking compatibility.

## Information Sources Reviewed

- HashiCorp S3 backend documentation: https://developer.hashicorp.com/terraform/language/backend/s3
- HashiCorp state locking documentation: https://developer.hashicorp.com/terraform/language/state/locking

## Decision

Use S3 remote state with versioning, encryption, Block Public Access, and native lockfiles through `use_lockfile = true`. Do not create a DynamoDB lock table in the initial version.

## Why This Decision Is Appropriate Now

It reduces fixed resources while preserving lock behavior for Terraform operations that can write state.

## Alternatives Considered

- S3 state with DynamoDB locking.
- Local state only.
- Terraform Cloud or HCP Terraform.

## Why Alternatives Were Rejected Or Deferred

- DynamoDB adds another account resource without a current requirement.
- Local state is not acceptable for shared infrastructure.
- HCP Terraform may be useful later but is not required for the first control-plane stage.

## Security Effects

State remains sensitive and must be encrypted, versioned, access-controlled, and excluded from Git.

## Privacy Effects

No customer data should be in state at this phase, but state may contain infrastructure metadata and ARNs.

## Reliability Effects

S3 versioning improves state recovery. Lockfiles reduce concurrent mutation risk.

## Cost Effects

Avoids DynamoDB recurring/storage/read-write costs. S3 storage cost is expected to be small.

## Operational Burden

Lower than managing a second lock table.

## Solo-Founder Recoverability

Versioned S3 state is straightforward for one operator to inspect and recover under a documented runbook.

## Product Impact

Provides reproducible infrastructure foundation before product runtime migration.

## Data-Lineage Impact

Infrastructure state changes become versioned and auditable, but this does not replace product decision lineage.

## Auditability Impact

S3 object versions, CloudTrail, Terraform plans, and Git commits provide evidence.

## Reversibility

Can migrate to DynamoDB locking or another backend later.

## Rollback Or Migration Path

Create DynamoDB lock table if required, update backend configuration, run approved `terraform init -migrate-state`, and verify locking.

## Evidence That Would Cause Reconsideration

- Terraform version support changes.
- Tooling requires DynamoDB locking.
- Concurrent operations become common enough to require additional guardrails.
