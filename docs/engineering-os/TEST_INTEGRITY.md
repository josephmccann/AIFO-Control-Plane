# Test-integrity enforcement

The test-integrity guard compares authenticated, immutable base and head commits. It binds every tracked path to its Git blob bytes, rejects dirty or unrelated revisions, derives mission and risk truth from GitHub, and emits a machine-generated report even when analysis cannot complete.

The reusable workflow executes only the kernel stored with the reviewed reusable-workflow revision. It never executes code from the pull-request head. A default-branch `pull_request_target` caller pins that reusable workflow to an exact Control Plane commit and grants read-only Actions, contents, issue, and pull-request access.

## Activation boundary

The caller does not enforce a PR until the caller commit itself is merged to the default branch and the required status check is configured. That bootstrap interval is an explicit enforcement gap; it cannot be closed by code inside the same unmerged PR. Closing it requires founder-approved merge and, separately, founder-approved live branch-protection configuration.

Authenticated, atomically consumed override interfaces exist in the kernel. The live workflow deliberately accepts no override, reviewer, or approval inputs. Overrides remain fail closed until the evidence and audit package supplies a trusted durable consumption ledger across workflow runs. Runner-local storage is not accepted as durable replay protection.
