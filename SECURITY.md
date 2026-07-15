# Security

Session state: ACTIVE — OPERATIONAL REFINEMENT

## Scope

This repository controls AWS infrastructure for the AI.FO control plane in AWS account `350480401760`, region `us-west-2`. The approved current-scope baseline is deployed and operationally complete. Product runtime infrastructure is not deployed.

## Reporting Security Issues

Do not open a public issue for suspected vulnerabilities, leaked credentials, customer data exposure, or infrastructure access concerns. Contact the repository owner privately and include:

- affected file, workflow, resource, or dependency;
- observed behavior;
- reproduction steps if safe;
- whether any secret or customer data may have been exposed.

## Non-Negotiable Controls

- No long-lived AWS access keys.
- No committed secrets.
- No public SSH.
- Systems Manager Session Manager for EC2 administration.
- IMDSv2 required on EC2 instances.
- Terraform state stored remotely in the approved S3 backend.
- GitHub Actions AWS access through OIDC and short-lived credentials.
- Separate human, plan, apply, and EC2 runtime permissions.
- Default deny for inbound network access.
- No product runtime deployment without a separate approval gate.

## Current Security Status

- Terraform remote state is stored in `aifo-terraform-state-350480401760-us-west-2`.
- GitHub OIDC provider is deployed.
- Plan role: `arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Plan`.
- Apply role: `arn:aws:iam::350480401760:role/AIFO-GitHubActions-Terraform-Apply`.
- Plan-role policy default version is `v4` and remains read-only.
- Apply role is unchanged and has only Terraform state access.
- OIDC trust is unchanged and restricted to exact repository/environment subjects.
- No apply workflow exists.
- `terraform-apply` environment exists but must remain unused because required reviewer protection is unavailable.
- EC2 instance `i-0254a9e2fcbcdebd7` exists and is stopped.
- EC2 administration is SSM-only; no SSH key is configured.
- Host security group has zero inbound rules.
- IMDSv2 is required.
- CloudTrail management-event logging is enabled.
- Session Manager logging is configured to encrypted CloudWatch Logs with 30-day retention.
- EventBridge Scheduler is configured for weekday start/stop and targets only the Terraform-managed instance.

## Credential Handling

Allowed:

- IAM Identity Center sessions for approved human AWS work.
- GitHub Actions OIDC role assumption for approved workflows.
- Non-secret GitHub repository variables such as role ARNs and backend names.

Not allowed:

- AWS access keys in GitHub secrets.
- AWS access keys in local files committed to Git.
- Secrets in Terraform variables committed to Git.
- Copying secrets into issues, PRs, documentation, or chat history.

## Product Data Sensitivity

AI.FO works with accounting data, QBO connections, AI prompts, verification, telemetry, uploads, and decision-support artifacts. Future runtime infrastructure must preserve:

- deterministic financial truth before AI interpretation;
- source lineage and provenance;
- separation between raw accounting rows and AI narrative inputs;
- customer data minimization;
- auditability without surveillance.

## Required Review Before Any Future Infrastructure Mutation

- Confirm AWS account and region.
- Confirm Terraform plan output.
- Confirm GitHub plan gate is clean on `main`.
- Confirm the EC2 instance operating schedule and budget posture.
- Confirm no public ingress rules are introduced.
- Confirm Session Manager logging retention and sensitive-output limitations.
- Confirm rollback and emergency access runbooks are current.
- Apply only with authenticated IAM Identity Center access after explicit human approval.
