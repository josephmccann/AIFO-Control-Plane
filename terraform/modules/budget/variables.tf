variable "name_prefix" {
  type        = string
  description = "Name prefix for the AWS Budget."
}

variable "monthly_budget_usd" {
  type        = number
  description = "Monthly budget limit in USD."
}

variable "notification_emails" {
  type        = list(string)
  description = "Email addresses for budget notifications."
  default     = []
}
