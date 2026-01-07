terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

resource "aws_s3_bucket" "knowledge_bucket" {
  bucket = "${var.project_name}-knowledge-bucket"
}

module "dynamodb" {
  source       = "./modules/dynamodb"
  project_name = var.project_name
}

module "api" {
  source       = "./modules/api"
  environment  = var.environment
  project_name = var.project_name
}

module "lambda" {
  source      = "./modules/lambda"
  environment = var.environment
  aws_region  = var.aws_region

  api_id                          = module.api.api_id
  api_execution_arn               = module.api.api_execution_arn
  project_name                    = var.project_name
  knowledge_bucket                = aws_s3_bucket.knowledge_bucket.bucket
  runtime                         = var.runtime
  alfred_usage_tracker_table_arn  = module.dynamodb.alfred_usage_tracker_table_arn
  alfred_usage_tracker_table_name = module.dynamodb.alfred_usage_tracker_table_name
}
