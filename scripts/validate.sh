#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_ROOTS=(
  "$ROOT_DIR/terraform/bootstrap/remote-state"
  "$ROOT_DIR/terraform/bootstrap/github-oidc"
  "$ROOT_DIR/terraform/environments/control-plane"
)
MISSING_LINTERS=()

echo "Running Engineering OS tests."
python3 -m unittest discover -s "$ROOT_DIR/tests/engineering_os" -p 'test_*.py' -v

echo "Checking Engineering OS Python syntax."
python3 -m py_compile "$ROOT_DIR"/engineering_os/*.py

echo "Checking shell syntax."
SHELL_FILES=()
PYTHON_FILES=()
while IFS= read -r -d '' file; do
  first_line=""
  IFS= read -r first_line < "$file" || true
  case "$file" in
    *.sh) SHELL_FILES+=("$file") ;;
    *.py) PYTHON_FILES+=("$file") ;;
    *)
      case "$first_line" in
        '#!'*bash*|'#!'*'/sh'|'#!'*'/dash'|'#!'*'/ksh') SHELL_FILES+=("$file") ;;
        '#!'*python*) PYTHON_FILES+=("$file") ;;
        *)
          if [[ -x "$file" ]]; then
            echo "Unclassified executable script: ${file#"$ROOT_DIR"/}" >&2
            exit 1
          fi
          ;;
      esac
      ;;
  esac
done < <(find "$ROOT_DIR/scripts" "$ROOT_DIR/tests" -type f -print0)

if (( ${#SHELL_FILES[@]} > 0 )); then
  bash -n "${SHELL_FILES[@]}"
fi

if (( ${#PYTHON_FILES[@]} > 0 )); then
  python3 -m py_compile "${PYTHON_FILES[@]}"
fi

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

if command -v shellcheck >/dev/null 2>&1; then
  echo "Running shellcheck."
  if (( ${#SHELL_FILES[@]} > 0 )); then
    shellcheck "${SHELL_FILES[@]}"
  fi
else
  MISSING_LINTERS+=("shellcheck")
fi

if command -v actionlint >/dev/null 2>&1; then
  echo "Running actionlint."
  actionlint "$ROOT_DIR"/.github/workflows/*.yml
else
  MISSING_LINTERS+=("actionlint")
fi

if (( ${#MISSING_LINTERS[@]} > 0 )); then
  echo "Missing lint tools: ${MISSING_LINTERS[*]}. Install pinned versions with ./scripts/install-dev-tools.sh."
fi

echo "Validation complete."
