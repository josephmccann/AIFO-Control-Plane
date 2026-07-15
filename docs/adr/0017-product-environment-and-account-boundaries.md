# ADR-0017: Product Environment And Account Boundaries

## Status

Proposed

## Context

AWS account `350480401760` is the Organizations management account and currently contains the control plane. Mixing production customer data, organization authority and nonproduction increases blast radius.

## Decision

Use local, staging and production environments. Keep staging/control in the current account with isolated resources; create one dedicated organization member account for production. Do not create per-tenant accounts or a complex OU program.

## Alternatives Considered

- One shared account: operationally simple, but weak management/control/nonproduction/production isolation.
- Three or more environment accounts now: stronger isolation but unnecessary founder overhead.

## Consequences

Cross-account access, billing and bootstrap need documentation. Production compromise is less likely to control the organization or nonproduction. Account creation and IAM changes require explicit later approval.

## Reversibility And Reconsideration

Additional accounts can be introduced later. Reconsider boundaries if compliance, team growth, customer contracts or incident evidence requires security/log-archive accounts.

## Sources

- [Reference architecture](../product-runtime-reference-architecture.md)
- Read-only `organizations:DescribeOrganization` evidence collected 2026-07-15
