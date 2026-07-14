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

Bootstrap and apply steps are documented in [../docs/runbooks/bootstrap.md](../docs/runbooks/bootstrap.md). No bootstrap root should be applied without explicit human approval.

The initial control-plane host defaults to `m7i-flex.2xlarge`, but current AWS pricing review shows continuous operation exceeds the $250 monthly budget before storage and public IPv4. Review [../docs/ec2-instance-recommendation.md](../docs/ec2-instance-recommendation.md) before first apply.
