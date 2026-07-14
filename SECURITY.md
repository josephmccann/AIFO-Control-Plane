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
- Terraform state stored remotely only after approved bootstrap.
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

- Control-plane Terraform is scaffolded but not applied.
- The EC2 host design has no inbound security-group rules and no SSH key.
- The initial host uses public IPv4 only for outbound egress and cost avoidance.
- The GitHub OIDC bootstrap root has created separate plan and apply roles.
- The apply role has no managed policies by default.
- Product runtime secrets, database, and storage are not yet provisioned in AWS.

## Required Pre-Deployment Review

Before any AWS bootstrap or apply:

- verify CloudTrail status;
- verify the AWS account ID and region;
- review Terraform plan output;
- confirm protected GitHub environments;
- confirm remote-state bucket name and lockfile behavior;
- confirm EC2 instance cost against the $250 budget;
- confirm no public ingress rules are introduced;
- confirm rollback and emergency access runbooks are current.
