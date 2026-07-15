# Assumptions Memory

The current source of truth is `docs/assumption-register.md`.

High-priority assumptions:

- The control-plane host is not the product runtime.
- The current product live demo remains outside AWS.
- Always-on `m7i-flex.2xlarge` exceeds the $250 budget when compute, public IPv4, and 100 GiB EBS are counted.
- GitHub required environment reviewers are unavailable on the current repository plan, so `terraform-apply` cannot serve as an automated apply approval boundary.
- A 100 GiB root volume fits the initial control-plane host if Docker/model caches remain bounded and product data is not stored on the host.
- The default 08:00-16:00 Monday-Friday `America/Los_Angeles` operating schedule is acceptable for first deployment unless the approval packet chooses another schedule.
- A first copy of CloudTrail management events plus low-volume CloudWatch Session Manager logs should add only a small recurring cost relative to the $250 budget.
- Cloudflare R2 remains the product upload storage target until a storage ADR changes that.
- Product PR #186 is merged at `3329c99`; its connector/account implementation is current product baseline.

Review assumptions before any first apply or product runtime design.
