# Evidence and audit

Audit events bind a proposal to actor, role, time, and source metadata derived
from authenticated GitHub state. Sequence numbers, mission identity, previous
hashes, and event hashes form a complete canonical chain. Missing, malformed,
reordered, cross-mission, or self-asserted metadata fails closed.

Evidence manifests are generated from validated mission and base-policy
documents, the complete audit head, exact base and head commits, closed status
check records, and byte-hashed artifacts. Producer-authored prose cannot supply
derived hashes, approval state, cleanup state, or deployment state.

The reusable evidence workflow has two runners. The producer-evidence runner
may execute pull-request code with read-only Actions and contents permission
and receives no issue write, pull-request write, secret, OIDC, deployment, or
cloud authority. Its required validation command comes from the versioned
target-repository caller, so the reusable workflow does not assume a language,
package manager, or Control Plane test path exists in the target. The command
is passed through the step environment and its output remains untrusted. An
empty or failing command stops evidence generation. A fresh runner downloads
only the retained artifact boundary,
checks out the immutable reusable-workflow kernel plus exact base and head
revisions, and runs the immutable test-integrity analyzer. It then recomputes
the producer bundle's repository, pull request, base/head bindings, artifact
sizes, and byte hashes before retaining validated output. The fresh runner
does not trust the producer workspace, tests, metadata, or environment.

Founder approval is an authenticated GitHub record bound independently to one
mission, action, repository, pull request, head SHA, environment, merge method,
validity interval, and issuer. It is atomically single-use. Merge approval keeps
deployment and cutover false; those actions require separate approvals.
Airtable-write approval also keeps deployment and cutover false and binds the
exact target plus canonical projected-record-set hash in its environment.
# Mission 26 activation ledger boundary

The initial Test Integrity baseline is activated only by an authenticated EOS
event pair. The authorization event binds the repository, Mission 26, exact
remediation commit and tree, baseline and canonical-inventory digests, all
workflow/kernel/manifest identities, rollback SHA, activation type, and a
high-entropy single-use nonce. A consumption event repeats that tuple and
references the authorization event hash and sequence.

Validation operates only on a complete authenticated event history. Duplicate
nonces, replayed authorization, orphan consumption, altered tuple members,
wrong repository or mission, cancellation/supersession, missing or truncated
history, and ambiguous partial consumption fail closed. The validator has no
append or persistence capability; event creation remains the existing EOS
authenticated append path. After a valid consumption event, the initial path
is permanently unavailable to ordinary activation requests. Recovery from an
ambiguous append requires a separately authorized EOS recovery mission.
