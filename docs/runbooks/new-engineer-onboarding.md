# New Engineer Onboarding

## Read First

1. `AGENTS.md`
2. `README.md`
3. `docs/product-runtime-inventory.md`
4. `docs/control-plane-fit-assessment.md`
5. `docs/security-model.md`
6. `docs/adr/README.md`
7. `workqueue/README.md`

## Local Setup

Install:

- Terraform `>= 1.10.0`
- GitHub CLI
- AWS CLI
- `shellcheck` and `actionlint` when available

Validate:

```bash
./scripts/validate.sh
git diff --check
```

## Working Rules

- Branch from `main`.
- Do not deploy from a local branch without explicit approval.
- Keep ADRs and runbooks updated with material changes.
- Treat AI.FO-Demo as the product source of truth for runtime requirements.
- Report skipped validation explicitly.
