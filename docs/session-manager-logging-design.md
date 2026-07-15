# Session Manager Logging Design

Date: 2026-07-14

## Recommendation

For the initial control-plane host, use CloudWatch Logs for Session Manager logging with a 30-day retention period and a customer-managed KMS key. Do not enable S3 session log duplication in the first version unless a compliance review requires it.

This design is implemented in Terraform. The log group, KMS key, Session Manager preferences document, EC2 instance role permissions, and host connectivity path were verified during the approved control-plane deployment. Session logging reached `/aifo/control-plane/session-manager` during the post-deployment Session Manager test.

## Rationale

Session Manager is the required administrative path, so session activity needs an audit trail. CloudWatch Logs gives enough operational evidence for early control-plane recovery and review without adding a second durable log store.

The privacy risk is that shell transcripts can contain sensitive command output if an operator prints secrets. Logging must therefore be paired with operator guidance:

- do not paste secrets into interactive shells;
- do not print environment files;
- do not run commands that dump tokens or customer data;
- use secret managers and one-time retrieval patterns when product secrets exist.

## Initial Settings

| Setting | Recommendation |
| --- | --- |
| Destination | CloudWatch Logs |
| Log group | `/aifo/control-plane/session-manager` |
| Retention | 30 days |
| S3 logging | Disabled initially |
| Customer-managed KMS key | Enabled |
| SSH-over-SSM logging | Do not use SSH-over-SSM as the normal path because AWS notes logging limitations for SSH/port forwarding sessions |

## Why Not S3 Initially

S3 is useful for longer retention and immutable archive patterns. It is deferred because the current host is not a product runtime, logs may contain sensitive operator output, and CloudWatch with short retention is enough for the first control-plane host.

## Why Customer-Managed KMS Now

CloudWatch Logs provides encryption at rest by default. A customer-managed KMS key adds policy management, key recovery, and monthly key cost, but it is justified here because the deployment requirement calls for an encrypted log group and the first host should be auditable before deployment.

## Terraform Implementation Path

The Terraform implementation adds:

- CloudWatch log group with retention.
- SSM Session Manager preferences document.
- KMS key for the log group and Session Manager session data.
- IAM permissions for the instance role to write session logs and use the KMS key.
- Runbook steps to verify logs after the first approved session.

Do not implement this with ad hoc console edits except as an explicitly documented emergency change.

## Sources

- Session Manager logging: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-logging.html
- CloudWatch Logs session logging: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-logging-cloudwatch-logs.html
- S3 session logging: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-logging-s3.html
- Session data KMS encryption: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-preferences-enable-encryption.html
- Update Session Manager preferences with CLI: https://docs.aws.amazon.com/systems-manager/latest/userguide/getting-started-configure-preferences-cli.html
