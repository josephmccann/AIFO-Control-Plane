# Open Decisions

Session state: ACTIVE - PRODUCT RUNTIME IMPLEMENTATION PARAMETERS PENDING

| ID | Decision | Recommendation | Owner | Needed by | Blocking |
| --- | --- | --- | --- | --- | --- |
| OD-006 | Product database implementation parameters | Managed RDS PostgreSQL direction; determine class, availability, RPO/RTO and PITR from evidence | Founder + Product + Infrastructure | Before staging design | Yes |
| OD-007 | R2 retention versus S3 | S3 production; R2 migration source only | Founder + Product + Infrastructure | Before upload hardening/staging | Yes |
| OD-008 | Product secrets/rotation | Secrets Manager, task roles, versioned QBO/session keyrings | Founder + Security + Product | Before staging secrets | Yes |
| OD-012 | Enforceable production deployment approval boundary | Select founder-enforced boundary; keep current apply environment unused | Founder + Infrastructure | Before staging pipeline design | Yes |
| OD-017 | Production account boundary | Dedicated organization member account; current account for control/nonprod | Founder + Infrastructure | Before production Terraform design | Yes |
| OD-018 | Compute/frontend implementation topology | CloudFront/private S3 plus ECS Fargate/ALB direction; exact task/network/NAT shape pending | Founder + Product + Infrastructure | Before staging design | Yes |
| OD-019 | Product domain and registrar/DNS recovery | Use a founder-controlled same-origin hostname; exact hostname pending custody evidence | Founder | Before Intuit production callback submission | Yes |
| OD-020 | AI-provider data handling | Anthropic commercial DPA/ZDR; disable or replace GMI until approved | Founder + Security/Privacy | Before customer-data provider testing | Yes |
| OD-021 | Session model | Retain PostgreSQL sessions; do not add Redis | Founder + Product | Before prerequisite implementation | No for design; yes for production |
| OD-022 | Availability and recovery objectives | Approve exact availability, RPO/RTO, PITR and restore cadence after workload/customer evidence | Founder + Infrastructure | Before sizing/backup design | Yes |
| OD-023 | Customer retention and deletion | Approve proposed matrix with counsel and implement evidence workflow | Founder + counsel + Product | Before customer contract/privacy language | Yes |
| OD-024 | Product-runtime recurring budget | Approve monthly target and review ceiling after updated sizing/current invoices | Founder | Before any resource creation | Yes |
| OD-025 | Multi-tenant Stripe authorization | Per-tenant OAuth or restricted-key record; singleton company binding limited to one-company synthetic/pilot use | Founder + Product + Security | Before second Stripe company or connector staging | Yes |
| OD-026 | Commercial account metadata source of truth | Persist/derive commercial terms per company or hide/label global pilot values | Founder + Product | Before shared multi-company staging | Yes |
| OD-027 | Connector observation correction history | Preserve immutable sync/correction lineage alongside idempotent current values | Product + Data + Security | Before connector customer-data testing | Yes |

## Recently Resolved

| ID | Decision | Resolution |
| --- | --- | --- |
| OD-001 | Remote-state bootstrap | Approved/applied 2026-07-14 |
| OD-002 | GitHub OIDC bootstrap | Approved/applied 2026-07-14 |
| OD-003 | GitHub Terraform environments | Created; apply environment remains unused |
| OD-004 | Control host schedule | 08:00-16:00 weekdays, America/Los_Angeles |
| OD-009 | PR #1 disposition | Closed as superseded; PR #2 merged |
| OD-010 | Terraform plan repository variables | Completed |
| OD-011 | Hardened control-plane apply | Approved/completed |
| OD-013 | Residual control-plane apply | Completed after validation |
| OD-014 | Plan-role policy updates | Applied through `v4` |
| OD-015 | Host patching | Manual approval-gated monthly approach accepted in ADR-0010 |
| OD-016 | Local actionlint/shellcheck | Resolved with pinned checksum-verified installer |
| OD-005 | Whether and when product runtime moves to AWS | Accepted in principle: gated AWS migration before real-customer data; no deployment approval |
