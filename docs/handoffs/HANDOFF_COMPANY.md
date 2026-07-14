# AI.FO Company Handoff

## Purpose

Canonical starting context for company-level constraints that affect infrastructure decisions.

## Company Context

AI.FO is led by a solo founder. The company needs leverage, not unnecessary operational complexity. Every artifact is expected to withstand review by experienced engineers, security reviewers, investors, partners, and future employees.

## Operating Philosophy

- Trust is earned through evidence, transparency, accurate execution, and clear limitations.
- Better context produces better decisions.
- Missing information is an active workflow.
- Deterministic financial truth comes before generative interpretation.
- Human authority remains central.
- Auditability must not become surveillance.
- Build for decisions, not engagement.
- Best-in-class work means clarity, restraint, maintainability, security, and cost discipline.

## Current Strategic Priorities

1. Put AI.FO into real founder hands.
2. Complete structured founder and finance-leader discovery.
3. Identify design partners.
4. Strengthen fundraising narrative with product evidence.
5. Build a secure, reproducible control plane without distracting from customer learning.

## Current Infrastructure State

- AWS account exists.
- Root MFA is enabled.
- IAM Identity Center is enabled.
- `AIFO-Platform-Admin` is assigned for human administration.
- Manual monthly AWS budget exists at $250.
- Private GitHub repository exists.
- Terraform scaffold exists and has passed earlier offline validation.
- No deployment has occurred.

## Decision Discipline

Every material infrastructure decision must record:

- current product requirement supported;
- founder principle implicated;
- known facts;
- assumptions;
- unknowns;
- information sources reviewed;
- decision;
- why now;
- alternatives;
- security, privacy, reliability, cost, operational, solo-founder, product, lineage, auditability, reversibility, and rollback effects;
- evidence that would cause reconsideration.

## Current Company-Level Risk

The largest immediate infrastructure risk is spending founder time and budget on systems that do not yet support the working product or design-partner path. The second-largest risk is under-documenting security and operational boundaries before AWS resources are created.
