locals {
  budget_notifications = length(var.notification_emails) > 0 ? {
    actual_80 = {
      comparison_operator = "GREATER_THAN"
      notification_type   = "ACTUAL"
      threshold           = 80
      threshold_type      = "PERCENTAGE"
    }
    actual_100 = {
      comparison_operator = "GREATER_THAN"
      notification_type   = "ACTUAL"
      threshold           = 100
      threshold_type      = "PERCENTAGE"
    }
    forecast_100 = {
      comparison_operator = "GREATER_THAN"
      notification_type   = "FORECASTED"
      threshold           = 100
      threshold_type      = "PERCENTAGE"
    }
  } : {}
}

resource "aws_budgets_budget" "monthly" {
  name         = "${var.name_prefix}-monthly-budget"
  budget_type  = "COST"
  limit_amount = tostring(var.monthly_budget_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  dynamic "notification" {
    for_each = local.budget_notifications

    content {
      comparison_operator        = notification.value.comparison_operator
      notification_type          = notification.value.notification_type
      threshold                  = notification.value.threshold
      threshold_type             = notification.value.threshold_type
      subscriber_email_addresses = var.notification_emails
    }
  }
}
