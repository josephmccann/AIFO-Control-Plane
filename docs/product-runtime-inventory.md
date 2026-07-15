# AI.FO Product Runtime Inventory

Date: 2026-07-15

Status: Current-state evidence at product repository `8df211e02f274d0a812771327c69b6d5b6c040d2`. Open PR #186 is not part of this baseline.

## Executive Finding

AI.FO is a single Node/Express and React application backed by PostgreSQL and Cloudflare R2, deployed through Replit's application-router/autoscale model. It combines a deterministic financial engine with QuickBooks Online ingestion, CSV uploads, Anthropic narrative generation, and a GMI-hosted verifier. The architecture is understandable and appropriate for a demo, but the repository does not contain sufficient evidence for real-customer production: database backup and restore are undefined, deployment is not independently reproducible, object and customer deletion are absent, tenant isolation exists only in application queries, QBO key rotation is not implemented, uploads are not integrity-scanned, and sensitive model-provider terms are unresolved.

## Evidence Boundary

Primary evidence reviewed includes `AGENTS.md`, `README.md`, `.replit`, `.env.example`, workspace manifests and lockfile, architecture/deployment/security documents, API and frontend entrypoints, database schema and migrations, upload/QBO/auth/AI/verifier routes and libraries, tests, workflows, launchd operational scripts, open PRs, recent commits, and the live `/api/healthz` response. No secret values or customer data were read or moved.

Current deployment ownership remains partly outside Git:

- Replit resource sizing, active environment variables, database backup behavior, deployment revision history, and rollback evidence are not committed.
- Current production database vendor, version, size, backup policy, and restore history are unresolved.
- Current R2 bucket configuration, object count, encryption policy, versioning, access logs, and lifecycle are unresolved.

## Application Topology

| Area | Current implementation | State and scaling implications |
| --- | --- | --- |
| Frontend | React 19 SPA, Vite, TypeScript/JavaScript, Tailwind; build runs type checks, `vite build`, then prerenders selected pages | Static output is horizontally safe. Relative `/api` calls assume a same-origin router unless `VITE_API_BASE` is configured. Canonical metadata points at `https://ai.fo/`. |
| Frontend hosting | Replit deployment routing is implied by `.replit`; no standalone static-host deployment manifest exists | Build is reproducible locally, but production publish, cache invalidation, and rollback are not repository-controlled. |
| API | Express 5 on Node, one `app.listen(PORT)` process; API bundles to one CommonJS artifact with esbuild | Stateless request handling is mostly scalable, but process-local rate limits and operational counters are not consistent across replicas. |
| Database | PostgreSQL through `node-postgres` and Drizzle ORM | Shared durable state. Connection pool size/TLS behavior depends on `DATABASE_URL`; no explicit production pool or certificate policy. |
| Schema changes | Drizzle schema, manual SQL migrations, `drizzle-kit push`, and startup DDL coexist | No single migration ledger, ordering rule, backward-compatible deployment contract, or rollback procedure. Startup migration errors are non-fatal. |
| Authentication | Passport Local, bcrypt cost 12, invite-only registration | Credentials are database records. No MFA, email verification, password reset, lockout, or breach-password control. |
| Sessions | `express-session`; `connect-pg-simple` when `DATABASE_URL` exists; seven-day cookie | PostgreSQL sessions are durable and replica-safe. Production cookie is `secure`, `httpOnly`, `sameSite=lax`; rotation and explicit logout-destruction evidence are incomplete. |
| Background work | No application queue or worker. QBO sync and upload processing execute synchronously in API requests | Long requests can time out or be retried; idempotency is partial. A QBO refresh helper exists, but no runtime scheduler invokes it. |
| Scheduled work | Founder-Mac launchd jobs generate nightly synthetic pressure evidence and mirror telemetry | This validates product behavior but is not a production runtime scheduler or customer-data recovery mechanism. |
| Upload path | Multer memory upload, 10 MB maximum, CSV/text/Excel MIME or extension allowlist | Entire file enters API memory. No signature validation, malware scanning, quarantine, checksum contract, or spreadsheet formula sanitization. |
| Object storage | Cloudflare R2 through the S3 SDK; local filesystem fallback when R2 variables are absent | R2 credentials are static provider keys. Local fallback is not horizontally durable and must never be allowed in staging/production. |
| AI provider | Anthropic API, `claude-sonnet-4-6` | Server-owned prompt construction limits caller control, but computed financial values and customer/vendor names can reach the provider. |
| Verifier | OpenAI-compatible GMI endpoint, default DeepSeek model; 55-second timeout and one retry | The verifier receives the generated narrative and source facts. GMI's current console terms say underlying models may store or train on inputs; contractual handling is not evidenced. |
| QuickBooks | Intuit OAuth 2.0, report/transaction ingestion, encrypted token fields in PostgreSQL | Rolling refresh token is stored after refresh. One application-wide AES-256-GCM key has no key version or implemented rotation path. |
| Email/notifications | No repository-grounded customer email or transactional notification provider | Password recovery, security notifications, and customer incident messaging are not implemented. |
| Health | `/api/healthz` returns application liveness | It does not test database, R2, QBO, AI, migration state, or readiness. |
| Logs | Console logs plus in-memory operational events and counters | No durable app-log sink, exception tracker, alert routing, trace context, or comprehensive redaction enforcement is evidenced. |

## Replit And Single-Instance Assumptions

- `.replit` selects Node 24, PostgreSQL 16, Python, an `api-server` artifact, application-router deployment, and autoscale behavior.
- There is no Dockerfile, OCI image definition, runtime user, or health-driven container deployment definition.
- Replit secrets and deployment settings are required but not represented as code.
- Startup seeds an admin and invite codes from environment values and attempts schema DDL. This assumes a single safe startup owner; simultaneous replicas could race.
- Rate-limit counters and operational health events live in process memory and reset on restart.
- Upload/QBO processing is synchronous and assumes request lifetime is sufficient.
- Local filesystem upload fallback assumes single-instance local development.
- Current public deployment exposes only liveness, not a readiness contract that an orchestrator can safely use.
- The package manager is required to be pnpm but its version and the Node version are not pinned in `package.json`; `.replit` is the only Node 24 pin.

## Principal Data Flows

The data classes below use `Public`, `Internal`, `Confidential`, and `Highly sensitive`.

| # | Flow | Entry and trust boundary | Data and stores | Secrets/processors | Failure, retry, idempotency | Audit and recovery |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | User authentication | Browser -> TLS router -> Express -> PostgreSQL | Credentials and session are highly sensitive; user/company/role are confidential | `SESSION_SECRET`; bcrypt; Passport | Auth limiter is per process. Session store persists. No lockout or MFA. | Login audit trail is not durable. Session restore depends on DB and same secret. |
| 2 | Company creation | Authenticated user -> company route -> PostgreSQL | Company identity confidential | Session authorization | User may create and rebind to a new company. No transaction/lifecycle guard prevents orphaned prior data. | Ordinary app logs only; recovery requires DB restore/manual repair. |
| 3 | QBO authorization | Browser -> API -> Intuit -> callback -> API | OAuth state in session; code and realm cross trust boundaries | QBO client ID/secret, redirect URI, session secret | State/user/company checked. Lost session or callback mismatch fails. | No durable OAuth audit event; callback DNS/TLS ownership is critical. |
| 4 | Token storage/refresh | API <-> Intuit; plaintext tokens exist in task memory | AES-GCM ciphertext, IV, tag, expiry in PostgreSQL; highly sensitive | `QBO_TOKEN_ENC_KEY`, QBO client secret | Refresh-on-use, one auth retry; newest rolling refresh token stored. Terminal errors mark revoked. | No key version or tested re-encryption/rotation runbook; key loss makes tokens unrecoverable. |
| 5 | Accounting ingestion | Authenticated sync -> Intuit reports/transactions -> engine -> PostgreSQL | GL, bank, AR/AP, names and derived metrics are highly sensitive | QBO tokens; Intuit processor | Synchronous. Partial upserts are idempotent, snapshots/review records can duplicate, multi-table writes are not one transaction. | Ops events are in memory; partial recovery is manual/re-run. |
| 6 | CSV/manual upload | Browser multipart -> API memory -> R2/local -> parser | Raw accounting file highly sensitive | R2 static access key and secret | R2 write precedes validation. Upload has no explicit retry or content hash. Failed parse can leave raw objects. | Filename/company/key may be logged. No manifest or quarantine. |
| 7 | File persistence | API -> R2 S3-compatible endpoint | Raw files at `<company>/raw/<type>-<time>.csv` | R2 credentials | Download retries three times; upload does not. Same-key collision unlikely but no checksum contract. | Bucket versioning, access logs, inventory, retention, and restore evidence unresolved. |
| 8 | PostgreSQL persistence | API -> PostgreSQL | Users, sessions, connections, uploads, metrics, signals, narratives and verifier records | `DATABASE_URL` | Multiple storage patterns; many tables lack FKs; no single transactional ingestion unit. | Provider backups and restore history unknown. Startup DDL can diverge from migrations. |
| 9 | Deterministic engine | API memory -> shared financial-engine library | Highly sensitive source/derived metrics transiently in process; outputs stored | No external secret | Deterministic tests are extensive; processing may partially persist around failures. | Synthetic pressure ledger is strong correctness evidence, not production data-recovery evidence. |
| 10 | Signal generation | Engine -> signal routes/storage | Confidential/highly sensitive metrics, signal IDs and evidence | No external provider | Some unique/upsert behavior; snapshot and review creation can repeat. | Database records provide partial lineage; no append-only audit log. |
| 11 | Narrative generation | Authenticated request -> server-owned snapshot -> Anthropic | Computed financial values and customer/vendor names can be highly sensitive | Anthropic API key | Provider error/repair paths may create several calls. No application-level idempotency key. | Output may persist in DB; provider default API retention is 30 days unless ZDR is contracted. |
| 12 | Verifier | API -> GMI aggregator/model -> API | Narrative plus financial source facts highly sensitive | GMI API key | 55-second timeout, one retry. Missing/unavailable verifier can still return a generated narrative with failed verification metadata. | Raw response preview is logged to console; DB schema can retain prompt/response. Provider custody is unresolved. |
| 13 | Memo/dashboard delivery | PostgreSQL/process -> API -> browser | Confidential/highly sensitive derived decisions and names | Session cookie | Reads usually scope by session company; some demo endpoints deliberately expose a synthetic tenant. | Browser output not separately audited. Public-demo data provenance must remain synthetic-only. |
| 14 | Session lifecycle | Browser cookie <-> API <-> PostgreSQL | Cookie and session record highly sensitive | Session secret | Seven-day expiry. Logout calls Passport logout; explicit store destruction/cookie-clear evidence is missing. Secret rotation invalidates all sessions. | Session-table backup restores active sessions unless explicitly excluded/expired. |
| 15 | Administrative action | Admin session -> admin routes -> PostgreSQL | Cross-tenant confidential metadata | Admin credential/session | Global `admin` role has broad cross-tenant access; no granular approval or just-in-time model. | Admin API limits raw verifier exposure, but durable admin-action audit log is absent. |
| 16 | Error/retry | Provider/DB/R2 failures -> route errors/logs | Errors can contain identifiers or provider metadata | All relevant provider secrets must be redacted | Retry policy differs by integration; no durable queue/dead-letter mechanism. Client retry may duplicate non-idempotent work. | Console/in-memory evidence is restart-sensitive; no centralized alert/incident link. |
| 17 | Data deletion | No complete customer-facing or operator workflow | Records, sessions, uploads, tokens, narratives and backups remain distributed | QBO revoke can be attempted | QBO disconnect deletes only after successful revoke. R2 delete helper is unused. No company cascade or backup expiry workflow. | Deletion proof, legal hold, tombstone, and completion evidence do not exist. |

## Data Classification And Handling Implications

| Data | Class | Required handling implication |
| --- | --- | --- |
| Public marketing pages and explicitly synthetic demo telemetry | Public | Integrity and provenance still required; never allow real customer data into the public demo tenant. |
| Terraform/deployment metadata without secrets | Internal | Repository access control, review history, and change audit. State itself is not ordinary metadata and remains protected. |
| Product telemetry containing aggregate test counts and commit IDs | Internal | Redact tenant/user/provider detail; bounded retention. |
| User email, company identity, customer/vendor names | Confidential | Tenant-scoped access, encrypted storage/transit, redacted logs, controlled processor disclosure. |
| Session metadata without cookie value | Confidential | Short retention, operator-only access, exclude from analytics where possible. |
| Application logs and audit logs | Confidential by default | Centralize, encrypt, redact, restrict, and separate operational logs from immutable audit evidence. |
| AI prompts and generated narratives | Confidential to highly sensitive | Minimize values/names, contract processor retention, never train by default, trace disclosures, allow deletion. |
| Verifier inputs and outputs | Highly sensitive | Same controls as source financial data; current GMI terms are not acceptable without verified contractual safeguards. |
| Financial statements, GL, bank transactions, AR/AP, transaction detail | Highly sensitive | Strong tenant isolation, least privilege, encryption, processor minimization, tested backup/restore/deletion. |
| Uploaded accounting files | Highly sensitive | Private object store, checksum, malware/quarantine control, limited presigned access, versioning, deletion evidence. |
| QBO access/refresh tokens and client secret | Highly sensitive credential | Envelope encryption with versioned keys, no logs, least-privilege decryption, rotation/revocation and access audit. |
| User password hashes | Highly sensitive credential | Never export/log; strong hashing, password-reset and compromise response. |
| Session cookies and server session records | Highly sensitive credential | Secure cookie attributes, regeneration/invalidation, bounded TTL, exclude or invalidate on restore where required. |
| Anthropic, GMI, database, storage and session secrets | Highly sensitive credential | Managed secret storage, workload identity, versioning, rotation, break-glass audit; never repository/env-file persistence. |
| Backups | Same as source, generally highly sensitive | Encrypted, access-isolated, immutable/retained by policy, restore-tested, deletion lifecycle understood. |
| Terraform state | Highly sensitive infrastructure metadata | Encrypted remote backend, tightly scoped access, versioning, no local/committed copy. |

## Confirmed Operational Risks

| Severity | Confirmed risk | Repository evidence and implication |
| --- | --- | --- |
| Critical | Production domain ownership is not established | `ai.fo` currently redirects to a domain-sale page while the frontend publishes `ai.fo` canonicals. Domain, DNS, TLS and OAuth ownership are hard gates. |
| Critical | Sensitive verifier disclosure lacks an acceptable processor contract | GMI is an aggregator and its current terms permit underlying models to store/train on input. Disable or replace this path before real customer data. |
| Critical | No database backup/restore evidence | No repository runbook, RPO/RTO, snapshot inventory, or restore test. Database loss or corrupt migration recovery is unproven. |
| High | Tenant isolation is application-only | Most queries use session `companyId`, but no database RLS and many tables lack FKs. A missed predicate or global admin compromise can cross tenants. |
| High | QBO key rotation is not implementable safely today | One unversioned environment key encrypts all tokens; no keyring/re-encryption workflow. Key loss or compromise has high blast radius. |
| High | Customer deletion is not implemented | No orchestrated company/data/object/session/token/backup deletion or evidence record. |
| High | Deployment and schema rollback are not controlled | Replit settings sit outside Git; migrations are fragmented and startup DDL is non-fatal. A bad release can leave mixed schema/application states. |
| High | Upload integrity controls are incomplete | Extension can bypass MIME, no signature/malware/quarantine/checksum, and raw object persists before validation. |
| High | Sensitive-data logging is not comprehensively controlled | General logs include identifiers/filenames/keys; verifier logs a raw response preview; centralized retention/redaction is absent. |
| High | Third-party AI disclosure is broader than “no raw rows” | Computed singleton values and customer/vendor names can reach Anthropic and GMI. Data minimization and processor approval are required. |
| Medium | Long synchronous requests lack durable retry semantics | QBO sync, upload processing and AI/verifier calls can time out; partial writes and duplicate snapshots/review items are possible. |
| Medium | Production authentication controls are beta-incomplete | No MFA, password reset, email verification, durable account lockout, or explicit session-revocation evidence. |
| Medium | No durable production observability | Liveness only, process-local counters, no central error alerting, dependency SLOs, or durable admin-action trail. |
| Medium | Reproducibility depends on external platform configuration | No container definition, package-manager version, or Git-controlled production deployment settings. |
| Medium | Current scheduled validation depends on a founder Mac | Nightly launchd execution is a founder-availability and workstation-availability dependency. |
| Medium | Public demo tenant boundary relies on convention | Public routes hardcode `integra-demo`; a process must ensure customer data can never bind to that tenant. |

## Unresolved Questions Requiring Evidence

1. What Replit plan, database product/version, compute limits, network controls, backups, restore procedure, deployment revision retention, and contractual security terms are active?
2. What are the live PostgreSQL size, connection count, extension set, collation, timezone, table cardinalities, and longest transaction/query profiles?
3. Are R2 encryption, versioning, lifecycle, access logging, event notifications, and bucket-level public-access controls enabled, and how many objects/bytes exist?
4. Is the Anthropic key attached to a commercial organization with an executed DPA and zero-data-retention arrangement?
5. What exact GMI product, underlying model provider, retention, training, data location, DPA, deletion, subprocessors, incident obligations, and audit reports apply to current calls?
6. Who legally and operationally controls `ai.fo`, `getaifo.com`, registrar access, DNS, recovery contacts, and Intuit production redirect configuration?
7. Has Intuit granted production credentials and completed the required security assessment?
8. Are any real customer or production-like financial records already present in PostgreSQL or R2? This must be answered without copying data into the assessment.
9. What customer contracts, privacy promises, retention commitments, deletion duties, residency constraints, and breach-notification windows apply?
10. What product launch date defines the calendar deadline for founder decisions and rehearsals?

## Current Validation Strengths

- Large deterministic financial-engine and generated frontend test corpus.
- Nightly synthetic pressure ledger with off-machine GitHub deadman monitoring.
- Strong route-level authorization regression tests for many tenant-scoped resources.
- QBO token encryption tamper/wrong-key tests and OAuth environment checks.
- AI route rejects caller-supplied prompt/tenant/raw data and pins the legacy endpoint absent.
- Admin privacy tests prevent raw verifier prompt/response from being returned through the reviewed admin API.
- Deployment-parity checks validate required environment presence and QBO callback shape without printing secret values.

These are valuable correctness controls. They do not replace real database integration tests, restore drills, deployment rehearsals, processor due diligence, or production security evidence.

## Validation Snapshot

Run against clean product `master` at `8df211e` on 2026-07-15:

- Frozen pnpm install: pass with pnpm 10.33.0 and Node 26.3.0. The repository itself does not pin these versions; `.replit` selects Node 24.
- Type checks and production build: pass. Vite warns that the main JS chunk is approximately 1.18 MB before gzip and Node reports a `module.register()` deprecation.
- API suite: 88 files passed, 982 tests passed, 5 skipped.
- Frontend/scripts suite: 139 files passed, 13,477 tests passed.
- `pnpm lock:preflight`: fail only on telemetry provenance because the public telemetry route does not expose both commit and `generatedAt`; eight other policy checks pass.
- `pnpm audit --prod --audit-level high`: unverified because the npm audit endpoints returned HTTP 410. GitHub Dependabot alerts are disabled, so no independent repository dependency-alert result exists.

The red lock preflight and missing dependency-security result are current product-baseline discrepancies. They are not changed by this documentation mission and must be resolved before a reproducible staging gate can pass.

## Source Notes

- Replit autoscale behavior and pricing are described in [Replit deployment pricing](https://docs.replit.com/billing/deployment-pricing).
- Intuit requires registered TLS redirect URIs and the latest rolling refresh token to be stored, per the [Intuit authorization FAQ](https://developer.intuit.com/app/developer/qbo/docs/develop/authentication-and-authorization/faq).
- Intuit states that production-connected apps are subject to platform requirements and annual security assessment in its [publishing requirements](https://developer.intuit.com/app/developer/qbo/docs/go-live/publish-app/platform-requirements).
- Anthropic documents 30-day standard API input/output retention and organization-specific ZDR in its [commercial retention guidance](https://privacy.claude.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data) and [API retention documentation](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention).
- GMI's [console terms](https://www.gmicloud.ai/en/legal/gmi-cloud-console-master-service-agreement) describe an aggregator and warn that underlying models may store or train on inputs; its [privacy policy](https://www.gmicloud.ai/legal/privacy) does not establish the precise API payload retention needed for this workload.
