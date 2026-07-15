# Developer Experience Workstream

## Objective

Make infrastructure work repeatable and understandable for a solo founder and future reviewers.

## Current Supports

- `scripts/validate.sh`.
- Pinned, checksum-verified local installation of `shellcheck` and `actionlint` through `scripts/install-dev-tools.sh`.
- Terraform root separation.
- README and architecture docs.
- Runbooks and ADR framework.

## Gaps

- No PR template.
- No automated Markdown linting.
- Product validation is not integrated into control-plane CI.

## Next Work

- Add PR template.
- Add product validation mapping before product runtime work.
