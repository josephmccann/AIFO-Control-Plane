output "vpc_id" {
  description = "Control-plane VPC ID."
  value       = module.network.vpc_id
}

output "public_subnet_ids" {
  description = "Public subnet IDs for the initial control-plane VPC."
  value       = module.network.public_subnet_ids
}

output "control_plane_instance_id" {
  description = "EC2 instance ID for the control-plane host."
  value       = module.compute.instance_id
}

output "control_plane_security_group_id" {
  description = "Security group ID for the control-plane host."
  value       = module.compute.security_group_id
}

output "control_plane_iam_role_name" {
  description = "IAM role name attached to the control-plane host."
  value       = module.compute.iam_role_name
}

output "cloudtrail_name" {
  description = "CloudTrail management trail name."
  value       = module.audit.cloudtrail_name
}

output "cloudtrail_bucket_name" {
  description = "S3 bucket receiving CloudTrail logs."
  value       = module.audit.cloudtrail_bucket_name
}

output "session_manager_log_group_name" {
  description = "CloudWatch Logs log group for Session Manager session logs."
  value       = module.session_manager_logging.log_group_name
}

output "session_manager_kms_key_arn" {
  description = "KMS key ARN used for Session Manager session data and log group encryption."
  value       = module.session_manager_logging.kms_key_arn
}

output "scheduler_start_schedule_name" {
  description = "EventBridge Scheduler start schedule name."
  value       = module.scheduler.start_schedule_name
}

output "scheduler_stop_schedule_name" {
  description = "EventBridge Scheduler stop schedule name."
  value       = module.scheduler.stop_schedule_name
}

output "scheduler_dead_letter_queue_url" {
  description = "EventBridge Scheduler dead-letter queue URL."
  value       = module.scheduler.dead_letter_queue_url
}

output "budget_name" {
  description = "AWS Budget name when Terraform budget management is enabled."
  value       = var.manage_budget ? module.budget[0].budget_name : null
}
