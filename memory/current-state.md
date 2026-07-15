# Current State

Date: 2026-07-15

Session state: ACTIVE - PRODUCT RUNTIME IMPLEMENTATION PARAMETERS PENDING

## Repository Checkpoint

- Control repository: `josephmccann/AIFO-Control-Plane`
- Inspected control `main`: `707e6298ed558fde06faea99b7e4b99b8b2b7adc`
- Working branch: `codex/product-runtime-architecture-decision-package`
- Product repository: `josephmccann/AI.FO-Demo`
- Inspected product `master`: `3329c99beb0713269b54bc5fd6a7fb39bf44f398`
- Product checkout remained on `master`, clean and unmodified.
- Control open PRs at reconstruction: none.
- Product PR #186 merged as `3329c99beb0713269b54bc5fd6a7fb39bf44f398` and is included in the baseline. Current open-PR state was re-reviewed during the refresh.

## Verified AWS Control Plane

- AWS account `350480401760`, region `us-west-2`, Organizations management account.
- Identity verified through IAM Identity Center profile `aifo-admin` and permission set `AIFO-Platform-Admin`.
- Remote state bucket `aifo-terraform-state-350480401760-us-west-2`, key `control-plane/terraform.tfstate`, native S3 lockfile.
- Read-only backend init and local plan succeeded with `0 to add, 0 to change, 0 to destroy`.
- Latest successful GitHub Terraform Plan: https://github.com/josephmccann/AIFO-Control-Plane/actions/runs/29380920338.
- Latest successful Terraform Validate: run `29380960040`.
- CloudTrail `aifo-control-plane-management-events` is logging and last delivery succeeded without error.
- Session Manager preference `SSM-SessionManagerRunShell` streams encrypted logs to `/aifo/control-plane/session-manager`, 30-day retention.
- Scheduler start/stop rules are enabled at 08:00/16:00 Monday-Friday, `America/Los_Angeles`, targeting only `i-0254a9e2fcbcdebd7`.
- EC2 instance `i-0254a9e2fcbcdebd7` is stopped and has no public IP while stopped.
- No apply workflow exists. Apply role remains state-access-only. `terraform-apply` remains unused.
- Product runtime infrastructure is not deployed.

Control repository validation and a fresh remote-backend Terraform plan passed after the architecture documentation changes; the plan remained `0 to add, 0 to change, 0 to destroy`.

## Product Runtime Finding

Current product is a Replit-associated Node/Express single process plus React/Vite static frontend, PostgreSQL/Drizzle, PostgreSQL sessions, Cloudflare R2 uploads, QBO OAuth/ingestion, Anthropic narratives and GMI verifier. Merged PR #186 adds session-derived account state, feature-flagged operating connectors, a Stripe read adapter, normalized observations, transactional/idempotent connector persistence and editable calibration suggestions. Product head has extensive deterministic and route-level tests but no general CI workflow or independently reproducible production deployment definition.

Critical current gaps:

- `ai.fo` redirects to a domain marketplace while product canonical tags claim it.
- Database/object backup and restore evidence is absent.
- GMI's published aggregator terms do not prove acceptable handling for sensitive verifier inputs and allow that underlying models may store/train on inputs.
- Tenant isolation is application-query based with broad global admin and no real-database cross-tenant suite/RLS.
- QBO token encryption uses one unversioned key with no rotation path.
- Customer deletion, upload quarantine/integrity/malware controls, controlled schema migration/rollback and durable app audit/alerting are incomplete.
- Product frozen install, typecheck/build and 14,516 tests pass (5 skipped) at `3329c99`; `pnpm lock:preflight` still fails only the telemetry provenance check. AI/deploy-parity checks correctly block without clean-checkout secrets/DB, and no GitHub product workflow has run on the merged head.
- The Stripe adapter uses one deployment-wide restricted key bound to one company; account plan/billing/support values are deployment-wide environment configuration. Neither is a multi-tenant production source of truth.
- New connector tables are application-tenant-scoped and idempotent but lack database FK/RLS/check enforcement and append-only correction history.

## Architecture Package

Completed analysis/drafts and approved strategic direction:

- Comprehensive runtime inventory and data classification/flows.
- First-cohort production requirements.
- Three-option weighted analysis.
- Proposed AWS reference architecture.
- STRIDE product threat model.
- Objective migration readiness gates.
- Product runtime cost model.
- ADR-0011 accepted in principle for AWS-before-customer-data timing; ADR-0012 through ADR-0022 remain Proposed.
- Founder decision packet.
- Product prerequisite hardening plan updated against merged PR #186.

Recommended path: migrate to a small AWS-managed runtime before onboarding real customer financial data. Use the current runtime only for synthetic demo/rehearsal. Expected product-runtime beta cost is `$400-$550/month`, with an `$800/month` review ceiling, separate from the current control-plane cost.

## Decision And Deployment Boundary

The strategic AWS migration direction is approved. Exact RDS size, NAT topology, hostname, RPO/RTO, PITR retention, monthly budget and other implementation parameters remain Proposed. No AWS product resources, product data, tokens, secrets, domains, certificates or callbacks changed. Future staging, migration rehearsal and production cutover remain blocked on founder decisions, product prerequisites, explicit resource/cost approval and objective evidence gates.
