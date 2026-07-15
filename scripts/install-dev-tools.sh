#!/usr/bin/env bash
set -euo pipefail

ACTIONLINT_VERSION="1.7.12"
SHELLCHECK_VERSION="0.11.0"
DEV_TOOLS_TEMP_DIR=""

cleanup_temp_dir() {
  if [[ -n "${DEV_TOOLS_TEMP_DIR:-}" ]]; then
    rm -rf "$DEV_TOOLS_TEMP_DIR"
    DEV_TOOLS_TEMP_DIR=""
  fi
}

normalize_os() {
  case "$1" in
    Darwin | darwin)
      echo "darwin"
      ;;
    Linux | linux)
      echo "linux"
      ;;
    *)
      echo "Unsupported operating system: $1" >&2
      return 1
      ;;
  esac
}

normalize_arch() {
  case "$1" in
    x86_64 | amd64)
      echo "amd64"
      ;;
    arm64 | aarch64)
      echo "arm64"
      ;;
    *)
      echo "Unsupported architecture: $1" >&2
      return 1
      ;;
  esac
}

verify_sha256() {
  local file="$1"
  local expected="$2"
  local actual

  if command -v shasum >/dev/null 2>&1; then
    actual="$(shasum -a 256 "$file" | awk '{print $1}')"
  elif command -v sha256sum >/dev/null 2>&1; then
    actual="$(sha256sum "$file" | awk '{print $1}')"
  else
    echo "A SHA-256 utility is required: install shasum or sha256sum." >&2
    return 1
  fi

  if [[ "$actual" != "$expected" ]]; then
    echo "SHA-256 mismatch for $file" >&2
    echo "Expected: $expected" >&2
    echo "Actual:   $actual" >&2
    return 1
  fi
}

actionlint_asset() {
  local os="$1"
  local arch="$2"

  case "$os/$arch" in
    darwin/amd64)
      echo "actionlint_1.7.12_darwin_amd64.tar.gz|5b44c3bc2255115c9b69e30efc0fecdf498fdb63c5d58e17084fd5f16324c644"
      ;;
    darwin/arm64)
      echo "actionlint_1.7.12_darwin_arm64.tar.gz|aba9ced2dee8d27fecca3dc7feb1a7f9a52caefa1eb46f3271ea66b6e0e6953f"
      ;;
    linux/amd64)
      echo "actionlint_1.7.12_linux_amd64.tar.gz|8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8"
      ;;
    linux/arm64)
      echo "actionlint_1.7.12_linux_arm64.tar.gz|325e971b6ba9bfa504672e29be93c24981eeb1c07576d730e9f7c8805afff0c6"
      ;;
    *)
      echo "Unsupported actionlint platform: $os/$arch" >&2
      return 1
      ;;
  esac
}

shellcheck_asset() {
  local os="$1"
  local arch="$2"

  case "$os/$arch" in
    darwin/amd64)
      echo "shellcheck-v0.11.0.darwin.x86_64.tar.gz|c2c15e08df0e8fbc374c335b230a7ee958c313fa5714817a59aa59f1aa594f51"
      ;;
    darwin/arm64)
      echo "shellcheck-v0.11.0.darwin.aarch64.tar.gz|339b930feb1ea764467013cc1f72d09cd6b869ebf1013296ba9055ab2ffbd26f"
      ;;
    linux/amd64)
      echo "shellcheck-v0.11.0.linux.x86_64.tar.gz|b7af85e41cc99489dcc21d66c6d5f3685138f06d34651e6d34b42ec6d54fe6f6"
      ;;
    linux/arm64)
      echo "shellcheck-v0.11.0.linux.aarch64.tar.gz|68a8133197a50beb8803f8d42f9908d1af1c5540d4bb05fdfca8c1fa47decefc"
      ;;
    *)
      echo "Unsupported ShellCheck platform: $os/$arch" >&2
      return 1
      ;;
  esac
}

require_tool() {
  local tool="$1"

  if ! command -v "$tool" >/dev/null 2>&1; then
    echo "Missing required tool: $tool" >&2
    return 1
  fi
}

download_archive() {
  local url="$1"
  local destination="$2"
  local checksum="$3"

  echo "Downloading $url"
  curl --fail --location --silent --show-error --output "$destination" "$url"
  verify_sha256 "$destination" "$checksum"
}

main() {
  local root_dir
  local install_dir
  local temp_dir
  local os
  local arch
  local actionlint_record
  local actionlint_archive
  local actionlint_checksum
  local shellcheck_record
  local shellcheck_archive
  local shellcheck_checksum

  require_tool curl
  require_tool tar

  root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  install_dir="$root_dir/build/bin"
  temp_dir="$(mktemp -d)"
  DEV_TOOLS_TEMP_DIR="$temp_dir"
  trap cleanup_temp_dir EXIT

  os="$(normalize_os "$(uname -s)")"
  arch="$(normalize_arch "$(uname -m)")"
  actionlint_record="$(actionlint_asset "$os" "$arch")"
  actionlint_archive="${actionlint_record%%|*}"
  actionlint_checksum="${actionlint_record#*|}"
  shellcheck_record="$(shellcheck_asset "$os" "$arch")"
  shellcheck_archive="${shellcheck_record%%|*}"
  shellcheck_checksum="${shellcheck_record#*|}"

  mkdir -p "$install_dir" "$temp_dir/actionlint" "$temp_dir/shellcheck"

  download_archive \
    "https://github.com/rhysd/actionlint/releases/download/v${ACTIONLINT_VERSION}/${actionlint_archive}" \
    "$temp_dir/$actionlint_archive" \
    "$actionlint_checksum"
  tar -xzf "$temp_dir/$actionlint_archive" -C "$temp_dir/actionlint"
  cp "$temp_dir/actionlint/actionlint" "$install_dir/actionlint"
  chmod 0755 "$install_dir/actionlint"

  download_archive \
    "https://github.com/koalaman/shellcheck/releases/download/v${SHELLCHECK_VERSION}/${shellcheck_archive}" \
    "$temp_dir/$shellcheck_archive" \
    "$shellcheck_checksum"
  tar -xzf "$temp_dir/$shellcheck_archive" -C "$temp_dir/shellcheck"
  cp \
    "$temp_dir/shellcheck/shellcheck-v${SHELLCHECK_VERSION}/shellcheck" \
    "$install_dir/shellcheck"
  chmod 0755 "$install_dir/shellcheck"

  echo "Installed actionlint $("$install_dir/actionlint" -version)"
  echo "Installed ShellCheck $("$install_dir/shellcheck" --version | awk '/^version:/ {print $2}')"
  echo "Run validation with: PATH=\"\$PWD/build/bin:\$PATH\" ./scripts/validate.sh"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
