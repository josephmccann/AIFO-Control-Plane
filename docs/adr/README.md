# Architecture Decision Records

ADRs record material infrastructure, security, cost, reliability, privacy, and product-fit decisions.

Use `0000-adr-template.md` for new records. Do not replace current-state docs or runbooks with ADRs; ADRs explain decisions, while runbooks explain operations.

## Index

| ADR | Status | Decision |
| --- | --- | --- |
| [0001](0001-product-gated-control-plane-scope.md) | Accepted | Scope the initial control plane to bootstrap and operator infrastructure, not product runtime hosting |
| [0002](0002-public-ipv4-ssm-only-control-host.md) | Accepted | Use a public IPv4 control host with zero inbound rules for initial egress |
| [0003](0003-native-s3-terraform-locking.md) | Accepted | Use native S3 lockfiles for Terraform state locking |
| [0004](0004-github-oidc-plan-apply-boundary.md) | Accepted | Use separate GitHub OIDC plan and apply roles scoped to exact environment subjects |
| [0005](0005-ec2-instance-selection.md) | Accepted | Default to `m7i-flex.2xlarge` only as the best x86 8 vCPU / 32 GiB candidate, with budget caveat |
| [0006](0006-session-manager-logging.md) | Accepted for first deployment | Use CloudWatch Logs with short retention for Session Manager logging |
| [0007](0007-manual-apply-boundary.md) | Accepted for initial deployment gate | Use manual IAM Identity Center applies until GitHub reviewer protection is available |
| [0008](0008-cloudtrail-management-events-baseline.md) | Accepted for first deployment | Create a multi-Region CloudTrail management-events baseline |
| [0009](0009-automated-ec2-operating-schedule.md) | Accepted for first deployment | Automate control-plane host start/stop with EventBridge Scheduler |
| [0010](0010-manual-host-patching.md) | Accepted for current single-host control plane | Use approval-gated manual patching and defer automation until scale or compliance justifies it |
| [0011](0011-github-native-engineering-operating-system.md) | Accepted by the 2026-07-15 founder mission directive | Use GitHub-native mission authority with a dependency-free, deny-by-default policy kernel |
