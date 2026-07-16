# Airtable reporting mirror

GitHub mission declarations, authenticated history, and the deterministic
mission projection remain authoritative. Airtable is a one-way reporting
mirror and cannot transition a mission, grant authority, approve a change, or
write back to GitHub.

Dry-run is the default and the only operational workflow mode in this package.
It projects a closed, versioned record containing only repository, mission ID,
state, risk tier, reviewed head, projection time, and the stable
`repository#mission_id` upsert key. Mission title, objective, acceptance
criteria, people, customer data, financial data, credentials, and free-form
prose are not projected.

The pure adapter contains a future live boundary for testing. A live upsert
requires all of the following:

- a schema-valid base-revision policy with `airtable_live_enabled: true`;
- exact base and table identifiers;
- an environment-sourced ephemeral credential, never a command-line token;
- a current authenticated single-use founder approval for
  `airtable_write`, bound to the authorizing mission, repository, pull request,
  head SHA, and exact `airtable:<base>:<table>:<record-set-hash>` environment;
- a trusted evidence verifier and persistent approval-consumption store.

Live requests use bounded batches of ten, a stable `upsert_key`, ten-second
timeouts, and at most three attempts for retryable failures. Any malformed
or oversized response, exhausted retry, or partial batch failure returns a
denial. Partial external writes are reported and never described as success.
The target table must define `upsert_key` as the unique merge field.

No Airtable environment, secret, base, table, or live workflow is created or
activated by this program. The reusable workflow rejects live mode until a
separately approved authenticated environment adapter exists.
