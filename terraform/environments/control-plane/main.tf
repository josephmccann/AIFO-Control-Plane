module "audit" {
  source = "../../modules/audit"

  name_prefix                                  = local.name_prefix
  aws_region                                   = var.aws_region
  cloudtrail_log_retention_days                = var.cloudtrail_log_retention_days
  cloudtrail_noncurrent_version_retention_days = var.cloudtrail_noncurrent_version_retention_days
  tags                                         = local.common_tags
}

module "session_manager_logging" {
  source = "../../modules/session-manager-logging"

  name_prefix              = local.name_prefix
  aws_region               = var.aws_region
  log_group_name           = var.session_manager_log_group_name
  retention_days           = var.session_manager_log_retention_days
  kms_deletion_window_days = var.session_manager_kms_deletion_window_days
  tags                     = local.common_tags
}

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

  name_prefix                     = local.name_prefix
  vpc_id                          = module.network.vpc_id
  vpc_cidr                        = module.network.vpc_cidr
  subnet_id                       = module.network.public_subnet_ids[0]
  instance_type                   = var.control_plane_instance_type
  ubuntu_ami_ssm_parameter        = var.ubuntu_ami_ssm_parameter
  root_volume_size_gb             = var.root_volume_size_gb
  enable_termination_protection   = var.enable_termination_protection
  enable_detailed_monitoring      = var.enable_detailed_monitoring
  session_manager_logging_enabled = true
  session_manager_log_group_arn   = module.session_manager_logging.log_group_arn
  session_manager_kms_key_arn     = module.session_manager_logging.kms_key_arn
  tags                            = local.common_tags
}

module "scheduler" {
  source = "../../modules/scheduler"

  name_prefix                  = local.name_prefix
  aws_region                   = var.aws_region
  instance_id                  = module.compute.instance_id
  enabled                      = var.ec2_schedule_enabled
  timezone                     = var.ec2_schedule_timezone
  start_schedule_expression    = var.ec2_start_schedule_expression
  stop_schedule_expression     = var.ec2_stop_schedule_expression
  maximum_retry_attempts       = var.ec2_schedule_maximum_retry_attempts
  maximum_event_age_in_seconds = var.ec2_schedule_maximum_event_age_in_seconds
  tags                         = local.common_tags
}

module "budget" {
  count = var.manage_budget ? 1 : 0

  source = "../../modules/budget"

  name_prefix         = local.name_prefix
  monthly_budget_usd  = var.monthly_budget_usd
  notification_emails = var.budget_notification_emails
}
