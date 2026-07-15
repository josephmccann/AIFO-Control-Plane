# Product Runtime Migration Readiness

Date: 2026-07-15

Status: Strategic AWS migration direction approved; implementation and migration are **not approved**

Statuses: `PASS`, `PARTIAL`, `FAIL`, `NOT STARTED`, `PENDING APPROVAL`. A blocking gate must be `PASS` with linked evidence before its dependent stage begins. Proposed documents count as evidence drafts, not approvals.

## Current Demo Deployment Evidence

The pre-prerequisite deployment hold is resolved: Replit successfully deployed product SHA `3329c99`, applied `0011_external_connectors.sql` transactionally, and passed public/authenticated smoke with connectors disabled, Stripe unconfigured, and zero connector/observation rows. Rollback SHA `30a8ed2` was retained but not exercised.

This is useful current-platform evidence, not a PASS for target staging or production. A canceled publish also showed that Replit's automatic schema diff can propose destructive table drops, and startup health returned transient HTTP 500 responses before stabilizing. The detailed checkpoint is [product-demo-deployment-checkpoint-3329c99.md](product-demo-deployment-checkpoint-3329c99.md).

## Gate Table

| ID | Gate | Pass/fail criteria and required evidence | Owner | Approver | Status | Blocking effect |
| --- | --- | --- | --- | --- | --- | --- |
| MR-01 | Current-runtime inventory complete | Implementation-level topology, dependencies, state, confirmed risks and unresolved facts reviewed against exact product SHA | Infrastructure + Product | Founder | PASS (draft PR) | Blocks architecture approval |
| MR-02 | Data-flow inventory complete | All 20 principal flows, including connector sync, account delivery and calibration suggestions, name boundaries, classification, stores, processors, secrets, failures, retries, idempotency, audit and recovery | Product + Security | Founder | PASS (draft PR) | Blocks threat-model approval |
| MR-03 | Data classification complete | Classification and handling requirements cover financial, identity, token, session, prompt, log, backup and infrastructure data | Security + Product | Founder + counsel where required | PASS (draft PR) | Blocks provider/storage design |
| MR-04 | Architecture ADR approved | ADR-0011 strategic timing accepted; ADR-0012 through ADR-0022 and any tenant-enforcement/provider ADR reviewed; selected topology, accounts, parameters and deferred items explicitly accepted | Infrastructure | Founder | PARTIAL: strategic direction approved; implementation parameters pending | Blocks staging infrastructure design approval |
| MR-05 | Threat model reviewed | Security review resolves every Critical/High threat or records approved time-bounded compensating control | Security | Founder | PENDING APPROVAL | Blocks staging design; Critical/High blocks production |
| MR-06 | Database architecture approved | RDS choice, version/class, Multi-AZ, TLS, pool, migration ledger, PITR, restore and deletion controls approved | Data + Infrastructure | Founder | PENDING APPROVAL | Blocks staging database |
| MR-07 | Storage decision approved | S3/R2 authority, migration manifest, checksum, versioning, quarantine, retention/deletion and rollback approved | Product + Infrastructure | Founder | PENDING APPROVAL | Blocks staging upload path |
| MR-08 | Secrets model approved | Secret inventory, task-role access, QBO keyring/versioning, session rotation, per-tenant Stripe/connector authorization and rotation/revocation, provider credentials and break-glass approved | Security + Product | Founder | PENDING APPROVAL | Blocks staging secrets/connectors |
| MR-09 | Domain/provider custody approved | Registrar/DNS ownership proven; production domain selected; Anthropic DPA/ZDR and verifier processor path accepted; Intuit production readiness documented | Founder + Security | Founder | FAIL | Blocks any real customer data and production |
| MR-10 | Cost estimate approved | Current invoices attached; AWS estimate assumptions reviewed; expected/upper thresholds and recurring-cost approval recorded | Infrastructure + Finance | Founder | PENDING APPROVAL | Blocks resource creation |
| MR-11 | Product prerequisites implemented | All 10 ordered items pass: reviewed migration ledger/publish SQL, readiness stabilization, QBO rotation, DB tenant tests, session/CSRF, upload quarantine, redaction, deletion, AI/verifier fail-closed and reproducible container; PR #186 connector/account scope included | Product | Security + Founder | PARTIAL: additive `0011` deployed successfully, but automatic destructive diff risk and startup readiness remain uncontrolled | Blocks staging validation |
| MR-12 | Staging environment validated | Approved Terraform applied only after separate authorization; isolated nonprod resources healthy with synthetic data and evidence index | Infrastructure | Founder | NOT STARTED | Blocks migration rehearsal/production design |
| MR-13 | Reproducible build | Clean clone, pinned Node/pnpm/base image, frozen lockfile, deterministic frontend/API/container build; artifact hashes/provenance recorded | Product + Platform | Infrastructure | PARTIAL: build/tests pass; runtime/tool versions unpinned and telemetry preflight fails | Blocks staging deploy |
| MR-14 | Reproducible deployment | Exact image/frontend digest deploys through documented OIDC pipeline into staging twice without console-only configuration; generated migration SQL reviewed; readiness passes a defined consecutive-success window | Platform | Founder | NOT STARTED: current Replit SHA deployed once successfully, but target artifact/pipeline/repeatability are absent | Blocks production deploy |
| MR-15 | Infrastructure plan reviewed | Product Terraform plan, security/cost review, no secrets/state in PR, expected resources and destroys explicitly classified | Infrastructure | Founder | NOT STARTED | Blocks every product-runtime apply |
| MR-16 | Database source backup completed | Source-provider backup/export created immediately before rehearsal/cutover, encrypted, inventoried, access-restricted, and expiry recorded | Data | Founder | NOT STARTED | Blocks rehearsal/cutover |
| MR-17 | Database restore tested | Source and RDS restore tests validate schema, row/table manifests, engine smoke, users/sessions policy and measured RTO/RPO | Data + Product | Founder | NOT STARTED | Blocks production |
| MR-18 | Object copy integrity tested | Inventory, counts, sizes and SHA-256 reconcile R2/source to S3; random content reads and version restore pass; no customer data without approval | Platform + Product | Security | NOT STARTED | Blocks storage cutover |
| MR-19 | QBO OAuth callback tested | Staging sandbox callback exact, TLS/DNS/state/session behavior and failure/rollback tested; production callback change plan approved | Product | Security + Founder | NOT STARTED | Blocks production QBO |
| MR-20 | QBO token refresh tested | Rolling refresh, concurrent refresh, revoke, terminal error, key rotation/re-encryption and no-token-log tests pass | Product + Security | Founder | PARTIAL | Blocks production QBO |
| MR-21 | Session persistence tested | Two API replicas preserve login; fixation/logout/expiry/CSRF/secret rotation/restore invalidation tests pass | Product | Security | NOT STARTED | Blocks production |
| MR-22 | Tenant-isolation tests passed | Real PostgreSQL two-tenant read/write/update/delete/export/admin/public-demo/account/connector/suggestion suite passes; singleton Stripe binding replaced or explicitly restricted; per-company account truth and RLS/equivalent evidence reviewed | Product + Data | Security | PARTIAL: PR #186 scopes routes/queries and tests, but DB enforcement and multi-tenant credential/account truth are absent | Blocks staging connector sign-off and production |
| MR-23 | Security review completed | IAM/network/KMS/S3/RDS/ECS/WAF/container/dependency/provider/auth findings closed; Critical/High zero | Security | Founder | NOT STARTED: dependency audit unavailable and Dependabot disabled | Blocks production |
| MR-24 | Sensitive-data logging review completed | Automated fixtures and manual sampling show no secrets, names, financial rows, prompts/responses or cookies in logs; retention/access tested | Security + Product | Founder | NOT STARTED | Blocks production |
| MR-25 | Load test passed | Staging supports assumed 25 rps burst, concurrent sessions, uploads and bounded provider jobs without unsafe DB connections/memory/latency | Product + Platform | Infrastructure | NOT STARTED | Blocks production sizing approval |
| MR-26 | Failure-mode testing completed | DB failover, task loss, QBO/Stripe/AI/verifier timeout, connector pagination/rate/error replay, R2/S3 error, queue replay, malformed upload, rejected destructive schema diff, migration failure, startup warm-up/readiness timeout and AZ path tested | Platform + Product | Founder | PARTIAL: destructive proposal was safely canceled and startup transient observed; automated rejection/readiness tests absent | Blocks production |
| MR-27 | Monitoring and alerts tested | Every required alert, including startup readiness timeout and schema/migration failure, is triggered in staging, reaches two founder-controlled channels, links a runbook and clears correctly | Platform | Founder | NOT STARTED | Blocks production |
| MR-28 | Incident runbook approved | Account takeover, cross-tenant, token/provider, upload, DB, domain, deletion, outage and communication procedures tabletop-tested | Security + Founder | Founder | NOT STARTED | Blocks production |
| MR-29 | Rollback tested | Prior image/frontend rollback under 30 minutes; compatible migration rollback/forward-fix and write-freeze/PITR decision exercised | Platform + Data | Founder | PARTIAL: rollback SHA `30a8ed2` identified, but rollback was not required or exercised | Blocks production |
| MR-30 | Founder recovery exercise completed | Founder on clean workstation recovers AWS/GitHub/registrar access, deploys known-good artifact, restores DB/object and revokes simulated compromise | Founder + Infrastructure | Founder with observer | NOT STARTED | Blocks production |
| MR-31 | Customer-data deletion tested | Test tenant removed from DB, sessions, QBO/connector credentials, external connections/observations, commercial account records, objects/versions, provider records and indexes; backup expiry/evidence record accurate | Product + Privacy | Founder + counsel where required | NOT STARTED | Blocks production |
| MR-32 | Migration rehearsal completed | Full timed synthetic/sanitized rehearsal includes backup, copy, schema, deploy, callback, validation, rollback and evidence; no unresolved P1/P2 | Program lead | Founder | NOT STARTED | Blocks cutover approval |
| MR-33 | Production cutover plan approved | Named roles, exact commands, freeze, comms, timing, health/data checks, go/no-go/rollback thresholds and customer plan approved | Program lead | Founder | NOT STARTED | Blocks production cutover |

## Stage Exit Rules

### Architecture approval

Strategic direction is complete through accepted-in-principle ADR-0011. Implementation architecture approval still requires MR-01 through MR-10 to be PASS. MR-09 is currently a hard failure because `ai.fo` ownership/application control and acceptable verifier data handling are not proven.

### Staging creation

Requires MR-04 through MR-11 and MR-15 to be PASS, including explicit generated-SQL review/destructive-diff rejection and readiness stabilization, plus founder authorization for resource creation and recurring cost. Documentation completion is not authorization to apply.

### Staging sign-off

Requires MR-12 through MR-15 and MR-18 through MR-28 to be PASS with synthetic data. Any Critical/High security finding fails the stage.

### Production creation

Requires staging sign-off, production account/cost approval, MR-16 through MR-31 PASS, and a separately reviewed production Terraform plan. Production may be created empty before customer data only under explicit founder approval.

### Production cutover

Requires every gate PASS, including MR-32 and MR-33. The cutover approver must confirm a current source backup, tested rollback, no unresolved P1/P2, verified domain/callback control, and named incident channel.

## Evidence Storage Standard

- Evidence links to immutable Git commits, workflow runs, artifact digests, sanitized command outputs, provider contract records, and dated drill reports.
- Evidence must not contain secrets, token values, customer rows, raw financial files, session cookies, Terraform state, or plan files.
- Every drill report records scope, timestamp, environment, owner, approver, expected result, actual result, elapsed time, findings, follow-up IDs, and evidence location.
- “Configured” without a restore/test result is not a pass for recovery controls.
