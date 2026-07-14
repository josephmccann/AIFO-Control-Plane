# Deployment Runbook

No deployment is currently approved.

## Deployment Boundary

The repository currently supports validation and planning only. There is no apply workflow. Any deployment requires:

- reviewed Terraform plan;
- human approval;
- confirmed rollback path;
- updated ADRs and runbooks;
- protected `terraform-apply` GitHub environment;
- no long-lived credentials.

## First Plan Sequence

```bash
cp terraform/environments/control-plane/backend.hcl.example \
  terraform/environments/control-plane/backend.hcl
```

```bash
./scripts/validate.sh
terraform -chdir=terraform/environments/control-plane init \
  -input=false \
  -backend-config=backend.hcl
terraform -chdir=terraform/environments/control-plane plan -input=false
```

Review the plan for:

- one VPC;
- one public subnet by default;
- Internet Gateway and outbound route;
- EC2 host with public IPv4;
- no inbound security-group rules;
- no SSH key;
- IMDSv2 required;
- SSM instance role only;
- HTTPS and DNS egress only;
- S3 gateway endpoint;
- no NAT Gateway;
- no interface endpoints;
- `manage_budget = false` unless importing the budget deliberately.

## Apply Boundary

Do not apply until the human approval gate is satisfied. A future apply workflow must use the `terraform-apply` protected environment with required reviewers.
