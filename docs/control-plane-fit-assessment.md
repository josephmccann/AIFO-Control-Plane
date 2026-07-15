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
| Infrastructure as code | Terraform scaffold, ADRs, runbooks, remote state, narrowed plan policy, and hardened control-plane resources exist | None for the approved current-scope control plane |
| Remote state | Bootstrap complete | None for planning |
| CI plan | Workflow exists, assumes the plan role through OIDC, and reports a clean main drift gate | None for planning |
| Product database | Not provisioned | Decide RDS or alternative only when product hosting scope is approved |
| Product object storage | Not provisioned | R2 currently documented; do not replace silently |
| Product secrets | Not provisioned | Need AWS Secrets Manager or approved equivalent design |
| Product runtime | Not provisioned | Future phase after deployment-readiness review |
| Observability | CloudTrail and Session Manager logging are deployed and verified for control-plane administration | Metrics and alerting remain future improvements |

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
2. No product secrets architecture.
3. No product database architecture.
4. No product object-storage migration decision.
5. GitHub required reviewers are unavailable on the current repository plan, so apply automation is blocked.
6. No apply workflow exists by design.

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

The current control-plane baseline is complete for the approved scope and must remain scoped. The next infrastructure work should be limited to either control-plane operational polish or a product-runtime architecture ADR; no product runtime deployment is approved.
