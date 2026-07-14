# Security

## Scope

This repository controls AWS infrastructure design for AI.FO. Terraform remote-state and GitHub OIDC bootstrap infrastructure has been deployed. The control-plane host and product runtime have not been deployed.

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

## Credential Handling

Allowed:

- IAM Identity Center sessions for approved human AWS work.
- GitHub Actions OIDC role assumption for approved workflows.
- Non-secret GitHub repository variables such as role ARNs and backend names.

Not allowed:

- AWS access keys in GitHub secrets.
- AWS access keys in local files committed to Git.
- Secrets in Terraform variables committed to Git.
- Copying secrets into issue, PR, or chat history.

## Product Data Sensitivity

AI.FO works with accounting data, QBO connections, AI prompts, verification, telemetry, uploads, and decision-support artifacts. Future runtime infrastructure must preserve:

- deterministic financial truth before AI interpretation;
- source lineage and provenance;
- separation between raw accounting rows and AI narrative inputs;
- customer data minimization;
- auditability without surveillance.

## Current Security Status

- Bootstrap Terraform has been applied for remote state and GitHub OIDC.
- Control-plane host Terraform has not been applied.
- The EC2 host design has no inbound security-group rules and no SSH key.
- The initial host uses public IPv4 only for outbound egress and cost avoidance.
- The GitHub OIDC bootstrap root has created separate plan and apply roles.
- The plan role is used by the GitHub plan workflow through OIDC.
- The `terraform-apply` GitHub environment exists, but required reviewers are unavailable on the current repository plan and the environment must remain unused.
- The apply role has only Terraform state access and no infrastructure mutation permissions.
- No apply workflow exists or may be created under the current GitHub approval limitation.
- Product runtime secrets, database, and storage are not yet provisioned in AWS.

## Required Pre-Deployment Review

Before any control-plane apply:

- verify CloudTrail status;
- verify the AWS account ID and region;
- review Terraform plan output;
- confirm remote-state bucket name and lockfile behavior;
- confirm EC2 schedule and cost against the $250 budget;
- confirm no public ingress rules are introduced;
- confirm rollback and emergency access runbooks are current.
- apply only with an authenticated IAM Identity Center session after an explicit approval packet.
