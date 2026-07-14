variable "aws_region" {
  type        = string
  description = "AWS region used for provider configuration."
  default     = "us-west-2"
}

variable "github_owner" {
  type        = string
  description = "GitHub organization or user that owns the repository."
}

variable "github_repository" {
  type        = string
  description = "GitHub repository name without owner."
  default     = "AIFO-Control-Plane"
}

variable "github_plan_environment" {
  type        = string
  description = "Protected GitHub environment used by the Terraform plan workflow."
  default     = "terraform-plan"
}

variable "github_apply_environment" {
  type        = string
  description = "Protected GitHub environment reserved for a future Terraform apply workflow."
  default     = "terraform-apply"
}

variable "role_name_prefix" {
  type        = string
  description = "Prefix for GitHub Actions Terraform IAM role names."
  default     = "AIFO-GitHubActions-Terraform"
}

variable "state_bucket_name" {
  type        = string
  description = "Terraform state S3 bucket name."
}

variable "state_key" {
  type        = string
  description = "Terraform state key for the control-plane environment."
  default     = "control-plane/terraform.tfstate"
}

variable "apply_role_managed_policy_arns" {
  type        = list(string)
  description = "Managed policy ARNs for the future apply role. Keep empty until the apply boundary is approved."
  default     = []
}

variable "plan_role_additional_policy_arns" {
  type        = list(string)
  description = "Optional additional managed policy ARNs for the plan role. Keep empty unless a reviewed plan failure proves more read access is required."
  default     = []
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
