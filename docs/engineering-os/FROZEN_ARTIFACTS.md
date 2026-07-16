# Frozen Artifacts

A frozen declaration identifies repository-relative POSIX path globs and may
bind a commit pin, sealed manifest SHA-256, protected engine version, release
condition, expiry, founder exception authority, and a one-shot marker. Invalid
or ambiguous paths, including absolute paths and traversal, fail closed.

A write to a frozen path is denied unless an authenticated, active, unexpired
exception matches the declaration and the exact mission, repository, pull
request, head SHA, concrete changed path set, and action. Its pins and release
condition must match the declaration and current observations. A one-shot
exception is denied after its identifier is recorded as consumed. An
exception authorizes only the frozen write; it does not grant deployment,
methodology, customer-data, merge, or other authority.

Reusable guards load declarations from the base revision. This prevents a
pull request from deleting or weakening its own freeze before evaluation.
No EDGAR integration is activated, targeted, collected, or scored by this
model. Adding a generic frozen-artifact interface does not change that disabled
boundary.
