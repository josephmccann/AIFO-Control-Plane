# Activation integration scope

Mission 31 closes the inactive Mission 26 test-integrity activation boundary. It
does not authorize, issue, or consume activation.

Every activation authorization binds the authoritative open Mission 26 issue,
its node ID and URL, and its authenticated Ready event sequence, event hash, and
declaration hash. Every lifecycle event also binds the exact mission-command
workflow revision, checked-out commit and tree, Actions run and attempt,
triggering actor, execution job, reusable test-integrity caller, immutable
kernel, and evidence manifest identities.

Attempted and completed consumption use the same closed consumer identity:
`github-actions[bot]`, the `append` job, this repository, and
`.github/workflows/mission-command.yml`. The authenticated Actions provenance
is separate from the founder who triggered the run. Missing, copied, stale,
extra, or contradictory fields fail closed before proposal and again before
append; rejection performs no append, nonce transition, or activation state
transition.

`ACTIVATION_DEPENDENCY_CLOSURE.json` is an attestation committed after the exact
implementation revision it names. This avoids self-referential Git hashes while
allowing the validator to recompute the complete base-to-final path set, every
file digest, dependency edge, transport pin, focused/full test result, evidence
digest, and two independent review checkpoints.
