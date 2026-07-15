# Known Risks

| Severity | Risk | Current Mitigation | Next Action |
| --- | --- | --- | --- |
| Critical | Running an always-on 8 vCPU / 32 GiB host can exceed the $250 monthly budget | EventBridge Scheduler runs the host only 08:00-16:00 Monday-Friday; instance is currently stopped | Keep scheduled operation; require budget exception before always-on use |
| High | Product database, secrets, and storage are not designed in AWS | Product runtime deferred | Create product runtime ADR when approved |
| High | GitHub required reviewers are unavailable for `terraform-apply` | No apply workflow; local IAM Identity Center apply only after approval packet | Decide future approval boundary before automation |
| High | Public IPv4 host has no ingress but still has internet-routable address | Zero SG ingress, SSM-only, IMDSv2 | Review private subnet migration later |
| Medium | 100 GiB root volume can fill if Docker/model caches are not pruned | Start/stop runbook includes disk hygiene; root volume configurable | Measure disk usage during routine host use |
| High | Merged Stripe/account surfaces are not multi-tenant production-ready | Feature flag defaults off; one-company binding; session-scoped routes and aggregate-only observations | Design per-tenant connector authorization/account truth before shared staging |
| Medium | Session Manager transcript logging can capture sensitive terminal output | CloudWatch Logs retention is 30 days; S3 duplication omitted; runbooks warn operators | Review after first sessions and before handling customer data |
| Low | Scheduler stop action can interrupt active work at 16:00 Pacific | Manual override documented; next scheduled stop still applies after schedules exist | Use manual stop/start consciously and adjust schedule through Terraform if the working pattern changes |
