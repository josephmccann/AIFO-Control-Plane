output "cloudtrail_name" {
  description = "CloudTrail trail name."
  value       = aws_cloudtrail.management.name
}

output "cloudtrail_arn" {
  description = "CloudTrail trail ARN."
  value       = aws_cloudtrail.management.arn
}

output "cloudtrail_bucket_name" {
  description = "S3 bucket receiving CloudTrail logs."
  value       = aws_s3_bucket.cloudtrail.id
}

output "cloudtrail_retention_days" {
  description = "CloudTrail S3 log retention period in days."
  value       = var.cloudtrail_log_retention_days
}
