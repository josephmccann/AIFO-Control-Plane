#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_ROOTS=(
  "$ROOT_DIR/terraform/bootstrap/remote-state"
  "$ROOT_DIR/terraform/bootstrap/github-oidc"
  "$ROOT_DIR/terraform/environments/control-plane"
)
classify_shebang() {
  local first_line="$1"

  if [[ "$first_line" =~ ^\#!(/usr/bin/env[[:space:]]+)?(bash|sh|dash|ksh)$ ]] \
      || [[ "$first_line" =~ ^\#!(/usr)?/bin/(bash|sh|dash|ksh)$ ]]; then
    echo "shell"
    return 0
  fi
  if [[ "$first_line" =~ ^\#!(/usr/bin/env[[:space:]]+)?python(3([.][0-9]+)?)?$ ]] \
      || [[ "$first_line" =~ ^\#!(/usr)?/bin/python(3([.][0-9]+)?)?$ ]]; then
    echo "python"
    return 0
  fi
  return 1
}

classify_script() {
  local file="$1"
  first_line=""
  extension_class=""
  shebang_class=""
  if [[ -L "$file" ]]; then
    echo "Symlinked validation path is not allowed: ${file#"$ROOT_DIR"/}" >&2
    return 1
  fi
  IFS= read -r first_line < "$file" || true
  case "$file" in
    *.sh) extension_class="shell" ;;
    *.py) extension_class="python" ;;
  esac

  if [[ "$first_line" == '#!'* ]]; then
    shebang_class="$(classify_shebang "$first_line" || true)"
    if [[ -z "$shebang_class" ]]; then
      echo "Unclassified executable script: ${file#"$ROOT_DIR"/}" >&2
      return 1
    fi
  fi
  if [[ -n "$extension_class" && -n "$shebang_class" && "$extension_class" != "$shebang_class" ]]; then
    echo "Conflicting script classification: ${file#"$ROOT_DIR"/}" >&2
    return 1
  fi
  if [[ -n "$extension_class" ]]; then
    echo "$extension_class"
  elif [[ -n "$shebang_class" ]]; then
    echo "$shebang_class"
  elif [[ -x "$file" ]]; then
    echo "Unclassified executable script: ${file#"$ROOT_DIR"/}" >&2
    return 1
  else
    echo "ignore"
  fi
}

main() {
  local file
  local classification
  local -a shell_files=()
  local -a python_files=()
  local -a missing_linters=()

  echo "Running Engineering OS tests."
  python3 -m unittest discover -s "$ROOT_DIR/tests/engineering_os" -p 'test_*.py' -v

  echo "Checking Engineering OS Python syntax."
  python3 -m py_compile "$ROOT_DIR"/engineering_os/*.py

  echo "Classifying validation files."
  while IFS= read -r -d '' file; do
    classification="$(classify_script "$file")"
    case "$classification" in
      shell) shell_files+=("$file") ;;
      python) python_files+=("$file") ;;
      ignore) ;;
      *)
        echo "Internal classification error: ${file#"$ROOT_DIR"/}" >&2
        return 1
        ;;
    esac
  done < <(find "$ROOT_DIR/scripts" "$ROOT_DIR/tests" \( -type f -o -type l \) -print0)

  echo "Checking shell syntax."
  if (( ${#shell_files[@]} > 0 )); then
    bash -n "${shell_files[@]}"
  fi

  echo "Checking classified Python syntax."
  if (( ${#python_files[@]} > 0 )); then
    python3 -m py_compile "${python_files[@]}"
  fi

  if ! command -v terraform >/dev/null 2>&1; then
    echo "Terraform is required for validation." >&2
    return 1
  fi

  echo "Checking Terraform formatting."
  terraform fmt -check -recursive "$ROOT_DIR/terraform"

  for tf_dir in "${TF_ROOTS[@]}"; do
    echo "Initializing Terraform without backend: ${tf_dir#"$ROOT_DIR"/}"
    terraform -chdir="$tf_dir" init -backend=false -input=false

    echo "Validating Terraform configuration: ${tf_dir#"$ROOT_DIR"/}"
    terraform -chdir="$tf_dir" validate -no-color
  done

  if [[ "${CI:-}" == "true" ]] \
      && { ! command -v shellcheck >/dev/null 2>&1 || ! command -v actionlint >/dev/null 2>&1; }; then
    "$ROOT_DIR/scripts/install-dev-tools.sh"
    PATH="$ROOT_DIR/build/bin:$PATH"
    export PATH
  fi

  for tool in shellcheck actionlint; do
    if ! command -v "$tool" >/dev/null 2>&1; then
      missing_linters+=("$tool")
    fi
  done
  if (( ${#missing_linters[@]} > 0 )); then
    echo "Missing lint tools: ${missing_linters[*]}. Install pinned versions with ./scripts/install-dev-tools.sh." >&2
    return 1
  fi

  echo "Running shellcheck."
  if (( ${#shell_files[@]} > 0 )); then
    shellcheck "${shell_files[@]}"
  fi

  echo "Running actionlint."
  actionlint "$ROOT_DIR"/.github/workflows/*.yml

  echo "Validation complete."
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
