output "state_bucket_name" {
  description = "Terraform state S3 bucket name."
  value       = aws_s3_bucket.state.id
}

output "control_plane_backend_hcl" {
  description = "Backend configuration values for the control-plane environment."
  value = {
    bucket       = aws_s3_bucket.state.id
    key          = "control-plane/terraform.tfstate"
    region       = var.aws_region
    encrypt      = true
    use_lockfile = true
  }
}
