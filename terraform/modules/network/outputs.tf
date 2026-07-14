output "vpc_id" {
  description = "VPC ID."
  value       = aws_vpc.this.id
}

output "vpc_cidr" {
  description = "VPC CIDR block."
  value       = aws_vpc.this.cidr_block
}

output "public_subnet_ids" {
  description = "Public subnet IDs."
  value       = aws_subnet.public[*].id
}

output "internet_gateway_id" {
  description = "Internet Gateway ID."
  value       = aws_internet_gateway.this.id
}

output "s3_gateway_endpoint_prefix_list_id" {
  description = "S3 gateway endpoint prefix list ID for security group egress rules."
  value       = aws_vpc_endpoint.s3.prefix_list_id
}
