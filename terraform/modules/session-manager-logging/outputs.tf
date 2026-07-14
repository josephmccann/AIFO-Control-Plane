output "log_group_name" {
  description = "CloudWatch Logs log group for Session Manager session logs."
  value       = aws_cloudwatch_log_group.session_manager.name
}

output "log_group_arn" {
  description = "CloudWatch Logs log group ARN for Session Manager session logs."
  value       = aws_cloudwatch_log_group.session_manager.arn
}

output "kms_key_arn" {
  description = "KMS key ARN used for Session Manager session data and log group encryption."
  value       = aws_kms_key.session_manager.arn
}

output "ssm_document_name" {
  description = "SSM Session Manager preferences document name."
  value       = aws_ssm_document.session_manager_preferences.name
}
