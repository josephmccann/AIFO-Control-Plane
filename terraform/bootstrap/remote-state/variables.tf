variable "aws_region" {
  type        = string
  description = "AWS region for the remote state bucket."
  default     = "us-west-2"
}

variable "state_bucket_name" {
  type        = string
  description = "Globally unique S3 bucket name for Terraform state."

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$", var.state_bucket_name))
    error_message = "state_bucket_name must be a valid S3 bucket name."
  }
}

variable "force_destroy" {
  type        = bool
  description = "Whether to allow Terraform to delete a non-empty state bucket. Keep false for production."
  default     = false
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to bootstrap resources."
  default = {
    Project   = "AI.FO"
    ManagedBy = "Terraform"
    Scope     = "bootstrap"
  }
}
