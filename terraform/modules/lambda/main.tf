module "assistant" {
  source = "./assistant"

  environment              = var.environment
  api_id                   = var.api_id
  api_execution_arn        = var.api_execution_arn
  project_name             = var.project_name
  knowledge_bucket         = var.knowledge_bucket
  runtime                  = var.runtime
  aws_region               = var.aws_region
  usage_tracker_table_arn  = var.usage_tracker_table_arn
  usage_tracker_table_name = var.usage_tracker_table_name
  lambda_name              = "assistant"
}
