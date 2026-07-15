# Open Decisions

Session state: ACTIVE — OPERATIONAL REFINEMENT

| ID | Decision | Owner | Needed By | Blocking |
| --- | --- | --- | --- | --- |
| OD-005 | Decide whether product runtime moves to AWS and when | Human + Product + Infrastructure | Before product hosting design | Yes |
| OD-006 | Decide AWS product database architecture | Product + Infrastructure | Before AWS product runtime | Yes |
| OD-007 | Decide whether to retain Cloudflare R2 or migrate uploads to S3 | Product + Infrastructure | Before AWS product runtime | Yes |
| OD-008 | Decide product secrets manager and rotation model | Product + Infrastructure | Before AWS product runtime | Yes |
| OD-012 | Decide whether to upgrade GitHub plan or choose another approval boundary for future apply automation | Human + Infrastructure | Before any apply workflow exists | Yes |
| OD-015 | Decide whether to add automated host patching or keep manual patch windows | Human + Infrastructure | Before routine host use | No |

## Recently Resolved

| ID | Decision | Resolution |
| --- | --- | --- |
| OD-001 | Approve or revise AWS remote-state bootstrap execution | Approved and applied on 2026-07-14 |
| OD-002 | Approve or revise GitHub OIDC bootstrap execution | Approved and applied on 2026-07-14 |
| OD-003 | Configure GitHub environments `terraform-plan` and `terraform-apply` | Completed; required reviewers unavailable, so apply environment remains unused |
| OD-004 | Accept the default first host operating schedule or approve an alternative/budget exception | 08:00-16:00 Monday-Friday in `America/Los_Angeles` accepted for current scope |
| OD-009 | Determine whether PR #1 is superseded by this branch | PR #1 was closed as superseded; PR #2 was squash-merged |
| OD-010 | Configure GitHub repository variables for Terraform plan | Completed |
| OD-011 | Approve hardened control-plane environment apply | Approved and completed in supervised steps |
| OD-013 | Decide whether to complete the residual control-plane apply after AWS validation clears | Resolved; residual apply completed after AWS validation cleared |
| OD-014 | Apply GitHub OIDC plan-role read-policy updates | Applied through policy default version `v4`; read-only verification passed |
| OD-016 | Decide whether to install `actionlint` and `shellcheck` locally or add containerized CI checks | Resolved with a pinned, checksum-verified local installer under `scripts/`; no new CI workflow or recurring cost |
