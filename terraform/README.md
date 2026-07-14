# Terraform

Terraform is organized by bootstrap roots, deployable environments, and reusable modules.

```text
terraform/
├── bootstrap/
│   ├── github-oidc/
│   └── remote-state/
├── environments/
│   └── control-plane/
└── modules/
    ├── budget/
    ├── compute/
    └── network/
```

The `control-plane` environment is the first deployable unit. Local validation should use `init -backend=false` until the remote state backend is created through an approved bootstrap process.

The intended backend is S3 with native lockfiles:

```hcl
use_lockfile = true
```

DynamoDB locking is not part of the initial backend.
