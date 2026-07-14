# Emergency Access Runbook

## Allowed Emergency Access Paths

- IAM Identity Center with `AIFO-Platform-Admin`.
- AWS root only for account recovery or root-only account operations.
- Systems Manager Session Manager for EC2 shell access after deployment.

## Disallowed Emergency Shortcuts

- Creating long-lived AWS access keys.
- Opening SSH to the internet.
- Adding broad unmanaged IAM policies without a dated recovery note.
- Copying secrets into chat, issues, or PRs.

## Root Account

Use root only when the action cannot be performed through IAM Identity Center. Record:

- reason for root use;
- time;
- action performed;
- evidence captured;
- follow-up to remove any temporary access.

## SSM Access

After host deployment, connect through Session Manager:

```bash
aws ssm start-session --target INSTANCE_ID --region us-west-2
```

If SSM is unavailable, diagnose IAM role, SSM agent, route table, DNS, and HTTPS egress. Do not add SSH ingress.

## Session Logging Guidance

When Session Manager logging is enabled, assume commands and output can be retained. Do not print secrets, tokens, `.env` files, QBO credentials, product customer data, or AI provider keys in an interactive session.
