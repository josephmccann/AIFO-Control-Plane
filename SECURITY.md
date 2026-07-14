# Security

## Scope

This repository controls AWS infrastructure design for AI.FO. Terraform remote-state and GitHub OIDC bootstrap infrastructure has been deployed. A partial hardened control-plane apply created audit, logging, network, IAM, and scheduler prerequisite resources. The control-plane host and product runtime have not been deployed.

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
- Control-plane Terraform is partially applied; EC2 launch is blocked by AWS `PendingVerification`.
- The EC2 host design has no inbound security-group rules and no SSH key.
- The initial host uses public IPv4 only for outbound egress and cost avoidance.
- The GitHub OIDC bootstrap root has created separate plan and apply roles.
- The plan role is used by the GitHub plan workflow through OIDC and has the approved read-only refresh policy for the hardened resource graph.
- The `terraform-apply` GitHub environment exists, but required reviewers are unavailable on the current repository plan and the environment must remain unused.
- The apply role has only Terraform state access and no infrastructure mutation permissions.
- No apply workflow exists or may be created under the current GitHub approval limitation.
- Product runtime secrets, database, and storage are not yet provisioned in AWS.
- CloudTrail management-event logging, Session Manager CloudWatch logging with KMS encryption, and Scheduler prerequisite resources are partially deployed.
- No EC2 instance exists; no Scheduler start or stop schedule exists yet.

## Required Pre-Deployment Review

Before any resumed control-plane apply:

- verify AWS account regional validation has cleared for EC2 launch;
- verify the existing CloudTrail trail, log bucket, lifecycle, and log-file validation settings;
- verify the AWS account ID and region;
- review Terraform plan output;
- confirm remote-state bucket name and lockfile behavior;
- confirm EC2 schedule and cost against the $250 budget;
- confirm Session Manager logging retention and sensitive-output limitations;
- confirm the residual plan contains only the EC2 host, Scheduler inline policy, and Scheduler start/stop schedules;
- confirm no public ingress rules are introduced;
- confirm rollback and emergency access runbooks are current.
- apply only with an authenticated IAM Identity Center session after an explicit approval packet.
