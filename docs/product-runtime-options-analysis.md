# Product Runtime Options Analysis

Date: 2026-07-15

Status: AWS-managed strategic direction approved; scores, sequence and implementation parameters remain Proposed

## Recommendation

Choose Option C, a gated AWS-managed product runtime, and complete migration readiness before onboarding the first real customer cohort. Keep the current Replit-associated deployment available only for synthetic demonstration and migration rehearsal until cutover. Do not place real customer financial data on the present runtime merely to accelerate launch.

This is not an endorsement of “AWS by default.” It wins because the current product requires managed PostgreSQL recovery, workload identity for object access, auditable secret custody, controlled artifacts and rollback, environment isolation, and founder-owned recovery evidence. The current platform could remain viable only after controls that overlap substantially with the migration work, while the hybrid option increases trust boundaries and operational ambiguity.

## Evaluation Method

Scores are 1 (poor) to 5 (strong). “Migration risk” scores safety: 5 means least migration risk. Weighted totals are normalized to 100.

| Criterion | Weight | A: harden current | B: hybrid | C: AWS managed |
| --- | ---: | ---: | ---: | ---: |
| Security and customer trust | 20 | 2 | 3 | 5 |
| Recoverability | 15 | 2 | 3 | 5 |
| Operational simplicity | 15 | 4 | 2 | 4 |
| Migration risk | 12 | 5 | 3 | 3 |
| Auditability | 10 | 2 | 3 | 5 |
| Founder recoverability | 10 | 2 | 3 | 5 |
| Reliability | 8 | 3 | 3 | 5 |
| Cost | 5 | 5 | 3 | 2 |
| Time to safe production | 3 | 4 | 3 | 3 |
| Lock-in and maintainability | 2 | 3 | 2 | 4 |
| **Weighted result** | **100** | **59.4** | **56.6** | **87.6** |

The weighting deliberately values trust, recovery, operability, audit evidence, and founder control over nominal hosting cost. For financial data, a cheap platform without restore or processor evidence is not a low-cost production system.

## Option A: Harden The Current Deployment Temporarily

### Topology

Continue the Replit application-router/autoscale deployment, current PostgreSQL service, Cloudflare R2, Anthropic, and GMI integrations. Add platform-level backups, central logs, production domains, secret governance, tested deployment rollback, and product controls in place.

### Assessment

| Dimension | Finding |
| --- | --- |
| Security | Platform can keep TLS and secrets, but workload/storage credentials remain static, tenant isolation remains application-only, and provider/DPA gaps remain. Precise production controls are outside the repository. |
| Reliability | Replit autoscale can absorb variable traffic and `3329c99` stabilized successfully, but transient startup HTTP 500 responses prove that warm-up/readiness behavior is not controlled. Long QBO/AI calls, multi-instance startup safety and database HA remain unproven. |
| Recoverability | Current rollback SHA is now identified and one additive migration deployed, but rollback was not exercised and database/object restore remains unproven. Founder-owned export, restore and platform-exit evidence are still required. |
| Operational complexity | Lowest near-term infrastructure burden and fastest to leave unchanged. The hidden burden is manual evidence collection across Replit, database, R2, registrar, Intuit, and two AI providers. |
| Reproducibility/rollback | Build is reproducible and exact live/rollback SHAs are known; deployment configuration, revision promotion, schema ordering and rollback execution are not fully in Git. Replit proposed destructive drops from schema divergence before the operator canceled promotion. |
| Auditability | Application/admin actions and platform changes do not have a repository-grounded, centralized audit design. |
| Vendor lock-in | Replit-specific deployment metadata and external platform configuration. R2 API is S3-compatible, but current credentials and bucket controls are provider-specific. |
| Customer-data exposure | Same Anthropic/GMI disclosure as other options; GMI is currently unacceptable for customer data without contract changes. |
| Failure blast radius | One deployment/database/security plane appears to hold demo and prospective customer runtime. Founder/platform account compromise is broad. |
| Suitability: first 10 | Not suitable on current evidence. Could become conditionally acceptable only if every backup, restore, domain, vendor, deletion, session, tenant, and rollback gate passes. |
| Suitability: next 50 | Weak. Synchronous work, process-local controls, platform-owned deployment state, and limited environment isolation become increasingly costly. |

### Cost And Work

- Estimated platform/runtime range: `$100-$400/month` plus PostgreSQL, R2, model usage, and any security/backup add-ons. The current invoices are required before approval; Replit documents request-based autoscale billing rather than a fixed production price in its [deployment pricing](https://docs.replit.com/billing/deployment-pricing).
- Required engineering is not small: backup/restore drill, container or independent artifact definition, schema migration control, central logs/alerts, tenant integration tests, deletion, key rotation, upload controls, provider contracts, domain recovery, and platform exit rehearsal.
- Founder decisions: accept Replit as a customer-data processor, approve its recovery/SLA evidence, approve current database provider, and accept continued platform concentration.

### Why Not Recommended

The work needed to make this safe does not create founder-controlled infrastructure recovery and leaves critical operational facts outside Git. The successful `3329c99` deployment narrows short-term deployment uncertainty and unblocks prerequisite design, but schema automation and startup readiness exposed additional platform-owned controls. It remains appropriate as a time-bounded synthetic demo, not as the first real-customer system of record.

## Option B: Hybrid Architecture

### Topology Variants Evaluated

1. Move PostgreSQL and secrets to AWS, retain Replit API/frontend and R2.
2. Move API/database/secrets to AWS, retain current frontend hosting and R2.
3. Move frontend/API/database to AWS but retain R2 indefinitely.

The least-bad hybrid is variant 2 for a short transition: AWS API/RDS/Secrets Manager, existing static frontend only until domain cutover, and R2 read/copy validation until S3 cutover.

### Assessment

| Dimension | Finding |
| --- | --- |
| Security | Managed DB/secrets improve custody, but Replit-to-private-DB connectivity and static R2 credentials add cross-provider paths. Keeping API on Replit prevents ECS workload identity from replacing R2 keys. |
| Reliability | Independent providers can reduce one provider's blast radius, but every user flow depends on more networks and control planes. Cross-provider outages and DNS/callback coordination increase failure modes. |
| Recoverability | RDS adds strong PITR, but end-to-end recovery still requires Replit deployment, R2, registrar, providers, and AWS. |
| Operational complexity | Highest of the options for a solo founder: several consoles, bills, access models, logs, incident channels, and cross-provider egress paths. |
| Reproducibility/rollback | Better for AWS components, still incomplete for retained platform components. Split cutover and rollback state can diverge. |
| Auditability | AWS changes can be audited; retained platform and R2 data access require separate evidence and correlation. |
| Vendor lock-in | Lower concentration, higher integration lock-in. R2 is S3-compatible but not identical in every governance capability. |
| Migration risk | Stages the move and allows copy validation, but dual systems create source-of-truth ambiguity. Dual-write is especially dangerous without reconciliation/idempotency design. |
| Customer-data exposure | Adds AWS without removing Replit/R2/AI processors. It may increase the processor list. |
| Failure blast radius | Component-specific failures are smaller; authentication, DNS, secrets, and data-lineage mistakes can span providers. |
| Suitability: first 10 | Acceptable only as a tightly time-boxed migration state with one authoritative writer and tested rollback. Not preferred as steady state. |
| Suitability: next 50 | Weak-to-moderate. Cross-provider operational tax grows, while core product load remains too small to justify it. |

### Explicit Cloudflare R2 Finding

R2 is inexpensive and has free internet egress; current public pricing is `$0.015/GB-month` for standard storage with a 10 GB free tier, as documented by [Cloudflare R2 pricing](https://developers.cloudflare.com/r2/pricing/). Retaining it avoids an object copy and reduces egress cost.

For this application, those savings are immaterial at an expected sub-100-GB beta footprint. S3 allows ECS task-role access without static object-store credentials, native AWS CloudTrail data-event integration, same-account KMS/access controls, versioning/inventory/checksum workflows, and a smaller recovery/control-plane surface. R2 should remain only as the current demo source and a read-only migration source until checksum-validated cutover. It should not remain the production write target solely for cost.

Avoid long-lived dual-write. Use an inventory manifest, initial copy, incremental delta copy, read-only freeze, final checksum/count reconciliation, then switch the single writer. Roll back by returning the writer to R2 only if no post-cutover production object was accepted, or by executing an approved reverse-copy reconciliation.

### Cost And Work

- Estimated `$250-$600/month`, excluding AI usage, depending on which Replit components remain and whether AWS private networking/NAT is always on.
- Engineering includes every AWS foundation item plus cross-provider connectivity, log correlation, migration reconciliation, and two rollback paths.

### Why Not Recommended

Hybrid reduces commitment but maximizes day-two cognitive load. Its only justified use is a short migration bridge, not the target architecture.

## Option C: AWS-Managed Product Runtime

### Topology

- Dedicated AWS production account; existing management/control account hosts nonproduction/control functions initially.
- CloudFront and AWS WAF front a private S3 static frontend and an internet-facing ALB API origin.
- Two ECS Fargate API tasks across Availability Zones; a small SQS-backed worker is added only when synchronous QBO/upload/AI jobs are extracted.
- RDS PostgreSQL Multi-AZ DB instance, encrypted gp3, 35-day PITR.
- Private S3 customer-object bucket with KMS, versioning, checksums, lifecycle, access audit, and quarantine workflow.
- AWS Secrets Manager and task roles; no static AWS credentials.
- CloudWatch logs/metrics/alarms, CloudTrail, GuardDuty, AWS Budgets/Cost Anomaly Detection, and minimal SNS alerting.
- GitHub OIDC builds immutable artifacts and produces plans; production deployment requires a new enforceable founder approval boundary.
- Merged connector/account state remains in the same RDS/application boundary. Stripe adds outbound HTTPS and managed-secret requirements, not a new service. A per-tenant connector authorization record replaces the current one-company environment binding before multi-company use.

### Assessment

| Dimension | Finding |
| --- | --- |
| Security | Strongest identity, network, secret, storage and audit integration. A separate production account materially limits control/nonproduction blast radius. Product fixes are still required; AWS does not solve tenant predicates, the singleton Stripe credential binding, global account metadata or provider disclosure. |
| Reliability | Two API tasks and Multi-AZ RDS remove the main infrastructure single points. External QBO/AI dependencies remain graceful-degradation concerns. |
| Recoverability | RDS PITR, S3 versioning, immutable images, Terraform reconstruction, cross-account founder access, and rehearsed restore provide the clearest recovery chain. |
| Operational complexity | Moderate and bounded. ECS/RDS/S3 are more components than Replit but are standard managed services. No Kubernetes, service mesh, microservices, Redis, or Aurora is needed. |
| Reproducibility/rollback | Infrastructure, images, task definitions, schema migrations, approvals, and prior revisions can be versioned and reconstructed. |
| Auditability | CloudTrail, workload IAM, S3/RDS logs, deployment events, and explicit audit records can share one evidence model. |
| Vendor lock-in | Uses AWS operational APIs, but PostgreSQL, OCI images, static assets, S3-compatible object semantics, Terraform, and standard DNS/TLS keep exits practical. |
| Migration risk | Highest one-time engineering change. Risk is bounded by staging, rehearsal, one writer, checksum reconciliation, PITR, and rollback gates. |
| Customer-data exposure | Removes Replit and R2 from production custody. Anthropic and any verifier still require explicit provider approval and minimization. |
| Failure blast radius | Production account and per-tier security groups isolate infrastructure. Application admin and tenant-query defects remain important shared risks. |
| Suitability: first 10 | Strong, once gates pass. Deliberately sized small and managed for founder operability. |
| Suitability: next 50 | Strong. Scale Fargate tasks/RDS class and introduce the already-defined simple worker without changing the core topology. |

### Cost And Work

- Expected incremental beta cost: `$350-$550/month` for production plus staging, security, backup, logging, and modest traffic, excluding existing control-plane cost and unusual AI usage.
- Reasonable upper bound: `$800/month` before a founder cost review.
- Primary work: production account boundary, container/release pipeline, network, ECS, RDS, S3, secrets, observability, schema discipline, product security controls, staging validation, migration tooling, rehearsals, and founder recovery drills.

## Migration Sequence

1. Strategic AWS timing is approved. Approve remaining requirements/ADRs; resolve domain ownership, retention, provider terms, production-account boundary, per-tenant connector authorization, commercial account truth and observation-history semantics.
2. Make product runtime independently buildable as an immutable container and convert schema changes to a single reviewed migration path.
3. Implement the ordered product prerequisites: controlled migrations/publish safety, readiness stabilization, QBO keyring rotation, tenant/account/connector integration tests and enforcement, session hardening, upload integrity/quarantine, logging redaction, deletion, AI/verifier fail-closed behavior and reproducible container artifact.
4. Design and review Terraform for nonproduction only. This package does not create it.
5. After explicit approval, build staging with synthetic data; validate restore, OAuth sandbox, uploads, AI minimization, rollback, and founder access.
6. Build production only after staging gates pass and recurring cost is approved.
7. Rehearse DB/object migrations using synthetic or explicitly approved sanitized data.
8. Back up and restore-test the current source, freeze writes, migrate once, reconcile, change DNS/OAuth only under an approved cutover plan, and retain rollback evidence.

## Launch Timing Decision

The first real customer cohort should launch after AWS migration and all production blocking gates pass. If commercial timing cannot wait, the safe response is to delay real-data onboarding, not to waive recovery or processor controls. The present platform can continue demonstrating synthetic product value while the narrow migration-readiness workstream executes.
