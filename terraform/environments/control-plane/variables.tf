variable "project_name" {
  type        = string
  description = "Short project identifier used in AWS resource names."
  default     = "aifo"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,20}$", var.project_name))
    error_message = "project_name must be lowercase, start with a letter, and contain only lowercase letters, numbers, and hyphens."
  }
}

variable "environment" {
  type        = string
  description = "Environment name used in AWS resource names and tags."
  default     = "control-plane"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{1,30}$", var.environment))
    error_message = "environment must be lowercase, start with a letter, and contain only lowercase letters, numbers, and hyphens."
  }
}

variable "owner" {
  type        = string
  description = "Owner tag value for provisioned resources."
  default     = "platform"
}

variable "aws_region" {
  type        = string
  description = "AWS region for the control-plane environment."
  default     = "us-west-2"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the control-plane VPC."
  default     = "10.80.0.0/20"
}

variable "az_count" {
  type        = number
  description = "Number of Availability Zones for the initial public subnet layout."
  default     = 1

  validation {
    condition     = var.az_count >= 1 && var.az_count <= 3
    error_message = "az_count must be between 1 and 3."
  }
}

variable "control_plane_instance_type" {
  type        = string
  description = "EC2 instance type for the Ubuntu control-plane host. Candidate 8 vCPU / 32 GiB types include m7i-flex.2xlarge, m7i.2xlarge, and m7a.2xlarge pending pricing and availability verification."
  default     = "m7i-flex.2xlarge"
}

variable "ubuntu_ami_ssm_parameter" {
  type        = string
  description = "Public SSM parameter path for the Ubuntu AMI ID."
  default     = "/aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id"
}

variable "root_volume_size_gb" {
  type        = number
  description = "Root EBS volume size for the control-plane host."
  default     = 100

  validation {
    condition     = var.root_volume_size_gb >= 50
    error_message = "root_volume_size_gb must be at least 50."
  }
}

variable "enable_termination_protection" {
  type        = bool
  description = "Enable EC2 termination protection for the control-plane host."
  default     = true
}

variable "enable_detailed_monitoring" {
  type        = bool
  description = "Enable EC2 detailed monitoring. Defaults to false for the cost-conscious initial control-plane host."
  default     = false
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

variable "session_manager_log_group_name" {
  type        = string
  description = "CloudWatch Logs log group name for Session Manager session logs."
  default     = "/aifo/control-plane/session-manager"
}

variable "session_manager_log_retention_days" {
  type        = number
  description = "CloudWatch Logs retention period for Session Manager session logs."
  default     = 30

  validation {
    condition     = contains([7, 14, 30, 60, 90, 120, 150, 180, 365], var.session_manager_log_retention_days)
    error_message = "session_manager_log_retention_days must be a supported CloudWatch Logs retention value."
  }
}

variable "session_manager_kms_deletion_window_days" {
  type        = number
  description = "Waiting period before deleting the Session Manager KMS key."
  default     = 30

  validation {
    condition     = var.session_manager_kms_deletion_window_days >= 7 && var.session_manager_kms_deletion_window_days <= 30
    error_message = "session_manager_kms_deletion_window_days must be between 7 and 30."
  }
}

variable "ec2_schedule_enabled" {
  type        = bool
  description = "Whether EventBridge Scheduler start and stop schedules are enabled."
  default     = true
}

variable "ec2_schedule_timezone" {
  type        = string
  description = "IANA timezone for EC2 start and stop schedules."
  default     = "America/Los_Angeles"
}

variable "ec2_start_schedule_expression" {
  type        = string
  description = "EventBridge Scheduler expression for starting the control-plane host."
  default     = "cron(0 8 ? * MON-FRI *)"
}

variable "ec2_stop_schedule_expression" {
  type        = string
  description = "EventBridge Scheduler expression for stopping the control-plane host."
  default     = "cron(0 16 ? * MON-FRI *)"
}

variable "ec2_schedule_maximum_retry_attempts" {
  type        = number
  description = "Maximum retry attempts for EventBridge Scheduler EC2 start/stop targets."
  default     = 3

  validation {
    condition     = var.ec2_schedule_maximum_retry_attempts >= 0 && var.ec2_schedule_maximum_retry_attempts <= 185
    error_message = "ec2_schedule_maximum_retry_attempts must be between 0 and 185."
  }
}

variable "ec2_schedule_maximum_event_age_in_seconds" {
  type        = number
  description = "Maximum event age for EventBridge Scheduler EC2 start/stop target retries."
  default     = 3600

  validation {
    condition     = var.ec2_schedule_maximum_event_age_in_seconds >= 60 && var.ec2_schedule_maximum_event_age_in_seconds <= 86400
    error_message = "ec2_schedule_maximum_event_age_in_seconds must be between 60 and 86400."
  }
}

variable "monthly_budget_usd" {
  type        = number
  description = "Monthly AWS budget limit in USD."
  default     = 250

  validation {
    condition     = var.monthly_budget_usd > 0
    error_message = "monthly_budget_usd must be greater than zero."
  }
}

variable "manage_budget" {
  type        = bool
  description = "Whether Terraform should manage the AWS Budget. Defaults to false because the initial account budget was created manually."
  default     = false
}

variable "budget_notification_emails" {
  type        = list(string)
  description = "Email addresses for AWS Budget notifications. Leave empty to create the budget without notifications."
  default     = []

  validation {
    condition = alltrue([
      for email in var.budget_notification_emails :
      can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", email))
    ])
    error_message = "budget_notification_emails must contain valid email addresses."
  }
}
