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
  default     = 200

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
