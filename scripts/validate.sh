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
  echo "Initializing Terraform without backend: ${tf_dir#$ROOT_DIR/}"
  terraform -chdir="$tf_dir" init -backend=false -input=false

  echo "Validating Terraform configuration: ${tf_dir#$ROOT_DIR/}"
  terraform -chdir="$tf_dir" validate -no-color
done

echo "Checking shell syntax."
bash -n "$ROOT_DIR"/scripts/*.sh

if command -v shellcheck >/dev/null 2>&1; then
  echo "Running shellcheck."
  shellcheck "$ROOT_DIR"/scripts/*.sh
else
  echo "shellcheck not found; skipping shell lint."
fi

echo "Validation complete."
