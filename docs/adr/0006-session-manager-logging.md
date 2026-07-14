# ADR-0006: Session Manager Logging Design

## Status

Accepted for design; not implemented.

## Current Product Requirement Supported

The control-plane host must be administered through Systems Manager Session Manager instead of SSH. Administrative actions should be auditable without turning infrastructure logs into broad surveillance or customer-data collection.

## Founder Principle Or Constitutional Principle Implicated

Principles 1, 6, 7, 14, 18, and 20: trust, preserved state of knowledge, decision process, transparent limits, auditability without surveillance, and disciplined operations.

## Known Facts

- Session Manager can log commands and output depending on session preferences.
- AWS documents CloudWatch Logs and S3 as session log destinations.
- AWS notes that logging is not available for Session Manager sessions that connect through port forwarding or SSH.
- The current control-plane host is not a product runtime and should not handle customer data yet.

## Assumptions

- 30-day CloudWatch retention is sufficient for initial troubleshooting and audit. Confidence: medium.
- Customer-managed KMS is not required before customer data or compliance commitments exist. Confidence: medium.

## Unknowns

- Future customer or compliance expectations for administrative session retention.
- Whether product runtime hosting will require different audit retention.
- Whether a customer-managed key will be required by diligence review.

## Information Sources Reviewed

- AWS Session Manager logging: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-logging.html
- AWS CloudWatch Logs session logging: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-logging-cloudwatch-logs.html
- AWS S3 session logging: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-logging-s3.html
- AWS Session data KMS encryption: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-preferences-enable-encryption.html
- AWS update Session Manager preferences: https://docs.aws.amazon.com/systems-manager/latest/userguide/getting-started-configure-preferences-cli.html

## Decision

Design the initial Session Manager logging path around CloudWatch Logs with 30-day retention. Defer S3 duplication and customer-managed KMS until a compliance, customer, or product-runtime requirement justifies the added retention and key-management burden.

## Why This Decision Is Appropriate Now

It provides an audit trail for administrative sessions while minimizing retained sensitive shell transcript data and avoiding unnecessary always-on services for a host that is not yet handling product runtime data.

## Alternatives Considered

- No session logging.
- CloudWatch Logs plus S3 archive.
- CloudWatch Logs with customer-managed KMS from day one.
- SSH-over-SSM.

## Why Alternatives Were Rejected Or Deferred

- No logging weakens auditability.
- S3 archive increases retention risk and operational burden before retention requirements are known.
- Customer-managed KMS adds policy complexity and monthly cost before there is a defined requirement.
- SSH-over-SSM is not the normal path because AWS documents logging limitations for SSH and port forwarding sessions.

## Security Effects

Improves auditability of administrative sessions. Residual risk remains if operators print secrets into session output.

## Privacy Effects

Short retention limits exposure. Operators must avoid printing product data, secrets, and tokens.

## Reliability Effects

CloudWatch Logs availability becomes part of the audit path, not the host access path.

## Cost Effects

CloudWatch Logs cost depends on ingestion and storage. Short retention reduces accumulation. S3 archive and customer-managed KMS monthly costs are deferred.

## Operational Burden

Low initial burden. Requires periodic review of log volume and retention.

## Solo-Founder Recoverability

CloudWatch Logs gives one operator a familiar place to inspect recent administrative activity without managing an archive bucket.

## Product Impact

No product runtime data should be logged. Future product hosting needs a separate audit and privacy review.

## Data-Lineage Impact

Administrative session logs support infrastructure action lineage but do not replace product recommendation lineage.

## Auditability Impact

Improves evidence for who did what during administrative sessions after implementation.

## Reversibility

Retention, destination, and KMS choices can be changed through Terraform before deployment or in a later reviewed change.

## Rollback Or Migration Path

Disable Session Manager logging preferences, reduce retention, add S3 archive, or add KMS encryption through a reviewed Terraform change.

## Evidence That Would Cause Reconsideration

- Customer or investor diligence requires longer retention.
- Sessions begin handling product runtime operations.
- Logs show sensitive material is frequently captured.
- CloudWatch costs exceed expectations.
