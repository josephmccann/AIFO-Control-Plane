# GitHub OIDC Bootstrap

Creates the GitHub Actions OIDC provider and separate AWS IAM roles for Terraform plan and future apply.

Trust policies are restricted to:

- The exact GitHub repository.
- A named protected GitHub environment for plan.
- A separate named protected GitHub environment for apply.

There is no apply workflow in this repository yet. The apply role exists for the future approval boundary and should receive least-privilege infrastructure permissions only when an approved apply process is added.

The plan role receives:

- S3 state and lockfile access for the configured backend object.
- A custom read policy for the initial control-plane resource graph.

`plan_role_additional_policy_arns` exists as an explicit reviewed escape hatch if the first real plan shows a missing read action. Do not attach AWS managed `ReadOnlyAccess` by default.
