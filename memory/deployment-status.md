# Deployment Status

## Current Status

Remote-state and GitHub OIDC bootstrap are complete in AWS account `350480401760`.

The GitHub OIDC plan-role read policy update was applied on 2026-07-14 after explicit approval. The apply role was not modified.

The hardened control-plane apply was attempted on 2026-07-14 after explicit approval and stopped on an AWS `PendingVerification` error during EC2 launch. Several prerequisite audit, logging, network, and IAM resources were created before the EC2 launch failure. No EC2 instance, EBS root volume, Scheduler start schedule, Scheduler stop schedule, Scheduler inline policy, product runtime resources, apply workflow, or apply-role infrastructure permissions were created.

GitHub planning configuration is complete:

- `terraform-plan` environment exists and is intentionally unblocked for automated planning.
- `terraform-apply` environment exists, but required reviewers are unavailable on the current GitHub repository plan.
- Repository variables are configured for the plan workflow.
- The plan workflow successfully assumed `arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Plan` through OIDC.
- `terraform-apply` must remain unused; no apply workflow may be created under the current GitHub approval limitation.

## Last Validated State

Bootstrap validation passed on 2026-07-14:

- `PATH="$PWD/build/bin:$PATH" AWS_PROFILE=aifo-admin AWS_SDK_LOAD_CONFIG=1 ./scripts/validate.sh`
- Refreshed remote-state plan produced only approved creates: `6 to add, 0 to change, 0 to destroy`.
- Refreshed GitHub OIDC plan produced only approved creates: `8 to add, 0 to change, 0 to destroy`.
- Post-apply remote-state plan exit code: `0`.
- Post-apply GitHub OIDC plan exit code: `0`.
- First GitHub control-plane plan run succeeded: https://github.com/josephmccann/AIFO-Control-Plane/actions/runs/29371131579.

Pre-deployment hardening PR #5 was squash-merged at `c4c998bb10289c91dc47013a0069adc0961b461f`.

OIDC read-policy update:

- Refreshed plan: `0 to add, 1 to change, 0 to destroy`.
- Applied change: `aws_iam_policy.plan_read_access`.
- Result: `0 added, 1 changed, 0 destroyed`.
- Default policy version after apply: `v2`.
- Read-only verification: passed; actions are limited to `Get`, `List`, `Describe`, `View`, `sts:GetCallerIdentity`, and tag read actions.
- Apply role verification: still has only `AIFO-GitHubActions-Terraform-StateAccess` attached and no inline policies.

Hardened control-plane apply:

- Refreshed plan: `33 to add, 0 to change, 0 to destroy`.
- Saved plan: `/tmp/aifo-control-plane-hardened.tfplan`.
- Apply result: partial; stopped during `module.compute.aws_instance.host` creation.
- AWS error: `PendingVerification`, indicating AWS is validating access to launch regional resources in `us-west-2`.
- Post-failure plan: `4 to add, 0 to change, 0 to destroy`.
- Remaining resources in the plan:
  - `module.compute.aws_instance.host`
  - `module.scheduler.aws_iam_role_policy.scheduler`
  - `module.scheduler.aws_scheduler_schedule.start_host`
  - `module.scheduler.aws_scheduler_schedule.stop_host`

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
- Plan read policy default version `v2` is read-only and includes refresh access for CloudTrail, KMS, CloudWatch Logs, EventBridge Scheduler, SQS, SSM, S3, EC2, IAM read APIs, Budgets read, STS identity, and tag reads.

Partial control-plane resources:

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

CloudTrail:

- Trail exists and is logging.
- Latest delivery succeeded at `2026-07-14T23:09:07Z`.
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
- No EC2 instance exists, so SSM managed-node registration and session connectivity could not be tested.

EC2:

- No control-plane EC2 instance was created.
- No control-plane EBS root volume was created.
- No control-plane key pair was created.
- Security group exists with zero inbound rules and egress restricted to HTTPS plus VPC CIDR DNS.

Scheduler:

- Schedule group exists.
- DLQ exists with SQS-managed SSE and 14-day message retention.
- Scheduler IAM role exists.
- Start and stop schedules were not created because the EC2 instance ID was not available.
- Scheduler inline policy was not created because it is scoped to the EC2 instance ARN.

## Warnings And Drift

- No Terraform drift detected for the remote-state bootstrap root after apply.
- GitHub OIDC bootstrap changed exactly one approved resource: `aws_iam_policy.plan_read_access`.
- Hardened control-plane environment is not converged; post-failure plan shows `4 to add, 0 to change, 0 to destroy`.
- AWS account regional resource validation blocked EC2 launch in `us-west-2`.
- CloudTrail latest delivery attempt succeeded at `2026-07-14T23:09:07Z`.
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

Resolve the AWS `PendingVerification` account/region validation blocker before any additional control-plane apply.

Required next actions:

1. Wait for AWS account validation to complete or open an AWS Support account-management case if it persists.
2. Re-run a read-only Terraform plan after validation clears.
3. Expected next plan, if nothing else changes: `4 to add, 0 to change, 0 to destroy`.
4. Review the residual plan before any further apply.
5. Do not run another control-plane apply until a renewed explicit approval gate.
6. After the EC2 instance is created in a future approved step, verify SSM online registration, perform one Session Manager connectivity test, then stop the instance manually.
