# Founder Decision: AI.FO Product Runtime Architecture

Date: 2026-07-15

Status: Decision requested; no deployment approval is implied

## 1. Executive Recommendation

Approve a gated migration to a small AWS-managed product runtime and require it to pass the full migration-readiness checklist before AI.FO accepts real financial data from its first approximately 10 customer companies.

Use a dedicated AWS production member account; CloudFront/WAF and private S3 for the React frontend; two ECS Fargate API tasks behind an ALB; RDS PostgreSQL Multi-AZ; private S3 for uploads; PostgreSQL sessions; Secrets Manager/task roles; CloudWatch/CloudTrail/GuardDuty; and immutable, approval-gated releases. Keep the current Replit-associated runtime only for synthetic demonstration and rehearsal until cutover.

Do not launch the real cohort on the current runtime. The current evidence does not prove database restore, object recovery, customer deletion, deploy/schema rollback, production domain control, QBO key rotation, or acceptable verifier data handling.

## 2. Why This Path

- It has the strongest weighted result: 87.6/100 versus 59.4 for hardening current and 56.6 for hybrid.
- It replaces hidden platform configuration with versioned artifacts, reviewed infrastructure plans and founder-executable recovery.
- It removes Replit and R2 from production data custody while avoiding Kubernetes, microservices, Aurora and Redis.
- It directly supports 15-minute RPO, 4-hour RTO, Multi-AZ service, immutable rollback and tested restore.
- It creates a clean workload-identity path: GitHub OIDC and ECS roles, no static AWS keys, and no static object-store credentials.
- It remains portable: React static assets, OCI images, PostgreSQL, Terraform and S3-compatible object semantics.

AWS does not solve product-layer risk. Tenant isolation, QBO key rotation, session/logout/CSRF controls, upload quarantine, deletion, schema discipline, provider minimization and fail-closed verification must be implemented before production.

## 3. What Must Happen Before The First Cohort

1. Approve the requirements and ADR set.
2. Prove ownership/recovery of the selected product domain and exact Intuit callbacks.
3. Obtain acceptable Anthropic commercial data terms/ZDR and disable or replace the GMI verifier unless precise no-training/retention/subprocessor terms are approved.
4. Implement one schema-migration path, readiness, tenant integration tests/RLS decision, QBO keyring rotation, session hardening, upload integrity/quarantine, deletion, structured redaction and durable audit events.
5. Build the product as a pinned, immutable, scanned container and versioned static artifact.
6. After separate resource/cost approval, validate staging using only synthetic/sanitized data.
7. Restore the source and target database, reconcile object checksums, test QBO sandbox/OAuth refresh, load/failure/monitoring/rollback, and complete founder recovery.
8. Rehearse the migration end to end and approve a command-level cutover/rollback plan.

## 4. What Can Wait

- Kubernetes, microservices, service mesh, Aurora, Redis, RDS Proxy, per-tenant databases/accounts, active-active multi-Region, third-party SIEM/APM, Macie, complex event architecture and advanced data warehouse/search systems.
- A durable SQS worker may wait until the current jobs are idempotent and measured request duration/retry evidence requires it.
- Additional AWS security/log-archive accounts may wait until compliance, team or incident evidence justifies them.

## 5. Architecture Summary

```text
Customer -> CloudFront/WAF -> private S3 frontend
                         \-> ALB -> two private ECS API tasks
                                      |-> Multi-AZ RDS PostgreSQL
                                      |-> private versioned S3 uploads
                                      |-> Secrets Manager via task role
                                      \-> QBO / Anthropic / approved verifier
GitHub OIDC -> immutable ECR/frontend artifacts -> staged, approved promotion
```

Production is isolated in a dedicated organization member account. Staging uses isolated resources in the existing management/nonproduction account. Database and tasks are private; only CloudFront/ALB are internet-facing. Same-origin `/api` preserves current cookies and OAuth behavior.

## 6. Security Summary

- Identity Center/hardware MFA for humans; GitHub OIDC and task roles for machines; no long-lived AWS credentials.
- Private RDS/S3/tasks, KMS encryption, TLS, WAF/rate controls, least privilege, CloudTrail/GuardDuty and restricted audit logs.
- Application-enforced tenant isolation must gain real DB integration tests and RLS or an explicitly approved equivalent.
- QBO token ciphertext gains key version, authenticated context and tested active/previous-key rotation.
- Customer/vendor names and singleton financial detail are removed from model input unless required and approved.
- Current GMI customer-data use is a hard blocker.
- Uploads are quarantined, signature/checksum/limit validated and malware-scanned before processing.

## 7. Reliability And Recovery Summary

- Availability objective: 99.5% monthly; two API tasks and Multi-AZ RDS.
- RPO: 15 minutes database, zero acknowledged object loss after successful durable response.
- RTO: 4 hours same Region, 8 hours Region-level.
- RDS 35-day PITR, monthly 12-month snapshot, S3 versioning/checksums/inventory, immutable artifacts and Terraform recovery.
- Restore before first customer and quarterly; founder recovery every six months.
- Prior image/frontend rollback under 30 minutes; database failures use tested forward-fix or PITR, not wishful code-only rollback.

## 8. Cost Summary

- Expected product-runtime beta: `$400-$550/month`.
- Reasonable operating upper bound: `$800/month` before founder review.
- Existing scheduled control-plane baseline remains approximately `$76/month` and is separate.
- Cutover month can temporarily add `$150-$400` for overlapping current/new environments.
- Primary risks: model tokens/repair retries, NAT fixed/data cost, verbose CloudWatch logs, RDS growth/backup copies, always-on staging, and unverified current platform/GMI invoices.

## 9. Migration Sequence

Approve decisions -> implement product prerequisites -> review nonproduction Terraform -> explicitly approve/create staging -> pass staging gates -> explicitly approve/create empty production -> rehearse source backup/copy/restore -> approve cutover -> freeze writes -> final DB/object reconciliation -> deploy/migrate -> change DNS/QBO callback -> validate -> observe rollback window -> retire old writes only after approval.

No production data, token, DNS or callback moves during the architecture mission.

## 10. Primary Risks

1. `ai.fo` currently resolves to a domain-sale redirect while product canonicals claim it.
2. GMI's published aggregator terms do not establish acceptable customer-payload handling and warn that underlying models may store/train on inputs.
3. Current DB/object backup and restore are unproven.
4. Tenant isolation depends on application predicates and a broad global admin.
5. One unversioned QBO encryption key has no rotation path.
6. Fragmented/startup migrations can create mixed schema/application state.
7. No complete customer deletion or backup-expiry workflow exists.
8. Upload type/integrity/malware controls are incomplete.
9. Logging can expose identifiers/provider content and is not centrally durable.
10. Current deployment and nightly validation depend on external platform/founder-workstation state outside Git.

## 11. Alternatives Rejected Or Deferred

- Harden current runtime for customer launch: rejected because safe controls overlap migration work and still leave recovery/platform state outside founder-controlled code.
- Permanent hybrid/R2 production: rejected due more processors, credentials, consoles, reconciliation and incident paths for immaterial storage savings.
- App Runner: deferred because ECS gives clearer release/network controls at modest additional burden.
- Aurora, Redis, Kubernetes, microservices and active-active Region: deferred as unsupported complexity.

## 12. Exact Founder Decisions Required

“T” is first real-customer onboarding. If T is not scheduled, the milestone condition is binding.

| Decision | Recommendation | Alternatives | Consequence | Latest safe decision date |
| --- | --- | --- | --- | --- |
| Migration timing | AWS before real customer data | Harden current; permanent hybrid | Delays onboarding but avoids unproven custody/recovery | Before any real customer signs data-access onboarding; target T-12 weeks |
| Production account | Dedicated AWS member account | Shared management account | Better blast-radius/recovery; modest bootstrap burden | Before production Terraform design, T-10 weeks |
| Compute/frontend | CloudFront/S3 + two ECS tasks/ALB | Existing hosting, App Runner, EC2 | Managed HA and reproducible rollback; fixed ALB/NAT cost | Before staging Terraform design, T-10 weeks |
| Database | RDS PostgreSQL Multi-AZ `t4g.medium` | Small instance after test; Aurora; current DB | Meets HA/PITR; roughly `$106/month` compute/storage baseline | Before staging DB design, T-10 weeks |
| Storage | S3 production, R2 migration source only | Retain R2; temporary hybrid | Removes static object credentials; requires checksum migration | Before upload prerequisite implementation, T-9 weeks |
| Secrets/QBO keys | Secrets Manager + versioned keyring | Parameter Store/current secrets | Enables least privilege/rotation; product changes required | Before staging secrets exist, T-9 weeks |
| Sessions | Retain PostgreSQL; no Redis | Redis; JWT | Simplest durable model; auth hardening required | Before product prerequisite freeze, T-8 weeks |
| Domain | `app.getaifo.com` unless `ai.fo` ownership proven | Acquire/use `ai.fo`; keep demo domain | Controls TLS/OAuth/customer trust | Before Intuit production callback submission, preferably T-10 weeks |
| AI provider handling | Anthropic commercial DPA/ZDR; disable/replace GMI | Approve GMI under negotiated evidence; deterministic-only narratives | May constrain verifier feature; prevents unapproved disclosure | Before any customer-data provider test, T-8 weeks |
| Retention/deletion | Approve proposed matrix with counsel | Shorter contract-specific periods | Creates truthful customer commitments and implementation scope | Before customer contract/privacy language, T-10 weeks |
| Recovery targets | 15-minute RPO/4-hour RTO, quarterly restore | Weaker cheaper target; tighter costlier target | Sets architecture/drill obligations | Before infrastructure sizing, T-10 weeks |
| Budget | `$400-$550` expected, `$800` review ceiling | Lower availability; higher managed controls | Authorizes recurring cost, not deployment | Before any resource creation, T-10 weeks |
| Production deployment approval | Create enforceable founder boundary separate from current unusable apply environment | Manual local approved deploy; paid GitHub protection | Determines who can change production | Before staging pipeline design, T-8 weeks |

## 13. Exact Approvals Required Before Deployment

Architecture approval is not deployment approval. Before any staging resource creation, approve the ADR set, recurring staging cost, exact Terraform plan, account/IAM changes and data rule (synthetic only). Before production resource creation, approve the production account, exact plan, recurring budget, security review and staging exit report. Before migration/cutover, approve source backup/data copy, token handling, DNS/TLS, QBO callbacks, customer communication, exact commands, owners, go/no-go and rollback thresholds.

## 14. Stop Conditions

Stop for any Terraform apply/destroy; AWS/IAM/Scheduler/host/resource mutation; apply-workflow or GitHub protection change; DNS/certificate/callback change; secret/key rotation; database/object/token/customer-data copy; product deployment; production code modification; destructive test; customer onboarding; or PR merge without the explicit approval scoped to that action.

## 15. Recommended Next Execution Workstream

Execute exactly one next workstream: **product-runtime prerequisite hardening design in the AI.FO-Demo repository**, covering one migration ledger/removal of startup DDL, QBO key-version rotation, real PostgreSQL tenant-isolation tests, session/logout/CSRF hardening, upload quarantine/checksums, structured redaction, readiness, deletion, and verifier fail-closed/provider abstraction. Produce a reviewable implementation plan and test strategy before any AWS staging Terraform.
