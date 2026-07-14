# Developer Experience Workstream

## Objective

Make infrastructure work repeatable and understandable for a solo founder and future reviewers.

## Current Supports

- `scripts/validate.sh`.
- Terraform root separation.
- README and architecture docs.
- Runbooks and ADR framework.

## Gaps

- `shellcheck` and `actionlint` are optional local tools.
- No PR template.
- No automated Markdown linting.
- Product validation is not integrated into control-plane CI.

## Next Work

- Add PR template.
- Add optional lint tooling guidance.
- Add product validation mapping before product runtime work.
