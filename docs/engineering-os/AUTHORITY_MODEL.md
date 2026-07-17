# Engineering OS Authority Model

Engineering OS authority is deny-by-default and scoped to one authenticated
mission. Read is the only default capability. Every write, merge, deployment,
cloud mutation, secret, customer-data, spend, or cutover action requires a
current record that binds the exact mission, repository, pull request, head
SHA, subject, concrete path set, and single action. The record also carries a
unique record identifier and nonce. The kernel asks an adapter-owned verifier
to retrieve the GitHub comment by exact repository, issue or pull-request
identity, and comment identity. This independently retrieved
authenticated GitHub source then binds the record kind, canonical payload SHA-256,
comment-body SHA-256, URL, actor, creation and edit times, head SHA, and
transport provenance. Changing any record field or reusing a source claim for
another payload invalidates the record. These raw mappings and
in-process constructor identity do not authenticate evidence; the verifier
must independently retrieve it from its transport boundary.

After all scope and time checks pass, a single-use authority record is inserted
into a file-backed SQLite ledger under `BEGIN IMMEDIATE`. Unique record-ID and
nonce constraints make the allow-and-consume decision atomic for sequential and
concurrent attempts, and the stored canonical binding digest makes the consumed
scope auditable. Initialization and every consume attest the exact SQLite
schema version, object set, column types and nullability, primary key, unique
nonce constraint, and supporting index. Partial, altered, additional, or
duplicate-capable schemas are refused without migration or data loss. The
kernel permits an injected temporary store for deterministic tests, but Task 3
has no operational adapter that selects or enables a local ledger. Public
workflows expose neither a ledger path nor authority execution; an
authenticated persistent GitHub-authoritative adapter remains later work.

An authority record is effective only during its strict UTC validity window,
while its status is `active`, and when its issuer is a configured founder.
Expiry is exclusive: a record is expired at its `expires_at` instant. A record
for one action never implies another action. Authority does not replace risk
classification, frozen-artifact exceptions, review, or founder approval.

Semantic domains name path patterns, owners, minimum tiers, and conflict
groups. Matching and intersection use the same parsed segment automaton for
`*`, `?`, character classes, negated character classes, and whole-segment
recursive `**`. Embedded or malformed recursive wildcards, classes, and ranges
are rejected. Declared globs are intersected conservatively with the
base-policy domain globs rather than interpreted as literal file names. Only `Claimed`,
`In Progress`, `Adversarial Review`, `Founder Approval`, `Merge Authorized`,
and `Incident` hold scope. Proposed and Ready missions do not reserve paths;
an expired lease remains in its execution state until an authenticated
transition releases it. Concurrent path or conflict-group ownership is denied
unless an active founder coordination record names exactly both missions and
both exact scopes, PR, head SHA, repository, expiry, and independently
retrieved canonical GitHub evidence.
The reusable guard does not accept caller-supplied coordination. Until a later
authenticated coordination-event adapter exists, every overlap is blocked.
These ownership checks do not alter mission lifecycle authority; they are
additional admission constraints and create no lifecycle event.

Policy is always read from the pull request's base revision. Consequently, a
pull request that changes governance or its own policy is Tier 2 and cannot
weaken the guard evaluating that same pull request.
