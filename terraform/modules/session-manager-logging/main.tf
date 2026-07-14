data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}

locals {
  account_id    = data.aws_caller_identity.current.account_id
  partition     = data.aws_partition.current.partition
  log_group_arn = "arn:${local.partition}:logs:${var.aws_region}:${local.account_id}:log-group:${var.log_group_name}"
}

data "aws_iam_policy_document" "kms" {
  statement {
    sid    = "EnableAccountKeyAdministration"
    effect = "Allow"

    principals {
      type        = "AWS"
      identifiers = ["arn:${local.partition}:iam::${local.account_id}:root"]
    }

    actions   = ["kms:*"]
    resources = ["*"]
  }

  statement {
    sid    = "AllowCloudWatchLogsUse"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["logs.${var.aws_region}.amazonaws.com"]
    }

    actions = [
      "kms:Decrypt",
      "kms:DescribeKey",
      "kms:Encrypt",
      "kms:GenerateDataKey*",
      "kms:ReEncrypt*",
    ]

    resources = ["*"]

    condition {
      test     = "ArnEquals"
      variable = "kms:EncryptionContext:aws:logs:arn"
      values   = [local.log_group_arn]
    }
  }
}

resource "aws_kms_key" "session_manager" {
  description             = "Encrypt AI.FO Session Manager session data and CloudWatch Logs."
  deletion_window_in_days = var.kms_deletion_window_days
  enable_key_rotation     = true
  policy                  = data.aws_iam_policy_document.kms.json

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-session-manager-logs"
    DataClass = "operator-session-audit"
  })
}

resource "aws_kms_alias" "session_manager" {
  name          = "alias/${var.name_prefix}-session-manager-logs"
  target_key_id = aws_kms_key.session_manager.key_id
}

resource "aws_cloudwatch_log_group" "session_manager" {
  name              = var.log_group_name
  kms_key_id        = aws_kms_key.session_manager.arn
  retention_in_days = var.retention_days

  tags = merge(var.tags, {
    Name      = var.log_group_name
    DataClass = "operator-session-audit"
    Retention = "${var.retention_days}-days"
  })
}

resource "aws_ssm_document" "session_manager_preferences" {
  name            = "SSM-SessionManagerRunShell"
  document_type   = "Session"
  document_format = "JSON"

  content = jsonencode({
    schemaVersion = "1.0"
    description   = "Regional Session Manager preferences for AI.FO control-plane host administration."
    sessionType   = "Standard_Stream"
    inputs = {
      s3BucketName                = ""
      s3KeyPrefix                 = ""
      s3EncryptionEnabled         = true
      cloudWatchLogGroupName      = aws_cloudwatch_log_group.session_manager.name
      cloudWatchEncryptionEnabled = true
      cloudWatchStreamingEnabled  = true
      kmsKeyId                    = aws_kms_key.session_manager.arn
      runAsEnabled                = false
      runAsDefaultUser            = ""
      idleSessionTimeout          = "20"
      maxSessionDuration          = "60"
      shellProfile = {
        linux   = "pwd"
        windows = "date"
      }
    }
  })

  tags = merge(var.tags, {
    Name      = "SSM-SessionManagerRunShell"
    DataClass = "operator-session-audit"
  })
}
