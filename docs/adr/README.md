# Architecture Decision Records

ADRs record material infrastructure, security, cost, reliability, privacy, and product-fit decisions.

Use `0000-adr-template.md` for new records. Do not replace current-state docs or runbooks with ADRs; ADRs explain decisions, while runbooks explain operations.

## Index

| ADR | Status | Decision |
| --- | --- | --- |
| [0001](0001-product-gated-control-plane-scope.md) | Accepted | Scope the initial control plane to bootstrap and operator infrastructure, not product runtime hosting |
| [0002](0002-public-ipv4-ssm-only-control-host.md) | Accepted | Use a public IPv4 control host with zero inbound rules for initial egress |
| [0003](0003-native-s3-terraform-locking.md) | Accepted | Use native S3 lockfiles for Terraform state locking |
| [0004](0004-github-oidc-plan-apply-boundary.md) | Accepted | Use separate GitHub OIDC plan and apply roles scoped to protected environments |
| [0005](0005-ec2-instance-selection.md) | Accepted | Default to `m7i-flex.2xlarge` only as the best x86 8 vCPU / 32 GiB candidate, with budget caveat |
| [0006](0006-session-manager-logging.md) | Accepted for design | Use CloudWatch Logs with short retention for initial Session Manager logging design |
