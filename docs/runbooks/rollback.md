# Rollback Runbook

## Before AWS Deployment

All current repository changes are reversible through Git:

```bash
git revert COMMIT_SHA
```

Do not rewrite history on shared branches.

## After Bootstrap

Remote state and OIDC resources should be rolled back with Terraform only after explicit approval.

General sequence:

1. Stop related GitHub workflows.
2. Remove or rotate affected repository variables.
3. Review current Terraform state.
4. Run `terraform plan -destroy` for the affected bootstrap root.
5. Preserve plan output in the private operational log.
6. Execute `terraform destroy` only after approval.

## After Control-Plane Host Deployment

Rollback options depend on the failure:

- bad user data: update Terraform and replace instance after plan review;
- bad security group: update rules and apply after approval;
- broken SSM: use EC2 console diagnostics only through approved human AWS access;
- cost incident: stop the instance, then review Terraform changes;
- compromised host: isolate security group egress, preserve forensic evidence if required, rotate roles/secrets, replace host.

## State Recovery

Use S3 object versioning on the state bucket. Restore a prior state version only after confirming:

- which Terraform root owns the state;
- which object version is known good;
- whether any AWS resources changed after that version;
- whether state restoration would hide real infrastructure drift.
