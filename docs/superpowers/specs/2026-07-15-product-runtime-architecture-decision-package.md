# Product Runtime Architecture Decision Package Specification

Date: 2026-07-15

## Objective

Produce a repository-grounded founder decision package for safely moving the AI.FO product runtime from its current Replit-associated deployment to a first-cohort production architecture. This mission produces analysis, proposed decisions, evidence gates, and durable repository memory only. It does not deploy or mutate infrastructure, migrate data, change product code, or approve a production topology.

## Authoritative Inputs

- Control-plane repository head inspected: `707e6298ed558fde06faea99b7e4b99b8b2b7adc`.
- Product repository head inspected initially: `8df211e02f274d0a812771327c69b6d5b6c040d2`; refreshed after PR #186 merge to `3329c99beb0713269b54bc5fd6a7fb39bf44f398`.
- Live AWS control-plane evidence collected read-only with profile `aifo-admin`.
- Open and recently merged pull requests, recent commits, workflows, tests, application code, schema, migrations, integrations, and deployment configuration from both repositories.
- Current official AWS, Cloudflare, Replit, Intuit, Anthropic, and GMI documentation where provider behavior or pricing is material.

## Scope

The package will:

1. Replace the partial runtime inventory with an implementation-level topology, data-flow, data-classification, and risk inventory.
2. Define a realistic security, reliability, recovery, operating, support, and cost baseline for approximately 10 customer companies.
3. compare a hardened current platform, a hybrid path, and an AWS-managed runtime using an explicit weighted matrix.
4. Define one recommended reference architecture without Terraform or deployed resources.
5. Threat-model the current and proposed runtime.
6. Define objective migration approval gates and required evidence.
7. Model current, hybrid, and AWS costs without false precision.
8. Draft proposed ADRs for every material decision.
9. Create a founder-facing decision packet that makes the recommendation and required approvals explicit.
10. Reconcile canonical memory, work queue, roadmap, changelog, architecture, security, readiness, ADR index, and handoff documents.

## Decision Posture

The analysis will optimize first for customer trust, recoverability, auditability, correctness, and solo-founder operability. It will avoid Kubernetes, premature microservices, and an elaborate account hierarchy. Managed services are justified where they materially reduce security or recovery risk.

The working recommendation to validate is a gated migration to an AWS-managed runtime before accepting the first cohort's real financial data. The current Replit-associated deployment remains useful as a synthetic demo and migration-rehearsal source, but repository evidence currently lacks sufficient backup, restore, deletion, deployment, provider-governance, and domain-control evidence for real-customer launch.

## Safety Boundary

- No `terraform apply` or `terraform destroy`.
- No AWS, Scheduler, IAM, host, DNS, certificate, GitHub environment, or product-runtime mutation.
- No product code edits.
- No data, database, object, token, callback, credential, or secret migration.
- No apply workflow.
- No merge.
- Read-only provider and repository checks are allowed.

## Deliverables

- `docs/product-runtime-inventory.md`
- `docs/product-runtime-requirements-beta-cohort.md`
- `docs/product-runtime-options-analysis.md`
- `docs/product-runtime-reference-architecture.md`
- `docs/security/product-runtime-threat-model.md`
- `docs/product-runtime-migration-readiness.md`
- `docs/product-runtime-cost-model.md`
- Proposed ADRs under `docs/adr/`
- `docs/decision-packets/PRODUCT_RUNTIME_ARCHITECTURE_FOUNDER_DECISION.md`
- Reconciled repository-memory and operating documents
- A validated, reviewable draft pull request

## Acceptance Criteria

- Every current-state claim is traceable to repository or live read-only evidence.
- Confirmed risks and unresolved questions are separated.
- The options matrix has explicit weights and one recommendation.
- Every migration gate names evidence, owner, approver, status, and blocking effect.
- Every material architectural choice is a Proposed ADR unless already founder-approved.
- Validation covers the control repository, a read-only Terraform plan, and the product repository's documented build and test entrypoints.
- The pull request states that no infrastructure or customer data changed.
