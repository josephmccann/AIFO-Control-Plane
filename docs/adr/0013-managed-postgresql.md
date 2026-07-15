# ADR-0013: Managed PostgreSQL Architecture

## Status

Proposed

## Context

PostgreSQL holds users, sessions, QBO ciphertext, ingestion state, metrics, signals and narratives. Current backup/restore and schema-control evidence is absent.

## Decision

Use private encrypted RDS PostgreSQL Multi-AZ with one standby, initially `db.t4g.medium`, 50 GiB gp3, 35-day PITR, deletion protection and quarterly restore tests. Use one migration ledger and remove runtime DDL before staging.

## Alternatives Considered

- Aurora PostgreSQL: no demonstrated scaling/availability requirement justifies its cost/complexity.
- Single-AZ production: rejected for customer-facing database availability.
- Self-managed PostgreSQL: rejected patching/recovery burden.

## Consequences

RDS provides managed failover and PITR; Multi-AZ/storage costs are accepted. Application connection pooling, TLS validation, migration ordering and restore evidence remain AI.FO responsibilities.

## Reversibility And Reconsideration

Standard PostgreSQL supports logical dump/restore or replication exit. Reconsider Aurora/read replicas/RDS Proxy only from measured connections, load or recovery objectives.

## Sources

- [RDS backup and recovery](https://docs.aws.amazon.com/prescriptive-guidance/latest/backup-recovery/rds.html)
- [RDS PostgreSQL pricing and Multi-AZ](https://aws.amazon.com/rds/postgresql/pricing/)
