# Roadmap

Session state: ACTIVE - PRODUCT RUNTIME IMPLEMENTATION PARAMETERS PENDING

This roadmap keeps the operationally complete control plane separate from the unapproved product runtime.

## Phase 0: Repository Operating Model

Status: Complete.

- Product context, principles, assumptions, ADRs, memory, workstreams and work queue established.
- PR #1 reconciled and closed as superseded.

## Phase 1: Bootstrap Readiness

Status: Complete and applied.

- S3 remote state/native lockfile, GitHub OIDC, separate plan/apply roles, environments and plan variables.
- Apply role remains state-access-only; no apply workflow.

## Phase 2: Hardened Control-Plane Baseline

Status: Complete for approved scope.

- CloudTrail, Session Manager logs, no-ingress EC2, Scheduler and drift gate operational.
- Instance `i-0254a9e2fcbcdebd7` stopped.
- Local plan and GitHub plan run `29380920338` clean.

Decision gate: no further AWS mutation without explicit human approval.

## Phase 3: Control-Plane Operational Refinement

Status: Ongoing, lower priority than product decision.

- Pinned actionlint/ShellCheck and approval-gated manual patching complete.
- Future: periodic stale-status checks, lightweight monthly cost evidence and Terraform state recovery drill.

## Phase 4: Product Runtime Architecture Decision

Status: Analysis complete; AWS-before-customer-data strategic direction approved; implementation decisions pending.

- Current-runtime inventory, data flows/classification and risk analysis complete.
- Beta-cohort requirements and weighted current/hybrid/AWS options complete.
- Reference architecture, threat model, readiness gates and cost model complete.
- ADR-0011 accepted in principle; ADR-0012 through ADR-0022 and resource-level parameters Proposed.
- Product baseline refreshed to merged PR #186 (`3329c99`) with connector/account/calibration implications incorporated.
- Recommended path: AWS-managed runtime before real-customer data; current runtime remains synthetic demo/rehearsal only.

Decision gates: domain/provider custody, architecture, retention, account, budget, recovery objectives and deployment approval boundary.

## Phase 5: Product Prerequisite Hardening

Status: Implementation not started; ordered documentation plan complete; recommended next workstream is item 1 only.

- One controlled database migration ledger; remove startup DDL.
- QBO versioned token-encryption keyring and rotation.
- Real-PostgreSQL tenant-isolation/RLS decision and tests.
- Session/logout/CSRF/rate/auth hardening.
- Upload quarantine, checksum, type/limit and malware controls.
- Structured redaction/audit events, readiness, deletion and verifier fail-closed/provider abstraction.
- Pinned container build and product CI design.

Decision gate: product-code changes require a separately scoped implementation mission and review.

## Phase 6: Staging Design And Validation

Status: Blocked; no resources approved.

- Review product Terraform, production account bootstrap design and cost.
- After explicit approval, create isolated staging with synthetic data only.
- Validate build/deploy, restore, QBO sandbox, storage, sessions, tenant isolation, security, load/failure, monitoring and rollback.

Decision gates: architecture/cost/account/IAM approval and exact Terraform plan/resource-creation approval.

## Phase 7: Migration Rehearsal

Status: Blocked.

- Source backup/restore evidence.
- Synthetic/sanitized DB and object manifest/checksum rehearsal.
- Timed deployment, callback, smoke, rollback and founder recovery exercise.

Decision gate: explicit rehearsal/data handling approval; no customer data by default.

## Phase 8: Production And Cutover

Status: Blocked.

- Empty production infrastructure only after staging gates and explicit approval.
- Production cutover only after all MR-01 through MR-33 gates pass.
- Controlled backup, freeze, final copy/reconcile, deploy/migrate, DNS/QBO callback, validation and rollback window.

Decision gates: production cost/resources, customer data, secrets, DNS/TLS, QBO callbacks and command-level cutover approval.

## Deferred

- Kubernetes, microservices, Aurora, Redis, active-active multi-Region, per-tenant accounts/databases and large observability stacks until evidence requires them.
- Private-network migration of the control-plane host remains separate and cost-gated.
