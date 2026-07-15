# ADR-0019: Product Logging And Observability

## Status

Proposed

## Context

Current logs are console output and process-local operational counters; the health endpoint is liveness only. Sensitive identifiers and verifier response previews can reach logs. Merged connector routes use safe error codes, but connector provider/metric/period/company data and privileged sync actions expand the redaction/audit surface.

## Decision

Use CloudWatch structured application logs/metrics/alarms, a separate restricted audit stream, correlation IDs and explicit redaction. Retain app logs 30 days, access logs at least 90 days, and audit/security evidence 365 days. Add GuardDuty and minimal founder alert routing; defer full APM/SIEM.

## Alternatives Considered

- Third-party observability suite now: deferred cost/complexity.
- Logs only: rejected because availability, backup, auth, provider and cost failures need active alarms.

## Consequences

The product must adopt an allowlist logger and remove raw response previews. Connector audit records identify actor/provider/outcome without credential or metric values, and connector-read failure must not appear as "not configured." Metrics avoid high-cardinality tenant labels. Every alarm needs a tested route and runbook.

## Reversibility And Reconsideration

Structured logs can be exported later. Add tracing/APM/SIEM only if incident diagnosis, compliance or scale evidence warrants it.

## Sources

- [Threat model](../security/product-runtime-threat-model.md)
- [Beta requirements](../product-runtime-requirements-beta-cohort.md)
