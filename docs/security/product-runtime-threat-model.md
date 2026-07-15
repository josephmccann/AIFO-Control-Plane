# Product Runtime Threat Model

Date: 2026-07-15

Status: Proposed, requires security/founder review before staging

Method: STRIDE-informed practical review. Ratings reflect the first 10-company cohort and highly sensitive financial data. “Existing” means evidenced at product head `3329c99`; proposed AWS controls are not yet deployed.

## Assets

- Customer identity, financial statements, GL/transaction/bank/AR/AP data, uploads, derived metrics, signals, narratives, and verifier evidence.
- User credentials, sessions, roles, invites, QBO tokens, Stripe/connector credentials, external observations, commercial account metadata, calibration suggestions, encryption keys, database/object backups.
- Deterministic financial-engine integrity, tenant boundaries, audit evidence, deployment artifacts, Terraform state, domains/DNS/TLS/OAuth callbacks.
- Founder identity/recovery factors and business continuity.

## Actors

- Customer user, customer administrator, AI.FO founder/administrator, future engineer/contractor.
- External attacker, credential thief, malicious customer/insider, compromised dependency or CI identity.
- Intuit, Stripe, future Gusto/Plaid providers, Anthropic, GMI and underlying model providers, Replit, Cloudflare, AWS, registrar/DNS providers.
- Automated agents acting with repository, CI, AWS or operator permissions.

## Trust Boundaries And Entry Points

1. Browser to CloudFront/Replit and API: login, registration/invites, cookies, JSON, multipart uploads.
2. API to PostgreSQL and object storage.
3. API to Intuit OAuth/report APIs, Stripe and future operating connectors, Anthropic, and GMI/model provider.
4. GitHub/CI to artifact registry and AWS through OIDC.
5. Human/agent to GitHub, AWS Identity Center, registrar/DNS, provider consoles, and break-glass channels.
6. Backup/restore and migration paths between current providers, staging, production, and recovery locations.
7. Public synthetic demo endpoints and telemetry.

## Threat Register

| ID | STRIDE | Threat/abuse case | Existing controls | Required controls/evidence | Residual risk | Owner |
| --- | --- | --- | --- | --- | --- | --- |
| TM-01 | S/E | Account takeover through password reuse, brute force, invite theft, session compromise, or admin phishing | Bcrypt 12, invite-only registration, secure production cookie, route auth, process-local limiter | Verified email/reset, durable limiter/lockout, admin phishing-resistant MFA, session regeneration/invalidation, login audit and alert tests | Medium | Product/Security |
| TM-02 | E/I | Cross-tenant read/write by missing predicate, forged company ID, global admin misuse, or orphan/rebind behavior | Most mounted routes derive tenant from session; broad authz regression tests | Real PostgreSQL multi-tenant integration tests, central tenant access layer, FK integrity, RLS or approved equivalent, public-demo tenant guard, admin audit/JIT access | Medium | Product/Data |
| TM-03 | I/E | QBO token theft from DB, logs, process, backup, environment, or key compromise | AES-256-GCM ciphertext, no token response/logging, task code validates key length | Secrets Manager keyring with versions/context, least-privilege decrypt, rotation/re-encryption/revocation drill, redaction scan, encrypted backup access separation | Medium | Product/Security |
| TM-04 | S/I | Session theft/fixation/replay or restored stale session | PostgreSQL store; Secure/HttpOnly/SameSite cookie in production | Regenerate on auth/role change, explicit destroy/clear logout, idle/absolute TTL, restore invalidation decision, CSRF/origin controls, session audit tests | Low-Medium | Product |
| TM-05 | I | Prompt/narrative leakage to unauthorized tenant, logs, browser, support or provider | Server-owned snapshot/prompt; caller raw prompt rejected; admin API hides raw verifier content | Data-minimization schema, no names/singleton detail by default, output authz integration tests, log prohibition, provider DPA/ZDR and disclosure register | Medium | Product/Privacy |
| TM-06 | I | Sensitive data in application/provider/load-balancer logs | Ops-event key redaction; several sanitized provider paths | Structured allowlist logger, remove verifier preview, automated secret/PII fixture tests, restricted retention, sampling review before launch and quarterly | Low-Medium | Platform/Security |
| TM-07 | T/D | Upload abuse: spoofed type, malicious file, formula payload, parser bomb, storage exhaustion | 10 MB cap, MIME/extension allowlist, memory upload | Signature/type validation, quarantine, SHA-256, malware scan, row/field/time limits, formula handling, WAF/rate/tenant quota, safe disposition | Medium | Product/Platform |
| TM-08 | T/R | Upload is altered, duplicated, lost, or processed before validation | R2 durable object write; timestamped keys | S3 checksum/version/inventory, accepted-state transaction, idempotency key, manifest, deterministic latest-file order, restore/corruption test | Low-Medium | Product/Data |
| TM-09 | I/T/E | Database compromise through credential theft, injection, public reachability, overprivileged app, or admin | Parameterized ORM/queries, managed PostgreSQL connection string | Private RDS, TLS verification, task-specific credentials, least DB grants, rotation, audit/log review, vulnerability tests, no public endpoint | Medium | Platform/Data |
| TM-10 | I/E | Secret compromise through repository, CI output, task definition, environment dumps, support shell | `.env` ignored, GitHub secret scan, no AWS static keys in control plane | Secrets Manager references, OIDC/task roles, no plaintext plan/log, secret access alerts, dual-version rotation, break-glass workflow and drill | Low-Medium | Platform/Security |
| TM-11 | T/E | Dependency compromise in npm package, action, base image or build tool | Frozen pnpm lockfile, preflight, GitGuardian checks, pinned control-plane tools | General CI, dependency review/audit, lockfile diff review, pinned actions/digests, minimal image, SBOM, ECR/container scan, provenance/signature | Medium | Product/Platform |
| TM-12 | T/E | CI/CD compromise deploys malicious code or infrastructure | GitHub OIDC control roles; control apply role cannot mutate; PR history | Separate product build/deploy roles, exact subject/ref/environment trust, protected founder approval, immutable digests, artifact attestation, branch/ruleset review, deploy audit | Medium | Platform/Founder |
| TM-13 | E/D | AWS account compromise or organization management-account takeover | Identity Center, root MFA, CloudTrail; control role separation | Dedicated production member account, hardware MFA, SCP/least privilege, GuardDuty, independent recovery factors, root/Identity Center drill, contact/billing alerts | Medium | Founder/Security |
| TM-14 | D | Founder lockout from AWS, GitHub, registrar, Intuit or model providers | Founder currently controls services; control handoff docs exist | Offline recovery index, two hardware factors, recovery email/phone, billing access, break-glass role, semiannual clean-workstation exercise | Low-Medium | Founder |
| TM-15 | T/D | Accidental deletion of company, DB, bucket, object, key or infrastructure | Terraform state/versioning for control plane; termination protection on control host | RDS/S3 deletion protection/versioning, least destructive permissions, two-step customer deletion, backups, recovery windows, CloudTrail alarms, tested restore | Low | Platform/Data |
| TM-16 | T/D | Failed application deployment causes outage | Product build/tests; Replit deployment revisions not evidenced | Immutable image, readiness, two tasks, ECS circuit breaker/alarm rollback, prior digest/prefix, smoke/bake, release runbook | Low | Platform/Product |
| TM-17 | T/D | Corrupt/incompatible migration causes data loss or mixed schema | Fragmented SQL/Drizzle/startup DDL; no controlled rollback | One migration ledger, remove startup DDL, expand/contract, one-off role/task, pre-restore point, copy rehearsal, forward-fix/PITR decision test | Medium | Product/Data |
| TM-18 | I | External AI provider retains/trains on financial facts or has unauthorized access | Anthropic API; GMI verifier; server-owned derived source | Anthropic commercial DPA/ZDR, minimize facts/names, approve regions/subprocessors; disable GMI until acceptable direct processor terms or replace; provider incident/deletion evidence | Medium after controls; Critical now | Founder/Privacy |
| TM-19 | I/R | Verifier provider exposure or manipulated verifier falsely marks content safe | GMI timeout/retry and structured response; result metadata | Approved provider/model, signed schema validation, fail closed, independent deterministic checks, no “verified” status on unavailable/error, adversarial tests | Medium | Product/Security |
| TM-20 | I/E | Insider/contractor browses customer data or retains credentials | Repository access controls and broad admin role | Named accounts, least privilege/JIT, production access approval, no shared secrets, audit review, offboarding checklist/revocation test, support-access customer policy | Medium | Founder/Security |
| TM-21 | D/R | Backup silently fails or cannot restore | No current product evidence | RDS backup event alarms, backup inventory, quarterly isolated restore with manifest/app checks, evidence retention and named owner | Low after drill; Critical now | Platform/Data |
| TM-22 | T/D | Restore returns inconsistent DB/objects/secrets/sessions or reactivates deleted data | No current end-to-end restore procedure | Recovery-set manifest, restore ordering, session invalidation, deleted-tenant reconciliation, object/version test, provider credential validation, timed exercise | Medium | Platform/Data |
| TM-23 | S/T | Domain/DNS/TLS/OAuth callback hijack or registrar loss | TLS on demo domain; exact QBO URI checks | Prove domain ownership, registrar hardware MFA/lock/recovery, least DNS access, DNSSEC if supported/operable, ACM validation control, change alerts, callback allowlist/cutover rollback | Low-Medium; Critical now for `ai.fo` | Founder/Platform |
| TM-24 | R | Administrative or customer-data action cannot be attributed | Ordinary DB rows and logs; no dedicated durable audit stream | Append-oriented audit events for auth/admin/QBO/upload/export/delete/deploy/migrate/restore; actor/correlation/outcome; restricted write/read; 365-day retention | Low-Medium | Product/Platform |
| TM-25 | T/R | Retry duplicates QBO sync, snapshots, narratives or reviews and corrupts decisions | Some upserts/unique constraints; provider retries vary | Durable idempotency keys/jobs, transaction boundaries, unique operation IDs, reconciliation and replay tests, DLQ once async | Low-Medium | Product/Data |
| TM-26 | D | External QBO/AI/verifier outage blocks core product or causes runaway cost | Errors handled variably; GMI timeout/retry | Timeouts/circuit breakers, graceful “source available/narrative unavailable” mode, job retry budgets, provider status/cost alerts, no false verified status | Low-Medium | Product/Platform |
| TM-27 | I | Public demo exposes customer data through hardcoded tenant or telemetry | Public routes target `integra-demo`; telemetry intended public/synthetic | Structural prohibition on QBO/customer uploads/users for demo tenant, synthetic provenance check, CI scan, periodic live response review | Low | Product/Security |
| TM-28 | R/I | Customer deletion claim is false because rows, objects, providers or backups remain | No complete workflow | Approved retention matrix, deletion orchestrator, provider deletion, object versions, FK/cascade inventory, backup expiry statement, evidence record and test | Medium | Product/Privacy |
| TM-29 | S/I/E | Singleton Stripe secret is used for the wrong tenant or exposed across a multi-company deployment | Connector flag off; admin-only route; session company must equal `AIFO_STRIPE_COMPANY_ID`; generic tables store no token | Per-tenant connector authorization/credential model, minimum scopes, managed secret versions, revocation drill, tenant integration tests and access audit | Medium; High before multi-tenant enablement | Product/Security |
| TM-30 | I/R | Environment-wide commercial account metadata is shown as tenant-specific truth | Account route derives company/user/QBO/uploads from session and is read-only | Per-company source of truth or explicit non-authoritative pilot labeling; tenant tests; administrative change audit; degraded-read distinction | Low-Medium | Product/Commercial Ops |
| TM-31 | T/R | Connector sync overwrites observation provenance or user mistakes a suggestion for authoritative financial truth | Transactional unique-key upsert; provider/metric/period/confidence retained; suggestions are editable and opt-in | Decide snapshot versus append-only history, immutable sync/audit ID, correction policy, source labeling and override-lineage regression tests | Medium | Product/Data |
| TM-32 | D | Synchronous Stripe pagination exhausts request time, provider quota, memory or cost | Feature flag off; admin-only explicit sync; errors reduce to safe codes | Explicit timeout/page/job budgets, rate/circuit controls, durable idempotent job when justified, dependency metrics and failure-mode tests | Low-Medium | Product/Platform |

## Highest-Priority Abuse Cases

1. An authenticated user changes a tenant identifier and reads another company's financial output.
2. A compromised global admin exports every tenant's data without a durable audit event.
3. An attacker obtains the single QBO encryption key and database backup, decrypting all refresh tokens.
4. A crafted upload consumes memory/parser resources, persists to raw storage, or injects formula content into a later export.
5. GMI or an underlying model stores/trains on a narrative and its source financial facts contrary to customer expectations.
6. A corrupt schema migration deploys successfully because startup DDL failure is non-fatal, leaving partial writes and no safe rollback.
7. Registrar compromise changes the product domain or QBO callback to capture credentials/tokens.
8. A backup appears healthy but fails during restore, leaving the founder unable to recover inside the promised RTO.
9. A deployment-wide Stripe key or commercial metadata is incorrectly treated as tenant-specific in a multi-company environment.
10. A repeated connector sync overwrites the only observation record and removes evidence needed to explain a calibration change.

## Review And Residual-Risk Rule

- Critical current risks block real-customer data and production cutover.
- High risks block production unless an explicitly approved compensating control and expiry date exist.
- Medium residual risks require owner, monitoring, and review date.
- The founder approves residual provider, retention, and global-admin risks; engineering cannot silently accept them.
- Re-review after architecture approval, after staging, before production, after any P1/P2 incident, and at least annually.
