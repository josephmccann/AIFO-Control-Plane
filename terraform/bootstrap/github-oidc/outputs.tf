output "aws_account_id" {
  description = "AWS account ID where OIDC roles are created."
  value       = data.aws_caller_identity.current.account_id
}

output "github_oidc_provider_arn" {
  description = "GitHub Actions OIDC provider ARN."
  value       = aws_iam_openid_connect_provider.github.arn
}

output "plan_role_arn" {
  description = "Role ARN for the Terraform plan workflow."
  value       = aws_iam_role.plan.arn
}

output "apply_role_arn" {
  description = "Role ARN reserved for a future Terraform apply workflow."
  value       = aws_iam_role.apply.arn
}

output "plan_trust_subject" {
  description = "Exact OIDC sub claim trusted by the plan role."
  value       = local.plan_environment_sub
}

output "apply_trust_subject" {
  description = "Exact OIDC sub claim trusted by the apply role."
  value       = local.apply_environment_sub
}
