# AI.FO Control Plane

Initial AWS infrastructure repository for the AI.FO control plane.

This repository is scaffolded for validation and planning only. It does not include an apply workflow, and the bootstrap scripts do not create AWS resources.

## Baseline

- AWS region: `us-west-2`
- Budget target: `$250` per month
- Human admin access: IAM Identity Center permission set `AIFO-Platform-Admin`
- CI/CD access: GitHub Actions OIDC, no static AWS keys
- Host access: AWS Systems Manager Session Manager, no public SSH
- Network default: one public subnet in one Availability Zone
- Host default: public IPv4 address, zero inbound security-group rules
- Egress default: HTTPS to the internet, DNS to the VPC resolver
- Intended host: Ubuntu EC2, 8 vCPU, 32 GB RAM

## Repository Layout

```text
.
├── .github/workflows/
│   ├── terraform-plan.yml
│   └── terraform-validate.yml
├── docs/
│   ├── architecture.md
│   ├── implementation-plan.md
│   └── security-model.md
├── scripts/
│   ├── bootstrap-github-oidc.sh
│   ├── bootstrap-local.sh
│   └── validate.sh
└── terraform/
    ├── bootstrap/
    │   ├── github-oidc/
    │   └── remote-state/
    ├── environments/control-plane/
    └── modules/
        ├── budget/
        ├── compute/
        └── network/
```

## What Terraform Defines

The deployable `control-plane` environment defines:

- VPC with DNS support
- One public subnet by default
- Internet Gateway and default route for outbound internet access
- S3 gateway endpoint for private S3 routing where applicable
- Ubuntu EC2 control-plane host with a public IPv4 address
- EC2 IAM role with `AmazonSSMManagedInstanceCore`
- Security group with no ingress rules
- Security group egress for HTTPS and DNS only
- Optional AWS Budget management, disabled by default

The host uses a public IPv4 address because the initial workload needs outbound internet access for package installation, GitHub clones, container pulls, and external API calls to services such as OpenAI, Anthropic, and Google. With zero inbound security-group rules and no SSH key, public addressing gives required egress without the recurring cost of a NAT Gateway. A later phase can migrate the host into private subnets once the extra cost and operational complexity are justified.

## Local Validation

Install Terraform `>= 1.10.0`, then run:

```bash
./scripts/bootstrap-local.sh
./scripts/validate.sh
```

The validation path initializes each Terraform root with:

```bash
terraform init -backend=false -input=false
```

`-backend=false` avoids any dependency on remote state infrastructure during local checks.

## GitHub Actions

Two workflows are included:

- `terraform-validate.yml`: formatting and Terraform validation without AWS credentials.
- `terraform-plan.yml`: Terraform plan using GitHub Actions OIDC role assumption.

There is no apply workflow.

The plan workflow runs in the protected GitHub environment `terraform-plan` and expects repository variables:

| Variable | Purpose |
| --- | --- |
| `AWS_TERRAFORM_PLAN_ROLE_ARN` | IAM role ARN assumed by GitHub Actions through OIDC |
| `TF_BACKEND_BUCKET` | S3 bucket for Terraform state |
| `TF_BACKEND_KEY` | State key, for example `control-plane/terraform.tfstate` |

Do not add AWS access keys as GitHub secrets.

## Terraform State

The S3 backend uses native S3 lockfiles:

```hcl
use_lockfile = true
```

DynamoDB locking is intentionally not part of the initial backend. Native S3 lockfiles require Terraform `>= 1.10.0`; the workflows pin Terraform `1.10.5`.

## Terraform Inputs

Start from the example file:

```bash
cp terraform/environments/control-plane/terraform.tfvars.example \
  terraform/environments/control-plane/terraform.tfvars
```

Review the values before any future plan or apply. Do not commit `terraform.tfvars` if it contains environment-specific or sensitive values.

## Budget Management

`manage_budget` defaults to `false` because an AWS Budget already exists manually.

To import the existing budget later:

1. Set `manage_budget = true`.
2. Set `monthly_budget_usd` and `budget_notification_emails` to match the existing budget.
3. Run an approved import, not an apply:

```bash
terraform -chdir=terraform/environments/control-plane import \
  'module.budget[0].aws_budgets_budget.monthly' \
  ACCOUNT_ID:BUDGET_NAME
```

Review the resulting plan before any future apply.

## Instance Type Candidates

The default instance type is `m7i-flex.2xlarge` because it targets 8 vCPU and 32 GiB RAM. Before first deployment, verify pricing and availability for:

- `m7i-flex.2xlarge`
- `m7i.2xlarge`
- `m7a.2xlarge`

## Deployment Status

No infrastructure has been deployed from this repository.

Before a future deployment, complete the implementation plan in [docs/implementation-plan.md](docs/implementation-plan.md), review the security model, and create the required remote-state and OIDC bootstrap resources through an approved process.
