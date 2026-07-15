# Deployment Readiness Review

Status: AWS control-plane baseline operationally complete for the approved current scope.

Session state: ACTIVE — OPERATIONAL REFINEMENT

This review is not approval to deploy product runtime infrastructure or to create an apply workflow.

## Current Verified State

- AWS account: `350480401760`
- Region: `us-west-2`
- Latest main commit inspected: `707e6298ed558fde06faea99b7e4b99b8b2b7adc`
- EC2 instance: `i-0254a9e2fcbcdebd7`
- EC2 state: `stopped`
- Local Terraform plan: `0 to add, 0 to change, 0 to destroy`
- GitHub Terraform Plan: https://github.com/josephmccann/AIFO-Control-Plane/actions/runs/29380920338
- GitHub plan classification: exit code `0`, `0` add / `0` change / `0` destroy, result `clean`
- Plan-role policy default version: `v4`
- Apply role: unchanged and state-access-only
- OIDC trust: unchanged
- Scheduler: unchanged
- Product runtime: not deployed

## Completed Preparation

- [x] Product runtime inventory created.
- [x] Control-plane fit assessment created.
- [x] Founder principle traceability matrix created.
- [x] Assumption register created.
- [x] Execution plan created.
- [x] ADR framework created.
- [x] Bootstrap runbook created.
- [x] Cost model created.
- [x] Session Manager logging design created.
- [x] CloudTrail management-events baseline designed and deployed.
- [x] Session Manager logging deployed.
- [x] EventBridge Scheduler start/stop automation deployed.
- [x] GitHub plan workflow configured.
- [x] GitHub plan drift gate completed.
- [x] Comprehensive product runtime inventory/data flows/classification completed in a draft decision package.
- [x] Beta requirements, options analysis, reference architecture, threat model, migration gate definitions, cost model and Proposed ADRs completed.

## Completed Bootstrap

- [x] Remote-state bucket created: `aifo-terraform-state-350480401760-us-west-2`.
- [x] Remote-state post-apply plan result: no drift.
- [x] GitHub OIDC provider created: `arn:aws:iam::350480401760:oidc-provider/token.actions.githubusercontent.com`.
- [x] Plan role created: `arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Plan`.
- [x] Apply role created: `arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Apply`.
- [x] State access policy created: `arn:aws:iam::350480401760:policy/AIFO-GitHubActions-Terraform-StateAccess`.
- [x] Plan read policy created and updated through default version `v4`.
- [x] Plan trust subject verified: `repo:josephmccann/AIFO-Control-Plane:environment:terraform-plan`.
- [x] Apply trust subject verified: `repo:josephmccann/AIFO-Control-Plane:environment:terraform-apply`.
- [x] OIDC audience verified: `sts.amazonaws.com`.
- [x] Apply role verified with only Terraform state access and no inline policies.

## Completed Control-Plane Deployment

- [x] CloudTrail management-events trail created and logging enabled.
- [x] Dedicated CloudTrail S3 log bucket created with public access blocked, versioning, encryption, lifecycle, and TLS-only policy.
- [x] VPC, public subnet, internet gateway, route table, S3 gateway endpoint, and no-ingress security group created.
- [x] Session Manager CloudWatch log group, KMS key, and preferences document created.
- [x] EC2 host created.
- [x] EC2 host verified and manually stopped after deployment validation.
- [x] Scheduler inline policy created.
- [x] Scheduler start schedule created.
- [x] Scheduler stop schedule created.
- [x] Scheduler targets only `i-0254a9e2fcbcdebd7`.
- [x] Session Manager connectivity test completed.
- [x] Session Manager logging reached `/aifo/control-plane/session-manager`.

## Not Deployed

- [ ] Product runtime infrastructure.
- [ ] Apply workflow.
- [ ] Product database.
- [ ] Product secrets.
- [ ] Product object storage migration.
- [ ] Domain/TLS/QBO callback migration.
- [ ] Founder approval of product requirements and ADR-0011 through ADR-0022.
- [ ] Product prerequisite hardening.
- [ ] Product staging environment and validation.
- [ ] Database/object restore and migration rehearsal.
- [ ] Founder recovery exercise.
- [ ] Product production cutover.

## Operational Gates

- [x] Main/manual Terraform Plan workflow fails on detailed exit code `2`.
- [x] Pull request Terraform Plan workflow allows detailed exit code `2` as proposed change.
- [x] Latest main/manual plan is clean.
- [x] EC2 instance is stopped.
- [x] Always-on host operation is not approved.

## Current Blockers

- GitHub required environment reviewers are unavailable on the current repository plan.
- `terraform-apply` exists but cannot enforce reviewer protection and must remain unused.
- Apply role has no infrastructure mutation permissions by design; future permissions require review.
- Apply workflow intentionally absent.
- Product runtime analysis is complete, but the design and deployment are not approved.
- `ai.fo` application ownership/control is not proven; it currently redirects to a domain marketplace while product canonicals claim it.
- Current GMI verifier data handling is not acceptable for customer data without negotiated evidence or replacement.
- Database/object backup and restore, customer deletion, QBO key rotation, tenant integration testing, upload integrity and controlled rollback gates have not passed.

The authoritative product migration gate table is [product-runtime-migration-readiness.md](product-runtime-migration-readiness.md). Staging creation requires architecture, cost, account/IAM, product-prerequisite and exact Terraform-plan approval. Production cutover requires all MR-01 through MR-33 gates to pass plus explicit customer-data, DNS/TLS and QBO callback approval.
