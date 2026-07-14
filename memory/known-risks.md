# Known Risks

| Severity | Risk | Current Mitigation | Next Action |
| --- | --- | --- | --- |
| Critical | Running an always-on 8 vCPU / 32 GiB host can exceed the $250 monthly budget | Documented in ADR-0005 | Human decision before apply |
| High | AWS account regional validation currently blocks EC2 launch in `us-west-2` | Apply stopped; no instance exists | Wait for validation email or open AWS Support account-management case |
| High | Control-plane Terraform state is partially applied | Post-failure plan shows only the EC2 instance and dependent Scheduler resources remain | Re-plan before any renewed apply; do not run destroy |
| High | Product database, secrets, and storage are not designed in AWS | Product runtime deferred | Create product runtime ADR when approved |
| High | GitHub required reviewers are unavailable for `terraform-apply` | No apply workflow; local IAM Identity Center apply only after approval packet | Decide future approval boundary before automation |
| High | Public IPv4 host has no ingress but still has internet-routable address | Zero SG ingress, SSM-only, IMDSv2 | Review private subnet migration later |
| Medium | 100 GiB root volume can fill if Docker/model caches are not pruned | Start/stop runbook includes disk hygiene; root volume configurable | Measure disk usage after deployment |
| Medium | Product PR #186 may change connector infrastructure requirements | Labeled as near-term, not baseline | Re-review after merge |
| Medium | Session Manager transcript logging can capture sensitive terminal output | CloudWatch Logs retention is 30 days; S3 duplication omitted; runbooks warn operators | Review after first sessions and before handling customer data |
| Low | Scheduler stop action can interrupt active work at 16:00 Pacific | Manual override documented; next scheduled stop still applies after schedules exist | Use manual stop/start consciously and adjust schedule through Terraform if the working pattern changes |
