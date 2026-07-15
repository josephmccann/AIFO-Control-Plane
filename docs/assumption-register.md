# Assumption Register

| ID | Assumption | Confidence | Supporting Evidence | Validation Method | Owner | Review Date |
| --- | --- | --- | --- | --- | --- | --- |
| A-001 | The initial EC2 host is an operator/control-plane host, not the production product runtime | Medium | Current Terraform defines one EC2 host and no product DB/runtime | Deployment-readiness review | Infrastructure | 2026-07-21 |
| A-002 | Public IPv4 plus zero inbound rules is acceptable for initial control-plane egress | Medium | Product needs broad outbound HTTPS; budget target is $250 | Security ADR and plan review before apply | Infrastructure | Before first apply |
| A-003 | `m7i-flex.2xlarge` is the best default x86 candidate, but not budget-approved for continuous operation | High | AWS Price List shows lower hourly cost than `m7i.2xlarge` and `m7a.2xlarge` in us-west-2; 730-hour compute estimate exceeds $250 | EC2 recommendation ADR and cost decision | Infrastructure | Before first apply |
| A-004 | Product runtime will need PostgreSQL before AWS production migration | High | Product README and DB package | Product hosting architecture ADR | Product + Infrastructure | Before product hosting design |
| A-005 | Cloudflare R2 remains the production upload-storage target until explicitly changed | Medium | Product README and secrets docs | Storage architecture decision | Product + Infrastructure | Before product hosting design |
| A-006 | The manual AWS Budget should not be managed by Terraform yet | High | User stated budget exists manually | Import review if requested | Infrastructure | Before budget changes |
| A-007 | GitHub environments `terraform-plan` and `terraform-apply` are acceptable names | Medium | Current workflow/docs use them | Human review during bootstrap | Infrastructure | Before OIDC bootstrap |
| A-008 | PR #1 handoff docs were broadly factual but incomplete | High | PR #1 was closed as superseded; PR #2 merged reconciled handoffs | None; retain as historical record | Infrastructure | Resolved |
| A-009 | Merged PR #186 connector/account implementation is current product baseline | High | Product `master` `3329c99`; merged PR #186 | Re-check exact head before implementation | Product + Infrastructure | Resolved 2026-07-15 |
| A-014 | One `STRIPE_SECRET_KEY`/company binding is limited to a one-company synthetic or pilot use | High | Connector route enforces `AIFO_STRIPE_COMPANY_ID`; no per-tenant credential table | Approve and test multi-tenant authorization model | Product + Security | Before connector staging |
| A-015 | `AIFO_ACCOUNT_*` values are deployment-wide and are not authoritative per-company commercial records | High | Merged account route reads environment configuration | Select per-company source of truth or explicitly hide/label fields | Product | Before shared staging |
| A-010 | Replit remains the current live demo deployment target | Medium | Product demo runbook references Replit | Confirm with founder before AWS product runtime work | Product + Infrastructure | Before product hosting design |
| A-011 | Control-plane should avoid NAT Gateway until a product/private-subnet need is approved | High | Cost target and current egress requirements | Cost ADR | Infrastructure | Before network changes |
| A-012 | Product validation commands must remain supported during migration | High | Product README and runbooks | Deployment parity pipeline | Product + Infrastructure | Before product runtime deployment |
| A-013 | EC2 detailed monitoring is not required for the first host | Medium | No current product runtime on host; cost discipline favors basic monitoring until observability ADR | Monitoring design review | Infrastructure | Before first apply |
