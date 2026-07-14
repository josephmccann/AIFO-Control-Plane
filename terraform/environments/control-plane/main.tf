module "network" {
  source = "../../modules/network"

  name_prefix = local.name_prefix
  aws_region  = var.aws_region
  vpc_cidr    = var.vpc_cidr
  az_count    = var.az_count
  tags        = local.common_tags
}

module "compute" {
  source = "../../modules/compute"

  name_prefix                   = local.name_prefix
  vpc_id                        = module.network.vpc_id
  vpc_cidr                      = module.network.vpc_cidr
  subnet_id                     = module.network.public_subnet_ids[0]
  instance_type                 = var.control_plane_instance_type
  ubuntu_ami_ssm_parameter      = var.ubuntu_ami_ssm_parameter
  root_volume_size_gb           = var.root_volume_size_gb
  enable_termination_protection = var.enable_termination_protection
  enable_detailed_monitoring    = var.enable_detailed_monitoring
  tags                          = local.common_tags
}

module "budget" {
  count = var.manage_budget ? 1 : 0

  source = "../../modules/budget"

  name_prefix         = local.name_prefix
  monthly_budget_usd  = var.monthly_budget_usd
  notification_emails = var.budget_notification_emails
}
