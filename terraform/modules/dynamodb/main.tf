module "usage_tracker_table" {
  source  = "terraform-aws-modules/dynamodb-table/aws"
  version = "4.2.0"

  name         = "${var.project_name}-usage-tracker-table"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attributes = [
    { name = "pk", type = "S" },
    { name = "sk", type = "S" },
  ]

  ttl_attribute_name = "expires_at"
  ttl_enabled        = true

  point_in_time_recovery_enabled = true

  tags = {
    Name        = "${var.project_name}-usage-tracker"
    Environment = var.environment
    Backup      = "enabled"
  }
}
