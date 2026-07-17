# Known Enforcement Gaps

This register maps every Engineering Constitution rule to a mechanical control
or an explicit residual gap. It also records external Layer 0 and adapter-level
limitations that the deterministic Layer 2 kernel cannot enforce by itself.
An entry marked Partial or Gap is not permission to bypass the control.
Unverifiable state fails closed at the EOS decision boundary.

## Constitutional coverage

| Rule | Summary | Status | Control or named gap | Risk | Owner | Closure path |
| --- | --- | --- | --- | --- | --- | --- |
| C-01 | GitHub and Git are authoritative; mirrors grant no authority | Partial | Mission parser, authenticated event history, one-way Airtable adapter; GAP-DELETABLE-COMMENTS remains | Medium: an administrator can remove source comments | Founder and repository administrator | Retain evidence artifacts and add an append-only external audit export if deletion risk becomes unacceptable |
| C-02 | Missions pin EOS version and exact Constitution bytes | Enforced | Mission schema and `validate_ready` compare version `1.0.0` and the canonical content hash | Low: repository history remains the trust root | EOS maintainer | Change only through the amendment procedure in C-10 |
| C-03 | Authority and transitions deny by default | Partial | Closed schemas, state transition table, authenticated adapters, and merge decision; GAP-BRANCH-PROTECTION remains | High: external repository settings can bypass local policy if misconfigured | Founder and repository administrator | Verify required checks and branch protection before activation and after settings changes |
| C-04 | Computed risk can only raise declared risk | Enforced | Risk classifier takes the maximum declared and computed tier using base policy | Medium: policy path coverage can become stale as repositories evolve | Repository owner | Update semantic ownership and Tier 2 paths in the same change as new surfaces |
| C-05 | Producer and adversary differ; founder alone authorizes merge | Partial | Definition of Ready, finding workflow, approval schema, and merge authorization; GAP-REQUIRED-REVIEWERS remains | High: GitHub plan cannot enforce every approval boundary mechanically | Founder | Keep auto-merge disabled and require exact founder approval until an enforceable external boundary exists |
| C-06 | Scope is bounded by paths, capabilities, ownership, frozen artifacts, and limits | Partial | Tier/path, authority, frozen, lease, and limit guards; GAP-PATH-SCOPED-CREDENTIALS remains | High: a broad repository token is not mechanically restricted to mission paths | Repository administrator | Migrate mutation adapters to a path-scoped GitHub App or equivalent capability broker |
| C-07 | Evidence comes from authenticated state and reproducible validation | Enforced | Split-privilege evidence workflow, byte hashes, exact revisions, test-integrity report, and approval validation | Medium: external check context names remain an activation dependency | EOS maintainer | Verify retained artifacts and exact check contexts during repository activation |
| C-08 | Valid findings remediate; limits and conflicts stop or park work | Enforced | Finding classification, lifecycle transition authorization, limit evaluation, and orphan recovery | Low: human classification still requires review quality | Producer and adversary | Preserve clean-context review and record finding dispositions |
| C-09 | Rollback and incidents preserve origin, evidence, action, and verification | Enforced | Mission and incident schemas, incident validator, rollback classes, and recovery verification | Medium: EOS does not execute rollback | Founder and operator | Keep execution authority separate and require a new approval for external recovery actions |
| C-10 | Amendments require version, schemas, tests, hash, and founder approval | Partial | Frozen policy paths, Constitution hash pin, test-integrity guard, and founder merge gate; GAP-BRANCH-PROTECTION remains | High: repository administrators retain external override power | Founder | Protect governance paths and verify approval/check settings before accepting an amendment |

## External and non-mechanical gaps

| Gap ID | Status | Risk | Mitigation | Owner | Closure path |
| --- | --- | --- | --- | --- | --- |
| GAP-PATH-SCOPED-CREDENTIALS | Open | High: GitHub tokens are repository-scoped rather than mission-path-scoped | Validate complete base/head diffs from base policy; grant write authority only to narrow authenticated adapters | Repository administrator | Use a GitHub App or capability broker that issues action and path-scoped authority |
| GAP-DELETABLE-COMMENTS | Open | Medium: administrators can delete authoritative issue comments | Authenticate complete histories, bind ready declarations by hash, and retain evidence artifacts | Founder | Add an append-only audit export with independently retained hashes if required |
| GAP-BRANCH-PROTECTION | External | High: local code cannot prove or enforce current repository settings | Founder approval, disabled auto-merge, required-check documentation, and read-only verification before readiness | Repository administrator | Configure and periodically verify exact branch rules after PR/check activation |
| GAP-PRIVATE-ACTIONS-ACCESS | Founder gate | High: AI.FO-Demo cannot invoke private Control Plane workflows until exact access is approved | Keep callers pinned and inactive; do not broaden repository access | Founder | Approve only the exact private Actions access needed for `josephmccann/AI.FO-Demo` |
| GAP-REQUIRED-REVIEWERS | Blocked | High: the current GitHub plan cannot enforce reviewers for the apply environment | No apply workflow; deployment and cloud mutation remain disabled | Founder | Upgrade the plan or approve another enforceable approval boundary before apply automation |
| GAP-STATUS-CHECK-CONTEXT | Activation gate | Medium: reusable workflow check names must match configured required checks exactly | Policy lists expected checks and merge authorization denies missing checks | Repository administrator | Run the first authorized caller, record actual check contexts, then configure and verify branch protection |

## Temporary actionlint compatibility

GitHub documents `job.workflow_repository`, `job.workflow_sha`, and
`job.workflow_file_path` as supported job-context properties for identifying
and checking out the source of a reusable workflow. See
the [GitHub Actions contexts reference](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts).
Pinned actionlint 1.7.12 predates those properties; upstream support is tracked
in [actionlint pull request 661](https://github.com/rhysd/actionlint/pull/661).

> This compatibility rule exists solely because the currently pinned actionlint version does not yet recognize officially supported GitHub reusable-workflow context fields.

The rule is limited to reusable workflows that use those three properties and
suppresses only the three corresponding unknown-property messages. Every other
actionlint diagnostic remains fail-closed.

> The compatibility rule must be removed once the pinned actionlint release supports these properties.

## Disabled capabilities

Repository policy keeps `auto_merge_enabled`, `airtable_live_enabled`,
`deployment_enabled`, `edgar_integration_enabled`, and
`orphan_recovery_enabled` false. Cloud mutation, spend, secrets, customer data,
deployment, cutover, and rollback execution require independent authority and
are not implied by mission or merge approval.
