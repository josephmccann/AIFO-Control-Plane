# Product Runtime Prerequisite Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Do not execute until a separately scoped product-code mission is authorized.

**Goal:** Harden the current `3329c99` product baseline into an independently deployable, tenant-safe and recoverable runtime without weakening the validated demo.

**Architecture:** Establish explicit migration and readiness controls first, then harden credentials, tenant boundaries, sessions, uploads, logs, deletion and model providers before producing the immutable deployment artifact. Each prerequisite is independently reviewed and preserves the currently validated Replit demo rollback boundary until superseded.

**Tech Stack:** Node.js, TypeScript, Express, PostgreSQL, Drizzle, React/Vite, pnpm, Vitest, Replit for the current demo, and the Proposed AWS-managed target.

## Global Constraints

- Do not modify `AI.FO-Demo` until a separately authorized implementation mission.
- Do not enable connectors or configure Stripe.
- Do not use customer financial data.
- Do not create or mutate AWS product-runtime resources.
- Preserve live demo SHA `3329c99beb0713269b54bc5fd6a7fb39bf44f398` and rollback reference `30a8ed24b7a30c74846c7bb322be24ef5ff6ec2c` until a later validated release supersedes them.
- Treat destructive or unexplained generated SQL as a hard stop.

---

Date: 2026-07-15

Status: Documentation-only plan based on live `AI.FO-Demo` `master` at `3329c99beb0713269b54bc5fd6a7fb39bf44f398`. The demo deployment dependency is resolved and item 1 is ready for a separately authorized product-code mission. No implementation has started.

## Goal And Exit Boundary

Prepare `AI.FO-Demo` for a synthetic-data staging deployment and, after all production gates pass, the first approximately 10 customer companies. Execute the work in the dependency order below. Each implementation pull request must be independently reviewable, preserve QBO recovery/trust evidence and sealed board-package behavior, and pass the repository's pinned validation.

PR #186 is now merged evidence, not a future assumption. It adds session-derived account data, feature-flagged Stripe/Gusto/Plaid connector surfaces, normalized observations, transactional idempotent persistence, and editable calibration suggestions. Its new tables and credential/configuration surfaces are included in every applicable prerequisite below.

The current Replit demo now runs `3329c99` successfully with connectors disabled and migration `0011_external_connectors.sql` applied transactionally. The deployment hold is resolved. During that deployment, an automatic schema-diff workflow proposed destructive drops and was canceled before promotion, and health returned transient HTTP 500 responses until startup stabilized. These facts strengthen item 1 and move readiness immediately behind it; they do not authorize implementation in this documentation mission.

## Dependency Sequence

```text
1 controlled migrations
  -> 2 readiness/health stabilization
  -> 3 QBO key rotation
  -> 4 tenant isolation
  -> 5 session/CSRF
  -> 6 upload quarantine
  -> 7 structured redaction
  -> 8 customer deletion
  -> 9 AI/verifier policy
  -> 10 reproducible artifact
```

Items 6, 7, and 9 may be developed in parallel after item 5, but item 8 consumes their storage/log/provider inventories, and item 10 is the final deployable-artifact proof. Item 2 must follow item 1 before another deployment mechanism is treated as a safe baseline. No customer data may enter staging; production remains blocked until every production gate passes.

## 1. Controlled Schema Migrations And Publish Safety

**Merged product files/components affected:** `db/migrations/0003_qbo_connections.sql`, `0007_onboarding_universal_constraints.sql`, `0008_metric_history.sql`, `0009_company_identity_and_track.sql`, `0010_seal_attestation.sql`, new `0011_external_connectors.sql`; `lib/db/src/schema/aifo.ts`; `lib/db/scripts/drizzle-push.mjs`; `artifacts/api-server/src/index.ts`, `lib/seed.ts`, `lib/storage.ts`, new `connectors/store.ts`; root and database package scripts.

**PR #186/deployment overlap:** Partial. Migration `0011` is explicit, additive, and was applied transactionally to the current demo. The final schema contains 2 connector tables, 4 constraints and 7 indexes with 0 connector/observation rows. Connector writes are transactional/idempotent. This proves the single migration can deploy; it does not establish a ledger, remove startup DDL, add company foreign keys/RLS/check constraints, or define expand/contract and rollback. Replit separately proposed destructive drops when environment schemas diverged, proving that automatic schema convergence is unsafe as production authority.

**Implementation:** Select one migration runner with an immutable ledger; baseline development and production independently; make startup schema mutation fatal/absent; add preflight schema-version checks; require expand/migrate/contract ordering; add constraints only after orphan/invalid-row checks. Capture and explicitly review generated SQL before every publish. Reconcile it to version-controlled migrations and the intended production schema. Any destructive or unexplained statement (`DROP`, truncation, destructive `ALTER`, implicit data rewrite or object removal) is a stop condition requiring a separately accepted migration/rollback plan. Never allow development schema state or an automatic diff to become production migration authority. Treat connector tables as first-class migration and restore scope.

**Acceptance/tests:** Empty-database migration; upgrade from independently captured development and production-like schema fixtures; repeat run is a no-op; concurrent runner lock; application refuses incompatible schema; expected SQL matches the reviewed migration set; a fixture that would drop an unrelated table is rejected before promotion; additive connector migration preserves unrelated tables/data; rollback rehearsal restores the pre-migration snapshot or forward-fixes; connector uniqueness and transaction tests remain green.

**Migration/rollback:** Back up first, capture source/target schema inventories, generate and review SQL, deploy additive schema before readers/writers, backfill with resumable batches, validate counts/constraints, then contract in a separately approved later release. Cancel before promotion on any destructive/unexplained proposal. Roll back application while schema remains backward-compatible; restore/PITR only under the approved recovery procedure. Keep `30a8ed24b7a30c74846c7bb322be24ef5ff6ec2c` as the current demo application rollback reference until superseded by a later validated deployment.

**Blocking:** Blocks staging, production, and customer data.

**ADR:** No new ADR. Covered by ADR-0013 and ADR-0021; record the selected migration tool in their implementation notes.

## 2. Readiness And Health Stabilization

**Merged product files/components affected:** `artifacts/api-server/src/routes/health.ts`, `routes/account.ts`, `routes/connectors.ts`, `app.ts`, `index.ts`; DB initialization in `lib/db/src/index.ts`, object/config initialization in `lib/storage.ts`, session store in `app.ts`, migration ledger from item 1; `lib/deployParity.ts`, `scripts/deployParity.ts`, `scripts/demoSmoke.ts`, `tests/deployParity.test.ts`; graceful shutdown to be added.

**PR #186/deployment overlap:** Partial. Account readiness includes connector status but masks connector-read failure as an empty list; feature flags keep connectors out of the critical path. During the validated demo publish, startup health returned transient HTTP 500 responses until initialization completed and then stabilized. This proves eventual health, not a safe liveness/readiness contract.

**Implementation:** Keep liveness process-local and non-500 once the HTTP process can serve; add a distinct readiness signal for compatible schema, completed startup, DB/session store and required object configuration. Classify optional QBO/Stripe/AI/verifier dependencies as degraded rather than causing restart loops. Expose no secrets/customer values; drain on SIGTERM; publish bounded dependency metrics. Deployment automation waits for a defined consecutive-success stabilization window and rejects a target that never stabilizes inside the approved timeout.

**Acceptance/tests:** Liveness and readiness are distinguishable; startup-in-progress does not advertise ready; DB/schema/session failure removes readiness; optional provider failure reports degraded; account endpoint distinguishes unavailable from unconfigured; consecutive readiness successes are required before smoke/promotion; transient failures inside the warm-up allowance do not promote prematurely; timeout causes failed deployment/rollback; startup and shutdown under load preserve acknowledged work.

**Migration/rollback:** Add endpoints/semantics before changing platform health targets. Validate locally and in a synthetic publish with recorded first-response, ready-at and stabilization timestamps. Retain the prior health target for rollback only if it cannot route traffic before readiness; never use an always-200 response that hides dependency failure.

**Blocking:** Blocks treating any deployment as staging-equivalent, and blocks production. It does not block development of later prerequisites once item 1 has established safe schema control.

**ADR:** No new ADR. Covered by ADR-0012 and ADR-0021.

## 3. QBO Key-Version Rotation

**Merged product files/components affected:** `artifacts/api-server/src/lib/qboTokenCrypto.ts`, `qboTokenStore.ts`, `qboOAuthClient.ts`; `routes/qbo.ts`, `routes/qboOAuth.ts`; `tests/qboTokenCrypto.test.ts`, `qboTokenStore.test.ts`, `qboOAuthClient.test.ts`, `qboOAuth.route.test.ts`, `qboSync.route.test.ts`; `db/migrations/0003_qbo_connections.sql`; `lib/db/src/schema/aifo.ts`; `.env.example`; `docs/SECRETS.md`.

**PR #186 overlap:** None for token cryptography. PR #186 correctly keeps credentials out of generic connector tables and preserves QBO recovery tests, reducing the risk that normalized observations become a token store.

**Implementation:** Add ciphertext key version and authenticated tenant/provider context; support active and bounded previous decrypt keys; implement a batched, idempotent re-encryption command with dry-run/progress evidence; distinguish routine rotation, compromise revocation, and key-loss recovery.

**Acceptance/tests:** Known-answer crypto tests; wrong-company/provider/version rejection; active/previous-key decrypt; re-encryption interruption/resume; no plaintext or ciphertext in logs/errors; sandbox OAuth refresh after rotation; emergency revocation invalidates or reconnects affected tenants predictably.

**Migration/rollback:** Add nullable version, backfill legacy rows under the old key, verify decrypt/re-encrypt row counts, switch writes to the new version, retain the old key for a bounded rollback window, then retire only after founder-approved evidence. Never print key material.

**Blocking:** Blocks staging with QBO secrets, production, and all customer data. Synthetic staging without QBO credentials may proceed only after items 1 and 2.

**ADR:** No new ADR. ADR-0015 already owns the keyring and rotation decision.

## 4. Database-Backed Tenant-Isolation Testing

**Merged product files/components affected:** `artifacts/api-server/src/routes/account.ts`, `routes/connectors.ts`, `routes/company.ts`, `routes/uploads.ts`, `routes/qbo.ts`, `routes/qboOAuth.ts`, `routes/aiGenerate.ts`, `routes/admin.ts`; `connectors/store.ts`, `connectors/stripeAdapter.ts`, `connectors/types.ts`; `lib/storage.ts`, `lib/auth.ts`; `tests/account.route.test.ts`, `connectorAdapter.test.ts`, `connectorStore.test.ts`, `connectors.route.test.ts`, `authz.test.ts`; `db/migrations/0011_external_connectors.sql`; `lib/db/src/schema/aifo.ts`; frontend `components/AccountPanel.jsx`, `CalibrationFields.jsx`, `pages/UploadWizard.jsx` and their tests.

**PR #186 overlap:** Meaningful but incomplete. Routes derive company from the session; connector reads/writes include `companyId`; sync is admin-only and `AIFO_STRIPE_COMPANY_ID` binds the single Stripe key to one company. New tests cover route and persistence behavior. The new tables still lack database-enforced tenant boundaries/FKs, the Stripe credential model supports only one assigned company, and account plan/status/billing/support fields are global environment values rather than per-company records.

**Implementation:** Build a real PostgreSQL two-tenant matrix for every data-owning route/store; verify positive and negative authorization, global-admin boundaries, object-key ownership, session rebinding, connector sync/read/suggestion isolation, and account metadata truth. Decide and implement RLS or an explicitly approved centralized query/constraint equivalent. Before onboarding more than one connector tenant, replace the singleton Stripe binding with a per-tenant credential/authorization record; store commercial account metadata per company or label it non-authoritative and hide it from multi-tenant production.

**Acceptance/tests:** Tenant A cannot read, mutate, infer existence, or trigger provider work for tenant B; admin behavior is explicit/audited; DB constraint/RLS tests survive direct query attempts; connector observations and suggestions never cross companies; connector-read failure is distinguishable from "no connectors"; all owned tables appear in a tenant-coverage manifest.

**Migration/rollback:** Add company FKs/constraints after orphan audits; introduce per-company account/connector records additively; dual-read only for a bounded verified window; keep connector flag off during backfill; rollback disables connectors and returns to prior read path without deleting records.

**Blocking:** Blocks production and customer data. Blocks staging connector tests until the per-tenant credential fixture and isolation suite exist; synthetic non-connector staging may proceed earlier.

**ADR:** A separate ADR is required only when choosing RLS versus the equivalent enforcement model and when selecting the multi-tenant connector credential/account source of truth. Tests themselves do not need an ADR.

## 5. Session And CSRF Hardening

**Merged product files/components affected:** `artifacts/api-server/src/app.ts`, `lib/auth.ts`, `routes/auth.ts`, `routes/company.ts`, `routes/uploads.ts`, `routes/qbo.ts`, `routes/qboOAuth.ts`, `routes/aiGenerate.ts`, `routes/connectors.ts`, `tests/authz.test.ts`, `tests/qboOAuth.route.test.ts`, `tests/connectors.route.test.ts`; PostgreSQL session store initialized by the API; frontend `artifacts/aifo/src/utils/apiClient.js` and authenticated forms.

**PR #186 overlap:** Partial. New account/connector routes use session-derived company identity and connector sync requires admin role. It adds a new privileged POST endpoint that must be covered by CSRF, origin, rate, reauthentication, and durable audit controls.

**Implementation:** Regenerate on authentication/role change; explicitly destroy server session and clear cookie on logout; enforce secure cookie/domain/proxy settings; add CSRF token or strict same-origin/custom-header validation to every state change; define session-secret rotation/invalidation; replace process-local auth abuse controls with durable or edge enforcement; add high-risk connector-sync audit and, if justified, recent-auth requirement.

**Acceptance/tests:** Session fixation fails; logout invalidates DB session; expired/revoked/rotated sessions fail; cross-origin state changes and missing/invalid CSRF fail; OAuth callback state remains valid; horizontal replicas share sessions; connector sync rejects non-admin, wrong tenant binding, and forged origin.

**Migration/rollback:** Roll out compatible cookie/CSRF reads before enforcement, observe synthetic clients, then enforce. Emergency rollback may disable new state-changing surfaces; never weaken secure production cookie settings.

**Blocking:** Blocks staging authentication validation, production, and customer data.

**ADR:** No new ADR. Covered by ADR-0016.

## 6. Upload Quarantine, Integrity, And Deterministic Ordering

**Merged product files/components affected:** `artifacts/api-server/src/routes/uploads.ts`, `lib/storage.ts`, financial-engine ingestion called by the upload route, `artifacts/aifo/src/pages/UploadWizard.jsx`, `components/CalibrationFields.jsx`, `utils/sourceHealth.js`, `utils/sourceActionLabels.js`, `tests/components/uploadWizard.test.jsx`, `calibrationFields.test.jsx`, `sourceHealth.test.js`, plus upload/object metadata in `lib/db/src/schema/aifo.ts`. PR #186's calibration suggestion integration must consume only accepted observations/files and preserve explicit user edits.

**PR #186 overlap:** Narrow UI overlap only. Editable connector suggestions reduce silent overwrite risk, but upload objects are still persisted before full validation and have no checksum/quarantine/malware/deterministic replay contract.

**Implementation:** Stream to quarantine; enforce byte limits, signatures and parser limits; calculate SHA-256 and content identity; sanitize names/formulas; scan or explicitly reject unsupported active content; promote only accepted objects; define deterministic multi-file ordering and duplicate policy; persist an immutable ingestion manifest and provenance for connector-assisted calibration.

**Acceptance/tests:** MIME/extension mismatch, oversized/zip-bomb/malformed/malicious fixtures fail safely; checksum duplicate behavior is deterministic; parser order is stable; rejected files never reach the engine; retry is idempotent; user-edited suggestions remain distinguishable from provider observations.

**Migration/rollback:** Existing objects remain read-only legacy inputs until inventoried; new writes use quarantine/accepted states. Rollback disables ingestion, not validation, and never promotes rejected files.

**Blocking:** Blocks staging upload validation, production, and uploaded customer data.

**ADR:** No separate ADR for the workflow. ADR-0014 covers storage; add an ADR only if a managed malware service or materially different storage topology is selected.

## 7. Structured Redaction

**Merged product files/components affected:** `artifacts/api-server/src/lib/log.ts`, `aiGeneration.ts`, `verify.ts`, `qboOAuthClient.ts`, `qboTokenStore.ts`, `storage.ts`; `routes/admin.ts`, `aiGenerate.ts`, `auth.ts`, `qbo.ts`, `qboOAuth.ts`, `uploads.ts`, new `account.ts`/`connectors.ts`; new `connectors/stripeAdapter.ts`/`store.ts`; `tests/adminPrivacy.test.ts`, `aiBoundary.test.ts`, `verify.test.ts`, `connectors.route.test.ts`, `account.route.test.ts`; application/audit event schemas to be added.

**PR #186 overlap:** Partial. Connector routes emit safe error codes instead of raw provider errors and Stripe persistence is aggregate-only. New account, provider, metric, period, company, and calibration data nevertheless expand the redaction inventory.

**Implementation:** One structured logger with allowlisted fields, request/correlation/tenant pseudonymous IDs, secret/header/token/filename/provider-payload redactors, separate restricted audit events, bounded error serialization, and a ban on raw prompts/verifier/Stripe responses in operational logs.

**Acceptance/tests:** Canary secrets/PII/financial values are absent across success and failure logs; error objects/cause chains redact; audit events prove who triggered connector sync without exposing observations/credentials; static checks prevent direct console use in production paths; retention/access policies are documented.

**Migration/rollback:** Introduce logger compatibility wrapper, convert highest-risk paths first, fail CI on regressions, then remove direct console usage. Rollback retains redaction; only transport/sink may be reverted.

**Blocking:** Blocks production and customer data; blocks staging with any realistic sensitive fixture.

**ADR:** No new ADR. Covered by ADR-0019.

## 8. Customer Deletion

**Merged product files/components affected:** company-owned tables in `lib/db/src/schema/aifo.ts` and `db/migrations/*.sql`; session records configured in `artifacts/api-server/src/app.ts`; QBO state in `lib/qboTokenStore.ts` and `routes/qboOAuth.ts`; uploads/R2 objects in `lib/storage.ts`/`routes/uploads.ts`; narratives/verifier records in `lib/aiGeneration.ts`/`verify.ts`; sealed packages in `routes/sealedSnapshots.ts`/`sealedSnapshotsPeriod.ts`; new `connectors/store.ts`, `external_connections` and `source_observations`; new account/connector credential records from item 4; backups and audit evidence.

**PR #186 overlap:** No deletion path. It expands the deletion graph with two tables and makes Stripe credential revocation/account metadata lifecycle explicit. Calibration suggestions are derived/transient UI inputs but persisted source observations are customer data.

**Implementation:** Maintain a machine-checked ownership manifest; authenticated/approved deletion request; revoke providers; stop jobs; delete sessions, active data, objects, observations and credentials in dependency order; tombstone only minimal evidence; define backup expiry/legal hold; support dry-run and resumable idempotent execution.

**Acceptance/tests:** Synthetic company fixture leaves no active rows/objects/tokens/sessions or cross-tenant effects; repeat deletion is safe; provider failure is surfaced/retried; connector tables and account records are included; backup-retention status and completion evidence are truthful; public synthetic demo is protected from accidental scope expansion.

**Migration/rollback:** Deletion is deliberately irreversible after final approval. Before execution, produce scoped manifest and backup/retention consequences; pause on partial provider failure; rollback applies only before destructive phase.

**Blocking:** Blocks production and customer data. Staging must pass synthetic deletion before production approval.

**ADR:** No new ADR. ADR-0022 owns retention/deletion policy; counsel/founder approval remains required.

## 9. AI-Provider Abstraction And Verifier Fail-Closed Behavior

**Merged product files/components affected:** `artifacts/api-server/src/lib/aiGeneration.ts`, `aiSnapshotSource.ts`, `verify.ts`; `routes/aiGenerate.ts`, `llmOutputs.ts`, `verifiability.ts`; `tests/aiBoundary.test.ts`, `aiGenerationTraceability.test.ts`, `aiGenerationVerifierRepair.test.ts`, `aiGenerationWordLimits.test.ts`, `verifierIntegration.test.ts`, `verify.test.ts`; `.env.example` and `docs/SECRETS.md`. Connector observations in `connectors/store.ts` and calibration suggestions in `routes/connectors.ts`/`components/CalibrationFields.jsx` may become upstream inputs and therefore enter the processor-disclosure boundary.

**PR #186 overlap:** Partial upstream-data control. Normalized observations preserve provider/confidence and suggestions are opt-in/editable, reducing accidental authority. PR #186 does not constrain AI disclosure, abstract providers, or change the verifier's current fail-open behavior.

**Implementation:** Define provider interface and approved-data contract; minimize/pseudonymize prompts; explicitly map whether connector-derived values may be sent; enforce timeout/budget/idempotency; disable unapproved providers; make required verification fail closed so no verified/sealed/customer-visible claim is emitted when verification is absent or invalid; preserve deterministic engine authority and observation lineage.

**Acceptance/tests:** Provider contract fixtures; no names/raw rows/tokens; connector-derived fields follow disclosure policy; unavailable/malformed/contradictory verifier blocks verified output; retry cannot duplicate sealed artifacts; provider switch/disable works by configuration; cost and latency bounds alert.

**Migration/rollback:** Ship abstraction with current provider behind disabled/customer-data-safe policy, compare synthetic outputs, then enable only after contractual approval. Rollback disables narratives/verifier and serves deterministic facts; it must not restore fail-open behavior.

**Blocking:** Blocks production and any customer data sent to AI/verifier. Deterministic-only synthetic staging may proceed.

**ADR:** Yes. A focused provider-data-processing and verifier-authority ADR is required before approving any customer-data provider, because this is a material custody/correctness decision not fully owned by the infrastructure ADRs.

## 10. Reproducible Containerized Build And Deployment Artifact

**Merged product files/components affected:** root `package.json`, `pnpm-workspace.yaml`, `pnpm-lock.yaml`; `artifacts/api-server/package.json` (including new Stripe SDK), `build.mjs`, `src/index.ts`; `artifacts/aifo/package.json`, `vite.config.ts`, `prerender.mjs`; `.replit`; `lib/*/package.json`; `db/migrations/*.sql`; readiness from item 2; `artifacts/api-server/src/lib/deployParity.ts`, `src/scripts/deployParity.ts`; `.github/workflows/*`.

**PR #186 overlap:** It updates the lockfile and package tests but does not add a pinned OCI build/runtime, non-root execution, SBOM/provenance, immutable artifact, or deployment manifest.

**Implementation:** Pin Node and pnpm; multi-stage deterministic build; non-root/read-only runtime; include exactly one API artifact plus migration metadata and separately versioned frontend artifact; lockfile-frozen install; digest pin base image; generate SBOM/provenance and vulnerability results; sign/attest artifact; run DB migrations as a separate release step; preserve local/Replit synthetic demo until cutover approval.

**Acceptance/tests:** Clean checkout produces the same dependency graph and functionally identical artifacts; typecheck/build/full tests pass inside the image; no secrets/build cache/source-only files; Stripe/QBO/AI TLS dependencies work; ARM64 versus x86 is evidence-based; readiness/smoke/deploy-parity pass; prior digest rollback succeeds with compatible schema.

**Migration/rollback:** Publish immutable version/digest without deploying; promote the same artifact through environments after approval; retain prior digests/static prefixes; rollback application/frontend independently while following item 1's schema compatibility rules.

**Blocking:** Blocks staging, production, and customer data.

**ADR:** No new ADR. Covered by ADR-0021; CPU architecture remains an implementation parameter until validated.

## PR #186 Cross-Cutting Architecture And Gate Changes

- The recommended CloudFront/S3 + ECS + RDS + S3 + Secrets Manager architecture remains fit; no new microservice, database, or Kubernetes topology is justified.
- Stripe becomes an explicit egress dependency and secret/rotation/revocation inventory item. The current singleton key/company binding is acceptable only for a one-company synthetic/pilot test, not the 10-company cohort.
- `external_connections`, `source_observations`, and future per-company commercial account records belong in the same PostgreSQL boundary, backup/restore test, tenant manifest, migration ledger, retention/deletion workflow, and audit model.
- Connector sync is currently synchronous and unbounded across Stripe pagination. Keep the feature off for customers until timeout/rate/idempotency/audit evidence exists; introduce a durable job/worker only after measured behavior justifies it.
- Observation uniqueness provides current-period idempotency but overwrites history. Before customer use, decide whether this is a current snapshot or whether append-only provenance is required; migration gates must test the chosen semantics.
- Aggregate-only Stripe persistence materially reduces exposure, and editable suggestions preserve user control. Both controls must be regression-tested.
- No merged evidence resolves exact RDS sizing, NAT topology, hostname, RPO/RTO, PITR retention, or monthly budget. Those implementation parameters remain Proposed.

## Required Validation Per Implementation Pull Request

Use repository-documented pinned commands, at minimum:

```bash
pnpm install --frozen-lockfile
pnpm run typecheck
pnpm build
pnpm -r --if-present test -- --run
pnpm deploy:parity -- --target=local --base-url=http://localhost:8080
pnpm validate:ai
pnpm demo:smoke
pnpm lock:preflight
git diff --check
```

Add the focused tests named in each prerequisite and run the real-PostgreSQL migration/tenant/restore suites where applicable. A known pre-existing validation failure must be recorded with its exact evidence; it is not silently waived.
