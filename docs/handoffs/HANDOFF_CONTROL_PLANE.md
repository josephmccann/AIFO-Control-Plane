# AI.FO Control Plane Handoff

Date: 2026-07-15

Session state: ACTIVE - FOUNDER PRODUCT RUNTIME DECISION PENDING

## Repository State

- Control main inspected: `707e6298ed558fde06faea99b7e4b99b8b2b7adc`.
- Product master inspected: `8df211e02f274d0a812771327c69b6d5b6c040d2`.
- Architecture work branch: `codex/product-runtime-architecture-decision-package`.
- Product checkout was clean and unmodified.
- Control open PRs at reconstruction: none.
- Product open PRs: #195, #186 and #180; none is in the inspected baseline.

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
- Product runtime not deployed.

## Product Architecture Decision

The repository now contains completed analysis and Proposed decisions:

- [Current runtime inventory](../product-runtime-inventory.md)
- [Beta requirements](../product-runtime-requirements-beta-cohort.md)
- [Options analysis](../product-runtime-options-analysis.md)
- [Reference architecture](../product-runtime-reference-architecture.md)
- [Threat model](../security/product-runtime-threat-model.md)
- [Migration gates](../product-runtime-migration-readiness.md)
- [Cost model](../product-runtime-cost-model.md)
- Proposed ADR-0011 through ADR-0022
- [Founder decision packet](../decision-packets/PRODUCT_RUNTIME_ARCHITECTURE_FOUNDER_DECISION.md)

Recommendation: complete a gated AWS-managed migration before accepting first-cohort real customer data. Use the current Replit-associated runtime only for synthetic demonstration and rehearsal. Proposed target is CloudFront/private S3, two ECS Fargate API tasks, RDS PostgreSQL Multi-AZ, private S3 uploads, Secrets Manager/task roles, structured CloudWatch audit/operations and a dedicated production AWS member account.

## Hard Blockers

- Founder architecture, account, recovery, retention, domain, provider and budget decisions are pending.
- `ai.fo` currently redirects to a domain marketplace while product canonicals claim it.
- Current GMI verifier terms are not approved for highly sensitive financial facts.
- Product prerequisites, staging, restore, tenant isolation, QBO rotation, upload integrity, deletion, monitoring, rollback, founder recovery and rehearsal gates have not passed.
- Expected product-runtime beta cost `$400-$550/month` and `$800` review ceiling are not approved.

## Next Narrow Workstream

Design product-runtime prerequisite hardening in `AI.FO-Demo`: one migration ledger/removal of startup DDL, QBO keyring rotation, database tenant-isolation tests, session/CSRF hardening, upload quarantine/integrity, structured redaction, readiness, deletion and verifier fail-closed/provider abstraction. Do not create runtime infrastructure.

## Guardrails

Do not apply/destroy Terraform; create/modify/delete AWS resources; start/modify the host; change Scheduler/IAM/GitHub protection; create an apply workflow; deploy product runtime; move data/tokens/secrets; change DNS/TLS/QBO callbacks; modify production product code; or merge the architecture PR without the action-specific founder approval.
