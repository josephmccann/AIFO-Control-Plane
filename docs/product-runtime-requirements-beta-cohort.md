# Product Runtime Requirements: First Beta Cohort

Date: 2026-07-15

Status: Proposed for founder approval

Scope: Approximately 10 customer companies, 2 to 5 users per company, fewer than 50 total users, low interactive traffic, and bursty ingestion/narrative workloads. These are trust-oriented beta requirements, not enterprise-scale promises.

## Recommended Service Baseline

| Requirement | Proposed target | Acceptance evidence |
| --- | --- | --- |
| Availability | 99.5% monthly customer-facing objective; architecture designed to avoid a single API or database-AZ failure | Synthetic availability measurement and monthly review; planned maintenance excluded only when announced |
| RTO | 4 hours for production service; 8 hours for a Region-level recovery | Timed database/application restore exercise |
| RPO | 15 minutes for PostgreSQL; no acknowledged object upload lost after successful durable response | PITR configuration and restore timestamp evidence; object checksum/version evidence |
| Maximum tolerable data loss | 15 minutes of committed database changes; zero successfully acknowledged source-file objects | Incident decision record if exceeded |
| Database backup | Automated daily anchor plus continuous transaction-log PITR retained 35 days | RDS settings and backup-status evidence |
| Long-retention backup | Monthly encrypted snapshot retained 12 months, subject to approved customer retention/deletion policy | Backup inventory and lifecycle evidence |
| Object recovery | Versioning enabled; noncurrent versions retained 90 days by default; deletion markers and lifecycle tested | Version restore and deletion test |
| Restore testing | Before first customer and quarterly; also after material DB/storage changes | Signed restore report with elapsed time and data-integrity checks |
| Production support | Founder-owned business-hours support; P1 security/data-loss acknowledgement within 1 hour, 24x7 escalation capability for active incidents | Published contact tree and incident drill |

## Security And Data Requirements

### Tenant isolation

- Every customer-owned table must have an explicit tenant key, foreign-key integrity where practical, and deny-by-default repository access functions.
- Add database row-level security for high-risk customer tables or prove through a documented alternative that every query path is centrally scoped. Route mock tests alone are insufficient.
- Build real PostgreSQL integration tests that attempt cross-tenant read, write, update, export, and delete through user and admin paths.
- Global administrator access must be exceptional, MFA-backed, logged, and limited to named founders/operators.
- The synthetic public-demo tenant must be structurally barred from ingesting customer connections or customer uploads.
- Connector reads, sync, observations, calibration suggestions and commercial account fields must pass the same real-PostgreSQL two-tenant suite. A deployment-wide provider key/company binding is not acceptable for multiple customer companies.
- Commercial plan, billing, support and renewal fields must be authoritative per company or explicitly omitted/labeled as non-authoritative pilot information.

### Encryption

- TLS 1.2 or later at all external and internal network boundaries; TLS termination and redirect policy tested.
- AWS-managed storage encryption is mandatory. Use customer-managed KMS keys for production database, customer objects, sensitive logs, backups, and Secrets Manager where separation/audit value justifies the small operational cost.
- QBO tokens remain application-layer encrypted. The ciphertext must include key version and authenticated context binding token, company, and environment.
- Passwords remain bcrypt or migrate to a reviewed memory-hard hash in a separate product decision; hashes are never logged or exported.

### Secrets and tokens

- Store database credentials, session secrets, QBO client secret/keyring, Stripe/future connector credentials, Anthropic credentials, and any approved verifier credentials in AWS Secrets Manager.
- ECS tasks retrieve only named secrets through workload identity; no static AWS credentials or general secret-list permission.
- Database credentials rotate automatically after staging validation. Vendor secrets rotate at least every 90 days where supported and immediately after suspected compromise.
- QBO encryption keys use an active/previous keyring. New writes use the active version; reads support previous versions during a tested re-encryption campaign.
- QBO disconnect, provider revocation, compromise response, and key-loss procedures must be rehearsed without exposing token values.
- Each connector credential must have an explicit tenant/provider authorization record, minimum provider scope, owner, version, rotation/revocation procedure and audit evidence. The merged singleton Stripe key is restricted to a one-company synthetic/pilot case.

### Sessions and authentication

- PostgreSQL-backed sessions are acceptable for the first cohort; Redis is not required.
- Cookies: opaque name, `Secure`, `HttpOnly`, `SameSite=Lax` or stricter, host-only scope, and seven-day maximum with idle expiry considered.
- Rotate session identifier at login and privilege change; destroy the server session and clear the cookie at logout.
- Session-secret rotation must have a documented mass-invalidation path. Active sessions are invalidated after credential compromise or database restore when required.
- Add CSRF protection for state-changing browser endpoints or prove an equivalent same-origin/header control. QBO state remains mandatory.
- Before first customer, implement password reset, verified email, durable brute-force protection, and founder/admin phishing-resistant MFA. Customer MFA may be a beta opt-in initially but must be on the near-term roadmap.

### Provider disclosure

- Send only the minimum derived facts required to generate or verify a narrative. Remove customer/vendor names and singleton transaction detail unless the specific feature requires them and the disclosure is approved.
- Anthropic requires a commercial organization, DPA, no-training confirmation, and preferably organization-specific ZDR before highly sensitive data.
- The current GMI verifier must be disabled for customer data unless AI.FO obtains an acceptable DPA, precise retention/no-training/subprocessor evidence, incident obligations, deletion rights, and an approved underlying model. Replacement with an approved direct provider is preferred.
- Provider input/output telemetry must track provider, model, request correlation ID, classification, and outcome without retaining prompt text in operational logs.

### Upload safety

- Production may not use local filesystem fallback.
- Validate file signature and parser contract, compute SHA-256, use a quarantine prefix/state, and scan for malware before processing or releasing the object.
- Do not rely on client MIME or extension. Cap size, row count, decompression, parse duration, formula-like cells, and field lengths.
- Object access is private. Presigned URLs are short-lived, content-disposition safe, tenant-scoped, and logged. AWS notes that Signature V4 presigned uploads can enforce checksums in its [presigned URL guidance](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html).

## Logging, Monitoring, And Audit

- Application logs are structured JSON with timestamp, environment, immutable deployment ID, request/correlation ID, route class, tenant pseudonym, outcome, latency, and sanitized error class.
- Never log secrets, token ciphertext/plaintext, cookies, passwords, raw uploads, prompts, generated narrative bodies, bank/transaction detail, customer/vendor names, or full provider responses.
- Maintain a separate append-oriented audit log for login/security events, admin access, QBO/connector connect/disconnect/sync, commercial-account change, calibration override, upload acceptance, data export/delete, secret rotation, deployment, schema migration, and restore.
- CloudWatch application logs: 30 days. Security/audit logs: 365 days hot or archived, subject to approved legal policy. Load-balancer and object-access logs: 90 days minimum.
- Required alerts: availability, 5xx/latency, ECS desired-task deficit/restart loop, RDS CPU/connections/storage/failover/backup, migration failure, QBO auth failure surge, AI/verifier error/cost surge, upload rejection/malware, CloudTrail/GuardDuty security findings, and monthly spend forecast.
- P1 alerts route to at least two founder-controlled channels. Every alert has an owner and runbook.
- Correlation IDs must cross API, asynchronous work, provider calls, and audit records. Full distributed tracing is deferred unless logs and metrics fail to localize incidents.

## Incident Response And Administrative Access

- Human AWS access uses IAM Identity Center only, with phishing-resistant MFA and no IAM user keys.
- Workloads use ECS task roles. CI uses GitHub OIDC with separate plan/deploy identities and protected approval boundaries.
- No SSH, public database, or standing direct production shell. Use audited ECS Exec only for approved incidents, disabled by default if the access boundary cannot be enforced.
- Severity definitions, notification tree, evidence preservation, containment, customer notification decision, recovery, and postmortem templates are required before launch.
- Founder break-glass access uses separately stored recovery factors, hardware keys, registrar recovery, AWS root recovery, and offline runbook copies. Exercise it before launch and every six months.

## Data Retention And Deletion

Founder and counsel must approve the final policy. The recommended beta default is:

| Data | Active retention | Deletion behavior |
| --- | --- | --- |
| Customer financial/database records | Contract term plus 30 days | Disable access immediately; primary deletion within 30 days; backups expire through policy within 90 days |
| Raw uploads | 13 months unless customer requests shorter | Primary and noncurrent versions deleted through an evidenced workflow; backup copies age out within 90 days |
| QBO tokens | Only while connected/contract active | Attempt provider revocation, then cryptographically and physically delete ciphertext; record outcome without token |
| Connector credentials/observations | Only while connected/contract active, subject to approved financial-record retention | Revoke/delete credential; delete connection/observations and record provider outcome without secret or metric value |
| Commercial account metadata | Contract term plus approved business-record period | Remove customer access immediately; retain only legally required content under restricted policy |
| Sessions | 7 days maximum; expired rows purged weekly | Immediate invalidation on logout, account disable, compromise, or customer termination |
| Narratives/verifier records | 13 months, without raw prompt/provider response unless needed for a documented audit purpose | Tenant deletion workflow; provider deletion handled under contract |
| Application logs | 30 days | Automatic lifecycle; security evidence extracted to audit log |
| Audit/security logs | 365 days | Tamper-resistant lifecycle; legal-hold exception is explicit and approved |
| Automated DB PITR | 35 days | Expires automatically; restored copies inherit deletion restrictions |
| Monthly backup | 12 months | Policy expiration; delete earlier when legally/technically required and documented |

Every deletion request must produce an immutable, content-free evidence record listing systems checked, completion time, exceptions, backup expiry date, operator, and approver. Do not promise deletion from immutable backups earlier than the architecture can prove.

## Environment And Change Requirements

| Environment | Purpose | Data rule | Isolation |
| --- | --- | --- | --- |
| Local | Development and unit tests | Synthetic only | Developer machine; no production secrets |
| Development | Optional shared integration or ephemeral previews | Synthetic only | Nonproduction account/resources and credentials |
| Staging | Production-parity migration, restore, security, QBO sandbox, and release validation | Synthetic or explicitly approved sanitized fixtures only | Separate VPC, DB, buckets, secrets, domain, and QBO sandbox credentials |
| Production | First-cohort customer service | Real customer data | Dedicated production AWS account and independently scoped resources |

- Production artifacts are built once, immutable, provenance-recorded, scanned, and promoted by digest.
- Pull request checks must include lockfile policy, type checks, build, API/frontend tests, migration checks, secret scanning, dependency review, and container vulnerability scan.
- Staging deploy is automatic only after checks; production deploy requires an explicit human approval boundary that the current `terraform-apply` environment does not provide.
- Schema changes are backward-compatible expand/migrate/contract steps. Startup DDL is removed before staging.
- Generated migration SQL is captured and explicitly reviewed against version-controlled migrations and the independently baselined target schema. Automatic development-to-production schema diff is never authoritative; destructive or unexplained SQL is a deployment stop condition.
- Liveness and readiness are separate. Promotion requires schema/dependency readiness plus a defined consecutive-success stabilization window; transient startup HTTP failures cannot be treated as either successful readiness or an immediate permanent failure without the bounded warm-up policy.
- Rollback to the prior image must be possible in under 30 minutes. Database changes need a tested forward-fix or restore strategy; “roll back code” alone is insufficient.
- A release is rolled back on failed health/readiness, migration failure, material 5xx/latency regression, auth/QBO failure, cross-tenant result, or data-integrity alarm.

## Capacity Assumptions

- 10 companies, 20 to 50 users, fewer than 10 concurrent interactive users typical.
- Normal API rate below 5 requests/second; short bursts below 25 requests/second.
- Database below 50 GiB in beta; object storage below 100 GiB in year one unless measured otherwise.
- Uploads remain at or below 10 MB each; up to 500 uploads/company/year is a planning bound.
- Nightly/scheduled work is I/O-bound and provider-bound, not sustained high CPU.
- Stripe sync is currently admin-triggered, synchronous and paginates subscriptions/invoices/refunds. Beta planning must bound tenant count, pages, duration, provider rate and retry/cost behavior before enabling it for customers.
- Two 0.5-vCPU/1-GiB API tasks are the initial production floor, subject to measured build/runtime memory. Increase to 1 vCPU/2 GiB if load and narrative concurrency evidence requires it.
- QBO and AI work should move to a durable job model before customer volume or request duration makes synchronous processing unreliable. A simple SQS-backed worker is sufficient; no microservice program is required.

## Cost Requirement

- Recommended incremental product-runtime target: `$350-$550/month` during beta, excluding the existing control-plane host, taxes, AWS support plan, and unusually high AI usage.
- Reasonable upper operating bound: `$800/month`; forecast alert at `$600`, actual alert at `$700`, and emergency review at `$800`.
- Third-party AI monthly limit begins at `$150` with provider-side hard/soft limits where available.
- A variance above 20% month-over-month or above 80% of a monthly threshold requires owner review.
- Do not trade away Multi-AZ database, tested backups, managed secrets, or security logging merely to meet the target.

## Beta Support Expectations

- Onboard companies deliberately, no more than two per week until two weeks of stable evidence exist.
- Maintain a named founder owner for every active tenant and QBO connection.
- Run daily automated health review and weekly cost/error/security review.
- Communicate planned maintenance at least 48 hours ahead when possible.
- Pause new onboarding after any unresolved P1/P2 security, tenant-isolation, restore, or data-integrity incident.

## Approval

This document becomes binding only after founder approval of the targets and counsel review of retention, deletion, provider disclosure, and incident-notification commitments. Until then, it is the recommended engineering baseline and a blocker to staging design finalization.
