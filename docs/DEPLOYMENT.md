# Deployment Guide

Complete infrastructure setup, deployment, and production operations for Alfred.

---

## Prerequisites

### AWS Account Setup

1. **AWS Account**: Active account with billing configured
2. **IAM User**: Create dedicated IAM user for deployment
3. **AWS CLI**: Installed and configured (`aws configure`)
4. **Terraform**: Version 1.0+
5. **AWS Permissions**: User must have access to:
   - Lambda, API Gateway, DynamoDB, S3, CloudWatch, IAM, Bedrock

### Required Tools

```bash
# Verify installations
aws --version        # v2.x
terraform --version  # v1.0+
python --version     # v3.12+
```

### AWS Credentials

Store credentials in `~/.aws/credentials`:

```
[default]
aws_access_key_id =AKIA...
aws_secret_access_key = ...

[staging]
aws_access_key_id = AKIA...
aws_secret_access_key = ...
```

Or use environment variables:

```bash
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=us-east-1
```

---

## Infrastructure Overview

### Architecture Diagram

```
┌─────────────────────────────────────────────┐
│  Clients (Web, Mobile)                      │
└────────────────┬────────────────────────────┘
                 │ HTTPS
┌────────────────▼────────────────────────────┐
│  API Gateway (HTTP API)                     │
│  - CORS validation                          │
│  - Rate limiting (CloudFlare optional)      │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│  Lambda Function (AssistantHandler)         │
│  - Python 3.12                              │
│  - 512 MB memory (configurable)             │
│  - 60s timeout                              │
└────────────┬──────────────────┬─────────────┘
             │                  │
    ┌────────▼────────┐  ┌──────▼───────┐
    │  Bedrock        │  │  DynamoDB    │
    │  (Nova Lite)    │  │  - Cache     │
    │  - Claude       │  │  - Usage     │
    └────────┬────────┘  └──────┬───────┘
             │                  │
    ┌────────▼────────┐  ┌──────▼───────┐
    │  S3 Bucket      │  │  CloudWatch  │
    │  - Knowledge    │  │  - Logs      │
    │    Base         │  │  - Metrics   │
    └─────────────────┘  └──────────────┘
```

### AWS Services Used

| Service         | Purpose              | Configuration                      |
| --------------- | -------------------- | ---------------------------------- |
| **Lambda**      | Serverless compute   | Python 3.12, 512MB, 60s timeout    |
| **API Gateway** | HTTP endpoint        | REST API (HTTP, not REST)          |
| **DynamoDB**    | NoSQL database       | 2 tables: cache, usage tracking    |
| **S3**          | Object storage       | Knowledge base storage             |
| **Bedrock**     | LLM inference        | Amazon Nova Lite inference profile |
| **CloudWatch**  | Logging & monitoring | All Lambda logs, metrics, alarms   |
| **IAM**         | Access control       | Least privilege roles              |

---

## Infrastructure-as-Code (Terraform)

### Project Structure

```
terraform/
├── main.tf              # Root configuration
├── variables.tf         # Input variables
├── outputs.tf           # Output values
├── backend.tf           # State backend (S3)
├── backend.auto.hcl     # Backend auto config
└── modules/
    ├── api/            # API Gateway setup
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── lambda/         # Lambda function
    │   ├── main.tf
    │   ├── variables.tf
    │   ├── outputs.tf
    │   └── function.zip
    └── dynamodb/       # DynamoDB tables
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

### State Management

```bash
# Initialize backend (first time)
terraform -chdir=terraform init

# Configure state backend in AWS S3
# Location: s3://alfred-terraform-state/prod/

# View state
terraform -chdir=terraform show

# Inspect specific resource
terraform -chdir=terraform state show aws_lambda_function.assistant
```

---

## Deployment Environments

### Development

```bash
# Environment: dev
# Region: us-east-1
# Bedrock Model: Amazon Nova Lite
# Rate Limit: 10 requests/day
# Cost: $$

export ENVIRONMENT=dev
export AWS_PROFILE=default
```

### Staging

```bash
# Environment: staging
# Region: us-east-1
# Bedrock Model: Amazon Nova Lite
# Rate Limit: 5 requests/day
# Cost: $$

export ENVIRONMENT=staging
export AWS_PROFILE=staging
```

### Production

```bash
# Environment: prod
# Region: us-east-1
# Bedrock Model: Amazon Nova Lite
# Rate Limit: 3 requests/day
# Cost: $$$

export ENVIRONMENT=prod
export AWS_PROFILE=prod
```

---

## Deployment Steps

### 1. Prepare Infrastructure Code

```bash
cd terraform

# Set environment variables
export AWS_REGION=us-east-1
export ENVIRONMENT=prod
export PROJECT_NAME=alfred
export RUNTIME=python3.12

# Review Terraform configuration
cat main.tf | grep -A 5 "resource\|module"
```

### 2. Initialize Terraform

```bash
# First time setup
terraform init

# If backend already exists
terraform init -upgrade
```

### 3. Plan Deployment

```bash
# Dry-run to see what will be created
terraform plan \
  -var="environment=$ENVIRONMENT" \
  -var="aws_region=$AWS_REGION" \
  -var="project_name=$PROJECT_NAME" \
  -out=tfplan

# Review output for any unexpected changes
```

### 4. Build Lambda Package

```bash
# Return to project root
cd ..

# Create deployment package
make build  # Or manually:

# Lambda layer + function code
zip -r lambda-package.zip src/ lambda_layer/

# Verify package size (should be < 250 MB)
ls -lh lambda-package.zip
```

### 5. Upload Knowledge Base to S3

```bash
# Create S3 bucket (if not exists)
aws s3 mb s3://alfred-knowledge-bucket-prod

# Upload knowledge base
aws s3 cp knowledge_base.json s3://alfred-knowledge-bucket-prod/

# Verify upload
aws s3 ls s3://alfred-knowledge-bucket-prod/
```

### 6. Apply Infrastructure

```bash
cd terraform

# Apply changes (requires confirmation)
terraform apply tfplan

# Saves state to S3 backend
# Creates all resources
```

### 7. Verify Deployment

```bash
# Get Lambda function details
aws lambda get-function --function-name alfred-assistant-handler

# Test Lambda invoke
aws lambda invoke \
  --function-name alfred-assistant-handler \
  --payload file://test-event.json \
  response.json

# View function logs
aws logs tail /aws/lambda/alfred-assistant-handler --follow

# Check DynamoDB tables
aws dynamodb list-tables | grep alfred

# Verify S3 bucket
aws s3 ls --summarize --recursive s3://alfred-knowledge-bucket-prod/
```

### 8. Test Endpoints

```bash
# Get API endpoint from Terraform output
API_ENDPOINT=$(terraform output -raw api_endpoint)

# Test health check
curl -X POST $API_ENDPOINT/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is your experience?",
    "userId": "deployment-test",
    "currentDate": "2026-03-12"
  }'

# Expected response:
# {"body": {"reply": "I am a Senior Cloud Software Engineer..."}}
```

### 9. Configure Monitoring & Alarms

```bash
# Create CloudWatch alarms
aws cloudwatch put-metric-alarm \
  --alarm-name alfred-lambda-errors \
  --alarm-description "Alert on Lambda errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanOrEqualToThreshold

# List alarms
aws cloudwatch describe-alarms --alarm-names alfred-lambda-errors
```

---

## Rollback Procedures

### Rollback to Previous Version

#### Option 1: Using Terraform State

```bash
# View existing deployments
terraform state list

# Show specific resource version
terraform state show aws_lambda_function.assistant

# Rollback to previous state (if saved)
terraform state pull > current.json  # Save current state
# Edit current.json to revert to previous version
terraform state push < previous.json

# Or simply re-apply with previous code
git checkout HEAD~1  # Go back one commit
terraform apply
```

#### Option 2: Using Lambda Versions

```bash
# List Lambda versions
aws lambda list-versions-by-function \
  --function-name alfred-assistant-handler

# Update alias to previous version
PREVIOUS_VERSION=5
aws lambda update-alias \
  --function-name alfred-assistant-handler \
  --name live \
  --routing-config AdditionalVersionWeight={${PREVIOUS_VERSION}=1.0}
```

#### Option 3: Manual Rollback

```bash
# Create quick rollback script
cat > rollback.sh << 'EOF'
#!/bin/bash
set -e

echo "Rolling back to previous deployment..."

# Download previous code
git checkout HEAD~1
make build

# Redeploy
cd terraform
terraform apply -auto-approve -refresh=false

echo "Rollback complete"
EOF

chmod +x rollback.sh
./rollback.sh
```

---

## Destruction (Removing Infrastructure)

### Destroy All Resources

```bash
cd terraform

# Plan destruction
terraform plan -destroy

# Destroy (requires confirmation)
terraform destroy

# Or auto-approve (dangerous!)
terraform destroy -auto-approve

# Remove S3 bucket (with data)
aws s3 rm s3://alfred-knowledge-bucket-prod --recursive

# Clean up DynamoDB tables
aws dynamodb delete-table --table-name alfred-runtime-cache
aws dynamodb delete-table --table-name alfred-usage-tracker
```

**⚠️ WARNING**: This is **PERMANENT**. Data cannot be recovered.

---

## Scaling

### Horizontal Scaling

```bash
# Lambda automatically scales. Adjust concurrency limits:

# Set reserved concurrency
aws lambda put-function-concurrency \
  --function-name alfred-assistant-handler \
  --reserved-concurrent-executions 100

# Set provisioned concurrency (always warm, higher cost)
aws lambda put-provisioned-function-concurrency \
  --function-name alfred-assistant-handler \
  --provisioned-concurrent-executions 10
```

### Vertical Scaling

```bash
# Increase Lambda memory (= more CPU, faster)
terraform apply -var="lambda_memory=1024"

# Adjust timeout if needed
terraform apply -var="lambda_timeout=120"
```

### DynamoDB Autoscaling

```bash
# Enable autoscaling for read/write capacity
aws application-autoscaling register-scalable-target \
  --service-namespace dynamodb \
  --resource-id table/alfred-runtime-cache \
  --scalable-dimension dynamodb:table:WriteCapacityUnits \
  --min-capacity 5 \
  --max-capacity 100

# Create scaling policy
aws application-autoscaling put-scaling-policy \
  --policy-name alfred-scale-writes \
  --service-namespace dynamodb \
  --scalable-dimension dynamodb:table:WriteCapacityUnits \
  --resource-id table/alfred-runtime-cache \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration TargetValue=70
```

---

## Cost Optimization

### Estimate Monthly Costs

```bash
# Calculate based on expected usage
python3 << 'EOF'
# Assumptions
daily_requests = 100
concurrent_users = 10
avg_response_time = 1.5  # seconds
lambda_memory_mb = 512

# Lambda costs
monthly_requests = daily_requests * 30
lambda_gb_seconds = (lambda_memory_mb / 1024) * avg_response_time * (monthly_requests / 1000)
lambda_compute = lambda_gb_seconds * 0.0000166667
lambda_requests = monthly_requests * 0.0000002
lambda_total = lambda_compute + lambda_requests

# Bedrock (Nova Lite input/output tokens)
avg_input_tokens = 500  # per request
avg_output_tokens = 150
input_cost = monthly_requests * avg_input_tokens / 1000 * 0.00000375  # $0.375 per million tokens
output_cost = monthly_requests * avg_output_tokens / 1000 * 0.00032  # $0.32 per million tokens
bedrock_total = input_cost + output_cost

# DynamoDB
read_capacity = 5
write_capacity = 5
dynamodb_total = (read_capacity + write_capacity) * 0.00013 * 730  # hours in month

# API Gateway
api_cost = monthly_requests * 0.035 / 1000

# Total
total = lambda_total + bedrock_total + dynamodb_total + api_cost

print(f"Lambda: ${lambda_total:.2f}")
print(f"Bedrock: ${bedrock_total:.2f}")
print(f"DynamoDB: ${dynamodb_total:.2f}")
print(f"API Gateway: ${api_cost:.2f}")
print(f"\nTotal monthly: ${total:.2f}")
EOF
```

### Cost Optimization Tips

1. **Use Amazon Nova Lite**: Cheaper than Claude 3.5, good accuracy
2. **Inference Profiles**: Lower cost than foundation models
3. **Caching**: Reduces LLM calls, saves on token costs
4. **Rate Limiting**: Prevents runaway costs from abuse
5. **DynamoDB On-Demand**: Better for variable traffic patterns
6. **Lambda Memory**: Right-size to balance cost vs. speed

---

## Monitoring & Alerts

### CloudWatch Dashboard

```bash
# Create dashboard
aws cloudwatch put-dashboard \
  --dashboard-name alfred-dashboard \
  --dashboard-body file://dashboard-config.json

# Example dashboard-config.json:
# {
#   "widgets": [
#     {
#       "type": "metric",
#       "properties": {
#         "metrics": [
#           ["AWS/Lambda", "Duration", {"stat": "Average"}],
#           ["AWS/Lambda", "Errors", {"stat": "Sum"}],
#           ["AWS/DynamoDB", "ConsumedReadCapacityUnits"]
#         ]
#       }
#     }
#   ]
# }
```

### Critical Alarms

```bash
# Lambda Error Rate
aws cloudwatch put-metric-alarm \
  --alarm-name alfred-high-error-rate \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --alarm-actions arn:aws:sns:us-east-1:123456789:alerts

# DynamoDB Throttling
aws cloudwatch put-metric-alarm \
  --alarm-name alfred-dynamodb-throttle \
  --metric-name UserErrors \
  --namespace AWS/DynamoDB \
  --table-name alfred-runtime-cache \
  --statistic Sum \
  --threshold 1

# High Latency
aws cloudwatch put-metric-alarm \
  --alarm-name alfred-high-latency \
  --metric-name Duration \
  --namespace AWS/Lambda \
  --statistic Average \
  --period 300 \
  --threshold 5000  # 5 seconds
```

### View Logs

```bash
# Real-time tail
aws logs tail /aws/lambda/alfred-assistant-handler --follow

# Last N lines
aws logs tail /aws/lambda/alfred-assistant-handler --max-items 50

# Specific time range
aws logs filter-log-events \
  --log-group-name /aws/lambda/alfred-assistant-handler \
  --start-time 1678300800000 \
  --end-time 1678387200000

# Search for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/alfred-assistant-handler \
  --filter-pattern "ERROR"
```

---

## Backup & Recovery

### Backup DynamoDB

```bash
# On-demand backup
aws dynamodb create-backup \
  --table-name alfred-runtime-cache \
  --backup-name alfred-cache-backup-2026-03-12

# List backups
aws dynamodb list-backups

# Restore from backup
aws dynamodb restore-table-from-backup \
  --target-table-name alfred-runtime-cache-restored \
  --backup-arn arn:aws:dynamodb:us-east-1:123456789:table/alfred-runtime-cache/backup/01234567890123-abcdefgh
```

### Backup S3 Knowledge Base

```bash
# Enable versioning
aws s3api put-bucket-versioning \
  --bucket alfred-knowledge-bucket-prod \
  --versioning-configuration Status=Enabled

# List versions
aws s3api list-object-versions \
  --bucket alfred-knowledge-bucket-prod

# Restore previous version
aws s3api get-object \
  --bucket alfred-knowledge-bucket-prod \
  --key knowledge_base.json \
  --version-id VersionId123 \
  knowledge_base.restored.json
```

---

## Production Checklist

- [ ] AWS account configured and credentials set
- [ ] Terraform initialized and backend configured
- [ ] Lambda code tested locally
- [ ] Knowledge base validated and uploaded to S3
- [ ] Environment variables configured correctly
- [ ] IAM roles and permissions reviewed
- [ ] API Gateway endpoint configured
- [ ] CORS origins whitelisted
- [ ] DynamoDB tables created with autoscaling
- [ ] Bedrock access verified (IAM policy, inference profile)
- [ ] CloudWatch alarms configured
- [ ] Monitoring dashboard created
- [ ] Rollback procedure tested
- [ ] DNS configured (if using custom domain)
- [ ] SSL certificate installed (API Gateway handles)
- [ ] Documentation updated
- [ ] Team notified of deployment

---

## Troubleshooting

### Lambda Function Errors

```bash
# Check function configuration
aws lambda get-function --function-name alfred-assistant-handler

# Check recent errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/alfred-assistant-handler \
  --filter-pattern "ERROR" \
  --start-time $(date -d '1 hour ago' +%s)000

# Update function code from existing zip
aws lambda update-function-code \
  --function-name alfred-assistant-handler \
  --zip-file fileb://lambda-package.zip
```

### Bedrock Access Issues

```bash
# Check IAM policy
aws iam get-role-policy \
  --role-name alfred-lambda-role \
  --policy-name bedrock-access

# Test Bedrock API
aws bedrock-runtime invoke-model \
  --model-id us.amazon.nova-lite-v1:0 \
  --body '{"messages":[{"role":"user","content":"Hello"}]}' \
  response.json
```

### DynamoDB Throttling

```bash
# Check capacity usage
aws dynamodb describe-table --table-name alfred-runtime-cache

# Increase on-demand capacity
aws dynamodb update-table \
  --table-name alfred-runtime-cache \
  --billing-mode PAY_PER_REQUEST
```

---

## Post-Deployment Steps

1. **Monitor closely** first 24 hours
2. **Test via production API** with real traffic
3. **Review CloudWatch metrics** and logs
4. **Validate response quality** from Bedrock
5. **Confirm rate limiting** working correctly
6. **Document any deviations** from plan
7. **Update runbook** with actual metrics
8. **Communicate** deployment success to team

---

## References

- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)

---

**For questions or issues, contact the DevOps team.**
