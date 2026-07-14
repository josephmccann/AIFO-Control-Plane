# Assumptions Memory

The current source of truth is `docs/assumption-register.md`.

High-priority assumptions:

- The control-plane host is not the product runtime.
- The current product live demo remains outside AWS.
- Always-on `m7i-flex.2xlarge` exceeds the $250 budget when compute, public IPv4, and 100 GiB EBS are counted.
- GitHub required environment reviewers are unavailable on the current repository plan, so `terraform-apply` cannot serve as an automated apply approval boundary.
- A 100 GiB root volume fits the initial control-plane host if Docker/model caches remain bounded and product data is not stored on the host.
- Cloudflare R2 remains the product upload storage target until a storage ADR changes that.
- Product PR #186 is near-term context but not current baseline until merged.

Review assumptions before any first apply or product runtime design.
