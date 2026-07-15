# AI.FO Product Handoff

## Purpose

Canonical starting context for product runtime, application architecture, financial truth boundaries, integrations, and deployment dependencies relevant to infrastructure.

## Current Product Reality

AI.FO is a working financial intelligence platform. It:

- ingests QuickBooks Online reports and accounting CSV exports;
- supports financial statements, AR, AP, sales, bank, transaction-detail, budget, subscription, and invoice-detail ingestion paths;
- computes financial metrics, ratios, scenarios, constraints, trends, and registered business signals through deterministic code;
- sends a server-built computed snapshot to the AI narrative layer;
- prevents AI from recalculating or changing deterministic financial truth;
- uses AI to synthesize CFO-grade narratives and verification;
- includes intelligence briefs, cash and runway analysis, expense intelligence, scenario modeling, ratio analysis, decision framing, memo generation, upload workflows, auth, admin, and board reporting.

## Current Stack

- React 19
- TypeScript
- Vite
- Tailwind
- Radix UI
- Recharts
- Express 5
- Node.js
- Passport
- PostgreSQL
- Drizzle ORM
- Vitest
- Playwright
- Cloudflare R2

## Runtime Dependencies

- PostgreSQL through `DATABASE_URL`.
- Cloudflare R2 for production upload storage.
- QuickBooks Online OAuth and sandbox sync.
- Anthropic for narrative generation.
- GMI Cloud or OpenAI-compatible verifier.
- Session secret and auth storage.
- CORS and API base URL configuration.

## Operational Validation

Important product commands include:

```bash
pnpm build
pnpm run typecheck
pnpm deploy:parity -- --target=local --base-url=http://localhost:8080
pnpm validate:ai
pnpm demo:smoke
pnpm --filter api-server demo:smoke -- --sync-qbo
pnpm qbo:seed-demo -- --dry-run
pnpm lock:preflight
git diff --check
```

## Current Open Product PRs Reviewed

- PR #180, draft: founder/company context and constitutional documents.
- PR #186, merged at `3329c99beb0713269b54bc5fd6a7fb39bf44f398`: top value-add surfaces, session-derived account panel, connector store, Stripe adapter, normalized observations and external-connectors migration.

PR #186 is current canonical baseline. Infrastructure implications are tracked in the runtime inventory, threat model, migration gates and prerequisite hardening plan.

Deployment checkpoint: the current Replit demo is healthy at `3329c99`; migration `0011` applied transactionally; public/authenticated smoke passed; connectors are disabled; Stripe is unconfigured; QBO sync was not run; connector/observation tables are empty; rollback `30a8ed2` was retained but not exercised. A destructive automatic schema proposal was canceled before promotion, and transient startup HTTP 500 responses preceded stable health. Future publishes require reviewed generated SQL and readiness stabilization.

## Infrastructure Implications

- Do not build product runtime infrastructure until the AWS migration scope is approved.
- Do not replace R2 with S3 without a storage ADR.
- Do not introduce databases, queues, or clusters for future connectors before merged product requirements exist.
- Preserve deterministic financial-engine authority over financial truth.
- Preserve observed/reported/derived/inferred/unknown distinctions in future telemetry and lineage design.
- Future runtime infrastructure must support product validation commands without leaking secrets.
