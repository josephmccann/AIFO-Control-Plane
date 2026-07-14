# Terraform Bootstrap

Bootstrap Terraform is separated from the deployable control-plane environment because it creates account-level prerequisites:

- `remote-state/`: S3 bucket for Terraform state with versioning, encryption, Block Public Access, and native S3 lockfile support.
- `github-oidc/`: GitHub OIDC provider plus separate plan and apply IAM roles.

Run these roots only through an approved bootstrap process using IAM Identity Center or another approved short-lived credential path. Do not use long-lived AWS keys.

The control-plane environment should use the remote state bucket with:

```hcl
use_lockfile = true
```

DynamoDB locking is intentionally not part of the initial backend design.
