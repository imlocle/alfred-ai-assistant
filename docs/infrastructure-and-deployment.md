# Infrastructure and Deployment

## Overview

Alfred's infrastructure is fully managed through Terraform with a modular design. All AWS resources are defined as code, enabling reproducible deployments across environments.

## Infrastructure Components

### AWS Services Used

- API Gateway (HTTP API): Public API endpoint
- Lambda: Serverless compute for backend logic
- DynamoDB: Usage tracking with TTL and point-in-time recovery
- S3: Knowledge base storage
- Bedrock: AI model inference (Nova Lite)
- CloudWatch: Logging (30-day retention), alarms, and monitoring
- IAM: Roles and permissions (least privilege)

### Terraform Structure

```
terraform/
├── backend.tf                    # Remote state configuration
├── main.tf                       # Root module orchestration
├── variables.tf                  # Input variables
├── outputs.tf                    # Output values
└── modules/
    ├── api/                      # API Gateway module
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── dynamodb/                 # DynamoDB tables module
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    └── lambda/                   # Lambda functions module
        ├── main.tf               # Module orchestration
        ├── variables.tf
        └── assistant/            # Assistant Lambda function
            ├── main.tf           # Function, IAM, alarms, API integration
            └── variables.tf
```

---

## Terraform Modules

### Root Module (`terraform/main.tf`)

Orchestrates all infrastructure: S3 bucket, API Gateway, DynamoDB, and Lambda modules.

### API Module (`terraform/modules/api/`)

HTTP API with CORS for `localhost:5173`, `imlocle.com`, and `imlocle.github.io`.

Outputs: `api_id`, `api_endpoint`, `api_execution_arn`

### DynamoDB Module (`terraform/modules/dynamodb/`)

Usage tracking table with pay-per-request billing, composite key (pk + sk), TTL on `expires_at`, and point-in-time recovery enabled.

Outputs: `usage_tracker_table_arn`, `usage_tracker_table_name`

### Lambda Module (`terraform/modules/lambda/assistant/`)

Lambda function configuration:

- Runtime: Python 3.13
- Timeout: 30 seconds
- Handler: `handlers.assistant_handler.lambda_handler`
- Lambda layer for shared dependencies

Environment variables:

- `USAGE_TRACKER_TABLE`: DynamoDB table name
- `KNOWLEDGE_BUCKET`: S3 bucket name
- `MODEL_ID`: Bedrock inference profile ID (e.g., `us.amazon.nova-lite-v1:0`)

IAM permissions (least privilege):

- S3: `GetObject`, `ListBucket` on knowledge bucket only
- Bedrock: `InvokeModel`, `InvokeModelWithResponseStream` on all foundation models and inference profiles (cross-region support)
- DynamoDB: `GetItem`, `UpdateItem`, `PutItem` on usage table only
- CloudWatch: Log group/stream creation

CloudWatch alarms:

- Lambda errors: >10 errors in 5 minutes
- Lambda duration: >10 second average
- Lambda throttles: >5 throttles in 5 minutes

---

## Build Process

### Makefile Targets

- `make clean`: Remove build artifacts
- `make zip-layer`: Build Lambda layer via Docker (Amazon Linux 2)
- `make zip-all`: Zip layer and function code
- `make deploy`: Full pipeline (clean → zip → terraform init → apply)

### Full Deployment

```bash
make clean && make deploy ENV=dev
```

Duration: ~2-3 minutes

### Incremental Deployment (code-only)

```bash
make zip-all
terraform -chdir=terraform apply -var="environment=dev" -auto-approve
```

Duration: ~30-60 seconds

---

## Remote State

Terraform state stored in S3 (`alfred-terraform-state-bucket`) with versioning for team collaboration and rollback.

---

## Environment Management

Deploy to different environments:

```bash
make deploy ENV=dev      # Development
make deploy ENV=staging  # Staging
make deploy ENV=prod     # Production
```

Resource naming follows: `{project_name}-{lambda_name}-{environment}` (e.g., `alfred-assistant-dev`)

---

## Knowledge Base Deployment

```bash
aws s3 cp knowledge_base.json s3://alfred-knowledge-bucket/knowledge_base.json
```

Lambda loads the new version on next cold start. No code deployment needed.

---

## Monitoring

### CloudWatch Logs

Log group: `/aws/lambda/alfred-assistant-{environment}`

Structured JSON format with request_id correlation:

```bash
aws logs tail /aws/lambda/alfred-assistant-dev --follow
```

### Debug Commands

```bash
# Test Lambda directly
aws lambda invoke \
  --function-name alfred-assistant-dev \
  --payload '{"body": "{\"question\": \"test\"}"}' \
  response.json

# Check DynamoDB table
aws dynamodb scan --table-name alfred-usage-tracker-table

# Verify S3 object
aws s3 ls s3://alfred-knowledge-bucket/
```

---

## Cost Estimate (1000 requests/month)

- Lambda: Free tier
- API Gateway: Free tier
- DynamoDB: Free tier + ~$0.20/GB PITR
- Bedrock (Nova Lite): ~$0.05
- S3: ~$0.01
- CloudWatch Alarms: ~$0.30
- Total: ~$0.56/month

---

## Troubleshooting

| Issue                       | Cause                      | Solution                                                         |
| --------------------------- | -------------------------- | ---------------------------------------------------------------- |
| Lambda timeout              | Bedrock response slow      | Increase timeout in `terraform/modules/lambda/assistant/main.tf` |
| CORS errors                 | Origin not allowed         | Add origin to `terraform/modules/api/main.tf`                    |
| Rate limit not working      | Table not found            | Verify `USAGE_TRACKER_TABLE` env var                             |
| Knowledge base not loading  | S3 bucket empty            | Upload `knowledge_base.json` and verify IAM                      |
| Bedrock AccessDenied        | IAM policy too restrictive | Verify IAM allows `bedrock:InvokeModel` on inference profiles    |
| Bedrock ValidationException | Wrong MODEL_ID format      | Use inference profile ID (e.g., `us.amazon.nova-lite-v1:0`)      |
