output "instance_id" {
  description = "EC2 instance ID."
  value       = aws_instance.host.id
}

output "security_group_id" {
  description = "Security group ID attached to the host."
  value       = aws_security_group.host.id
}

output "iam_role_name" {
  description = "IAM role name attached to the host instance profile."
  value       = aws_iam_role.host.name
}

output "private_ip" {
  description = "Private IP address of the host."
  value       = aws_instance.host.private_ip
}
