# Assumptions Memory

The current source of truth is `docs/assumption-register.md`.

High-priority assumptions:

- The control-plane host is not the product runtime.
- The current product live demo remains outside AWS.
- Always-on `m7i-flex.2xlarge` exceeds the $250 budget when compute, public IPv4, and EBS are counted.
- Protected GitHub environments will be available in the repository.
- Cloudflare R2 remains the product upload storage target until a storage ADR changes that.
- Product PR #186 is near-term context but not current baseline until merged.

Review assumptions before any first apply or product runtime design.
