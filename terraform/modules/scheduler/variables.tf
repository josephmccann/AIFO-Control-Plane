variable "name_prefix" {
  type        = string
  description = "Name prefix for EventBridge Scheduler resources."
}

variable "aws_region" {
  type        = string
  description = "AWS region for EventBridge Scheduler resources."
}

variable "instance_id" {
  type        = string
  description = "EC2 instance ID controlled by the schedules."
}

variable "enabled" {
  type        = bool
  description = "Whether the start and stop schedules are enabled."
  default     = true
}

variable "timezone" {
  type        = string
  description = "IANA time zone used by the schedules."
  default     = "America/Los_Angeles"
}

variable "start_schedule_expression" {
  type        = string
  description = "EventBridge Scheduler expression for starting the host."
  default     = "cron(0 8 ? * MON-FRI *)"
}

variable "stop_schedule_expression" {
  type        = string
  description = "EventBridge Scheduler expression for stopping the host."
  default     = "cron(0 16 ? * MON-FRI *)"
}

variable "maximum_retry_attempts" {
  type        = number
  description = "Maximum Scheduler retry attempts when EC2 start or stop invocation fails."
  default     = 3

  validation {
    condition     = var.maximum_retry_attempts >= 0 && var.maximum_retry_attempts <= 185
    error_message = "maximum_retry_attempts must be between 0 and 185."
  }
}

variable "maximum_event_age_in_seconds" {
  type        = number
  description = "Maximum age in seconds for Scheduler retry attempts."
  default     = 3600

  validation {
    condition     = var.maximum_event_age_in_seconds >= 60 && var.maximum_event_age_in_seconds <= 86400
    error_message = "maximum_event_age_in_seconds must be between 60 and 86400."
  }
}

variable "dlq_message_retention_seconds" {
  type        = number
  description = "Retention period for Scheduler dead-letter queue messages."
  default     = 1209600

  validation {
    condition     = var.dlq_message_retention_seconds >= 60 && var.dlq_message_retention_seconds <= 1209600
    error_message = "dlq_message_retention_seconds must be between 60 and 1209600."
  }
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to Scheduler resources."
  default     = {}
}
