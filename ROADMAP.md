# Roadmap

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
- First GitHub Actions plan succeeded through OIDC.
- Exact human execution steps prepared.
- EC2 instance recommendation documented against current AWS pricing.
- Cost model documented against the $250 monthly budget.

Completed resources:

- State bucket: `aifo-terraform-state-350480401760-us-west-2`
- OIDC provider: `arn:aws:iam::350480401760:oidc-provider/token.actions.githubusercontent.com`
- Plan role: `arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Plan`
- Apply role: `arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Apply`
- State access policy: `arn:aws:iam::350480401760:policy/AIFO-GitHubActions-Terraform-StateAccess`
- Plan read policy: `arn:aws:iam::350480401760:policy/AIFO-GitHubActions-Terraform-PlanReadAccess`

## Phase 2: Cost-Aligned Control-Plane Host

Status: Blocked pending reviewed cost-aligned plan, operating schedule decision, and explicit apply approval.

- Keep `terraform-apply` unused because required reviewers are unavailable on the current GitHub plan.
- Keep apply workflow absent.
- Review plan for no inbound access, IMDSv2, SSM-only administration, and expected costs.
- Review 100 GiB root volume fit.
- Review start/stop runbook.
- Select 8-hours-per-weekday or 12-hours-per-day operating schedule.

Decision gate: human approval before any local IAM Identity Center apply.

## Phase 3: Hardening

Status: Planned.

- Session Manager logging.
- CloudWatch log retention.
- Patch management.
- Cost alerts and recurring cost model.
- EventBridge Scheduler start/stop automation after first host deployment.
- Backup and restore drills for Terraform state.
- Least-privilege policy refinement based on observed plan requirements.
- Static analysis additions such as `actionlint`, `shellcheck`, and Terraform security linting.

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
