# Known Risks

| Severity | Risk | Current Mitigation | Next Action |
| --- | --- | --- | --- |
| Critical | Running an always-on 8 vCPU / 32 GiB host can exceed the $250 monthly budget | Documented in ADR-0005 | Human decision before apply |
| High | Product database, secrets, and storage are not designed in AWS | Product runtime deferred | Create product runtime ADR when approved |
| High | Terraform bootstrap would create IAM and S3 resources | Approval gate | Do not run apply without approval |
| High | Public IPv4 host has no ingress but still has internet-routable address | Zero SG ingress, SSM-only, IMDSv2 | Review private subnet migration later |
| Medium | Plan role custom policy may miss a read action during first GitHub plan | Additional policy ARN escape hatch | Refine only from observed failure |
| Medium | Product PR #186 may change connector infrastructure requirements | Labeled as near-term, not baseline | Re-review after merge |
| Medium | Current control-plane has no Session Manager log retention design | Runbook notes future work | Add monitoring work item |
