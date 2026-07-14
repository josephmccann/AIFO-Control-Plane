variable "name_prefix" {
  type        = string
  description = "Name prefix for compute resources."
}

variable "vpc_id" {
  type        = string
  description = "VPC ID for the control-plane host."
}

variable "vpc_cidr" {
  type        = string
  description = "VPC CIDR block used for DNS egress."
}

variable "subnet_id" {
  type        = string
  description = "Public subnet ID for the initial control-plane host."
}

variable "instance_type" {
  type        = string
  description = "EC2 instance type for the control-plane host."
}

variable "ubuntu_ami_ssm_parameter" {
  type        = string
  description = "Public SSM parameter path for the Ubuntu AMI ID."
}

variable "root_volume_size_gb" {
  type        = number
  description = "Root EBS volume size in GiB."
}

variable "enable_termination_protection" {
  type        = bool
  description = "Whether to enable EC2 termination protection."
}

variable "enable_detailed_monitoring" {
  type        = bool
  description = "Whether to enable EC2 detailed monitoring for the control-plane host."
  default     = false
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to compute resources."
  default     = {}
}
