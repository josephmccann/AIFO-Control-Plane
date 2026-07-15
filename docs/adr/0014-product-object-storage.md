# ADR-0014: Product Object Storage

## Status

Proposed

## Context

The current upload path writes raw files to R2 with static credentials and lacks checksum, scan, version, retention, deletion and restore evidence. R2 is cheap and S3-compatible.

## Decision

Use private versioned SSE-KMS S3 as the production object store. Keep R2 read-only during a manifest/checksum-validated migration, then retire production write credentials. Do not use permanent dual-write.

## Alternatives Considered

- Retain R2: cheaper egress, but preserves static credentials and another audit/recovery plane.
- Dual-write indefinitely: rejected source-of-truth and reconciliation risk.

## Consequences

ECS task roles remove static object credentials and AWS audit/KMS/inventory controls are unified. Migration requires one writer, inventory, SHA-256 reconciliation, freeze and rollback criteria. S3 egress may cost more, but beta volumes are small.

## Reversibility And Reconsideration

Objects and manifests remain portable. Reconsider R2 only if measured egress becomes material and it proves equivalent identity, audit, retention, deletion and recovery controls.

## Sources

- [Cloudflare R2 pricing](https://developers.cloudflare.com/r2/pricing/)
- [Amazon S3 security best practices](https://docs.aws.amazon.com/AmazonS3/latest/userguide/security-best-practices.html)
