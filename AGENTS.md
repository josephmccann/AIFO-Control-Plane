# AGENTS.md

Operational rules for AI agents working in this repository.

## Scope

- Work only inside this repository.
- Treat all prior charter, product-context, founder-principle, and approval-gate instructions as binding unless the user explicitly changes them.
- Inspect the existing AI.FO product context before material infrastructure design. The current inventory is `docs/product-runtime-inventory.md`.
- Do not deploy infrastructure unless the user explicitly asks for deployment in a later task.
- Do not run `terraform apply`, `terraform destroy`, or any command that creates, updates, or deletes AWS resources.
- Do not create, rotate, print, or store long-lived AWS access keys.
- Do not commit secrets, `.tfstate` files, local plans, credentials, or generated build output.

## AWS Access Model

- Human access uses IAM Identity Center.
- The human admin permission set is `AIFO-Platform-Admin`.
- GitHub Actions uses OIDC role assumption.
- GitHub Actions must not use static AWS access keys.
- GitHub Actions plan and apply roles must be separate.
- OIDC trust must be scoped to the exact repository and protected GitHub environment.
- Systems Manager Session Manager is the only intended administrative access path for EC2 hosts.
- Public SSH is not allowed.

## Infrastructure Guardrails

- Default AWS region: `us-west-2`.
- Default monthly budget target: `$250`.
- Budget management is disabled by default because a budget exists manually.
- Initial network shape is one public subnet in one Availability Zone.
- Public IPv4 is allowed only for outbound internet access, with no inbound security-group rules.
- EC2 instance metadata must require IMDSv2.
- EC2 administration must remain SSM-only.
- Terraform state must not be committed.
- Terraform S3 backend locking should use native S3 lockfiles when supported.

## Safe Validation Commands

These commands are allowed because they do not deploy or mutate AWS resources:

```bash
terraform fmt -check -recursive terraform
terraform -chdir=terraform/environments/control-plane init -backend=false -input=false
terraform -chdir=terraform/environments/control-plane validate -no-color
bash -n scripts/*.sh
```

Use `scripts/validate.sh` as the standard local validation entrypoint.

## Change Expectations

- Keep changes narrow and consistent with the existing structure.
- Update docs when changing security, networking, IAM, or deployment behavior.
- Add or update ADRs under `docs/adr/` for material decisions.
- Keep `memory/` and `workqueue/` current for long-running work.
- Prefer explicit deny-by-default infrastructure patterns.
- Treat cost, access, auditability, and rollback as first-class design constraints.
- Do not build product runtime infrastructure until the current product requirement and migration decision are documented.
