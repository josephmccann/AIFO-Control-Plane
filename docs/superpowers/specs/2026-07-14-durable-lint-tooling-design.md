# Durable Lint Tooling Design

## Goal

Make `shellcheck` and `actionlint` reproducibly available to local contributors without changing AWS resources, adding a new GitHub Actions dependency, or increasing recurring cloud cost.

## Constraints

- Keep `scripts/validate.sh` as the standard validation entrypoint.
- Install generated binaries only under ignored `build/bin`; never commit them.
- Pin upstream versions and SHA-256 digests.
- Support the repository's practical developer and CI platforms: macOS and Linux on `arm64`/`aarch64` and `amd64`/`x86_64`.
- Fail closed on unsupported platforms, download failures, or checksum mismatches.
- Do not install system packages or require administrator privileges.
- Do not add or modify AWS resources, Terraform behavior, GitHub OIDC, or deployment workflows.

## Selected Approach

Add a repository-owned installer that downloads official release archives for `actionlint` v1.7.12 and ShellCheck v0.11.0, validates each archive against its pinned GitHub release digest, and installs the executables into `build/bin`.

This is preferred to package-manager-only documentation because it is deterministic across supported platforms. It is preferred to a new CI action or workflow because it does not introduce another third-party workflow dependency or recurring CI execution cost.

## Components

### Installer

`scripts/install-dev-tools.sh` will:

1. Detect and normalize the operating system and architecture.
2. Select the exact official archive name and pinned digest for each tool.
3. Download into a temporary directory with `curl --fail --location --silent --show-error`.
4. Verify SHA-256 before extraction.
5. Install only the expected executable into `build/bin`.
6. Print installed versions and the required `PATH` command.

The installer will expose its platform-mapping functions when sourced, while executing installation only when run directly. This provides a testable shell interface without network mocks or test-only production flags.

### Validation

`scripts/validate.sh` will continue running Terraform formatting/validation and shell syntax checks. When `shellcheck` or `actionlint` is absent, it will provide one precise remediation command. When present, it will run both linters.

### Tests

A dependency-free shell test will source the installer and verify all four supported platform mappings plus rejection of unsupported operating systems and architectures. A live installer smoke test will verify official downloads, checksums, extraction, and executable versions on the current platform.

### Documentation And State

Update contributor guidance, the developer-experience workstream, open decisions, work queue, roadmap, and changelog so the repository records the tooling choice and the exact local workflow.

## Security And Failure Behavior

- Every archive is authenticated by a pinned SHA-256 digest obtained from the official GitHub release asset metadata.
- Temporary files are deleted on exit.
- A checksum mismatch prevents extraction and installation.
- Existing binaries are replaced only after their corresponding archive passes verification.
- No credentials, AWS calls, Terraform state, or customer data are involved.

## Success Criteria

- Platform-mapping tests pass on Bash without third-party test frameworks.
- The installer places verified `actionlint` v1.7.12 and ShellCheck v0.11.0 binaries in `build/bin` on the current supported platform.
- `PATH="$PWD/build/bin:$PATH" ./scripts/validate.sh` runs Terraform validation, `shellcheck`, and `actionlint` successfully.
- `git diff --check` and YAML parsing pass.
- The working tree contains no generated binaries or archives.
