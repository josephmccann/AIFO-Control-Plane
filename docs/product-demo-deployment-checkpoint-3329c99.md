# Product Demo Deployment Checkpoint: `3329c99`

Date: 2026-07-15

Status: Successful current Replit demo deployment; connectors disabled; not production approval

## Outcome

The merged product baseline deployment dependency is resolved.

| Evidence | Result |
| --- | --- |
| Live demo SHA | `3329c99beb0713269b54bc5fd6a7fb39bf44f398` |
| Prior rollback SHA | `30a8ed24b7a30c74846c7bb322be24ef5ff6ec2c` |
| Deployment | Completed successfully |
| Migration | `0011_external_connectors.sql` applied transactionally |
| Final connector schema | 2 tables, 4 constraints, 7 indexes |
| Connector data | 0 connector rows, 0 observation rows |
| Public smoke | Passed |
| Authenticated smoke | Passed |
| QBO sync | Not run |
| Connector flag | Disabled |
| Stripe | Unconfigured |
| Rollback | Not required |
| Final health | Stable at target SHA |

This proves that the additive connector migration and disabled connector foundation can deploy on the current demo platform without populating connector/customer records. It does not prove a general migration framework, rollback execution, customer-data safety, multi-tenant connector authorization, production readiness, or AWS deployment readiness.

## Operational Findings

### Automatic schema-diff risk

When development and production schemas diverged, Replit's automatic schema-diff workflow proposed destructive table drops. The publish was canceled before promotion and no destructive SQL ran.

Required control for every future Replit publish:

1. Capture the generated SQL before promotion.
2. Review every statement against the intended, version-controlled migration set and current production schema.
3. Treat any `DROP`, destructive `ALTER`, truncation, implicit data rewrite, or unexplained object removal as a stop condition.
4. Do not promote until the discrepancy is understood and the migration/rollback plan is explicitly accepted.
5. Keep development schema experimentation separate from production migration authority; automatic schema convergence is never authoritative.

### Startup health stabilization

Health checks returned transient HTTP 500 responses while startup was incomplete and stabilized after successful startup. A deployment must not treat the first successful process launch or an eventually healthy endpoint as sufficient readiness evidence.

Future publish validation must distinguish process liveness from dependency/schema readiness, wait for a defined consecutive-success stabilization window, and fail promotion or roll back when readiness does not stabilize inside the approved timeout.

## Architecture Consequences

- The pre-refactor demo deployment hold is closed, so controlled-migration prerequisite work may begin when separately authorized.
- Prerequisite 1 is strengthened, not satisfied: one additive migration succeeded, while the automatic destructive proposal proves the need for one explicit production migration ledger and reviewed SQL.
- Startup readiness moves immediately after migration control in the prerequisite sequence.
- The proposed AWS architecture is unchanged. Exact sizing, topology, recovery, domain, cost, provider, and deployment-approval parameters remain Proposed.
- Connectors remain a disabled foundation only. Stripe is unconfigured, no connector data exists, and no independent authorization model for the 10-company cohort exists.

## Safety Boundary

This checkpoint does not authorize connector enablement, Stripe configuration, QBO synchronization, customer financial data, product-code changes, AWS runtime resources, DNS/callback changes, secret changes, or PR #13 merge.
