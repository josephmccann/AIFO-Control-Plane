# ADR-0018: Product Domain And TLS Ownership

## Status

Proposed

## Context

`demo.getaifo.com` serves the current app, while `ai.fo` redirects to a domain marketplace and the frontend claims `ai.fo` canonicals. QBO requires exact registered HTTPS callbacks.

## Decision

Use a founder-controlled `app.getaifo.com` production name and `staging.getaifo.com` unless ownership of `ai.fo` is proven and separately approved. Founder controls registrar/DNS recovery and hardware MFA. Use CloudFront/Route 53/ACM after an approved cutover plan; API remains same-origin `/api`.

## Alternatives Considered

- Use `ai.fo` immediately: rejected until ownership and recovery are proven.
- Separate API domain: rejected unnecessary CORS/cookie/OAuth complexity.

## Consequences

DNS, certificate and QBO production callback changes are hard cutover gates and require explicit later approval. Old callback/domain stays available during validated rollback overlap when provider rules allow.

## Reversibility And Reconsideration

DNS is reversible within TTL and provider constraints. Reconsider the branded domain only after documented control and migration tests.

## Sources

- [Intuit authorization FAQ](https://developer.intuit.com/app/developer/qbo/docs/develop/authentication-and-authorization/faq)
- Live DNS/HTTP evidence collected 2026-07-15
