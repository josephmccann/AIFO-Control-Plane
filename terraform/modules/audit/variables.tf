variable "name_prefix" {
  type        = string
  description = "Name prefix for audit resources."
}

variable "aws_region" {
  type        = string
  description = "AWS region where the CloudTrail home trail and S3 log bucket are created."
}

variable "cloudtrail_log_retention_days" {
  type        = number
  description = "Days before CloudTrail S3 log objects expire."
  default     = 365

  validation {
    condition     = var.cloudtrail_log_retention_days >= 90
    error_message = "cloudtrail_log_retention_days must be at least 90."
  }
}

variable "cloudtrail_noncurrent_version_retention_days" {
  type        = number
  description = "Days before noncurrent CloudTrail S3 object versions expire."
  default     = 30

  validation {
    condition     = var.cloudtrail_noncurrent_version_retention_days >= 1
    error_message = "cloudtrail_noncurrent_version_retention_days must be at least 1."
  }
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to audit resources."
  default     = {}
}
