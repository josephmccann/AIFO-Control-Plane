# AI.FO Control Plane Handoff

Date: 2026-07-15

Session state: ACTIVE - PRODUCT RUNTIME IMPLEMENTATION PARAMETERS PENDING

## Repository State

- Control main inspected: `707e6298ed558fde06faea99b7e4b99b8b2b7adc`.
- Product master inspected: `3329c99beb0713269b54bc5fd6a7fb39bf44f398`.
- Architecture work branch: `codex/product-runtime-architecture-decision-package`.
- Product checkout was clean and unmodified.
- Control open PRs at reconstruction: none.
- Product PR #186 is merged and included in the inspected baseline; open PRs were re-reviewed during refresh.
- Current Replit demo is healthy at `3329c99`; rollback reference `30a8ed2`; connectors disabled; Stripe unconfigured; no connector/observation rows.

## Verified Control Plane

- AWS account `350480401760`, Organizations management account, region `us-west-2`.
- Human access through IAM Identity Center `AIFO-Platform-Admin`; automation through GitHub OIDC only.
- S3 state bucket `aifo-terraform-state-350480401760-us-west-2`, key `control-plane/terraform.tfstate`, native lockfile.
- Plan/apply roles remain separate; apply role is state-access-only; no apply workflow; `terraform-apply` unused.
- Local Terraform plan: `0 to add, 0 to change, 0 to destroy`.
- Latest clean GitHub plan: https://github.com/josephmccann/AIFO-Control-Plane/actions/runs/29380920338.
- CloudTrail logging/delivery healthy.
- Session Manager encrypted CloudWatch logging active, 30-day retention.
- Scheduler enabled at 08:00/16:00 weekdays, `America/Los_Angeles`, targeting only `i-0254a9e2fcbcdebd7`.
- Instance `i-0254a9e2fcbcdebd7` stopped with no public IP while stopped.
- AWS product runtime not deployed; current Replit demo remains live at `3329c99`.

## Product Architecture Decision

The repository now contains completed analysis, an accepted strategic direction and Proposed implementation decisions:

- [Current runtime inventory](../product-runtime-inventory.md)
- [Beta requirements](../product-runtime-requirements-beta-cohort.md)
- [Options analysis](../product-runtime-options-analysis.md)
- [Reference architecture](../product-runtime-reference-architecture.md)
- [Threat model](../security/product-runtime-threat-model.md)
- [Migration gates](../product-runtime-migration-readiness.md)
- [Cost model](../product-runtime-cost-model.md)
- ADR-0011 accepted in principle; ADR-0012 through ADR-0022 Proposed
- [Founder decision packet](../decision-packets/PRODUCT_RUNTIME_ARCHITECTURE_FOUNDER_DECISION.md)

Approved direction: complete a gated AWS-managed migration before accepting first-cohort real customer data. Use the current Replit-associated runtime only for synthetic demonstration and rehearsal. Service topology and exact RDS size, NAT topology, hostname, recovery/retention targets and budget remain Proposed. Merged PR #186 fits the core reference architecture but adds per-tenant Stripe authorization, account-metadata truth and observation-lineage decisions.

## Hard Blockers

- Founder implementation, account, recovery, retention, domain, provider, connector-tenancy and budget decisions are pending; strategic migration timing is resolved.
- `ai.fo` currently redirects to a domain marketplace while product canonicals claim it.
- Current GMI verifier terms are not approved for highly sensitive financial facts.
- Product prerequisites, staging, restore, tenant isolation, QBO rotation, upload integrity, deletion, monitoring, rollback, founder recovery and rehearsal gates have not passed.
- Replit proposed destructive schema drops during an environment-divergence publish; it was canceled before promotion. Generated SQL review and destructive-diff rejection are mandatory.
- Startup health returned transient HTTP 500 responses before stabilizing; separate readiness and stabilization evidence is required.
- Expected product-runtime beta cost `$400-$550/month` and `$800` review ceiling are not approved.

## Next Narrow Workstream

The deployment hold is resolved. After separate product-code authorization, execute prerequisite 1 only in a dedicated `AI.FO-Demo` worktree: one migration ledger, independent environment baselines, generated-SQL review, destructive-diff rejection and removal of startup DDL. Readiness stabilization is prerequisite 2. Do not create runtime infrastructure.

## Guardrails

Do not apply/destroy Terraform; create/modify/delete AWS resources; start/modify the host; change Scheduler/IAM/GitHub protection; create an apply workflow; deploy product runtime; move data/tokens/secrets; change DNS/TLS/QBO callbacks; modify production product code; or merge the architecture PR without the action-specific founder approval.
