# ADR-0022: Customer Data Retention And Deletion

## Status

Proposed

## Context

The current product has no complete customer deletion workflow. Customer data spans PostgreSQL, sessions, R2, QBO, AI/verifier providers, logs and backups.

## Decision

Adopt the beta retention matrix in `product-runtime-requirements-beta-cohort.md`: active customer data for contract plus 30 days, raw uploads/narratives 13 months by default, app logs 30 days, audit logs 365 days, PITR 35 days and monthly backups 12 months. Implement tested deletion with content-free evidence and truthful backup expiry.

## Alternatives Considered

- Indefinite retention: rejected privacy, breach and cost risk.
- Immediate deletion from every immutable backup: rejected as technically misleading without a designed tombstone/restore-reconciliation process.
- One period for all data: rejected because operational/audit/source data have different duties.

## Consequences

Founder/counsel approval is mandatory. Restores must reapply deletion tombstones or otherwise prevent deleted tenants from reappearing. Provider contracts must support the promised deletion behavior.

## Reversibility And Reconsideration

Policies can shorten after workflow validation; lengthening requires customer/legal review. Contract, regulation or customer requirements supersede the proposed defaults.

## Sources

- [Beta requirements](../product-runtime-requirements-beta-cohort.md)
- [Threat model](../security/product-runtime-threat-model.md)
