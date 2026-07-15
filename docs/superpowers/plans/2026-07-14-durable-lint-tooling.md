# Durable Lint Tooling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Provide reproducible, checksum-verified local installation and execution of `actionlint` and `shellcheck` without changing AWS or adding recurring CI cost.

**Architecture:** A sourceable Bash installer owns platform normalization, official release asset selection, checksum verification, extraction, and installation into ignored `build/bin`. A dependency-free Bash test exercises the pure platform mapping before network operations; the existing validation entrypoint discovers and runs the installed tools.

**Tech Stack:** Bash 3.2+, curl, tar, SHA-256 (`shasum` or `sha256sum`), Terraform 1.10.5, actionlint 1.7.12, ShellCheck 0.11.0.

## Global Constraints

- Work only inside this repository.
- Do not create, update, or delete AWS resources.
- Do not add a GitHub apply workflow or change Terraform deployment behavior.
- Put generated executables only in ignored `build/bin`.
- Verify every downloaded archive against its pinned SHA-256 digest before extraction.
- Support Darwin/Linux and amd64/arm64 only; reject everything else.

---

### Task 1: Platform Mapping Contract

**Files:**
- Create: `tests/install-dev-tools-test.sh`
- Create: `scripts/install-dev-tools.sh`

**Interfaces:**
- Consumes: normalized OS (`darwin` or `linux`) and architecture (`amd64` or `arm64`).
- Produces: `actionlint_asset <os> <arch>` and `shellcheck_asset <os> <arch>`, each printing `<archive>|<sha256>` or returning nonzero for unsupported input.

- [x] **Step 1: Write the failing mapping test**

Create a Bash test that sources `scripts/install-dev-tools.sh`, asserts the exact archive/digest pair for all four supported platform combinations, and asserts rejection of unsupported OS/architecture inputs.

- [x] **Step 2: Run the mapping test and verify RED**

Run: `bash tests/install-dev-tools-test.sh`

Expected: nonzero because `scripts/install-dev-tools.sh` or its mapping functions do not exist.

- [x] **Step 3: Implement the minimal sourceable mapping functions**

Define pinned version constants, `actionlint_asset`, and `shellcheck_asset` with explicit `case` branches for each supported pair. Guard executable behavior with:

```bash
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
```

- [x] **Step 4: Run the mapping test and verify GREEN**

Run: `bash tests/install-dev-tools-test.sh`

Expected: `install-dev-tools platform mapping tests passed.`

### Task 2: Verified Installer

**Files:**
- Modify: `scripts/install-dev-tools.sh`
- Modify: `tests/install-dev-tools-test.sh`

**Interfaces:**
- Consumes: official GitHub release archive URLs, `curl`, `tar`, and one supported SHA-256 utility.
- Produces: executable `build/bin/actionlint` v1.7.12 and `build/bin/shellcheck` v0.11.0.

- [x] **Step 1: Add failing tests for platform normalization and checksum rejection**

Test `normalize_os` and `normalize_arch` with supported `uname` values and unsupported values. Create a temporary file and assert `verify_sha256` accepts its correct digest and rejects an incorrect digest.

- [x] **Step 2: Run tests and verify RED**

Run: `bash tests/install-dev-tools-test.sh`

Expected: nonzero because normalization/checksum functions are undefined.

- [x] **Step 3: Implement installation behavior**

Add:

- dependency checks for `curl`, `tar`, and a SHA-256 utility;
- OS/architecture normalization;
- a temporary directory with an exit trap;
- archive download with curl fail/redirect/error flags;
- checksum verification before extraction;
- exact executable extraction and installation into `build/bin`;
- installed-version output and a `PATH` reminder.

- [x] **Step 4: Run unit tests and verify GREEN**

Run: `bash tests/install-dev-tools-test.sh`

Expected: all assertions pass.

- [x] **Step 5: Run live installer smoke test**

Run: `./scripts/install-dev-tools.sh`

Expected: both official archives verify, `build/bin/actionlint` reports 1.7.12, and `build/bin/shellcheck` reports 0.11.0.

### Task 3: Validation Integration And Repository State

**Files:**
- Modify: `scripts/validate.sh`
- Modify: `.github/workflows/terraform-plan.yml`
- Modify: `CONTRIBUTING.md`
- Modify: `README.md`
- Modify: `SECURITY.md`
- Modify: `workstreams/developer-experience.md`
- Modify: `memory/current-state.md`
- Modify: `memory/deployment-status.md`
- Modify: `memory/open-decisions.md`
- Modify: `memory/infrastructure-roadmap.md`
- Modify: `workqueue/README.md`
- Modify: `ROADMAP.md`
- Modify: `CHANGELOG.md`
- Modify: `docs/deployment-readiness-review.md`
- Modify: `docs/handoffs/HANDOFF_CONTROL_PLANE.md`

**Interfaces:**
- Consumes: `actionlint` and `shellcheck` from `PATH`.
- Produces: one standard validation run covering Terraform, Bash syntax, ShellCheck, and GitHub Actions syntax when tools are installed, with an exact installer hint otherwise.

- [x] **Step 1: Add validation assertions to the test**

Assert `scripts/validate.sh` contains invocations for both linters and points missing-tool output at `./scripts/install-dev-tools.sh`.

- [x] **Step 2: Run tests and verify RED**

Run: `bash tests/install-dev-tools-test.sh`

Expected: nonzero because `validate.sh` does not invoke `actionlint` or the installer hint.

- [x] **Step 3: Update validation and documentation**

Run ShellCheck against `scripts/*.sh` and `tests/*.sh`, run `actionlint`, and emit the installer remediation when either tool is missing. Apply behavior-preserving workflow lint fixes exposed by `actionlint`. Document installation and update OD-016/WQ state plus roadmap/changelog references.

- [x] **Step 4: Run tests and verify GREEN**

Run: `PATH="$PWD/build/bin:$PATH" bash tests/install-dev-tools-test.sh`

Expected: all assertions pass.

- [x] **Step 5: Run full verification**

Run:

```bash
PATH="$PWD/build/bin:$PATH" AWS_PROFILE=aifo-admin AWS_SDK_LOAD_CONFIG=1 ./scripts/validate.sh
git diff --check
ruby -ryaml -e 'ARGV.each { |path| YAML.load_file(path); puts "#{path}: ok" }' .github/workflows/*.yml
git status --short
```

Expected: all commands exit zero; both linters run; only intended source/docs/test files are tracked or modified; `build/` remains ignored.

- [x] **Step 6: Commit implementation**

```bash
git add .github/workflows/terraform-plan.yml scripts tests CONTRIBUTING.md README.md SECURITY.md workstreams/developer-experience.md memory/current-state.md memory/deployment-status.md memory/open-decisions.md memory/infrastructure-roadmap.md workqueue/README.md ROADMAP.md CHANGELOG.md docs/deployment-readiness-review.md docs/handoffs/HANDOFF_CONTROL_PLANE.md docs/superpowers/plans/2026-07-14-durable-lint-tooling.md
git commit -m "chore: add reproducible lint tooling"
```
