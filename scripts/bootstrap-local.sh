#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_ROOTS=(
  "$ROOT_DIR/terraform/bootstrap/remote-state"
  "$ROOT_DIR/terraform/bootstrap/github-oidc"
  "$ROOT_DIR/terraform/environments/control-plane"
)

require_tool() {
  local tool="$1"
  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "Missing required tool: $tool" >&2
    return 1
  fi
}

require_tool terraform

for tf_dir in "${TF_ROOTS[@]}"; do
  echo "Initializing Terraform locally without a backend: ${tf_dir#$ROOT_DIR/}"
  terraform -chdir="$tf_dir" init -backend=false -input=false
done

echo
echo "Local bootstrap complete."
echo "No AWS resources were created or changed."
echo
echo "Next steps:"
echo "  1. Review terraform/environments/control-plane/terraform.tfvars.example"
echo "  2. Run ./scripts/validate.sh"
echo "  3. Bootstrap remote state and OIDC only through an approved process"
