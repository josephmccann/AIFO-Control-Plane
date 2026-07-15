# Deployment Status

## Current Status

Session state: ACTIVE - PRODUCT RUNTIME ARCHITECTURE DECISION

The approved current-scope AWS control-plane baseline is operationally complete in AWS account `350480401760`, Region `us-west-2`.

Remote-state bootstrap, GitHub OIDC bootstrap, CloudTrail, Session Manager logging, no-ingress EC2, and EventBridge Scheduler start/stop automation have been deployed after explicit approval. Product runtime infrastructure has not been deployed. No apply workflow exists.

The EC2 control-plane host is intentionally stopped:

- Instance ID: `i-0254a9e2fcbcdebd7`
- Instance type: `m7i-flex.2xlarge`
- Root volume: 100 GiB encrypted gp3
- Administration: SSM Session Manager only
- SSH key: none
- Inbound security-group rules: zero
- IMDSv2: required
- Termination protection: enabled

GitHub planning configuration is complete:

- `terraform-plan` environment exists and is intentionally unblocked for automated planning.
- `terraform-apply` environment exists, but required reviewers are unavailable on the current GitHub repository plan.
- Repository variables are configured for the plan workflow.
- The plan workflow successfully assumed `arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Plan` through OIDC.
- `terraform-apply` must remain unused; no apply workflow may be created under the current GitHub approval limitation.

## Last Validated State

Current validation state:

- `PATH="$PWD/build/bin:$PATH" AWS_PROFILE=aifo-admin AWS_SDK_LOAD_CONFIG=1 ./scripts/validate.sh`
- Local Terraform control-plane plan: `0 to add, 0 to change, 0 to destroy`.
- Latest successful GitHub Terraform Plan: https://github.com/josephmccann/AIFO-Control-Plane/actions/runs/29380920338.
- GitHub plan classification: exit code `0`, `0` add / `0` change / `0` destroy, result `clean`.
- EC2 instance state: `stopped`.
- GitHub plan-role policy default version: `v4`.

Local tooling verification:

- ShellCheck v0.11.0 installed through the repository-pinned, checksum-verified installer and passed.
- `actionlint` v1.7.12 installed through the repository-pinned, checksum-verified installer and passed.

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
- Plan read policy default version: `v4`
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
- Plan read policy default version `v4` is read-only and includes refresh access for CloudTrail, KMS, CloudWatch Logs, EventBridge Scheduler, SQS, SSM, S3, EC2, IAM read APIs, Budgets read, STS identity, tag reads, and scoped CloudTrail log-bucket metadata reads.

Control-plane resources:

- CloudTrail trail: `aifo-control-plane-management-events`.
- CloudTrail ARN: `arn:aws:cloudtrail:us-west-2:350480401760:trail/aifo-control-plane-management-events`.
- CloudTrail log bucket: `aifo-control-plane-cloudtrail-350480401760-us-west-2`.
- VPC: `vpc-0f73b1daaa9fc17ab`.
- Public subnet: `subnet-03ce35314c75b8e1f`.
- Security group: `sg-0190e01bae800bb1a`.
- S3 gateway endpoint: `vpce-058114f11531d5fdd`.
- EC2 IAM role: `aifo-control-plane-ec2-ssm-role`.
- EC2 instance profile: `aifo-control-plane-ec2-profile`.
- Session Manager log group: `/aifo/control-plane/session-manager`.
- Session Manager KMS key: `arn:aws:kms:us-west-2:350480401760:key/e36ac1c5-105c-42c1-92f9-06fcf02cb772`.
- Session Manager preferences document: `SSM-SessionManagerRunShell`.
- Scheduler group: `aifo-control-plane-host`.
- Scheduler role: `aifo-control-plane-scheduler-role`.
- Scheduler DLQ: `https://sqs.us-west-2.amazonaws.com/350480401760/aifo-control-plane-scheduler-dlq`.
- Scheduler start schedule: 08:00 Monday-Friday, `America/Los_Angeles`.
- Scheduler stop schedule: 16:00 Monday-Friday, `America/Los_Angeles`.
- EC2 instance: `i-0254a9e2fcbcdebd7`.

CloudTrail:

- Trail exists and is logging.
- Multi-Region enabled.
- Global service events enabled.
- Log-file validation enabled.
- Management events enabled for read and write events.
- Data event selectors are empty.
- S3 log bucket is not public.
- Bucket versioning, encryption, lifecycle, and public-access block are active.
- Bucket policy denies insecure transport.

Session Manager:

- CloudWatch log group exists.
- Retention is 30 days.
- KMS encryption is active with a customer-managed key.
- SSM Session Manager preferences document exists and is active.
- EC2 managed-node registration reached online during post-deployment verification.
- A Session Manager connectivity test succeeded after deployment.
- Session logs reached `/aifo/control-plane/session-manager`.
- The instance is currently stopped, so live Session Manager access requires an approved start.

EC2:

- EC2 instance exists: `i-0254a9e2fcbcdebd7`.
- Instance state: `stopped`.
- Instance type: `m7i-flex.2xlarge`.
- Root volume: 100 GiB encrypted gp3.
- No key pair exists on the instance.
- IMDSv2 is required.
- Termination protection is enabled.
- Security group exists with zero inbound rules and egress restricted to HTTPS plus VPC CIDR DNS.

Scheduler:

- Schedule group exists.
- DLQ exists with SQS-managed SSE and 14-day message retention.
- Scheduler IAM role exists.
- Scheduler inline policy is scoped to the EC2 instance ARN.
- Start and stop schedules target only `i-0254a9e2fcbcdebd7`.
- Start schedule: 08:00 Monday-Friday, `America/Los_Angeles`.
- Stop schedule: 16:00 Monday-Friday, `America/Los_Angeles`.
- Retry and dead-letter behavior are configured.

## Warnings And Drift

- No Terraform drift detected for the remote-state bootstrap root after apply.
- No Terraform drift detected for the GitHub OIDC bootstrap root after the final plan-role policy update.
- No Terraform drift detected for the control-plane root after final verification.
- `terraform-plan` GitHub environment exists but has no protection rules.
- `terraform-apply` GitHub environment exists but cannot enforce required reviewers on the current GitHub repository plan.
- GitHub required reviewers failed with a GitHub platform limitation; do not weaken AWS OIDC trust to compensate.
- Bootstrap Terraform state exists locally under ignored paths; do not commit local state or plan files.
- GitHub Actions emits Node 20 deprecation notices for upstream actions.

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

No additional deployment is approved.

Before any future apply:

1. Create a narrow ADR or approval packet.
2. Run local validation and a read-only Terraform plan.
3. Confirm the GitHub Terraform Plan drift gate is clean on `main`.
4. Obtain explicit approval for the exact resources and cost.
5. Do not create an apply workflow unless an enforceable approval boundary exists.
