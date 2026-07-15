# ADR-0012: Product Compute Topology

## Status

Proposed

## Context

The product is one Express process plus a static Vite frontend. It has low cohort traffic, PostgreSQL sessions and long synchronous integrations. Kubernetes, Lambda and microservices are unsupported by current evidence.

## Decision

Serve the private-S3 static frontend through CloudFront/WAF and run the API as two ECS Fargate tasks across two AZs behind an ALB. Use one immutable image and add a simple SQS-backed worker from the same image only after jobs are idempotent.

## Alternatives Considered

- App Runner: less explicit network/deployment control.
- Elastic Beanstalk/EC2: unnecessary host lifecycle burden.
- Lambda: poor fit for current process/session/long-call behavior.
- Kubernetes: rejected operational overhead.

## Consequences

Two tasks remove the API process single point; rolling deployments can use circuit-breaker rollback. ALB/NAT add fixed cost. The product must add readiness, graceful shutdown, a non-root container and bounded connections.

## Reversibility And Reconsideration

OCI images and PostgreSQL keep migration practical. Reconsider compute when sustained load, team size, job volume or availability requirements exceed ECS service scaling.

## Sources

- [AWS ECS rolling deployments](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-type-ecs.html)
- [Reference architecture](../product-runtime-reference-architecture.md)
