# ADR-0001: Product-Gated Control-Plane Scope

## Status

Accepted

## Current Product Requirement Supported

AI.FO currently has a working product in `AI.FO-Demo` with PostgreSQL, QBO, R2, Anthropic, verifier, ingestion, deterministic financial-engine, and demo validation requirements. The control plane must support this product, but should not prematurely replace the current live-demo deployment.

## Founder Principle Or Constitutional Principle Implicated

Principles 3, 14, 15, 20, and 23: better context, transparent limitations, deterministic truth before generative interpretation, best-in-class work, and building for decisions rather than engagement.

## Known Facts

- The product repo is available locally at `/Users/joemccann/code/AI.FO-Demo`.
- The product currently references `https://demo.getaifo.com` and Replit-oriented deployment validation.
- The current control-plane Terraform provisions bootstrap and a single operator host, not a product runtime.
- Product runtime needs include PostgreSQL, R2 or a deliberate storage replacement, QBO OAuth, AI provider egress, secrets, and validation pipelines.

## Assumptions

- The control-plane host is an operator/agent host, not the production product runtime. Confidence: medium.
- AWS product hosting is a future migration decision. Confidence: medium.

## Unknowns

- Whether the first AWS product runtime should use EC2, ECS, App Runner, Elastic Beanstalk, or another service.
- Whether uploads should remain in Cloudflare R2 or migrate to AWS S3.
- Whether managed PostgreSQL is required before design-partner use.

## Information Sources Reviewed

- `AI.FO-Demo/README.md`
- `AI.FO-Demo/AGENTS.md`
- `AI.FO-Demo/docs/ARCHITECTURE.md`
- `AI.FO-Demo/docs/OPERATIONAL_MONITORING_RUNBOOK.md`
- `AI.FO-Demo/docs/UX_ACCEPTANCE_CRITERIA.md`
- `AI.FO-Demo/docs/DATA_VISUALIZATION_ACCEPTANCE_CRITERIA.md`
- `AI.FO-Demo/docs/QB_OAUTH_IMPLEMENTATION.md`
- `AI.FO-Demo/docs/SECRETS.md`

## Decision

The initial AWS control plane remains scoped to reproducible Terraform state, GitHub OIDC, SSM-only administrative access, and a single operator host. Product runtime hosting, database, secrets, and storage are deferred to explicit future ADRs.

## Why This Decision Is Appropriate Now

It gives the solo founder a secure, auditable infrastructure foundation without displacing active product learning or building runtime systems before migration requirements are validated.

## Alternatives Considered

- Build product runtime infrastructure immediately.
- Keep the control plane as documentation only.
- Move all product dependencies to AWS now.

## Why Alternatives Were Rejected Or Deferred

- Immediate runtime hosting would force database, secrets, storage, QBO callback, deployment, and customer-data decisions before the live product migration is scoped.
- Documentation-only work would not create reproducible bootstrap paths.
- Replacing R2 or current live-demo deployment silently would violate source-system and product-context constraints.

## Security Effects

Reduces premature customer-data blast radius in AWS. Keeps bootstrap and operator access reviewable before production data is introduced.

## Privacy Effects

No customer financial data is moved by this decision.

## Reliability Effects

Avoids creating a partially understood production runtime. Reliability work can focus first on state, access, and recovery.

## Cost Effects

Avoids recurring database, NAT, load balancer, and managed runtime cost until product migration is approved.

## Operational Burden

Adds documentation and review discipline, but avoids immediate runtime operations.

## Solo-Founder Recoverability

Small scope makes the system easier to reason about and recover. Future runtime decisions must include recovery paths.

## Product Impact

Supports product work by documenting actual runtime needs and blocking hypothetical infrastructure.

## Data-Lineage Impact

Preserves the boundary that deterministic product outputs own financial truth and AI layers explain them.

## Auditability Impact

Creates dated inventory and ADR evidence for why product runtime was not built in the first control-plane phase.

## Reversibility

Fully reversible through Git before AWS bootstrap. Future runtime work can build on these docs.

## Rollback Or Migration Path

If product migration becomes urgent, create product runtime ADRs and implement a separate Terraform environment after approval.

## Evidence That Would Cause Reconsideration

- A design partner requires AWS-hosted production runtime.
- Current demo hosting becomes unreliable or noncompliant.
- Product validation shows R2/Replit paths block customer use.
