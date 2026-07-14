# Deployment Status

## Current Status

Remote-state and GitHub OIDC bootstrap are complete in AWS account `350480401760`.

No control-plane EC2 host, product runtime resources, GitHub repository variables, GitHub environments, CloudTrail resources, apply workflow, or additional apply-role permissions were created.

## Last Validated State

Pre-bootstrap validation passed on 2026-07-14:

- `PATH="$PWD/build/bin:$PATH" AWS_PROFILE=aifo-admin AWS_SDK_LOAD_CONFIG=1 ./scripts/validate.sh`
- Refreshed remote-state plan produced only approved creates: `6 to add, 0 to change, 0 to destroy`.
- Refreshed GitHub OIDC plan produced only approved creates: `8 to add, 0 to change, 0 to destroy`.
- Post-apply remote-state plan exit code: `0`.
- Post-apply GitHub OIDC plan exit code: `0`.

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
- `terraform-apply` GitHub environment has not been created.
- GitHub repository variables have not been created.
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
- Future apply workflow must use protected environment `terraform-apply`.
- Human approval is required before creation or use.

## Next Deployment Gate

Configure GitHub environments and repository variables before first GitHub plan.

Required next actions:

1. Configure `terraform-plan` protection rules.
2. Create and protect `terraform-apply` with required reviewers before any future apply workflow exists.
3. Add repository variables:
   - `AWS_TERRAFORM_PLAN_ROLE_ARN=arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Plan`
   - `TF_BACKEND_BUCKET=aifo-terraform-state-350480401760-us-west-2`
   - `TF_BACKEND_KEY=control-plane/terraform.tfstate`
4. Create `terraform/environments/control-plane/backend.hcl` locally from the example when running local plans.
5. Do not run the control-plane environment apply until a separate approval gate.
