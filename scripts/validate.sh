#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_ROOTS=(
  "$ROOT_DIR/terraform/bootstrap/remote-state"
  "$ROOT_DIR/terraform/bootstrap/github-oidc"
  "$ROOT_DIR/terraform/environments/control-plane"
)

if ! command -v terraform >/dev/null 2>&1; then
  echo "Terraform is required for validation." >&2
  exit 1
fi

echo "Checking Terraform formatting."
terraform fmt -check -recursive "$ROOT_DIR/terraform"

for tf_dir in "${TF_ROOTS[@]}"; do
  echo "Initializing Terraform without backend: ${tf_dir#"$ROOT_DIR"/}"
  terraform -chdir="$tf_dir" init -backend=false -input=false

  echo "Validating Terraform configuration: ${tf_dir#"$ROOT_DIR"/}"
  terraform -chdir="$tf_dir" validate -no-color
done

echo "Checking shell syntax."
bash -n "$ROOT_DIR"/scripts/*.sh "$ROOT_DIR"/tests/*.sh

if command -v shellcheck >/dev/null 2>&1; then
  echo "Running shellcheck."
  shellcheck "$ROOT_DIR"/scripts/*.sh "$ROOT_DIR"/tests/*.sh
else
  echo "shellcheck not found; install pinned lint tools with ./scripts/install-dev-tools.sh."
fi

if command -v actionlint >/dev/null 2>&1; then
  echo "Running actionlint."
  actionlint "$ROOT_DIR"/.github/workflows/*.yml
else
  echo "actionlint not found; install pinned lint tools with ./scripts/install-dev-tools.sh."
fi

echo "Validation complete."
