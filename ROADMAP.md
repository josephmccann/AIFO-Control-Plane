# Roadmap

This roadmap is intentionally conservative. The control plane must support the actual AI.FO product while avoiding infrastructure for hypothetical future systems.

## Phase 0: Repository Operating Model

Status: In progress on `docs/product-context-operating-model`.

- Product runtime inventory.
- Principle traceability matrix.
- Assumption register.
- Control-plane fit assessment.
- ADR framework.
- Runbooks, memory, workstreams, and workqueue.
- PR #1 handoff reconciliation.

## Phase 1: Bootstrap Readiness

Status: Not deployed.

- Remote-state bootstrap root for S3 state and native lockfiles.
- GitHub OIDC bootstrap root.
- Separate Terraform plan and apply roles.
- Protected GitHub environments documented.
- Exact human execution steps prepared.
- EC2 instance recommendation documented against current AWS pricing.

Decision gate: human approval before AWS resource creation or `terraform apply`.

## Phase 2: First Plan And Control-Plane Host

Status: Deferred.

- Execute remote-state bootstrap.
- Execute GitHub OIDC bootstrap.
- Configure repository variables.
- Run GitHub Actions Terraform plan.
- Review plan for no inbound access, IMDSv2, SSM-only administration, and expected costs.
- Add protected apply workflow only after approval boundary is accepted.

Decision gate: human approval before apply.

## Phase 3: Hardening

Status: Planned.

- Session Manager logging.
- CloudWatch log retention.
- Patch management.
- Cost alerts and recurring cost model.
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
