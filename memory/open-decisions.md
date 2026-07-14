# Open Decisions

| ID | Decision | Owner | Needed By | Blocking |
| --- | --- | --- | --- | --- |
| OD-004 | Accept the default first host operating schedule or approve an alternative/budget exception | Human + Infrastructure | Before first apply | Yes |
| OD-005 | Decide whether product runtime moves to AWS and when | Human + Product + Infrastructure | Before product hosting design | Yes |
| OD-006 | Decide AWS product database architecture | Product + Infrastructure | Before AWS product runtime | Yes |
| OD-007 | Decide whether to retain Cloudflare R2 or migrate uploads to S3 | Product + Infrastructure | Before AWS product runtime | Yes |
| OD-008 | Decide product secrets manager and rotation model | Product + Infrastructure | Before AWS product runtime | Yes |
| OD-011 | Approve hardened control-plane environment apply | Human + Infrastructure | After reviewed plan, cost acceptance, and schedule acceptance | Yes |
| OD-012 | Decide whether to upgrade GitHub plan or choose another approval boundary for future apply automation | Human + Infrastructure | Before any apply workflow exists | Yes |
| OD-013 | Decide whether to resume the partial control-plane apply after AWS validation clears | Human + Infrastructure | After read-only re-plan shows only expected residual resources | Yes |

## Recently Resolved

| ID | Decision | Resolution |
| --- | --- | --- |
| OD-001 | Approve or revise AWS remote-state bootstrap execution | Approved and applied on 2026-07-14 |
| OD-002 | Approve or revise GitHub OIDC bootstrap execution | Approved and applied on 2026-07-14 |
| OD-003 | Configure GitHub environments `terraform-plan` and `terraform-apply` | Completed; required reviewers unavailable, so apply environment remains unused |
| OD-010 | Configure GitHub repository variables for Terraform plan | Completed |
| OD-009 | Determine whether PR #1 is superseded by this branch | PR #1 was closed as superseded; PR #2 was squash-merged |
| OD-014 | Apply GitHub OIDC plan-role read-policy update | Applied on 2026-07-14; read-only verification passed |
