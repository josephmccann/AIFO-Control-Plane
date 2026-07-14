# Control-Plane Fit Assessment

## Product Fit

The current control plane supports the operator and infrastructure-management layer for AI.FO. It does not yet host the AI.FO product runtime.

This is appropriate for the current stage because the product still needs disciplined migration planning from the live demo environment into AWS. The control plane should first provide secure access, reproducible Terraform state, OIDC-based CI, bootstrap runbooks, and a documented approval boundary before it provisions customer-data runtime systems.

## Current Runtime Needs

AI.FO currently needs:

- Node.js 20+ execution.
- pnpm workspace builds.
- PostgreSQL.
- Express API server.
- React/Vite frontend build and serving.
- Session auth.
- QBO OAuth and API egress.
- Anthropic API egress.
- Verifier-provider egress.
- R2 object storage or deliberate replacement.
- Secure secrets.
- Validation commands that can run without leaking secrets.

## Current Deployment And Data Needs

| Need | Current control-plane support | Gap |
| --- | --- | --- |
| Infrastructure as code | Terraform scaffold, ADRs, runbooks, and narrowed plan policy exist | Needs approved bootstrap and future apply policy design |
| Remote state | Bootstrap code exists | Needs approved execution |
| CI plan | Workflow exists | Needs OIDC role and protected environment |
| Product database | Not provisioned | Decide RDS or alternative only when product hosting scope is approved |
| Product object storage | Not provisioned | R2 currently documented; do not replace silently |
| Product secrets | Not provisioned | Need AWS Secrets Manager or approved equivalent design |
| Product runtime | Not provisioned | Future phase after deployment-readiness review |
| Observability | Not provisioned | Need log, metric, alerting plan |

## Current Integration Needs

Outbound integration egress is mandatory for:

- Intuit QuickBooks.
- Anthropic.
- GMI Cloud or OpenAI-compatible verifier.
- Cloudflare R2.
- GitHub.
- npm/pnpm registries.
- Future operating-data systems.

The current EC2 public egress design supports this. It remains a control-plane host decision, not a product production network decision.

## Testing And Validation Needs

The control plane must preserve the ability to run:

- Terraform format and validation.
- Shell syntax checks.
- GitHub workflow validation.
- Product build and typecheck in future CI.
- Product smoke and AI validation commands in approved secret-backed environments.
- Demo and QBO validation without exposing private accounting data.

## Immediate Infrastructure Gaps

1. No product runtime architecture ADR.
2. No cost model beyond the EC2 recommendation.
3. No product secrets architecture.
4. No monitoring architecture or Session Manager log retention.
5. CloudTrail status has not been verified.
6. GitHub protected environments are not configured.
7. Remote-state and OIDC bootstrap have not been approved or executed.
8. No apply workflow exists by design.

## Infrastructure Not To Build Yet

Do not build these until product migration requirements and approval gates are met:

- EKS, ECS cluster, service mesh, or queueing platform.
- Multi-AZ managed production database.
- NAT Gateway.
- Product runtime production environment.
- Cross-company analytics or learning infrastructure.
- Paid observability stack.
- Broad data lake.

## Fit Conclusion

The current scaffold is a suitable first control-plane baseline, but it must remain scoped. The next work should validate this branch, open it for review, and resolve the bootstrap and cost approval gates before any AWS resource is created.
