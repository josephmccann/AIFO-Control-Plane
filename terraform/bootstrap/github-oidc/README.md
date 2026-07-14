# GitHub OIDC Bootstrap

Creates the GitHub Actions OIDC provider and separate AWS IAM roles for Terraform plan and future apply.

Trust policies are restricted to:

- The exact GitHub repository.
- A named protected GitHub environment for plan.
- A separate named protected GitHub environment for apply.

There is no apply workflow in this repository yet. The apply role exists for the future approval boundary and should receive least-privilege infrastructure permissions only when an approved apply process is added.
