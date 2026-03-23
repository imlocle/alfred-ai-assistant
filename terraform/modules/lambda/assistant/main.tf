data "aws_caller_identity" "current" {}

locals {
  name          = "${var.project_name}-${var.lambda_name}"
  function_name = "${local.name}-${var.environment}"
  handler_path  = "assistant_handler"
}

# Lambda Role
resource "aws_iam_role" "lambda_role" {
  name = "${local.name}-lambda-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# Lambda Policy
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${local.name}-lambda-policy-${var.environment}"
  role = aws_iam_role.lambda_role.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ],
        Resource = [
          "arn:aws:s3:::${var.knowledge_bucket}",
          "arn:aws:s3:::${var.knowledge_bucket}/*",
        ]
      },
      {
        Effect = "Allow",
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
        ],
        Resource = [
          "arn:aws:bedrock:*::foundation-model/*",
          "arn:aws:bedrock:*:*:inference-profile/*"
        ]
      },
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow",
        Action = [
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:PutItem"
        ],
        Resource = [
          var.usage_tracker_table_arn,
          "${var.usage_tracker_table_arn}/*"
        ]
      }
    ]
  })
}

# Lambda Basic Execution Role
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}


#####################################
# Lambda Function
#####################################

resource "aws_lambda_function" "this" {
  function_name = local.function_name
  handler       = "handlers.${local.handler_path}.lambda_handler"
  runtime       = var.runtime
  role          = aws_iam_role.lambda_role.arn
  timeout       = 30

  filename         = "${path.root}/builds/${local.function_name}.zip"
  source_code_hash = filebase64sha256("${path.root}/builds/${local.function_name}.zip")

  layers = [aws_lambda_layer_version.common_dependencies.arn]
  depends_on = [null_resource.force_lambda_update,
    aws_lambda_layer_version.common_dependencies
  ]

  environment {
    variables = {
      ENVIRONMENT         = var.environment
      USAGE_TRACKER_TABLE = var.usage_tracker_table_name
      KNOWLEDGE_BUCKET    = var.knowledge_bucket
      MODEL_ID            = "us.amazon.nova-lite-v1:0"
    }
  }
}

#####################################
# CloudWatch Log Group with Retention
#####################################

resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${local.function_name}"
  retention_in_days = 30

  tags = {
    Environment = var.environment
    Application = var.project_name
  }
}

#####################################
# Lambda Layer
#####################################

resource "aws_lambda_layer_version" "common_dependencies" {
  filename            = "${path.root}/builds/python.zip"
  layer_name          = "${local.name}-common-deps"
  compatible_runtimes = [var.runtime]

  lifecycle {
    create_before_destroy = true
  }

  source_code_hash = filebase64sha256("${path.root}/builds/python.zip")
}

#####################################
# API Gateway Integration
#####################################

resource "aws_lambda_permission" "allow_apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this.arn
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${var.api_execution_arn}/*/*"
}

resource "aws_apigatewayv2_integration" "this" {
  api_id                 = var.api_id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.this.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "this" {
  api_id    = var.api_id
  route_key = "POST /ask"
  target    = "integrations/${aws_apigatewayv2_integration.this.id}"
}


#####################################
# Trigger a deployment
#####################################
resource "null_resource" "force_lambda_update" {
  triggers = {
    always_run = timestamp()
  }

  provisioner "local-exec" {
    command = "touch ${path.root}/builds/${local.function_name}.zip"
  }
}

#####################################
# CloudWatch Alarms
#####################################

resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${local.function_name}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "Alert when Lambda errors exceed threshold"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.this.function_name
  }

  tags = {
    Environment = var.environment
    Application = var.project_name
  }
}

resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  alarm_name          = "${local.function_name}-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Average"
  threshold           = "10000"
  alarm_description   = "Alert when Lambda duration is high"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.this.function_name
  }

  tags = {
    Environment = var.environment
    Application = var.project_name
  }
}

resource "aws_cloudwatch_metric_alarm" "lambda_throttles" {
  alarm_name          = "${local.function_name}-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "Alert when Lambda is being throttled"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.this.function_name
  }

  tags = {
    Environment = var.environment
    Application = var.project_name
  }
}
