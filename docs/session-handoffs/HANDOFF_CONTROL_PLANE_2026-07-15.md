# AI.FO Control Plane Session Handoff

Session state: HISTORICAL CHECKPOINT - SUPERSEDED BY `docs/handoffs/HANDOFF_CONTROL_PLANE.md`

## 2026-07-15 Reconciliation Addendum

- Current verified main head is `707e6298ed558fde06faea99b7e4b99b8b2b7adc`.
- Latest clean GitHub Terraform Plan is https://github.com/josephmccann/AIFO-Control-Plane/actions/runs/29380920338.
- Pinned ShellCheck v0.11.0 and actionlint v1.7.12 are now installed by repository tooling and validation passes; the historical warnings below are resolved.
- The product-runtime architecture analysis is complete in a draft decision package, but all product deployment remains unapproved and blocked.
- Use [the canonical current handoff](../handoffs/HANDOFF_CONTROL_PLANE.md) when resuming work. The remainder of this document preserves the pre-update checkpoint as historical evidence.

## Mission Objective

Build and operate a secure, reproducible, cost-aware AWS control plane for AI.FO that supports the current product without deploying product runtime infrastructure prematurely.

The approved current-scope control-plane baseline is operationally complete.

## Completed Architecture

- Terraform remote state in S3 with native lockfile support.
- GitHub Actions OIDC provider and separate plan/apply roles.
- GitHub Terraform Plan workflow with drift gate.
- VPC with one public subnet in one Availability Zone.
- Internet Gateway and outbound route.
- S3 gateway endpoint.
- No-ingress EC2 control-plane host.
- SSM-only administration.
- IMDSv2 required.
- 100 GiB encrypted gp3 root volume.
- Multi-Region CloudTrail management-events baseline.
- Dedicated encrypted CloudTrail S3 log bucket.
- Session Manager logging to encrypted CloudWatch Logs.
- EventBridge Scheduler start/stop automation.
- Scheduler dead-letter queue.

## Exact Account And Region

- AWS account: `350480401760`
- Region: `us-west-2`
- IAM Identity Center profile: `aifo-admin`

## Terraform State

- State bucket: `aifo-terraform-state-350480401760-us-west-2`
- State key: `control-plane/terraform.tfstate`
- Locking: native S3 lockfile
- Terraform version used in workflow: `1.10.5`

## Repository State

- Repository: `josephmccann/AIFO-Control-Plane`
- Latest main commit at checkpoint start: `b9e1b539474efa30086d9031b3118cfe241ffa28`
- This handoff PR will create the post-checkpoint merge SHA.

## EC2 Host

- Instance ID: `i-0254a9e2fcbcdebd7`
- Current state: `stopped`
- Instance type: `m7i-flex.2xlarge`
- Root volume: 100 GiB encrypted gp3
- SSH key: none
- Inbound security-group rules: zero
- IMDSv2: required
- Termination protection: enabled
- Public IPv4: only while running; ignored for stopped-state Terraform drift

## Operating Schedule

- Start schedule: 08:00 Monday-Friday
- Stop schedule: 16:00 Monday-Friday
- Timezone: `America/Los_Angeles`
- Manual start outside schedule is allowed only as an approved emergency override.
- A manual start does not disable the next scheduled stop.

## CloudTrail Status

- Trail: `arn:aws:cloudtrail:us-west-2:350480401760:trail/aifo-control-plane-management-events`
- Multi-Region: enabled
- Management events: enabled
- Data events: not enabled
- Log-file validation: enabled
- Log bucket: `aifo-control-plane-cloudtrail-350480401760-us-west-2`
- Bucket public access: blocked
- Bucket lifecycle: enabled

## Session Manager Status

- Administration path: Session Manager only
- Log group: `/aifo/control-plane/session-manager`
- Retention: 30 days
- KMS key: `arn:aws:kms:us-west-2:350480401760:key/e36ac1c5-105c-42c1-92f9-06fcf02cb772`
- Connectivity: tested successfully after deployment
- Logging: verified to reach the log group
- Current note: instance is stopped, so active SSM shell access requires an approved start

## GitHub OIDC

- OIDC provider: `arn:aws:iam::350480401760:oidc-provider/token.actions.githubusercontent.com`
- Plan role: `arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Plan`
- Apply role: `arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Apply`
- Plan trust subject: `repo:josephmccann/AIFO-Control-Plane:environment:terraform-plan`
- Apply trust subject: `repo:josephmccann/AIFO-Control-Plane:environment:terraform-apply`
- OIDC audience: `sts.amazonaws.com`
- Apply role: state-access-only; no inline policies

## GitHub Environments And Variables

- `terraform-plan`: exists and is used for automated planning
- `terraform-apply`: exists but must remain unused because required reviewers are unavailable
- `AWS_TERRAFORM_PLAN_ROLE_ARN=arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Plan`
- `TF_BACKEND_BUCKET=aifo-terraform-state-350480401760-us-west-2`
- `TF_BACKEND_KEY=control-plane/terraform.tfstate`

## Plan-Role Policy

- Policy ARN: `arn:aws:iam::350480401760:policy/AIFO-GitHubActions-Terraform-PlanReadAccess`
- Default version: `v4`
- Policy is read-only.
- Final added statement: `ReadCloudTrailLogBucketMetadata`
- Statement scope: `arn:aws:s3:::aifo-control-plane-cloudtrail-350480401760-us-west-2`

## Latest Successful Plans

- Local Terraform plan: `0 to add, 0 to change, 0 to destroy`
- GitHub Terraform Plan: https://github.com/josephmccann/AIFO-Control-Plane/actions/runs/29378532712
- GitHub classification: exit code `0`, `0` add / `0` change / `0` destroy, result `clean`

## Verified Drift-Gate Behavior

- `workflow_dispatch` exit `0`: `clean`, pass
- `workflow_dispatch` exit `2`: `unexpected drift`, fail
- `pull_request` exit `2`: `proposed change`, pass
- exit `1`: fail

## Cost Posture

- Budget target: `$250` monthly
- Approved posture: scheduled operation
- 8 hours per weekday estimate: about `$76.30` monthly before low-volume logs/taxes
- 12 hours per day estimate: about `$149.64` monthly before low-volume logs/taxes
- Always-on estimate: about `$291.27` monthly before low-volume logs/taxes
- Always-on operation is not approved.

## Known Warnings

- GitHub Actions reports Node 20 deprecation notices for upstream actions.
- `shellcheck` is unavailable locally and is skipped by `scripts/validate.sh`.
- `actionlint` is unavailable locally.
- GitHub required environment reviewers are unavailable on the current repository plan.
- Product runtime infrastructure is not deployed.

## Remaining Risks

- Product runtime architecture remains unresolved.
- Product database, secrets, object storage, domain/TLS, and QBO callback migration are not designed in AWS.
- Running the EC2 host continuously would exceed the current budget posture.
- Session Manager logs can capture sensitive terminal output; operators must not print secrets or customer data.
- Public IPv4 is used for cost-effective outbound egress while the host has zero inbound rules.

## Unresolved Decisions

- Whether and when AI.FO product runtime moves to AWS.
- Product database architecture.
- Product secrets and rotation model.
- Whether to retain Cloudflare R2 or migrate product storage to S3.
- Whether to upgrade GitHub plan for required reviewers or use another approval boundary for future apply automation.
- Whether to add host patch automation or keep manual patch windows.

## Explicit Product-Runtime Boundary

Do not deploy product runtime infrastructure from this repository without a separate approved ADR and approval packet.

Out of scope:

- Product API/frontend hosting.
- PostgreSQL hosting.
- Product secrets.
- Product object storage.
- QBO OAuth callback migration.
- Domain/TLS migration.
- Customer data hosting.

## Exact Commands To Resume

```bash
cd ~/code/AIFO-Control-Plane
git switch main
git pull --ff-only origin main
git status --short --branch
```

```bash
aws sts get-caller-identity --profile aifo-admin --output json
```

```bash
PATH="$PWD/build/bin:$PATH" AWS_PROFILE=aifo-admin AWS_SDK_LOAD_CONFIG=1 ./scripts/validate.sh
```

```bash
PATH="$PWD/build/bin:$PATH" AWS_PROFILE=aifo-admin AWS_SDK_LOAD_CONFIG=1 \
terraform -chdir=terraform/environments/control-plane plan \
  -no-color -input=false -lock=false -detailed-exitcode
```

```bash
aws ec2 describe-instances \
  --profile aifo-admin \
  --region us-west-2 \
  --instance-ids i-0254a9e2fcbcdebd7 \
  --query 'Reservations[].Instances[].{InstanceId:InstanceId,State:State.Name,InstanceType:InstanceType,PublicIp:PublicIpAddress}' \
  --output table
```

```bash
gh run view 29378532712 --json url,headSha,event,status,conclusion,jobs
```

## Next Highest-Value Task

After the Codex CLI update, do not begin deployment work. First verify this handoff, then choose one narrow task:

1. Add durable workflow/tooling lint support for `actionlint` and `shellcheck`.
2. Create a product-runtime architecture ADR without deploying anything.
3. Draft the host patching and maintenance runbook.

## Stop Conditions

Stop immediately and ask for explicit approval if any task requires:

- `terraform apply`;
- `terraform destroy`;
- AWS resource creation, modification, or deletion;
- starting the EC2 instance outside an approved schedule/emergency;
- changing Scheduler configuration;
- adding an apply workflow;
- modifying the apply role;
- deploying product runtime infrastructure;
- storing credentials or secrets;
- changing repository visibility;
- force-pushing or rewriting history.

## Codex 5.6 Resume Prompt

```text
Resume the AI.FO AWS control-plane mission from /Users/joemccann/code/AIFO-Control-Plane.

Treat docs/session-handoffs/HANDOFF_CONTROL_PLANE_2026-07-15.md as the canonical startup context. Confirm the repository is on main, pull latest, verify a clean working tree, confirm AWS identity with profile aifo-admin, verify EC2 instance i-0254a9e2fcbcdebd7 remains stopped, run repository validation, and run a read-only Terraform control-plane plan.

Do not deploy, do not run terraform apply or destroy, do not start the EC2 instance, do not modify Scheduler, do not create an apply workflow, do not modify the apply role, and do not deploy product runtime infrastructure.

After verification, propose the next narrow task from the handoff work queue.
```
