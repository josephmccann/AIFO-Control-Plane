data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}

locals {
  account_id       = data.aws_caller_identity.current.account_id
  partition        = data.aws_partition.current.partition
  schedule_state   = var.enabled ? "ENABLED" : "DISABLED"
  instance_arn     = "arn:${local.partition}:ec2:${var.aws_region}:${local.account_id}:instance/${var.instance_id}"
  scheduler_target = "arn:${local.partition}:scheduler:::aws-sdk:ec2"
}

resource "aws_scheduler_schedule_group" "control_plane" {
  name = "${var.name_prefix}-host"

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-host"
  })
}

resource "aws_sqs_queue" "scheduler_dlq" {
  name                      = "${var.name_prefix}-scheduler-dlq"
  message_retention_seconds = var.dlq_message_retention_seconds
  sqs_managed_sse_enabled   = true

  tags = merge(var.tags, {
    Name      = "${var.name_prefix}-scheduler-dlq"
    DataClass = "scheduler-failure-events"
    Retention = "${var.dlq_message_retention_seconds}-seconds"
  })
}

data "aws_iam_policy_document" "scheduler_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "scheduler" {
  name               = "${var.name_prefix}-scheduler-role"
  assume_role_policy = data.aws_iam_policy_document.scheduler_assume_role.json
  description        = "Allows EventBridge Scheduler to start and stop only the AI.FO control-plane host."

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-scheduler-role"
  })
}

data "aws_iam_policy_document" "scheduler" {
  statement {
    sid = "StartStopOnlyControlPlaneHost"
    actions = [
      "ec2:StartInstances",
      "ec2:StopInstances",
    ]
    resources = [local.instance_arn]
  }

  statement {
    sid       = "SendFailuresToDeadLetterQueue"
    actions   = ["sqs:SendMessage"]
    resources = [aws_sqs_queue.scheduler_dlq.arn]
  }
}

resource "aws_iam_role_policy" "scheduler" {
  name   = "${var.name_prefix}-scheduler-policy"
  role   = aws_iam_role.scheduler.id
  policy = data.aws_iam_policy_document.scheduler.json
}

resource "aws_scheduler_schedule" "start_host" {
  name                         = "${var.name_prefix}-host-start"
  group_name                   = aws_scheduler_schedule_group.control_plane.name
  description                  = "Start the AI.FO control-plane host for the approved weekday operating window."
  schedule_expression          = var.start_schedule_expression
  schedule_expression_timezone = var.timezone
  state                        = local.schedule_state

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = "${local.scheduler_target}:startInstances"
    role_arn = aws_iam_role.scheduler.arn
    input = jsonencode({
      InstanceIds = [var.instance_id]
    })

    dead_letter_config {
      arn = aws_sqs_queue.scheduler_dlq.arn
    }

    retry_policy {
      maximum_event_age_in_seconds = var.maximum_event_age_in_seconds
      maximum_retry_attempts       = var.maximum_retry_attempts
    }
  }
}

resource "aws_scheduler_schedule" "stop_host" {
  name                         = "${var.name_prefix}-host-stop"
  group_name                   = aws_scheduler_schedule_group.control_plane.name
  description                  = "Stop the AI.FO control-plane host at the end of the approved weekday operating window."
  schedule_expression          = var.stop_schedule_expression
  schedule_expression_timezone = var.timezone
  state                        = local.schedule_state

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = "${local.scheduler_target}:stopInstances"
    role_arn = aws_iam_role.scheduler.arn
    input = jsonencode({
      InstanceIds = [var.instance_id]
    })

    dead_letter_config {
      arn = aws_sqs_queue.scheduler_dlq.arn
    }

    retry_policy {
      maximum_event_age_in_seconds = var.maximum_event_age_in_seconds
      maximum_retry_attempts       = var.maximum_retry_attempts
    }
  }
}
