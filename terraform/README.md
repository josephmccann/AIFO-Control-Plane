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
    ├── audit/
    ├── budget/
    ├── compute/
    ├── scheduler/
    ├── session-manager-logging/
    └── network/
```

The `control-plane` environment is the first deployable unit. Terraform remote state has been bootstrapped, but local validation can still use `init -backend=false` when remote state is not needed.

The intended backend is S3 with native lockfiles:

```hcl
use_lockfile = true
```

DynamoDB locking is not part of the initial backend.

Bootstrap and apply steps are documented in [../docs/runbooks/bootstrap.md](../docs/runbooks/bootstrap.md). The remote-state and GitHub OIDC bootstrap roots were applied after explicit human approval on 2026-07-14. Do not run the control-plane environment apply without separate approval.

The initial control-plane host defaults to `m7i-flex.2xlarge` with a 100 GiB encrypted gp3 root volume, but current AWS pricing review shows continuous operation exceeds the $250 monthly budget after compute, storage, and public IPv4 are counted. The control-plane environment now also includes CloudTrail management events, Session Manager logging, and EventBridge Scheduler start/stop automation. Review [../docs/ec2-instance-recommendation.md](../docs/ec2-instance-recommendation.md) and [../docs/runbooks/ec2-start-stop.md](../docs/runbooks/ec2-start-stop.md) before first apply.
