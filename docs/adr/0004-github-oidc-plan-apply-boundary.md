# ADR-0004: GitHub OIDC Plan And Apply Boundary

## Status

Accepted

## Current Product Requirement Supported

AI.FO needs auditable CI/CD without long-lived AWS keys, with human approval before AWS mutation.

## Founder Principle Or Constitutional Principle Implicated

Principles 1, 6, 8, 14, 20, and 22: trust, preserved decision state, human authority, transparent limits, best-in-class discipline, and no silent policy adaptation.

## Known Facts

- GitHub Actions OIDC enables cloud access without storing long-lived cloud credentials as GitHub secrets.
- GitHub OIDC subject claims can include an environment claim.
- AWS trust policies can restrict audience and subject claims.
- Current repository includes only validate and plan workflows, not apply.
- The `terraform-plan` and `terraform-apply` GitHub environments exist.
- Required environment reviewers are unavailable on the current GitHub repository plan.
- The first GitHub plan workflow successfully assumed the plan role through OIDC.

## Assumptions

- GitHub environments named `terraform-plan` and `terraform-apply` are acceptable. Confidence: high.
- The exact repository is `josephmccann/AIFO-Control-Plane`. Confidence: high.

## Unknowns

- Final apply role permission set.
- Whether GitHub required reviewers will become available through a plan upgrade or repository ownership change.

## Information Sources Reviewed

- GitHub OIDC with AWS: https://docs.github.com/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services
- GitHub OIDC reference: https://docs.github.com/actions/reference/openid-connect-reference
- AWS IAM roles for GitHub Actions blog: https://aws.amazon.com/blogs/security/use-iam-roles-to-connect-github-actions-to-actions-in-aws/

## Decision

Use separate GitHub Actions roles for plan and apply. Restrict each OIDC trust policy to the exact repository and GitHub environment subject. Create no apply workflow until the approval boundary, permissions, rollback, and recovery procedures are reviewed.

Because required environment reviewers are unavailable, keep `terraform-apply` unused and leave the apply role without infrastructure mutation permissions.

## Why This Decision Is Appropriate Now

It allows automated planning while preserving human authority over mutation and avoiding static credentials.

## Alternatives Considered

- One shared plan/apply role.
- Long-lived AWS access keys in GitHub secrets.
- Local-only Terraform operations.

## Why Alternatives Were Rejected Or Deferred

- Shared roles blur read and write boundaries.
- Static keys violate the repository charter and increase credential leak risk.
- Local-only operations reduce auditability and repeatability.

## Security Effects

Improves credential posture with short-lived role sessions and explicit trust conditions. Residual risk is overbroad role permissions, which must remain narrow and reviewed.

## Privacy Effects

No product data is accessed by CI in the initial plan workflow.

## Reliability Effects

Plan automation improves review quality. Apply is intentionally absent to avoid accidental mutation.

## Cost Effects

No direct recurring cost for OIDC roles.

## Operational Burden

Requires GitHub environment configuration and role maintenance.

## Solo-Founder Recoverability

Clear role separation makes it easier to disable or rotate one boundary without breaking all workflows.

## Product Impact

Allows infrastructure review without impacting the current product runtime.

## Data-Lineage Impact

GitHub workflow logs, plans, commits, and role sessions provide infrastructure lineage.

## Auditability Impact

CloudTrail STS events and GitHub workflow history identify role assumption and plan activity.

## Reversibility

Roles can be removed or trust policies changed through approved Terraform.

## Rollback Or Migration Path

Disable the workflow, remove repository variables, revoke role trust, or destroy OIDC resources through an approved process.

## Evidence That Would Cause Reconsideration

- GitHub environment protection cannot be configured as expected.
- Plan role permissions prove insufficient or too broad.
- A different CI system becomes the source of truth.
