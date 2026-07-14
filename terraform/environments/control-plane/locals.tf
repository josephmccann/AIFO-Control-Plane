locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = {
    Project     = "AI.FO"
    ManagedBy   = "Terraform"
    Environment = var.environment
    Owner       = var.owner
    Repository  = "AIFO-Control-Plane"
  }
}
