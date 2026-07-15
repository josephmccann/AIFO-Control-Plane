# ADR-0021: Product Deployment And Rollback

## Status

Proposed

## Context

The product build is testable, but production deployment configuration and rollback are platform-owned and schema mutation is fragmented. The `3329c99` Replit publish succeeded, while another automatic schema-diff attempt proposed destructive drops and was canceled. Startup health also returned transient HTTP 500 responses before stabilizing.

## Decision

Build one immutable OCI image and versioned frontend artifact with commit/lockfile/provenance evidence. Promote by digest through staging, run one-off audited migrations, require explicit generated-SQL review and stop on destructive/unexplained proposals. Separate liveness from dependency/schema readiness and require a consecutive-success stabilization window. Require founder production approval, use ECS health/alarm rollback, retain the prior frontend prefix/image, and test application/migration recovery before launch.

## Alternatives Considered

- Build separately per environment: rejected artifact drift.
- Console deployment: rejected reproducibility/audit gaps.
- Automatic production deploy from `main`: rejected absent enforceable approval and migration gates.

## Consequences

CI/CD and product code need container, readiness, graceful shutdown, migration and smoke-test work. Failed schema/data migrations may require forward-fix or PITR rather than simple code rollback.

## Reversibility And Reconsideration

Rolling ECS revisions are reversible. Add canary/blue-green only if release frequency/impact evidence justifies added machinery.

## Sources

- [ECS deployment failure detection](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-failure-detection.html)
- [Reference architecture](../product-runtime-reference-architecture.md)
