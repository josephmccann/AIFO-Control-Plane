variable "name_prefix" {
  type        = string
  description = "Name prefix for Session Manager logging resources."
}

variable "aws_region" {
  type        = string
  description = "AWS region for Session Manager logging resources."
}

variable "log_group_name" {
  type        = string
  description = "CloudWatch Logs log group name for Session Manager session logs."
  default     = "/aifo/control-plane/session-manager"
}

variable "retention_days" {
  type        = number
  description = "CloudWatch Logs retention period for Session Manager session logs."
  default     = 30

  validation {
    condition     = contains([7, 14, 30, 60, 90, 120, 150, 180, 365], var.retention_days)
    error_message = "retention_days must be a CloudWatch Logs supported retention value."
  }
}

variable "kms_deletion_window_days" {
  type        = number
  description = "Waiting period before the Session Manager KMS key can be deleted."
  default     = 30

  validation {
    condition     = var.kms_deletion_window_days >= 7 && var.kms_deletion_window_days <= 30
    error_message = "kms_deletion_window_days must be between 7 and 30."
  }
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to Session Manager logging resources."
  default     = {}
}
