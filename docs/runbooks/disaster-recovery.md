# Disaster Recovery Runbook

## Current Scope

Bootstrap infrastructure has been deployed. Disaster recovery currently covers Git repository history, Terraform configuration, the S3 Terraform state bucket, and GitHub OIDC bootstrap resources. The control-plane host and product runtime have not been deployed.

## Recovery Priorities

1. Preserve repository history.
2. Preserve Terraform state.
3. Preserve audit evidence.
4. Restore administrative access through IAM Identity Center and SSM.
5. Recreate infrastructure from Terraform only after plan review.

## Terraform State Loss

If the S3 state object is deleted or corrupted after bootstrap:

1. Stop all Terraform workflows.
2. Identify the affected backend key.
3. Inspect S3 object versions.
4. Restore the last known-good version after approval.
5. Run `terraform plan -refresh-only` to detect drift.

## GitHub OIDC Failure

If GitHub Actions cannot assume the plan role:

1. Verify protected environment name.
2. Verify repository variables.
3. Verify OIDC provider exists.
4. Verify role trust subject:
   - `repo:josephmccann/AIFO-Control-Plane:environment:terraform-plan`
5. Use IAM Identity Center for local read-only planning if needed.

## EC2 Host Failure

If the host is unreachable through SSM after deployment:

1. Confirm instance is running.
2. Confirm SSM agent status if visible.
3. Confirm outbound HTTPS egress.
4. Confirm IAM instance profile has `AmazonSSMManagedInstanceCore`.
5. Replace the instance through Terraform if recovery is faster and no data is local-only.

Do not add SSH ingress as an emergency workaround.
