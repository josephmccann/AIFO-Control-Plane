# Deployment Runbook

No deployment is currently approved.

## Deployment Boundary

The repository currently supports validation and planning only. There is no apply workflow. Any deployment requires:

- reviewed Terraform plan;
- human approval;
- confirmed rollback path;
- updated ADRs and runbooks;
- authenticated IAM Identity Center session while GitHub required reviewers are unavailable;
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
- 100 GiB encrypted gp3 root volume;
- no NAT Gateway;
- no interface endpoints;
- `manage_budget = false` unless importing the budget deliberately.
- CloudTrail management-events trail with no data event selectors.
- Dedicated CloudTrail S3 bucket with encryption, public access blocked, lifecycle retention, and CloudTrail-only write policy.
- Session Manager CloudWatch log group with KMS encryption and 30-day retention.
- `SSM-SessionManagerRunShell` preferences document.
- EventBridge Scheduler start and stop schedules scoped to the single EC2 instance.
- Scheduler DLQ and retry policy.
- No apply workflow or apply-role mutation permissions.

## Apply Boundary

Do not apply until the human approval gate is satisfied. Because GitHub required environment reviewers are unavailable on the current repository plan, do not create an apply workflow and do not use `terraform-apply`. The current apply path is a supervised local apply using IAM Identity Center after an explicit approval packet.

Approved local apply command shape:

```bash
AWS_PROFILE=aifo-admin AWS_SDK_LOAD_CONFIG=1 \
terraform -chdir=terraform/environments/control-plane apply -input=false
```

The reviewed plan must be regenerated immediately before apply and must match the approved resource set.

## First Host Deployment Operating Posture

Create the host running, not immediately stopped, so cloud-init, SSM registration, Session Manager logging, and emergency access can be verified before handing the host to the schedule.

To avoid accidental continuous billing, schedule the first apply inside the 08:00-16:00 Monday-Friday `America/Los_Angeles` operating window. If the apply must happen outside that window, run the manual stop command in [ec2-start-stop.md](ec2-start-stop.md) immediately after verification.
