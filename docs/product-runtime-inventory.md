# Product Runtime Inventory

## Status

This inventory was created from the local `AI.FO-Demo` checkout at `/Users/joemccann/code/AI.FO-Demo` on 2026-07-14. It records observed product facts that must guide control-plane infrastructure work.

## Product Reality Summary

AI.FO is a working financial intelligence platform. It ingests QuickBooks Online reports and accounting CSV exports, reconciles them into financial datasets, computes deterministic financial snapshots and registered business signals, and sends a server-built computed snapshot to an AI narrative and verifier layer. Raw accounting rows, prompt text, tokens, realm IDs, company identifiers, customer names, vendor names, and accounting values are excluded from normal public telemetry and AI-generation boundaries where documented.

The central product boundary is implemented and documented: the deterministic financial engine owns financial truth, while the AI layer explains and verifies computed outputs.

## Applications And Packages

| Path | Package | Purpose |
| --- | --- | --- |
| `artifacts/aifo` | `@workspace/aifo` | React 19, TypeScript, Vite frontend, public home, authenticated cockpit, upload, analysis, board and admin surfaces |
| `artifacts/api-server` | `@workspace/api-server` | Express 5 API server, auth, ingestion, QBO OAuth/sync, AI generation, verifier, telemetry, admin ops |
| `lib/db` | `@workspace/db` | PostgreSQL schema and Drizzle ORM integration |
| `lib/financial-engine` | `@workspace/financial-engine` | Deterministic financial engine and signal registry |
| `lib/api-spec` | `@workspace/api-spec` | OpenAPI specification and codegen configuration |
| `lib/api-zod` | `@workspace/api-zod` | Shared Zod validation schemas |
| `lib/api-client-react` | `@workspace/api-client-react` | Generated frontend API client |
| `scripts` | `@workspace/scripts` | Utility scripts and seed support |

## Build Commands

| Command | Meaning |
| --- | --- |
| `pnpm install` | Install workspace dependencies; pnpm is required by preinstall |
| `pnpm build` | Typecheck libraries and build workspace packages |
| `pnpm run typecheck` | Typecheck libraries and artifact packages |
| `pnpm --filter @workspace/db push` | Apply Drizzle schema to the configured PostgreSQL database |
| `pnpm --filter api-server dev` | Start API server with root `.env` loaded when present |
| `pnpm --filter aifo dev` | Start frontend dev server |
| `pnpm --filter api-server build` | Build API server |
| `pnpm --filter aifo build` | Build frontend and prerender |

## Runtime Services

| Service | Current use |
| --- | --- |
| Node.js 20+ | API server, scripts, frontend build and dev tooling |
| PostgreSQL | Users, sessions, companies, uploads, datasets, invite codes, QBO connections, and related product state |
| Express 5 | API server and authentication routes |
| Passport | Session authentication |
| Drizzle ORM | Database schema and data access |
| Cloudflare R2 | Production raw CSV upload storage |
| Local disk uploads | Development fallback under `artifacts/api-server/.uploads/` |
| QuickBooks Online | OAuth, sandbox sync, reports, transaction and bank activity |
| Anthropic | Narrative generation through server-owned AI boundary |
| GMI Cloud or OpenAI-compatible verifier | Independent AI output verification |
| Airtable | Nightly pressure-test operational ledger in the product repo |
| GitHub Actions | Off-machine deadman workflow and repository automation |
| macOS launchd | Current local nightly pressure-test scheduler in product repo |

## Database Requirements

The product requires PostgreSQL through `DATABASE_URL`. The API stores sessions using PostgreSQL when configured. Product docs reference Drizzle schema push through `pnpm --filter @workspace/db push`.

Database-backed areas observed in docs and package layout:

- users and authentication sessions;
- invite codes;
- companies;
- uploads and datasets;
- QBO connections and encrypted token metadata;
- external connectors in open PR #186;
- sealed snapshots, board package, telemetry and trust evidence support.

Control-plane implication: production migration cannot be complete until PostgreSQL hosting, backup, restore, encryption, access control, schema migration, and secret management are designed. The current control-plane Terraform does not yet provision product PostgreSQL.

## Storage Requirements

| Storage | Requirement |
| --- | --- |
| PostgreSQL | Durable transactional product state and session store |
| Cloudflare R2 | Production upload object storage |
| Local upload directory | Development fallback only, ignored in Git |
| GitHub repository | Source, workflow history, branch and PR audit |
| Terraform S3 state bucket | Control-plane infrastructure state |
| Future backups | Required for PostgreSQL and any production object storage |

## Integration Requirements

Current integrations:

- QuickBooks Online OAuth and reports.
- Anthropic narrative generation.
- GMI Cloud or compatible verifier.
- Cloudflare R2.
- PostgreSQL.
- Airtable for product nightly pressure-test ledger.
- GitHub Actions and GitHub repository state.

Validated near-term integrations:

- Stripe-style operating metric connectors are represented in product PR #186 but are not merged into the product baseline.
- Future direct integrations are documented for payroll, CRM, banking, subscription billing, product, industry, workforce, POS, e-commerce, construction, healthcare, education, and other systems.

## Open Product Pull Requests Reviewed

| PR | Status | Infrastructure interpretation |
| --- | --- | --- |
| `josephmccann/AI.FO-Demo#180` | Draft | Founder context and constitutional docs reinforce control-plane principles but are not merged product baseline |
| `josephmccann/AI.FO-Demo#186` | Open | Connector/store/Stripe work is near-term product context, not a current infrastructure requirement until merged |

## Environment Variables

Required or production-critical:

- `DATABASE_URL`
- `SESSION_SECRET`
- `AI_INTEGRATIONS_ANTHROPIC_API_KEY`
- `AI_INTEGRATIONS_ANTHROPIC_BASE_URL`
- `GMI_CLOUD_API_KEY`
- `GMI_CLOUD_BASE_URL`
- `GMI_CLOUD_MODEL`
- `PORT`
- `NODE_ENV`

QuickBooks:

- `QBO_CLIENT_ID`
- `QBO_CLIENT_SECRET`
- `QBO_ENVIRONMENT`
- `QBO_REDIRECT_URI`
- `QBO_TOKEN_ENC_KEY`
- `QBO_SUCCESS_REDIRECT`
- `AIFO_QBO_SEED_COMPANY_ID`

Storage:

- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET_NAME`
- `LOCAL_UPLOAD_DIR`

Deployment validation:

- `AIFO_DEPLOY_TARGET`
- `AIFO_API_BASE_URL`
- `AIFO_VALIDATION_COMPANY_ID`
- `AIFO_VALIDATION_PERIOD_LABEL`
- `AIFO_DEMO_SMOKE_COMPANY_ID`
- `AIFO_DEMO_SMOKE_EMAIL`
- `AIFO_DEMO_SMOKE_PASSWORD`
- `AIFO_DEMO_SMOKE_EXPECT_SIGNALS`
- `AIFO_DEMO_SMOKE_EXPECT_APPLICABLE_SIGNALS`

Other:

- `AIFO_CORS_ORIGINS`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`
- `AIRTABLE_API_KEY`
- `BASE_PATH`
- `REPL_ID`

## Test And Validation Commands

Product docs identify these commands as operationally important:

```bash
pnpm build
pnpm run typecheck
pnpm deploy:parity -- --target=local --base-url=http://localhost:8080
pnpm validate:ai
pnpm demo:smoke
pnpm --filter api-server demo:smoke -- --sync-qbo
pnpm qbo:seed-demo -- --dry-run
pnpm qbo:seed-demo
cd artifacts/aifo && npx vitest run
cd artifacts/api-server && npx vitest run
pnpm --filter aifo test:e2e tests/e2e/data-visualization.spec.ts
pnpm lock:preflight
git diff --check
```

Control-plane implication: any product-hosting infrastructure must support running these validation commands in local, staging, and production-like contexts without exposing secrets.

## Deployment Assumptions

Observed:

- Current live demo is `https://demo.getaifo.com`.
- Replit is referenced as current deployed validation target.
- Local development uses API port `8080` and frontend Vite port `5173`.
- Production QBO OAuth, deployment parity, operational monitoring, browser E2E, and security/privacy review are planned phases.
- Remote smoke can target `AIFO_API_BASE_URL=https://demo.getaifo.com`.

Not yet established in control plane:

- AWS production runtime architecture for the product application.
- PostgreSQL managed service selection.
- Domain and TLS ownership in AWS.
- R2 versus AWS S3 migration decision for uploads.
- Secrets manager selection for product runtime.

## Current Operational Risks

| Severity | Risk | Evidence |
| --- | --- | --- |
| High | Product production runtime requirements are not yet translated into control-plane infrastructure | Control-plane currently provisions operator host only |
| High | Customer financial data, QBO tokens, AI prompts, and telemetry require strong separation and auditability before AWS production hosting | Product security docs and UX acceptance criteria |
| High | PostgreSQL backup and restore path is not yet defined in control-plane | Product depends on PostgreSQL |
| Medium | Product currently references Replit and local launchd operational paths that may not map directly to AWS | Product README and demo runbook |
| Medium | Open product PR #186 may change connector and storage requirements | PR #186 open |
| Medium | Validation commands need secret-backed environments and must not leak private data | Demo validation and ops runbooks |
| Low | Current control-plane host egress is broad HTTPS by design | Needed for package, GitHub, model, and API access |

## Live Demo Dependencies

- `https://demo.getaifo.com`
- Replit Secrets and database, per product docs
- Intuit sandbox redirect URI registered exactly
- QBO sandbox company and optional seeded deterministic records
- Anthropic and verifier credentials
- Public-safe telemetry artifact and live fetch behavior
- Smoke credentials when shell DB differs from deployed runtime DB

## Documentation Versus Implementation Discrepancies

| Item | Observation | Control-plane interpretation |
| --- | --- | --- |
| Product docs describe R2 as production storage, but local fallback exists | R2 is optional locally but production-facing | Do not assume AWS S3 replaces R2 without an explicit migration decision |
| Product README says `AI_INTEGRATIONS_ANTHROPIC_API_KEY` is required; verifier can short-circuit when unset in `.env.example` | Full demo validation requires both Anthropic and GMI | Separate development and validation requirements |
| Product docs reference Replit deployment | Control-plane is AWS-focused | Treat AWS product hosting as a future migration, not current fact |
| Product PR #186 adds connector/account surfaces | Not merged into current product baseline | Design connector infrastructure only as near-term deferred work |
| Handoff PR #1 says protected environments for future plan/apply workflows | Current plan workflow already declares `environment: terraform-plan`; environment itself still needs GitHub configuration | Add GitHub environment setup to bootstrap runbook |

## Infrastructure Traceability

| Infrastructure component | Requirement supported | Status |
| --- | --- | --- |
| SSM-only EC2 control-plane host | Secure operator/agent execution without SSH keys or inbound ports | Current requirement |
| Public IPv4, zero ingress, HTTPS egress | Package installs, GitHub clones, container pulls, model/API calls without NAT Gateway cost | Current requirement |
| S3 Terraform state bucket with lockfile | Reproducible infrastructure source of truth and safe concurrent planning | Current requirement |
| GitHub OIDC plan/apply roles | No long-lived AWS keys and auditable CI access | Current requirement |
| Protected GitHub environments | Human approval boundaries for apply and sensitive operations | Current requirement |
| Optional budget import | Existing manual budget, future IaC ownership | Deferred current requirement |
| PostgreSQL runtime infrastructure | Product database dependency | Deferred future requirement |
| Secrets manager | Product runtime secrets and QBO token protection | Validated near-term requirement |
| Product runtime hosting | API/frontend production migration from Replit | Deferred future requirement |
| Centralized logs and Session Manager logging | Auditability and operational triage | Validated near-term requirement |
| Private subnet/NAT or endpoints | Reduced public addressing and controlled egress | Deferred future requirement |
