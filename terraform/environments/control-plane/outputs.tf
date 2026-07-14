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

output "budget_name" {
  description = "AWS Budget name when Terraform budget management is enabled."
  value       = var.manage_budget ? module.budget[0].budget_name : null
}
