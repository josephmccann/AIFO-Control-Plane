data "aws_ssm_parameter" "ubuntu_ami" {
  name = var.ubuntu_ami_ssm_parameter
}

data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "host" {
  name               = "${var.name_prefix}-ec2-ssm-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-ec2-ssm-role"
  })
}

resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.host.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

data "aws_iam_policy_document" "session_manager_logging" {
  count = var.session_manager_logging_enabled ? 1 : 0

  statement {
    sid = "DescribeCloudWatchLogsForSessionManager"
    actions = [
      "logs:DescribeLogGroups",
      "logs:DescribeLogStreams",
    ]
    resources = ["*"]
  }

  statement {
    sid = "WriteSessionLogs"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["${var.session_manager_log_group_arn}:*"]
  }

  statement {
    sid = "UseSessionManagerKmsKey"
    actions = [
      "kms:Decrypt",
      "kms:DescribeKey",
      "kms:Encrypt",
      "kms:GenerateDataKey*",
    ]
    resources = [var.session_manager_kms_key_arn]
  }
}

resource "aws_iam_role_policy" "session_manager_logging" {
  count = var.session_manager_logging_enabled ? 1 : 0

  name   = "${var.name_prefix}-session-manager-logging"
  role   = aws_iam_role.host.id
  policy = data.aws_iam_policy_document.session_manager_logging[0].json
}

resource "aws_iam_instance_profile" "host" {
  name = "${var.name_prefix}-ec2-profile"
  role = aws_iam_role.host.name

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-ec2-profile"
  })
}

resource "aws_security_group" "host" {
  name_prefix            = "${var.name_prefix}-host-"
  description            = "No-ingress security group for the Session Manager managed public control-plane host."
  vpc_id                 = var.vpc_id
  revoke_rules_on_delete = true

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-host"
  })
}

resource "aws_vpc_security_group_egress_rule" "host_https_to_internet" {
  security_group_id = aws_security_group.host.id
  description       = "Allow outbound HTTPS for package installs, GitHub, registries, SSM, and external APIs."
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 443
  ip_protocol       = "tcp"
  to_port           = 443
}

resource "aws_vpc_security_group_egress_rule" "host_dns_udp" {
  security_group_id = aws_security_group.host.id
  description       = "Allow DNS resolution to the VPC resolver."
  cidr_ipv4         = var.vpc_cidr
  from_port         = 53
  ip_protocol       = "udp"
  to_port           = 53
}

resource "aws_vpc_security_group_egress_rule" "host_dns_tcp" {
  security_group_id = aws_security_group.host.id
  description       = "Allow TCP DNS resolution to the VPC resolver."
  cidr_ipv4         = var.vpc_cidr
  from_port         = 53
  ip_protocol       = "tcp"
  to_port           = 53
}

resource "aws_instance" "host" {
  ami                         = data.aws_ssm_parameter.ubuntu_ami.value
  instance_type               = var.instance_type
  subnet_id                   = var.subnet_id
  associate_public_ip_address = true
  iam_instance_profile        = aws_iam_instance_profile.host.name
  vpc_security_group_ids      = [aws_security_group.host.id]
  monitoring                  = var.enable_detailed_monitoring
  disable_api_termination     = var.enable_termination_protection
  user_data_replace_on_change = true
  user_data = templatefile("${path.module}/cloud-init.yaml.tftpl", {
    hostname = "${var.name_prefix}-host"
  })

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
    instance_metadata_tags      = "enabled"
  }

  root_block_device {
    encrypted             = true
    delete_on_termination = true
    volume_size           = var.root_volume_size_gb
    volume_type           = "gp3"
  }

  volume_tags = merge(var.tags, {
    Name = "${var.name_prefix}-host-root"
  })

  tags = merge(var.tags, {
    Name          = "${var.name_prefix}-host"
    AccessPath    = "ssm-session-manager"
    PublicIngress = "disabled"
  })

  lifecycle {
    precondition {
      condition     = var.root_volume_size_gb >= 50
      error_message = "The control-plane host root volume must be at least 50 GiB."
    }

    precondition {
      condition = (
        !var.session_manager_logging_enabled ||
        (var.session_manager_log_group_arn != null && var.session_manager_kms_key_arn != null)
      )
      error_message = "Session Manager logging requires session_manager_log_group_arn and session_manager_kms_key_arn."
    }
  }
}
