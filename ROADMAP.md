# Roadmap

Session state: PARKED — SAFE FOR CODEX CLI UPDATE

This roadmap is intentionally conservative. The control plane must support the actual AI.FO product while avoiding infrastructure for hypothetical future systems.

## Phase 0: Repository Operating Model

Status: Complete.

- Product runtime inventory.
- Principle traceability matrix.
- Assumption register.
- Control-plane fit assessment.
- ADR framework.
- Runbooks, memory, workstreams, and workqueue.
- PR #1 handoff reconciliation completed; PR #1 closed as superseded.

## Phase 1: Bootstrap Readiness

Status: Complete and applied.

- Remote-state bootstrap root for S3 state and native lockfiles applied.
- GitHub OIDC bootstrap root applied.
- Separate Terraform plan and apply roles created.
- GitHub environments created.
- Repository variables configured for Terraform plan.
- GitHub Actions plan succeeds through OIDC.
- Apply role remains state-access-only.
- Exact human execution steps documented.

## Phase 2: Hardened Control-Plane Baseline

Status: Complete for approved current scope.

- CloudTrail management-events baseline deployed.
- Session Manager logging deployed.
- VPC/network baseline deployed.
- No-ingress EC2 host deployed.
- EC2 instance `i-0254a9e2fcbcdebd7` is stopped.
- 100 GiB encrypted gp3 root volume deployed.
- EventBridge Scheduler start and stop schedules deployed.
- Scheduler inline policy and DLQ deployed.
- Local Terraform plan is clean.
- GitHub Terraform Plan is clean on `main`: https://github.com/josephmccann/AIFO-Control-Plane/actions/runs/29378532712.
- GitHub plan-role read policy default version is `v4`.

Decision gate: no further AWS mutation without explicit human approval.

## Phase 3: Operational Refinement

Status: Next.

- Install or add CI support for `actionlint` and `shellcheck`.
- Add periodic documentation checks for stale deployment status.
- Add patch-management runbook for the stopped control-plane host.
- Add cost-review cadence and lightweight monthly cost evidence.
- Run a Terraform state recovery drill from S3 versioning.

## Phase 4: Product Runtime Design

Status: Deferred until product deployment scope is approved.

- PostgreSQL hosting decision.
- Product secrets architecture.
- Product object storage decision: retain Cloudflare R2 or deliberately migrate.
- Runtime hosting decision for API/frontend.
- Domain, TLS, and QBO OAuth callback migration.
- Product validation pipeline using existing AI.FO-Demo commands.

Decision gates: spending, secrets, customer data, deployment, and production approval.

## Phase 5: Private Network Migration

Status: Deferred.

- Private subnets.
- NAT Gateway, NAT instance, or endpoint-based egress decision.
- Interface endpoints where cost-justified.
- Removal of public IPv4 from the control-plane host.

Decision gate: cost and security review.
