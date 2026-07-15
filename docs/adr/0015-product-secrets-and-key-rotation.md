# ADR-0015: Product Secrets And Key Rotation

## Status

Proposed

## Context

Database, session, QBO, Anthropic, GMI/R2 credentials are environment values. QBO tokens use one unversioned AES key, preventing safe rotation.

## Decision

Use environment-specific AWS Secrets Manager secrets, customer-managed KMS where justified, ECS task-role retrieval and no static AWS keys. Implement active/previous session and QBO keyrings, ciphertext key version, idempotent token re-encryption, and audited break-glass access.

## Alternatives Considered

- Parameter Store for secrets: workable but weaker native secret lifecycle for this small inventory.
- Existing platform secrets: rejected for the target because custody/audit/recovery remain split.
- One immutable QBO key: rejected compromise/key-loss blast radius.

## Consequences

The product must support secret refresh and dual versions. Vendor secrets rotate manually when provider APIs require it; RDS credentials may rotate automatically after staging proof. Access policies name exact secrets.

## Reversibility And Reconsideration

Secret values can move to another managed vault through controlled rotation. Reconsider vault tooling only when multi-cloud or compliance evidence justifies it.

## Sources

- [AWS Secrets Manager authorization](https://docs.aws.amazon.com/service-authorization/latest/reference/list_awssecretsmanager.html)
- [ECS IAM roles](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/security-iam-roles.html)
