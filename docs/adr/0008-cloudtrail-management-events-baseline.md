# ADR-0008: Create A Multi-Region CloudTrail Management Events Baseline

## Status

Accepted for first control-plane deployment

## Current Product Requirement Supported

The control plane must provide auditable evidence for IAM, STS, EC2, SSM, S3, Terraform, and operator actions before the first host is deployed.

## Founder Principle Or Constitutional Principle Implicated

Principles 1, 6, 7, 14, 18, and 20: trust through evidence, preserved decision state, decision process, transparent limits, auditability without surveillance, and disciplined work.

## Known Facts

- Read-only inspection on 2026-07-14 returned no CloudTrail trails in `us-west-2`.
- AWS recommends one trail that logs management events in all Regions as a security best practice.
- The first copy of ongoing management events delivered to S3 by trails is free, but S3 storage and requests still cost money.
- CloudTrail log-file integrity validation creates signed digest files that support later verification.

## Assumptions

- Account-level CloudTrail is appropriate because AWS Organizations was not provided as part of the current baseline. Confidence: high.
- 365-day CloudTrail retention is sufficient for initial investor/customer diligence and solo-founder operations. Confidence: medium.
- CloudTrail data events are not currently required because no product runtime data bucket, Lambda, or customer-data AWS store exists. Confidence: high.

## Unknowns

- Whether a future organization trail will replace the account-level trail.
- Future customer or compliance retention requirements.
- Actual monthly CloudTrail S3 log volume.

## Information Sources Reviewed

- AWS CloudTrail security best practices: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/best-practices-security.html
- AWS multi-Region trails: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/receive-cloudtrail-log-files-from-multiple-regions.html
- AWS CloudTrail log-file validation: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-log-file-validation-intro.html
- AWS CloudTrail S3 bucket policy: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/create-s3-bucket-policy-for-cloudtrail.html
- AWS CloudTrail costs: https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-trail-manage-costs.html
- AWS CloudTrail pricing: https://aws.amazon.com/cloudtrail/pricing/
- Terraform `aws_cloudtrail`: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/cloudtrail

## Decision

Create an account-level, multi-Region CloudTrail trail for management events only. Enable global service events and log-file validation. Deliver logs to a dedicated S3 bucket with server-side encryption, versioning, full public-access blocking, TLS-only bucket policy, CloudTrail-only write permissions, and lifecycle expiration.

Do not enable CloudTrail data events in the first deployment.

## Why This Decision Is Appropriate Now

It provides the audit baseline needed before EC2 host deployment without introducing high-volume data event logging for resources that do not exist yet.

## Alternatives Considered

- No CloudTrail before first host deployment.
- Single-Region CloudTrail.
- Organization trail.
- Management plus data events.
- CloudTrail Lake.

## Why Alternatives Were Rejected Or Deferred

- No CloudTrail leaves infrastructure mutation without a durable AWS audit trail.
- Single-Region trails can miss global service activity and enabled-Region activity.
- Organization trail requires confirmed AWS Organizations scope and permissions not in the current baseline.
- Data events are deferred because there is no current AWS product data store.
- CloudTrail Lake adds cost and query capability before there is a current requirement.

## Security Effects

Improves auditability for management-plane actions and supports log integrity validation.

## Privacy Effects

Management events record API metadata, not product accounting rows. Future data events require a separate privacy and cost review.

## Reliability Effects

CloudTrail delivery depends on the S3 bucket policy and bucket availability. Log-file validation helps detect tampering after delivery.

## Cost Effects

The first copy of management events is free from CloudTrail. Recurring costs are primarily S3 storage/requests for logs and digest files. Initial expected cost is well under $1/month for a low-activity solo-founder account, but actual cost depends on API volume.

## Operational Burden

Low. Operators must monitor bucket growth and lifecycle behavior.

## Solo-Founder Recoverability

CloudTrail gives one operator durable evidence for unexpected infrastructure changes.

## Product Impact

No product runtime resources or customer-data paths are introduced.

## Data-Lineage Impact

Adds infrastructure action lineage that complements Git history, Terraform state, and GitHub Actions logs.

## Auditability Impact

Materially improves auditability before the host exists.

## Reversibility

Retention and event selectors can be changed through Terraform. Destroying the log bucket requires explicit approval and may fail while retained objects exist.

## Rollback Or Migration Path

Disable logging or change event selectors through a reviewed Terraform change. Migrate to an organization trail later by creating the organization trail, validating delivery, and then retiring the account-level trail.

## Evidence That Would Cause Reconsideration

- AWS Organizations becomes the control-plane baseline.
- Data events become required for product data buckets, Lambda, or high-value resources.
- S3 log volume or costs exceed expectations.
- Compliance requires longer retention or object lock.
