output "usage_tracker_table_arn" {
  value = module.usage_tracker_table.dynamodb_table_arn
}

output "usage_tracker_table_name" {
  value = module.usage_tracker_table.dynamodb_table_id
}
