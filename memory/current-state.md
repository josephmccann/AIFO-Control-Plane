# Current State

Date: 2026-07-15

Session state: ACTIVE - PRODUCT RUNTIME ARCHITECTURE DECISION

## Repository Checkpoint

- Control repository: `josephmccann/AIFO-Control-Plane`
- Inspected control `main`: `707e6298ed558fde06faea99b7e4b99b8b2b7adc`
- Working branch: `codex/product-runtime-architecture-decision-package`
- Product repository: `josephmccann/AI.FO-Demo`
- Inspected product `master`: `8df211e02f274d0a812771327c69b6d5b6c040d2`
- Product checkout remained on `master`, clean and unmodified.
- Control open PRs at reconstruction: none.
- Product open PRs: #195 documentation checkpoint, #186 product surfaces/connectors, #180 founder context. They are not part of the inspected product baseline.

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

Current product is a Replit-associated Node/Express single process plus React/Vite static frontend, PostgreSQL/Drizzle, PostgreSQL sessions, Cloudflare R2 uploads, QBO OAuth/ingestion, Anthropic narratives and GMI verifier. Product head has extensive deterministic and route-level tests but no general CI workflow or independently reproducible production deployment definition.

Critical current gaps:

- `ai.fo` redirects to a domain marketplace while product canonical tags claim it.
- Database/object backup and restore evidence is absent.
- GMI's published aggregator terms do not prove acceptable handling for sensitive verifier inputs and allow that underlying models may store/train on inputs.
- Tenant isolation is application-query based with broad global admin and no real-database cross-tenant suite/RLS.
- QBO token encryption uses one unversioned key with no rotation path.
- Customer deletion, upload quarantine/integrity/malware controls, controlled schema migration/rollback and durable app audit/alerting are incomplete.
- Product typecheck/build and 14,459 tests pass, but `pnpm lock:preflight` fails the telemetry provenance check and dependency audit is unverified because npm audit endpoints return HTTP 410 and Dependabot alerts are disabled.

## Architecture Package

Completed analysis/drafts:

- Comprehensive runtime inventory and data classification/flows.
- First-cohort production requirements.
- Three-option weighted analysis.
- Proposed AWS reference architecture.
- STRIDE product threat model.
- Objective migration readiness gates.
- Product runtime cost model.
- Proposed ADR-0011 through ADR-0022.
- Founder decision packet.

Recommended path: migrate to a small AWS-managed runtime before onboarding real customer financial data. Use the current runtime only for synthetic demo/rehearsal. Expected product-runtime beta cost is `$400-$550/month`, with an `$800/month` review ceiling, separate from the current control-plane cost.

## Decision And Deployment Boundary

Analysis is complete but architecture is not approved. No AWS product resources, product data, tokens, secrets, domains, certificates or callbacks changed. Future staging, migration rehearsal and production cutover remain blocked on founder decisions, product prerequisites, explicit resource/cost approval and objective evidence gates.
