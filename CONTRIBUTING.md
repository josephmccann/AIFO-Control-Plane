# Contributing

This repository manages the AI.FO AWS control plane. Treat every change as infrastructure work for a product that handles financial data, accounting integrations, AI narration boundaries, and founder decision support.

## Ground Rules

- Work from a dedicated branch; do not push directly to `main`.
- Do not run `terraform apply`, `terraform destroy`, or AWS-mutating commands without explicit human approval.
- Do not create, store, rotate, print, or commit long-lived AWS credentials.
- Do not commit secrets, `.tfstate`, plan files, local `.tfvars`, `.env`, generated credentials, or session logs.
- Keep product context current by reviewing `docs/product-runtime-inventory.md` before material infrastructure design.
- Update documentation and ADRs in the same change as architecture, IAM, networking, state, security, or cost behavior changes.

## Required Local Validation

Install the repository-pinned lint tools into ignored `build/bin`:

```bash
./scripts/install-dev-tools.sh
```

Run these before commit:

```bash
PATH="$PWD/build/bin:$PATH" ./scripts/validate.sh
PATH="$PWD/build/bin:$PATH" bash tests/install-dev-tools-test.sh
git diff --check
ruby -ryaml -e 'ARGV.each { |path| YAML.load_file(path); puts "#{path}: ok" }' .github/workflows/*.yml
```

`scripts/validate.sh` prints the installer command if either linter is absent. If a check is skipped, document the skip in the PR.

## Pull Request Expectations

Every PR should identify:

- product requirement or operational need supported;
- affected founder principle or security boundary;
- Terraform roots changed;
- validation performed;
- skipped validation and reason;
- cost effect;
- rollback path;
- deployment or approval gate, if any.

## Commit Style

Use conventional commit messages such as:

- `docs: add bootstrap runbook`
- `chore: tighten terraform plan role policy`
- `feat: add session logging module`

Keep commits logically scoped. Do not combine unrelated architecture, formatting, and documentation changes unless they are part of one coherent decision.

## Decision Records

Material decisions require an ADR under `docs/adr/`. Use `docs/adr/0000-adr-template.md`.

Material decisions include:

- AWS account, IAM, OIDC, trust policy, or permission boundaries;
- network topology or ingress/egress policy;
- Terraform state and backend behavior;
- product runtime, database, storage, secrets, or observability architecture;
- recurring cost changes;
- recovery, backup, retention, audit, or privacy policy;
- any exception to SSM-only, no-public-ingress, no-static-keys, or deterministic-product-boundary requirements.

## External Research

For significant architecture decisions, prefer official vendor documentation:

- AWS documentation and AWS pricing sources;
- HashiCorp Terraform documentation;
- GitHub Actions documentation;
- official OpenAI, Anthropic, Google, Intuit, Cloudflare, PostgreSQL, and relevant vendor docs.

Blogs can inform options but should not be the sole basis for a material decision.
