#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# shellcheck source=../scripts/install-dev-tools.sh
# ROOT_DIR is resolved from this test's location.
# shellcheck disable=SC1091
source "$ROOT_DIR/scripts/install-dev-tools.sh"

assert_equal() {
  local expected="$1"
  local actual="$2"
  local message="$3"

  if [[ "$actual" != "$expected" ]]; then
    printf 'FAIL: %s\nexpected: %s\nactual:   %s\n' "$message" "$expected" "$actual" >&2
    exit 1
  fi
}

assert_fails() {
  local message="$1"
  shift

  if "$@" >/dev/null 2>&1; then
    printf 'FAIL: %s\n' "$message" >&2
    exit 1
  fi
}

assert_file_contains() {
  local file="$1"
  local expected="$2"
  local message="$3"

  if ! grep -Fq "$expected" "$file"; then
    printf 'FAIL: %s\nmissing text: %s\n' "$message" "$expected" >&2
    exit 1
  fi
}

assert_file_occurrences() {
  local file="$1"
  local expected_text="$2"
  local expected_count="$3"
  local message="$4"
  local actual_count

  actual_count="$(grep -Fc "$expected_text" "$file" || true)"
  assert_equal "$expected_count" "$actual_count" "$message"
}

assert_equal \
  "actionlint_1.7.12_darwin_amd64.tar.gz|5b44c3bc2255115c9b69e30efc0fecdf498fdb63c5d58e17084fd5f16324c644" \
  "$(actionlint_asset darwin amd64)" \
  "actionlint Darwin amd64 mapping"
assert_equal \
  "actionlint_1.7.12_darwin_arm64.tar.gz|aba9ced2dee8d27fecca3dc7feb1a7f9a52caefa1eb46f3271ea66b6e0e6953f" \
  "$(actionlint_asset darwin arm64)" \
  "actionlint Darwin arm64 mapping"
assert_equal \
  "actionlint_1.7.12_linux_amd64.tar.gz|8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8" \
  "$(actionlint_asset linux amd64)" \
  "actionlint Linux amd64 mapping"
assert_equal \
  "actionlint_1.7.12_linux_arm64.tar.gz|325e971b6ba9bfa504672e29be93c24981eeb1c07576d730e9f7c8805afff0c6" \
  "$(actionlint_asset linux arm64)" \
  "actionlint Linux arm64 mapping"

assert_equal \
  "shellcheck-v0.11.0.darwin.x86_64.tar.gz|c2c15e08df0e8fbc374c335b230a7ee958c313fa5714817a59aa59f1aa594f51" \
  "$(shellcheck_asset darwin amd64)" \
  "ShellCheck Darwin amd64 mapping"
assert_equal \
  "shellcheck-v0.11.0.darwin.aarch64.tar.gz|339b930feb1ea764467013cc1f72d09cd6b869ebf1013296ba9055ab2ffbd26f" \
  "$(shellcheck_asset darwin arm64)" \
  "ShellCheck Darwin arm64 mapping"
assert_equal \
  "shellcheck-v0.11.0.linux.x86_64.tar.gz|b7af85e41cc99489dcc21d66c6d5f3685138f06d34651e6d34b42ec6d54fe6f6" \
  "$(shellcheck_asset linux amd64)" \
  "ShellCheck Linux amd64 mapping"
assert_equal \
  "shellcheck-v0.11.0.linux.aarch64.tar.gz|68a8133197a50beb8803f8d42f9908d1af1c5540d4bb05fdfca8c1fa47decefc" \
  "$(shellcheck_asset linux arm64)" \
  "ShellCheck Linux arm64 mapping"

assert_fails "actionlint rejects unsupported OS" actionlint_asset windows amd64
assert_fails "actionlint rejects unsupported architecture" actionlint_asset linux 386
assert_fails "ShellCheck rejects unsupported OS" shellcheck_asset windows amd64
assert_fails "ShellCheck rejects unsupported architecture" shellcheck_asset linux 386

assert_equal "darwin" "$(normalize_os Darwin)" "normalize Darwin"
assert_equal "linux" "$(normalize_os Linux)" "normalize Linux"
assert_equal "amd64" "$(normalize_arch x86_64)" "normalize x86_64"
assert_equal "amd64" "$(normalize_arch amd64)" "normalize amd64"
assert_equal "arm64" "$(normalize_arch arm64)" "normalize arm64"
assert_equal "arm64" "$(normalize_arch aarch64)" "normalize aarch64"
assert_fails "reject unsupported uname OS" normalize_os FreeBSD
assert_fails "reject unsupported uname architecture" normalize_arch i386

TEMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TEMP_DIR"' EXIT
printf 'aifo\n' > "$TEMP_DIR/checksum-fixture"
verify_sha256 \
  "$TEMP_DIR/checksum-fixture" \
  "d45aeddb0d323ec40c937fac67b55f99f0903e1478bec971d20c258be8520599"
assert_fails \
  "reject checksum mismatch" \
  verify_sha256 \
  "$TEMP_DIR/checksum-fixture" \
  "0000000000000000000000000000000000000000000000000000000000000000"

CLEANUP_DIR="$TEMP_DIR/installer-cleanup"
DEV_TOOLS_TEMP_DIR="$CLEANUP_DIR"
mkdir -p "$CLEANUP_DIR"
cleanup_temp_dir
if [[ -e "$CLEANUP_DIR" ]]; then
  echo "FAIL: installer temporary directory was not removed" >&2
  exit 1
fi
assert_equal "" "$DEV_TOOLS_TEMP_DIR" "cleanup clears temporary directory state"

assert_file_contains \
  "$ROOT_DIR/scripts/validate.sh" \
  'classify_discovered_paths' \
  "validation classifies discovered scripts before linting"
assert_file_contains \
  "$ROOT_DIR/scripts/validate.sh" \
  "shellcheck \"\${SHELL_FILES[@]}\"" \
  "validation lints the classified shell path set"
assert_file_occurrences \
  "$ROOT_DIR/scripts/validate.sh" \
  "bash \"\$ROOT_DIR/tests/install-dev-tools-test.sh\"" \
  "1" \
  "complete validation runs this shell regression exactly once"
assert_file_contains \
  "$ROOT_DIR/scripts/validate.sh" \
  "actionlint" \
  "validation runs actionlint"
assert_file_contains \
  "$ROOT_DIR/scripts/validate.sh" \
  "./scripts/install-dev-tools.sh" \
  "validation points to the reproducible installer"
assert_file_occurrences \
  "$ROOT_DIR/scripts/validate.sh" \
  "./scripts/install-dev-tools.sh" \
  "1" \
  "validation prints one shared installer remediation"

echo "install-dev-tools tests passed."
