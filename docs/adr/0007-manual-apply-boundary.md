# ADR-0007: Use Manual IAM Identity Center Apply Boundary Until GitHub Reviewer Protection Is Available

## Status

Accepted for initial control-plane deployment gate

## Current Product Requirement Supported

AI.FO needs auditable infrastructure deployment without long-lived AWS keys and without silent mutation of AWS resources. The current control plane still does not host product runtime or customer data.

## Founder Principle Or Constitutional Principle Implicated

Principles 1, 8, 14, 20, and 22: earn trust through evidence, keep human authority central, state limits clearly, operate with discipline, and avoid silent policy adaptation.

## Known Facts

- Remote-state and GitHub OIDC bootstrap infrastructure has been deployed.
- GitHub repository variables for planning are configured.
- The `terraform-plan` environment exists and the plan workflow successfully assumes `arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Plan`.
- The `terraform-apply` environment exists.
- GitHub rejected required reviewer protection for `terraform-apply` because the current repository plan does not support it.
- No apply workflow exists.
- The apply role has only Terraform state access and no infrastructure mutation permissions.

## Assumptions

- IAM Identity Center profile `aifo-admin` remains the approved short-lived human credential path. Confidence: high.
- A local supervised apply after an approval packet is safer than an unprotected GitHub apply workflow. Confidence: high.
- GitHub reviewer protection may become available through a future plan or ownership change. Confidence: medium.

## Unknowns

- Whether the GitHub account plan will be upgraded.
- Whether another approval system will become the preferred deployment control.
- Final least-privilege mutation permissions for a future apply role.

## Information Sources Reviewed

- GitHub OIDC with AWS: https://docs.github.com/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services
- GitHub OIDC reference: https://docs.github.com/actions/reference/openid-connect-reference
- GitHub environment limitation observed through GitHub API response during environment configuration.
- AWS IAM Identity Center administrative access exists for the account.

## Decision

Do not create an apply workflow and do not use `terraform-apply` while required reviewers are unavailable.

For the first control-plane host deployment, use a local Terraform apply only after an explicit approval packet is reviewed, using an authenticated IAM Identity Center session:

```bash
AWS_PROFILE=aifo-admin AWS_SDK_LOAD_CONFIG=1 \
terraform -chdir=terraform/environments/control-plane apply -input=false
```

The plan must be regenerated immediately before apply and must match the approved resource set.

## Why This Decision Is Appropriate Now

It preserves short-lived credentials and human approval without pretending GitHub can enforce a reviewer gate that is currently unavailable.

## Alternatives Considered

- Create an apply workflow without required reviewers.
- Weaken AWS OIDC trust so another GitHub context can assume the apply role.
- Add infrastructure mutation permissions to the apply role now.
- Upgrade GitHub plan immediately.
- Delay all deployment until GitHub reviewer protection is available.

## Why Alternatives Were Rejected Or Deferred

- An unprotected apply workflow would weaken the deployment boundary.
- Weakening OIDC trust would increase blast radius.
- Apply-role mutation permissions are unnecessary until an automated apply boundary exists.
- GitHub plan changes require a human account/billing decision.
- Delaying all deployment is unnecessary if a reviewed local IAM Identity Center apply is explicitly approved.

## Security Effects

Maintains no long-lived AWS keys and keeps infrastructure mutation under a human IAM Identity Center session. Reduces automation risk by keeping `terraform-apply` unused.

## Privacy Effects

No product customer data is introduced. Future product data infrastructure still requires separate review.

## Reliability Effects

Local apply depends on the operator environment and must be validated immediately before execution. GitHub planning remains the review path.

## Cost Effects

No direct recurring cost. Avoids paid GitHub plan assumptions until the approval need is explicit.

## Operational Burden

Manual apply adds a small operator burden but is appropriate for a solo-founder first deployment.

## Solo-Founder Recoverability

The path is recoverable with IAM Identity Center, local Terraform, remote state, and documented rollback procedures.

## Product Impact

No product runtime impact. It preserves the control-plane-only scope.

## Data-Lineage Impact

Git commits, GitHub plan logs, Terraform state, and the approval packet preserve infrastructure decision lineage.

## Auditability Impact

AWS CloudTrail should record the IAM Identity Center session and Terraform API calls once CloudTrail is configured or confirmed. GitHub records plan workflow execution.

## Reversibility

A future PR can add a protected apply workflow once required reviewers or an equivalent approval boundary exists.

## Rollback Or Migration Path

Keep local apply as the path until:

1. GitHub required reviewers are available or an equivalent gate is accepted.
2. Apply role permissions are reviewed and added through Terraform.
3. An apply workflow is reviewed in a PR.
4. A rollback runbook is current.

## Evidence That Would Cause Reconsideration

- GitHub required reviewers become available.
- A better approval system is adopted.
- Local apply proves error-prone.
- Control-plane deployment frequency increases enough to justify stronger automation.
