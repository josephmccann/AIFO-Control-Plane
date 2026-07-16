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
cloud authority. A fresh runner downloads only the retained artifact boundary,
checks out the immutable reusable-workflow kernel, and validates the bundle.
The fresh runner does not trust the producer workspace or environment.

Founder approval is an authenticated GitHub record bound independently to one
mission, action, repository, pull request, head SHA, environment, merge method,
validity interval, and issuer. It is atomically single-use. Merge approval keeps
deployment and cutover false; those actions require separate approvals.
