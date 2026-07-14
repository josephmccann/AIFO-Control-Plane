# Bootstrap Runbook

This runbook records the AWS remote state and GitHub OIDC bootstrap process. The bootstrap was completed after explicit approval on 2026-07-14. Running additional `terraform apply`, creating GitHub environments, creating repository variables, or deploying the control-plane host still requires explicit human approval.

## Preconditions

- AWS account ID confirmed: `350480401760`.
- IAM Identity Center session active for `AIFO-Platform-Admin`.
- No long-lived AWS keys in the shell or GitHub.
- GitHub repository confirmed as `josephmccann/AIFO-Control-Plane`.
- GitHub environments planned:
  - `terraform-plan`
  - `terraform-apply`
- Terraform `>= 1.10.0` installed.

## Completed Remote State Bootstrap

- State bucket: `aifo-terraform-state-350480401760-us-west-2`
- Apply result: `6 added, 0 changed, 0 destroyed`
- Post-apply plan: no drift
- Versioning: enabled
- Encryption: `AES256`
- Public access: blocked
- Ownership controls: `BucketOwnerEnforced`
- Bucket policy: denies insecure transport

## Remote State Plan Pattern

```bash
cp terraform/bootstrap/remote-state/terraform.tfvars.example \
  terraform/bootstrap/remote-state/terraform.tfvars
```

Edit `terraform/bootstrap/remote-state/terraform.tfvars` locally:

```hcl
aws_region        = "us-west-2"
state_bucket_name = "aifo-terraform-state-350480401760-us-west-2"
force_destroy     = false
```

Review without creating resources:

```bash
terraform -chdir=terraform/bootstrap/remote-state init -input=false
terraform -chdir=terraform/bootstrap/remote-state plan -input=false
```

The bootstrap apply has already been completed. Human approval is required before any future apply:

```bash
terraform -chdir=terraform/bootstrap/remote-state apply -input=false
```

## Completed GitHub OIDC Bootstrap

- OIDC provider: `arn:aws:iam::350480401760:oidc-provider/token.actions.githubusercontent.com`
- Plan role: `arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Plan`
- Apply role: `arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Apply`
- State access policy: `arn:aws:iam::350480401760:policy/AIFO-GitHubActions-Terraform-StateAccess`
- Plan read policy: `arn:aws:iam::350480401760:policy/AIFO-GitHubActions-Terraform-PlanReadAccess`
- Plan trust subject: `repo:josephmccann/AIFO-Control-Plane:environment:terraform-plan`
- Apply trust subject: `repo:josephmccann/AIFO-Control-Plane:environment:terraform-apply`
- Audience: `sts.amazonaws.com`
- Apply role permissions: state access only, no inline policies
- Post-apply plan: no drift

## GitHub OIDC Plan Pattern

```bash
cp terraform/bootstrap/github-oidc/terraform.tfvars.example \
  terraform/bootstrap/github-oidc/terraform.tfvars
```

Edit `terraform/bootstrap/github-oidc/terraform.tfvars` locally:

```hcl
aws_region               = "us-west-2"
github_owner             = "josephmccann"
github_repository        = "AIFO-Control-Plane"
github_plan_environment  = "terraform-plan"
github_apply_environment = "terraform-apply"

state_bucket_name = "aifo-terraform-state-350480401760-us-west-2"
state_key         = "control-plane/terraform.tfstate"
```

Review without creating resources:

```bash
terraform -chdir=terraform/bootstrap/github-oidc init -input=false
terraform -chdir=terraform/bootstrap/github-oidc plan -input=false
```

The bootstrap apply has already been completed. Human approval is required before any future apply:

```bash
terraform -chdir=terraform/bootstrap/github-oidc apply -input=false
```

## GitHub Repository Configuration

GitHub environments are configured:

- `terraform-plan`
- `terraform-apply`

The plan environment is used for automated planning. The apply environment exists, but GitHub required environment reviewers are unavailable on the current repository plan. It must remain unused and no apply workflow may be created.

Current status:

- `terraform-plan` exists but has no protection rules.
- `terraform-apply` exists but has no required reviewer protection.
- Repository variables have been created.

Repository variables configured after OIDC bootstrap:

| Variable | Value |
| --- | --- |
| `AWS_TERRAFORM_PLAN_ROLE_ARN` | `arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Plan` |
| `TF_BACKEND_BUCKET` | `aifo-terraform-state-350480401760-us-west-2` |
| `TF_BACKEND_KEY` | `control-plane/terraform.tfstate` |

Do not set AWS access keys as GitHub secrets.

## Control-Plane Plan Verification

```bash
cp terraform/environments/control-plane/backend.hcl.example \
  terraform/environments/control-plane/backend.hcl
```

```bash
terraform -chdir=terraform/environments/control-plane init \
  -input=false \
  -backend-config=backend.hcl

terraform -chdir=terraform/environments/control-plane validate -no-color
terraform -chdir=terraform/environments/control-plane plan -input=false
```

Stop before any apply.

## Rollback

If remote state bootstrap was applied incorrectly and no dependent state exists, review:

```bash
terraform -chdir=terraform/bootstrap/remote-state plan -destroy -input=false
```

If OIDC bootstrap was applied incorrectly, remove repository variables, disable workflows, review trust policies, and use Terraform destroy only after explicit approval.
