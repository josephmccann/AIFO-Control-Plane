# Test-integrity enforcement

The test-integrity guard compares authenticated, immutable base and head commits. It binds every tracked path to its Git blob bytes, rejects dirty or unrelated revisions, derives mission and risk truth from GitHub, and emits a machine-generated report even when analysis cannot complete.

The reusable workflow executes only the kernel stored with the reviewed reusable-workflow revision. It never executes code from the pull-request head. A default-branch `pull_request_target` caller pins that reusable workflow to an exact Control Plane commit and grants read-only Actions, contents, issue, and pull-request access.

Executable test discovery is parser-backed and fail closed. Python semantics bind function kind, signature and defaults, decorators and parametrization, return metadata, module collection metadata, enclosing-class bases/decorators/collection state, and inherited skip or `__test__` disablement. JavaScript semantics bind nested suite scopes and suite modifiers; static dot, bracket, computed-string, and alias forms are normalized, while dynamic or indirect collection references that cannot be proven equivalent are rejected. Duplicate runtime identities, unsupported declarations, semantic assertion/body changes, newly inherited skips, and ambiguous renames require an authenticated override. Test-runner configuration is protected recursively in every package.

Coverage deltas are accepted only when a sealed trusted adapter result binds the coverage bytes and source manifest to an independently retrieved successful GitHub Actions run, exact workflow revision, artifact identity and digest, repository, commit, and transport timestamp. Repositories without coverage evidence do not need an attestation; configured coverage with unavailable or mismatched transport evidence fails closed.

The adapter and kernel share one non-resetting resource budget across policy and manifest validation, Git discovery, filesystem reconciliation, parsing, semantic comparison, GitHub transport, coverage verification, and report construction. Caps cover filesystem entries (including directories), total processed bytes, paths, Git records, GitHub pagination/items/responses, and coverage artifacts. Directory paths are validated and charged before enqueueing, so wide empty fanout and deep trees cannot evade the streamed traversal budget. Resource failures preserve the pre-initialized machine denial report.

## Activation boundary

The caller does not enforce a PR until the caller commit itself is merged to the default branch and the required status check is configured. That bootstrap interval is an explicit enforcement gap; it cannot be closed by code inside the same unmerged PR. Closing it requires founder-approved merge and, separately, founder-approved live branch-protection configuration.

Authenticated, atomically consumed override interfaces exist in the kernel. The live workflow deliberately accepts no override, reviewer, or approval inputs. Overrides remain fail closed until the evidence and audit package supplies a trusted durable consumption ledger across workflow runs. Runner-local storage is not accepted as durable replay protection.
