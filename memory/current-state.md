# Current State

Date: 2026-07-16

Session state: ACTIVE — OPERATIONAL REFINEMENT

## Repository

- Repository: `josephmccann/AIFO-Control-Plane`
- Latest main commit at checkpoint start: `b9e1b539474efa30086d9031b3118cfe241ffa28`
- Product repository: `/Users/joemccann/code/AI.FO-Demo`
- Product baseline observed earlier: `8df211e02f274d0a812771327c69b6d5b6c040d2`
- Current product remains a working financial intelligence platform with deterministic financial engine, QBO ingestion, CSV ingestion, PostgreSQL, R2, AI narrative generation, and verifier support.

## AWS Baseline

- AWS account: `350480401760`
- Region: `us-west-2`
- Terraform state bucket: `aifo-terraform-state-350480401760-us-west-2`
- Terraform state key: `control-plane/terraform.tfstate`
- Backend locking: native S3 lockfile
- EC2 instance: `i-0254a9e2fcbcdebd7`
- EC2 state: `stopped`
- Instance type: `m7i-flex.2xlarge`
- Root volume: 100 GiB encrypted gp3
- Administration: SSM Session Manager only
- SSH key: none
- Inbound security-group rules: zero
- IMDSv2: required
- Termination protection: enabled
- Public IPv4: assigned only while running for outbound egress; released while stopped

## Deployed Control-Plane Resources

- CloudTrail: `arn:aws:cloudtrail:us-west-2:350480401760:trail/aifo-control-plane-management-events`
- CloudTrail bucket: `aifo-control-plane-cloudtrail-350480401760-us-west-2`
- VPC: `vpc-0f73b1daaa9fc17ab`
- Public subnet: `subnet-03ce35314c75b8e1f`
- Security group: `sg-0190e01bae800bb1a`
- S3 gateway endpoint: `vpce-058114f11531d5fdd`
- EC2 role/profile: `aifo-control-plane-ec2-ssm-role`, `aifo-control-plane-ec2-profile`
- Session Manager log group: `/aifo/control-plane/session-manager`
- Session Manager KMS key: `arn:aws:kms:us-west-2:350480401760:key/e36ac1c5-105c-42c1-92f9-06fcf02cb772`
- Scheduler group: `aifo-control-plane-host`
- Scheduler role: `aifo-control-plane-scheduler-role`
- Scheduler DLQ: `https://sqs.us-west-2.amazonaws.com/350480401760/aifo-control-plane-scheduler-dlq`
- Scheduler start: 08:00 Monday-Friday, `America/Los_Angeles`
- Scheduler stop: 16:00 Monday-Friday, `America/Los_Angeles`

## Bootstrap Resources

- OIDC provider: `arn:aws:iam::350480401760:oidc-provider/token.actions.githubusercontent.com`
- Plan role: `arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Plan`
- Apply role: `arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Apply`
- State access policy: `arn:aws:iam::350480401760:policy/AIFO-GitHubActions-Terraform-StateAccess`
- Plan read policy: `arn:aws:iam::350480401760:policy/AIFO-GitHubActions-Terraform-PlanReadAccess`
- Plan read policy default version: `v4`
- Plan trust subject: `repo:josephmccann/AIFO-Control-Plane:environment:terraform-plan`
- Apply trust subject: `repo:josephmccann/AIFO-Control-Plane:environment:terraform-apply`
- OIDC audience: `sts.amazonaws.com`
- Apply role: state-access-only, no inline policies

## Verification

- Local Terraform plan: `0 to add, 0 to change, 0 to destroy`
- Latest GitHub Terraform Plan: https://github.com/josephmccann/AIFO-Control-Plane/actions/runs/29378532712
- GitHub plan classification: exit code `0`, `0` add / `0` change / `0` destroy, result `clean`
- Drift gate behavior verified:
  - `workflow_dispatch` exit `0`: clean, pass
  - `workflow_dispatch` exit `2`: unexpected drift, fail
  - `pull_request` exit `2`: proposed change, pass
- Session Manager connectivity test succeeded after host deployment.
- Session Manager logging reached `/aifo/control-plane/session-manager`.
- Current EC2 state is stopped, so active SSM shell access requires a start action inside an approved window or emergency override.

## Current Warnings

- GitHub Actions emits Node 20 deprecation warnings for upstream actions.
- `terraform-apply` environment exists but required reviewers are unavailable on the current repository plan.
- No apply workflow exists and none should be added until an enforceable approval boundary exists.
- Always-on `m7i-flex.2xlarge` exceeds the $250 budget posture; scheduled operation remains required.
- Product runtime infrastructure is not deployed.

## Product Runtime Boundary

No AWS product runtime, production database, product secrets, QBO callback migration, product storage migration, domain/TLS migration, or customer-data hosting has been approved or deployed from this repository.

## Engineering Operating System

- EOS version: `1.0.0`
- Engineering Constitution SHA-256: `a255c0976949d8acae91f7d46e85cc083a15e242ccbd62e587c4e3163b29265e`
- Reviewed Control Plane prerequisite: `8eb0554e1b0796485ad5354dcc5fed02c633b343`
- Reviewed Demo telemetry prerequisite: `ca56ecc9740edce719df8584b3cd345286c3a777`
- Independently reviewed Demo Package 8: `eddc1ca024305d222ef716a27005472590d0a087`
- Independently reviewed Control Plane Package 9: `f422b5c704c34e0ed4ec939f91e36cf1b1bf58a9`
- Current Control Plane repair kernel awaiting independent review: `59dc1b0fa60786dfa32ac55c41029e2a485a7b11`
- Current independently reviewed Demo PR head: `18a44a0f05ebed6b9f52587081c18abf47972eb9`
- Final reconciled Demo `origin/master`: `52ca01c7c8b034b212feede58ddcc77d9c37c388`
- Final reconciliation inspected Demo commits `83e76fd790ad94c040ebd6cd955f98ffb81cd4e5` and `52ca01c7c8b034b212feede58ddcc77d9c37c388`; they had no direct EOS file overlap and were merged without conflicts.
- Control Plane PR 16 and Demo PR 202 are open and unmerged.
- Private reusable-workflow transport uses the founder-approved `access_level=user` setting. Exact caller repository, owner, workflow identity, workflow provenance, and evidence checks are the fail-closed trust boundary.
- Live Demo caller run `29558117893` passed exact caller authorization, the reconciled first-policy bootstrap, mission history, and the frozen-path gate. It then failed closed because the mission omitted three exact generated-client validation paths and because the package detector treated a newly added test command as weakening. Mission issue 201 now includes only those three exact paths, with declaration SHA-256 `b91e5315d29c8ba40134efd6d38e366781f30d2070cd18c8739c2ffd3ced8e23`. The detector repair at `32f37e247700ca5b8ef52b2a9844f8af21088d1f` permits only a test-command-only strengthening, while unrelated package changes remain ambiguous and removals or changes remain fail-closed.
- Live Demo caller run `29559793584` passed caller authorization, mission history, tier/path, and frozen-path validation, then failed closed at test integrity because the authenticated kernel action did not materialize the Engineering Constitution required for mission-readiness verification. Kernel content commit `59dc1b0fa60786dfa32ac55c41029e2a485a7b11` copies only that exact additional file, verifies byte identity, and rejects missing or symlinked source content. Every reusable workflow now pins that exact kernel pending independent review and a live rerun.
- Auto-merge, deployment, cloud mutation, live Airtable writes, orphan mutation, and EDGAR integration remain disabled.
- Neither EOS branch has been merged.
