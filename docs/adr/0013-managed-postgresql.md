# ADR-0013: Managed PostgreSQL Architecture

## Status

Proposed

## Context

PostgreSQL holds users, sessions, QBO ciphertext, ingestion state, metrics, signals and narratives. Merged PR #186 adds `external_connections` and `source_observations` with application-level tenant keys and idempotent upserts but without company foreign keys/RLS/check constraints. Current backup/restore and schema-control evidence is absent.

## Decision

Use private encrypted managed RDS PostgreSQL, deletion protection and restore tests. The current planning scenario is Multi-AZ with one standby, `db.t4g.medium`, 50 GiB gp3 and 35-day PITR; class, availability shape, storage, RPO/RTO and retention remain Proposed until workload/recovery evidence is approved. Use one migration ledger, independently baseline source/target schemas, review generated SQL, stop on destructive/unexplained diffs, include connector/account tables in tenant/restore manifests, and remove runtime DDL before staging.

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
