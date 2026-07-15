# ADR-0020: Product Backup And Restore

## Status

Proposed

## Context

Current database/object backup and restore behavior is not evidenced. Financial data requires explicit RPO/RTO and founder-executable recovery.

## Decision

Set 15-minute RPO and 4-hour same-Region RTO. Use RDS 35-day PITR, monthly snapshots retained 12 months, S3 versioning/checksums/inventory, immutable artifacts and Terraform recovery. Restore before first customer and quarterly; exercise founder access every six months.

## Alternatives Considered

- Daily snapshots only: rejected 24-hour loss window.
- Multi-Region active/active: deferred as unjustified complexity.
- Backup configuration without drills: rejected because restorable evidence is the control.

## Consequences

Backup storage/copies add cost and deletion complexity. Restore reports must reconcile sessions, deleted tenants, objects, secrets, schema and application health. Cross-Region copies require residency/cost approval.

## Reversibility And Reconsideration

Retention can be adjusted after legal/customer approval. Tighten RTO/RPO when contracts or measured incident impact require it.

## Sources

- [RDS backup guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/backup-recovery/rds.html)
- [Migration readiness](../product-runtime-migration-readiness.md)
