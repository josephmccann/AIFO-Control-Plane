output "schedule_group_name" {
  description = "EventBridge Scheduler schedule group name."
  value       = aws_scheduler_schedule_group.control_plane.name
}

output "start_schedule_name" {
  description = "EventBridge Scheduler start schedule name."
  value       = aws_scheduler_schedule.start_host.name
}

output "stop_schedule_name" {
  description = "EventBridge Scheduler stop schedule name."
  value       = aws_scheduler_schedule.stop_host.name
}

output "execution_role_arn" {
  description = "IAM role ARN used by EventBridge Scheduler."
  value       = aws_iam_role.scheduler.arn
}

output "dead_letter_queue_url" {
  description = "Scheduler dead-letter queue URL."
  value       = aws_sqs_queue.scheduler_dlq.url
}

output "dead_letter_queue_arn" {
  description = "Scheduler dead-letter queue ARN."
  value       = aws_sqs_queue.scheduler_dlq.arn
}
