# Engineering OS Authority Model

Engineering OS authority is deny-by-default and scoped to one authenticated
mission. Read is the only default capability. Every write, merge, deployment,
cloud mutation, secret, customer-data, spend, or cutover action requires a
current record that binds the exact mission, repository, pull request, head
SHA, subject, concrete path set, and single action.

An authority record is effective only during its strict UTC validity window,
while its status is `active`, and when its issuer is a configured founder.
Expiry is exclusive: a record is expired at its `expires_at` instant. A record
for one action never implies another action. Authority does not replace risk
classification, frozen-artifact exceptions, review, or founder approval.

Semantic domains name path patterns, owners, minimum tiers, and conflict
groups. Concurrent path or conflict-group ownership is denied unless an
active founder coordination record names exactly both missions and both exact
scopes. These ownership checks do not alter mission lifecycle authority; they
are additional admission constraints and create no lifecycle event.

Policy is always read from the pull request's base revision. Consequently, a
pull request that changes governance or its own policy is Tier 2 and cannot
weaken the guard evaluating that same pull request.
