# Deployment Status

## Current Status

No AWS infrastructure has been deployed from this repository.

Current review PR: https://github.com/josephmccann/AIFO-Control-Plane/pull/2

## Last Validated State

Offline validation passed on 2026-07-14:

- `PATH="$PWD/build/bin:$PATH" ./scripts/validate.sh`
- `git diff --check`
- GitHub workflow YAML parse with Ruby `YAML.load_file`
- Markdown code-fence balance check
- Secret-pattern scan for AWS keys and private-key headers

Skipped:

- `shellcheck`, because it is not installed locally.

## External Resources Known To Exist

Reported by user:

- AWS account.
- Root MFA.
- IAM Identity Center.
- Human admin permission set `AIFO-Platform-Admin`.
- Manual AWS Budget target: $250/month.
- Private GitHub repository.

These resources are not imported into Terraform state.

## Apply Workflows

- No apply workflow exists.
- Future apply workflow must use protected environment `terraform-apply`.
- Human approval is required before creation or use.

## Next Deployment Gate

Bootstrap remote state and GitHub OIDC only after explicit human approval.
