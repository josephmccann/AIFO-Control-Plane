# Deployment Status

## Current Status

Remote-state and GitHub OIDC bootstrap are complete in AWS account `350480401760`.

No control-plane EC2 host, product runtime resources, CloudTrail resources, apply workflow, or additional apply-role permissions have been created.

GitHub planning configuration is complete:

- `terraform-plan` environment exists and is intentionally unblocked for automated planning.
- `terraform-apply` environment exists, but required reviewers are unavailable on the current GitHub repository plan.
- Repository variables are configured for the plan workflow.
- The plan workflow successfully assumed `arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Plan` through OIDC.
- `terraform-apply` must remain unused; no apply workflow may be created under the current GitHub approval limitation.

## Last Validated State

Pre-bootstrap validation passed on 2026-07-14:

- `PATH="$PWD/build/bin:$PATH" AWS_PROFILE=aifo-admin AWS_SDK_LOAD_CONFIG=1 ./scripts/validate.sh`
- Refreshed remote-state plan produced only approved creates: `6 to add, 0 to change, 0 to destroy`.
- Refreshed GitHub OIDC plan produced only approved creates: `8 to add, 0 to change, 0 to destroy`.
- Post-apply remote-state plan exit code: `0`.
- Post-apply GitHub OIDC plan exit code: `0`.
- First GitHub control-plane plan run succeeded: https://github.com/josephmccann/AIFO-Control-Plane/actions/runs/29371131579.

Skipped:

- `shellcheck`, because it is not installed locally.

## Bootstrap Execution Results

Remote-state apply:

- Result: `6 added, 0 changed, 0 destroyed`.
- State bucket: `aifo-terraform-state-350480401760-us-west-2`.
- Backend output:
  - bucket: `aifo-terraform-state-350480401760-us-west-2`
  - key: `control-plane/terraform.tfstate`
  - region: `us-west-2`
  - encrypt: `true`
  - use_lockfile: `true`

GitHub OIDC apply:

- Result: `8 added, 0 changed, 0 destroyed`.
- OIDC provider: `arn:aws:iam::350480401760:oidc-provider/token.actions.githubusercontent.com`
- Plan role: `arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Plan`
- Apply role: `arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Apply`
- State access policy: `arn:aws:iam::350480401760:policy/AIFO-GitHubActions-Terraform-StateAccess`
- Plan read policy: `arn:aws:iam::350480401760:policy/AIFO-GitHubActions-Terraform-PlanReadAccess`
- Plan trust subject: `repo:josephmccann/AIFO-Control-Plane:environment:terraform-plan`
- Apply trust subject: `repo:josephmccann/AIFO-Control-Plane:environment:terraform-apply`
- OIDC audience: `sts.amazonaws.com`

## Verification Results

Remote state:

- Versioning: enabled.
- Public access block:
  - `BlockPublicAcls = true`
  - `IgnorePublicAcls = true`
  - `BlockPublicPolicy = true`
  - `RestrictPublicBuckets = true`
- Server-side encryption: `AES256`.
- Policy status: not public.
- Ownership controls: `BucketOwnerEnforced`.
- Bucket policy: denies `s3:*` when `aws:SecureTransport` is `false`.

OIDC and IAM:

- OIDC provider exists with client ID `sts.amazonaws.com`.
- Plan role trust policy is restricted to the exact repository environment subject for `terraform-plan`.
- Apply role trust policy is restricted to the exact repository environment subject for `terraform-apply`.
- Both trust policies require audience `sts.amazonaws.com`.
- Plan role attached policies:
  - `AIFO-GitHubActions-Terraform-StateAccess`
  - `AIFO-GitHubActions-Terraform-PlanReadAccess`
- Apply role attached policies:
  - `AIFO-GitHubActions-Terraform-StateAccess`
- Apply role inline policies: none.
- Apply role has no infrastructure mutation permissions attached beyond Terraform state access.

## Warnings And Drift

- No Terraform drift detected for the two bootstrap roots after apply.
- CloudTrail was not changed; read-only inspection returned no trails in `us-west-2`.
- `terraform-plan` GitHub environment exists but has no protection rules.
- `terraform-apply` GitHub environment exists but cannot enforce required reviewers on the current GitHub repository plan.
- GitHub required reviewers failed with a GitHub platform limitation; do not weaken AWS OIDC trust to compensate.
- Bootstrap Terraform state exists locally under ignored paths; do not commit local state or plan files.

## External Resources Known To Exist

- AWS account `350480401760`.
- Root MFA.
- IAM Identity Center.
- Human admin permission set `AIFO-Platform-Admin`.
- Manual AWS Budget target: $250/month, budget name `First budget`.
- Private GitHub repository.

The manual AWS Budget is not imported into Terraform state.

## Apply Workflows

- No apply workflow exists.
- No apply workflow may be created while `terraform-apply` cannot enforce required reviewers.
- The apply role must remain state-access-only until a future apply boundary is reviewed and approved.
- Control-plane applies must use an authenticated IAM Identity Center session after an explicit approval packet is reviewed.

## Next Deployment Gate

Review the revised cost-aligned plan and approve or reject a scheduled manual control-plane apply.

Required next actions:

1. Confirm the revised plan proposes 14 additions, 0 changes, 0 destroys, and a 100 GiB gp3 root volume.
2. Choose the initial operating schedule, preferably 8 hours per weekday.
3. Review the EC2 start/stop runbook.
4. Create `terraform/environments/control-plane/backend.hcl` locally from the example when running local plans.
5. Do not run the control-plane environment apply until a separate approval gate.
