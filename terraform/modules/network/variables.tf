variable "name_prefix" {
  type        = string
  description = "Name prefix for network resources."
}

variable "aws_region" {
  type        = string
  description = "AWS region used to build VPC endpoint service names."
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC."
}

variable "az_count" {
  type        = number
  description = "Number of Availability Zones to use for public subnets."
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to network resources."
  default     = {}
}
