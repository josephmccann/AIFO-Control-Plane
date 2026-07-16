# Frozen Artifacts

A frozen declaration identifies repository-relative POSIX path globs and may
bind a commit pin, sealed manifest SHA-256, protected engine version, release
condition, expiry, founder exception authority, and a one-shot marker. Invalid
or ambiguous paths, including absolute paths and traversal, fail closed.

A write to a frozen path is denied unless an authenticated, active, unexpired
exception matches the declaration and the exact mission, repository, pull
request, head SHA, concrete changed path set, action, configured founder
identity, and authenticated GitHub source. Pins and sealed manifests are
derived from exact commits in the local Git object database by the public
validator, including its own complete base and head Git trees and NUL-delimited
no-rename diff. The CLI accepts no caller-authored Git tree,
authenticated-source, release, reservation, consumption-snapshot, or ledger
evidence.

Exception, release, and reservation records use the same independently
retrieved canonical GitHub evidence as authority and coordination: exact issue
or pull-request and comment identities, record kind, canonical payload and body
digests, actor, timestamps, head SHA, and transport provenance are inseparable.
A one-shot exception also requires one exact verifier-authenticated release,
one verifier-authenticated durable reservation, and an atomic SQLite consume of
its identifier and nonce before allow is returned. Exact schema attestation and
unique constraints deny altered ledgers, sequential replay, and races.
An exception authorizes only the frozen write; it does not grant deployment,
methodology, customer-data, merge, or other authority.

Reusable guards load declarations from the base revision. This prevents a
pull request from deleting or weakening its own freeze before evaluation.
Until Task 5 supplies authenticated exception, release, reservation, and
consumption records, no exception is accepted by the reusable workflow and a
write to a frozen path fails closed. The kernel's injected SQLite store exists
for pure validation and deterministic tests; there is no caller-selected ledger
and no operational exception execution until the persistent GitHub-authoritative
Task 5 adapter exists.
No EDGAR integration is activated, targeted, collected, or scored by this
model. Adding a generic frozen-artifact interface does not change that disabled
boundary.
