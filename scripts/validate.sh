#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TF_ROOTS=(
  "$ROOT_DIR/terraform/bootstrap/remote-state"
  "$ROOT_DIR/terraform/bootstrap/github-oidc"
  "$ROOT_DIR/terraform/environments/control-plane"
)
DISCOVERY_STATUS_PREFIX="AIFO_VALIDATION_DISCOVERY_STATUS:"
SHELL_FILES=()
PYTHON_FILES=()
VALIDATION_RUNTIME_PATHS=(
  "scripts/validate.sh"
  "scripts/engineering-os/validate-activation-closure"
  "docs/engineering-os/ACTIVATION_DEPENDENCY_CLOSURE.json"
  "outputs/mission-32-closure-records-ready.json"
  "outputs/mission-32-validation/exact-head-ci-ready.log"
  "outputs/mission-32-review-a-ready.md"
  "outputs/mission-32-review-b-ready.md"
  "outputs/mission-32-reconciliation-ready.md"
  "schemas/engineering-os/activation-closure.schema.json"
  "engineering_os/schema.py"
  "engineering_os/errors.py"
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
  elif [[ "${file##*/}" != *.* ]]; then
    echo "Unclassified script path: ${file#"$ROOT_DIR"/}" >&2
    return 1
  else
    echo "ignore"
  fi
}

verify_tracked_validation_state() {
  if ! git -C "$ROOT_DIR" diff --quiet HEAD -- "${VALIDATION_RUNTIME_PATHS[@]}" \
      || ! git -C "$ROOT_DIR" diff --cached --quiet HEAD -- "${VALIDATION_RUNTIME_PATHS[@]}"; then
    echo "Validation changed the tracked closure runtime surface." >&2
    return 1
  fi
}

discover_validation_paths() {
  local status

  if find "$ROOT_DIR/scripts" "$ROOT_DIR/tests" \( -type f -o -type l \) -print0; then
    status=0
  else
    status=$?
  fi
  printf '%s%s\0' "$DISCOVERY_STATUS_PREFIX" "$status"
}

classify_discovered_paths() {
  local file
  local classification
  local discovery_status=""

  while IFS= read -r -d '' file; do
    case "$file" in
      "$DISCOVERY_STATUS_PREFIX"*)
        discovery_status="${file#"$DISCOVERY_STATUS_PREFIX"}"
        continue
        ;;
    esac
    classification="$(classify_script "$file")"
    case "$classification" in
      shell) SHELL_FILES+=("$file") ;;
      python) PYTHON_FILES+=("$file") ;;
      ignore) ;;
      *)
        echo "Internal classification error: ${file#"$ROOT_DIR"/}" >&2
        return 1
        ;;
    esac
  done < <(discover_validation_paths)

  if [[ ! "$discovery_status" =~ ^[0-9]+$ ]]; then
    echo "Validation file discovery did not produce a terminal status." >&2
    return 1
  fi
  if (( discovery_status != 0 )); then
    echo "Validation file discovery failed with status $discovery_status." >&2
    return 1
  fi
}

main() {
  local -a missing_linters=()

  SHELL_FILES=()
  PYTHON_FILES=()

  echo "Running Engineering OS tests."
  python3 -m unittest discover -s "$ROOT_DIR/tests/engineering_os" -p 'test_*.py' -v
  verify_tracked_validation_state

  echo "Checking Engineering OS Python syntax."
  python3 -m py_compile "$ROOT_DIR"/engineering_os/*.py

  echo "Classifying validation files."
  classify_discovered_paths

  echo "Checking shell syntax."
  if (( ${#SHELL_FILES[@]} > 0 )); then
    bash -n "${SHELL_FILES[@]}"
  fi

  echo "Checking classified Python syntax."
  if (( ${#PYTHON_FILES[@]} > 0 )); then
    python3 -m py_compile "${PYTHON_FILES[@]}"
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
  if (( ${#SHELL_FILES[@]} > 0 )); then
    shellcheck "${SHELL_FILES[@]}"
  fi

  echo "Running actionlint."
  actionlint "$ROOT_DIR"/.github/workflows/*.yml

  verify_tracked_validation_state
  echo "Replaying the governed activation closure."
  closure_head="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["final"]["sha"])' \
    "$ROOT_DIR/docs/engineering-os/ACTIVATION_DEPENDENCY_CLOSURE.json")"
  materialization_head="$(git rev-parse HEAD)"
  "$ROOT_DIR/scripts/engineering-os/validate-activation-closure" \
    "$ROOT_DIR/docs/engineering-os/ACTIVATION_DEPENDENCY_CLOSURE.json" \
    "$closure_head" "$materialization_head"

  echo "Validation complete."
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
