# Bootstrap Runbook

This runbook prepares AWS remote state and GitHub OIDC. It is not approval to execute. Running `terraform apply` or creating IAM resources requires explicit human approval.

## Preconditions

- AWS account ID confirmed.
- IAM Identity Center session active for `AIFO-Platform-Admin`.
- No long-lived AWS keys in the shell or GitHub.
- GitHub repository confirmed as `josephmccann/AIFO-Control-Plane`.
- GitHub environments planned:
  - `terraform-plan`
  - `terraform-apply`
- Terraform `>= 1.10.0` installed.

## Remote State Plan

```bash
cp terraform/bootstrap/remote-state/terraform.tfvars.example \
  terraform/bootstrap/remote-state/terraform.tfvars
```

Edit `terraform/bootstrap/remote-state/terraform.tfvars` locally:

```hcl
aws_region        = "us-west-2"
state_bucket_name = "aifo-terraform-state-ACCOUNT_ID-us-west-2"
force_destroy     = false
```

Review without creating resources:

```bash
terraform -chdir=terraform/bootstrap/remote-state init -input=false
terraform -chdir=terraform/bootstrap/remote-state plan -input=false
```

Human approval gate before:

```bash
terraform -chdir=terraform/bootstrap/remote-state apply -input=false
```

## GitHub OIDC Plan

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

state_bucket_name = "aifo-terraform-state-ACCOUNT_ID-us-west-2"
state_key         = "control-plane/terraform.tfstate"
```

Review without creating resources:

```bash
terraform -chdir=terraform/bootstrap/github-oidc init -input=false
terraform -chdir=terraform/bootstrap/github-oidc plan -input=false
```

Human approval gate before:

```bash
terraform -chdir=terraform/bootstrap/github-oidc apply -input=false
```

## GitHub Repository Configuration

Create protected environments in GitHub before using OIDC:

- `terraform-plan`
- `terraform-apply`

The apply environment must require manual reviewer approval before any future apply workflow exists.

Set repository variables after OIDC bootstrap:

```bash
gh variable set AWS_TERRAFORM_PLAN_ROLE_ARN \
  --repo josephmccann/AIFO-Control-Plane \
  --body "PLAN_ROLE_ARN"

gh variable set TF_BACKEND_BUCKET \
  --repo josephmccann/AIFO-Control-Plane \
  --body "aifo-terraform-state-ACCOUNT_ID-us-west-2"

gh variable set TF_BACKEND_KEY \
  --repo josephmccann/AIFO-Control-Plane \
  --body "control-plane/terraform.tfstate"
```

Do not set AWS access keys as GitHub secrets.

## Post-Bootstrap Verification

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
