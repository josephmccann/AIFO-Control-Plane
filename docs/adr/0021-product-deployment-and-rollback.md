# ADR-0021: Product Deployment And Rollback

## Status

Proposed

## Context

The product build is testable, but production deployment configuration and rollback are platform-owned and schema mutation is fragmented.

## Decision

Build one immutable OCI image and versioned frontend artifact with commit/lockfile/provenance evidence. Promote by digest through staging, run one-off audited migrations, require founder production approval, use ECS health/alarm rollback and retain the prior frontend prefix/image. Test application and migration recovery before launch.

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
