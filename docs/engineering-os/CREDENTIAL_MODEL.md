# Engineering OS Credential Model

GitHub Actions uses the ephemeral repository token with minimal job
permissions and `persist-credentials: false`. Validation jobs are read-only,
load the policy and enforcement code from the base revision, and receive no
secret, OIDC, deployment, cloud, issue-write, or pull-request-write authority.

GitHub's ordinary repository credential cannot path-scope the Git credential.
The kernel validates declared paths and blocks merge authorization when scope
is invalid, but this is a policy check rather than a credential-level path
restriction. This gap must remain explicit; the current system does not claim
that it enforces path-scoped Git credentials.

The migration path is a dedicated GitHub App with narrowly selected repository
permissions and an expiring installation token minted only after mission,
repository, pull request, head SHA, path, and action checks pass. The App would
still require branch protection and the same base-policy guard because GitHub
App repository permissions are not themselves path-specific. Until that
separate design is approved and implemented, write credentials are outside
these reusable validation jobs.
