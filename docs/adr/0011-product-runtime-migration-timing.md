# ADR-0011: Product Runtime Migration Timing

## Status

Accepted in principle — strategic direction only

## Context

The current Replit-associated runtime works as a synthetic demo but lacks repository-grounded backup/restore, deletion, deployment rollback, domain custody, and acceptable verifier-processor evidence. The first cohort will entrust highly sensitive financial information.

## Decision

Migrate to an AWS-managed, founder-operable reference architecture and pass every production gate before accepting real first-cohort customer data. Keep the current deployment only for synthetic demonstration and migration rehearsal until cutover.

This acceptance fixes the strategic direction and timing. It does not accept or authorize the proposed implementation parameters in ADR-0012 through ADR-0022, including exact RDS size, NAT topology, hostname, RPO/RTO, PITR retention, recurring budget, resources, data movement, DNS, callbacks, or deployment.

## Alternatives Considered

- Launch on a hardened current platform: deferred because safe hardening duplicates much of the migration work without creating founder-owned recovery.
- Permanent hybrid: rejected because it increases processors, failure paths and solo-founder burden.

## Consequences

- Commercial onboarding may wait for architecture, product prerequisites, staging and rehearsal.
- Migration is deliberate and evidence-gated, not a big-bang infrastructure apply.
- No AWS runtime deployment is authorized by this strategic decision.

## Security, Privacy, Reliability, Cost

This reduces platform ambiguity and improves recoverability/auditability. It adds approximately `$400-$550/month` product-runtime cost and meaningful one-time engineering work. External AI processors still require separate approval.

## Reversibility And Reconsideration

Before data cutover, the choice is fully reversible. Reconsider if the current provider produces independently verified recovery, security, deployment, processor and founder-exit evidence that meets all beta requirements at materially lower total burden.

## Sources

- [Product runtime inventory](../product-runtime-inventory.md)
- [Options analysis](../product-runtime-options-analysis.md)
- [Migration readiness](../product-runtime-migration-readiness.md)
