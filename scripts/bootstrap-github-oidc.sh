#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/build"

usage() {
  cat <<'USAGE'
Render GitHub Actions OIDC trust policies for review.

This script does not call AWS and does not create resources.

Required environment variables:
  AWS_ACCOUNT_ID       AWS account ID
  GITHUB_REPOSITORY    GitHub repository in owner/name format

Optional environment variables:
  PLAN_ROLE_NAME       Plan role name for display only, default AIFO-GitHubActions-Terraform-Plan
  APPLY_ROLE_NAME      Apply role name for display only, default AIFO-GitHubActions-Terraform-Apply
  PLAN_ENVIRONMENT     Protected GitHub environment for plan, default terraform-plan
  APPLY_ENVIRONMENT    Protected GitHub environment for apply, default terraform-apply

Example:
  AWS_ACCOUNT_ID=123456789012 \
  GITHUB_REPOSITORY=owner/AIFO-Control-Plane \
  ./scripts/bootstrap-github-oidc.sh
USAGE
}

AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-}"
GITHUB_REPOSITORY="${GITHUB_REPOSITORY:-}"
PLAN_ROLE_NAME="${PLAN_ROLE_NAME:-AIFO-GitHubActions-Terraform-Plan}"
APPLY_ROLE_NAME="${APPLY_ROLE_NAME:-AIFO-GitHubActions-Terraform-Apply}"
PLAN_ENVIRONMENT="${PLAN_ENVIRONMENT:-terraform-plan}"
APPLY_ENVIRONMENT="${APPLY_ENVIRONMENT:-terraform-apply}"

if [[ -z "$AWS_ACCOUNT_ID" || -z "$GITHUB_REPOSITORY" ]]; then
  usage >&2
  exit 1
fi

mkdir -p "$OUT_DIR"

render_policy() {
  local role_name="$1"
  local environment_name="$2"
  local output_file="$3"

  cat >"$output_file" <<JSON
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${AWS_ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:${GITHUB_REPOSITORY}:environment:${environment_name}"
        }
      }
    }
  ]
}
JSON
  echo "Rendered trust policy for role: $role_name"
  echo "Output: $output_file"
}

PLAN_OUT_FILE="$OUT_DIR/github-oidc-plan-trust-policy.json"
APPLY_OUT_FILE="$OUT_DIR/github-oidc-apply-trust-policy.json"

render_policy "$PLAN_ROLE_NAME" "$PLAN_ENVIRONMENT" "$PLAN_OUT_FILE"
render_policy "$APPLY_ROLE_NAME" "$APPLY_ENVIRONMENT" "$APPLY_OUT_FILE"
echo
echo "No AWS resources were created or changed."
echo "Review the generated policy before using it in an approved IAM bootstrap process."
