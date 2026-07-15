# ADR-0016: Session Persistence And Authentication

## Status

Proposed

## Context

The application already stores sessions in PostgreSQL. This is horizontally safe for the expected load, while authentication lacks several customer controls.

## Decision

Retain PostgreSQL-backed Passport sessions for the first cohort; do not add Redis. Add session regeneration, explicit logout destruction, durable rate controls, CSRF/origin defense, secret-rotation invalidation, verified reset/email flows and phishing-resistant founder/admin MFA.

## Alternatives Considered

- Redis/ElastiCache: rejected as an unsupported stateful dependency at current scale.
- Stateless JWT browser sessions: rejected revocation/key-rotation complexity and sensitive claims risk.

## Consequences

RDS becomes both product and session availability dependency, already addressed by Multi-AZ. Restores must decide whether to invalidate restored sessions. Expired rows need scheduled cleanup.

## Reversibility And Reconsideration

Session store interfaces allow later Redis migration. Reconsider when measured session write load, connection pressure or independent session availability requires it.

## Sources

- [Runtime inventory](../product-runtime-inventory.md)
- [Beta requirements](../product-runtime-requirements-beta-cohort.md)
