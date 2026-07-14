# Open Decisions

| ID | Decision | Owner | Needed By | Blocking |
| --- | --- | --- | --- | --- |
| OD-001 | Approve or revise AWS remote-state bootstrap execution | Human + Infrastructure | Before first GitHub plan | Yes |
| OD-002 | Approve or revise GitHub OIDC bootstrap execution | Human + Infrastructure | Before first GitHub plan | Yes |
| OD-003 | Configure protected GitHub environments `terraform-plan` and `terraform-apply` | Human + Infrastructure | Before OIDC plan workflow succeeds | Yes |
| OD-004 | Accept budget impact of an 8 vCPU / 32 GiB host or choose smaller/scheduled host | Human + Infrastructure | Before first apply | Yes |
| OD-005 | Decide whether product runtime moves to AWS and when | Human + Product + Infrastructure | Before product hosting design | Yes |
| OD-006 | Decide AWS product database architecture | Product + Infrastructure | Before AWS product runtime | Yes |
| OD-007 | Decide whether to retain Cloudflare R2 or migrate uploads to S3 | Product + Infrastructure | Before AWS product runtime | Yes |
| OD-008 | Decide product secrets manager and rotation model | Product + Infrastructure | Before AWS product runtime | Yes |
| OD-009 | Determine whether PR #1 is superseded by this branch | Human | Before merging handoff docs | No |
