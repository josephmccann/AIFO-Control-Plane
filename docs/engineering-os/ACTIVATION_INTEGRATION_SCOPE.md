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

## Identity roles and the Model B compatibility chain

Activation binds several identities that were previously conflated. They are
distinct roles and may never be substituted for one another:

- **Historical baseline identity** — `baseline_generation_commit` and
  `baseline_generation_tree` are the commit and tree embedded in the reviewed
  baseline artifact, and `baseline_artifact_sha256` is that artifact's digest.
- **Historical remediation identity** — `remediation_head` and
  `remediation_tree` name the reviewed remediation.
- **Historical analyzer, workflow, caller, kernel, and manifest identities** —
  the surface as it stood when the baseline was generated and reviewed.
- **Active execution identity** — `active_execution_commit` and
  `active_execution_tree` are the live authenticated checkout of the command
  run, and are the only fields the ledger compares the checkout against.

Historical fields do not advance with the default branch. Binding them to the
live checkout to make provenance validation pass would assert a correspondence
that no reviewer ever approved: the artifact digest describes one tree while the
tuple claims another.

Because the default branch advances after the baseline was reviewed, the gap is
closed by an explicit **Model B compatibility chain** rather than by
regenerating the baseline. Regeneration is rejected: it would establish a
baseline over a governed corpus that was never subjected to the Mission 26
canonical-findings analysis, and would produce an artifact no reviewer has
independently reviewed, which `establish_initial_baseline` requires.

The chain proves the reviewed artifact still means what it meant. It enumerates
every commit between the baseline identity and the active execution identity and
records, at each one, the blob digests of the baseline generator and analyzer
surface:

- `docs/engineering-os/TEST_INTEGRITY_CANONICAL_FINDINGS.json`
- `engineering_os/canonical.py`
- `engineering_os/python_imports.py`
- `engineering_os/test_integrity.py`
- `engineering_os/test_integrity_cli.py`
- `scripts/engineering-os/validate-test-integrity`

Ancestry is not a proof, and neither is final-tree equality. A change introduced
at an intermediate commit and reverted before the end is rejected, because the
reviewed baseline stopped meaning what it meant at that commit. Range gaps,
duplicate commits, and merges importing undeclared history all fail closed.
Those six paths are prohibited by the governing mission so the guarantee is
self-enforcing rather than merely asserted.

The chain is derived from authenticated Git history at command time. A committed
chain cannot name the commit that contains it, so
`outputs/mission-35-compatibility-chain.json` is a point-in-time snapshot
retained as reviewable evidence; the authoritative chain is the one the command
run derives and validates.

An authorization issued before this separation existed is reported as
`ACTIVATION_AUTHORIZATION_SUPERSEDED`. It remains authenticated, append-only,
visible, and unconsumed, but can never be attempted or consumed, because it
pairs an opaque historical artifact digest with whatever the default branch has
since become.

### Merge parents and pre-baseline ancestry

The enumerated range is `rev-list baseline..active`. Every commit reachable from
the active execution commit and not reachable from the reviewed baseline is
therefore enumerated, by definition. A merge parent is consequently either
inside that range or an ancestor of the baseline — there is no third case.

Commits reachable from an ancestor of the baseline are already subsumed by the
reviewed baseline artifact, which captured the governed inventory at the
baseline commit. Accepting such a parent is a correctness requirement, not a
relaxation: the real default-branch topology contains one, because the reviewed
baseline was produced on a side branch while the mainline continued
independently.

The validator has no repository access and cannot compute ancestry, so the
chain builder verifies it against Git and declares the result in
`pre_baseline_parents`. A parent that is neither enumerated, nor the baseline,
nor a declared pre-baseline ancestor fails closed as
`COMPATIBILITY_CHAIN_PARENT_UNDECLARED`, and the builder itself fails closed
with `ACTIVATION_COMPATIBILITY_PARENT_UNDECLARED` before any event is
constructed. A commit that is both enumerated and declared pre-baseline, or a
declaration naming the baseline itself, is contradictory and is rejected.

The range is validated as a DAG reachable from the active execution commit
rather than as a linear predecessor walk. A linear walk cannot express a real
merge topology, and it could not detect an enumerated commit that sits outside
the active commit's history; such an orphan is now rejected.

### Activation nonce retirement

Every nonce that has appeared in any activation authorization event is
permanently reserved and can never be reused by a later authorization. This
holds for structurally superseded authorizations: they are excluded from active
authorization selection, but their nonces stay retired.

Selection and retirement are deliberately separate concerns. A superseded
authorization is skipped when choosing the active authorization — so a valid
replacement can be appended — while its nonce is still added to the retired set,
so the replacement may not reuse it.

Retirement is enforced at two independent layers, and neither trusts the other:

- `authorize_command_proposal` rejects a proposed authorization whose nonce
  matches any prior authorization event, including superseded ones, before any
  event can be appended.
- `validate_activation_ledger` reserves the nonce of every superseded
  authorization and rejects a live authorization that reuses one, so a manually
  constructed or malformed history that bypasses the proposal path still fails
  closed. Both paths return `ACTIVATION_NONCE_RETIRED`.

A distinct fresh nonce is unaffected and authorizes normally. Single-use
activation is unchanged: repeated authorization, attempt, or consumption still
fail closed.

### Activation readiness snapshot

`outputs/eos-activation-readiness/activation-readiness-snapshot.json` and its
Markdown twin are an immutable, evidence-only checkpoint of the complete
pre-authorization state, bound to a recorded source-of-truth commit. They record
repository identity, mission and declaration bindings, the historical-versus-active
baseline identity separation, the Model B compatibility-chain proof, the
activation-ledger state including fail-closed retired-nonce behavior, the
validation record, the security boundaries, and the documented-but-unexecuted
founder activation sequence.

`scripts/engineering-os/validate-activation-readiness` deterministically checks
that the JSON and Markdown refer to the same commit, tree, event hashes, and
artifact digests, and that the committed digest file matches the artifact bytes.
Git object identities and authenticated event hashes are authoritative; the
snapshot timestamp is informational. The raw retired nonce never appears in the
snapshot — only its SHA-256 digest identity and the authenticated authorization
event hash are recorded — and no real replacement nonce is present.
