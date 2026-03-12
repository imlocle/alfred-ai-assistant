# Deployment Runbook

**Purpose**: Complete step-by-step guide for deploying Alfred to AWS environments.  
**Audience**: DevOps engineers, SREs, deployment personnel  
**Updated**: March 2026

---

## Pre-Deployment Checklist

### Prerequisites

- [ ] AWS CLI configured with appropriate credentials
- [ ] Terraform installed (v1.0+)
- [ ] Docker installed (for Lambda layer builds)
- [ ] S3 bucket for Terraform state created and versioned
- [ ] Knowledge base JSON file prepared
- [ ] SSL certificates ready (if applicable)
- [ ] Deployment checklist signed by team lead

### Access & Permissions

- [ ] Requester has IAM permissions for Lambda, API Gateway, DynamoDB, S3, CloudWatch
- [ ] AWS account access verified
- [ ] Terraform state bucket accessible
- [ ] KMS keys available (if using encrypted state)

---

## Environment Setup

### 1. Initialize Terraform State (First Deployment Only)

```bash
# Create state bucket (one-time)
aws s3 mb s3://alfred-terraform-state-bucket-${ENV} --region us-west-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket alfred-terraform-state-bucket-${ENV} \
  --versioning-configuration Status=Enabled

# Block public access
aws s3api put-public-access-block \
  --bucket alfred-terraform-state-bucket-${ENV} \
  --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
```

### 2. Create S3 Knowledge Base Bucket

```bash
# Create bucket
aws s3 mb s3://alfred-knowledge-bucket-${ENV} --region us-west-1

# Enable versioning for rollback capability
aws s3api put-bucket-versioning \
  --bucket alfred-knowledge-bucket-${ENV} \
  --versioning-configuration Status=Enabled

# Block public access
aws s3api put-public-access-block \
  --bucket alfred-knowledge-bucket-${ENV} \
  --public-access-block-configuration \
  "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"

# Upload knowledge base
aws s3 cp knowledge_base.json \
  s3://alfred-knowledge-bucket-${ENV}/knowledge_base.json
```

### 3. Configure Environment

Create `.env.${ENV}` file:

```bash
ENV=dev|staging|prod
AWS_REGION=us-west-1
AWS_ACCOUNT_ID=123456789012

# Application Settings
MODEL_ID=us.amazon.nova-lite-v1:0
TEMPERATURE=0.2
MAX_TOKENS=200

# DynamoDB Settings
USAGE_TRACKER_TABLE=alfred-usage-tracker-${ENV}
CACHE_TTL_SECONDS=3600
RATE_LIMIT_MAX_REQUESTS=50

# S3 Knowledge Base
KNOWLEDGE_BASE_BUCKET=alfred-knowledge-bucket-${ENV}

# CORS Settings
ALLOWED_ORIGINS=https://imlocle.com,http://localhost:5173

# Logging
LOG_LEVEL=INFO
```

---

## Deployment Steps

### Phase 1: Build Lambda Layer

```bash
# Clean previous builds
make clean

# Build Lambda layer (includes boto3, botocore, bedrock SDK)
make build

# Verify layer structure
ls -la lambda_layer/python/
```

### Phase 2: Terraform Plan & Apply

```bash
# Navigate to Terraform directory
cd terraform

# Initialize Terraform (first time only)
terraform init \
  -backend-config="bucket=alfred-terraform-state-bucket-${ENV}" \
  -backend-config="key=alfred-${ENV}/terraform.tfstate" \
  -backend-config="region=us-west-1" \
  -backend-config="encrypt=true" \
  -backend-config="dynamodb_table=alfred-terraform-locks"

# Plan deployment
terraform plan \
  -var="environment=${ENV}" \
  -var="aws_region=us-west-1" \
  -out=tfplan

# Review plan output carefully
# Verify no unexpected resources will be destroyed

# Apply changes
terraform apply tfplan

# Save outputs
terraform output -json > outputs-${ENV}.json
```

### Phase 3: Verify Deployment

```bash
# Get API Gateway endpoint
API_ENDPOINT=$(terraform output -raw api_endpoint)
echo "API Endpoint: $API_ENDPOINT"

# Test basic connectivity
curl -X POST $API_ENDPOINT/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Who is Loc Le?"}'

# Verify Lambda function exists
aws lambda get-function --function-name alfred-handler-${ENV} --region us-west-1

# Verify DynamoDB tables
aws dynamodb list-tables --region us-west-1 | grep alfred

# Verify S3 buckets
aws s3 ls | grep alfred-${ENV}

# Check CloudWatch logs
aws logs tail /aws/lambda/alfred-handler-${ENV} --follow --since 5m
```

---

## Deployment by Environment

### Development Environment

```bash
# Full deployment with data reset
make clean && make build && make deploy ENV=dev

# After deployment
export API_ENDPOINT=$(cd terraform && terraform output -raw api_endpoint)
curl $API_ENDPOINT/health
```

### Staging Environment

```bash
# Blue-green deployment
make deploy ENV=staging STRATEGY=blue-green

# Validation tests
pytest integration_tests/ -v --baseurl=$API_ENDPOINT

# Monitor for 30 minutes before production
```

### Production Environment

```bash
# Managed deployment with alarms
make deploy-prod \
  --enable-alarms \
  --notify-slack \
  --require-approval

# Rollout monitoring
kubectl logs -f deployment/alfred-prod --all-containers=true
```

---

## Post-Deployment Validation

### 1. Health Checks

```bash
#!/bin/bash
# Run quick health checks post-deployment

ENDPOINT=$1
REGION=$2

echo "🔍 Performing post-deployment validation..."

# Lambda Health
echo "✓ Lambda Function Active:"
aws lambda get-function-concurrency --function-name alfred-handler-${REGION}

# API Gateway
echo "✓ API Gateway Response:"
curl -s -w "\nStatus: %{http_code}\n" $ENDPOINT/health

# DynamoDB Connectivity
echo "✓ DynamoDB Tables:"
aws dynamodb describe-table --table-name alfred-usage-tracker-${REGION} \
  --query 'Table.TableStatus'

# S3 Knowledge Base
echo "✓ S3 Knowledge Base:"
aws s3 ls s3://alfred-knowledge-bucket-${REGION}/

echo "✅ All systems operational"
```

### 2. Smoke Tests

```bash
# Run quick smoke tests
curl -X POST $API_ENDPOINT/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Who are you?",
    "requestContext": {"requestId": "smoke-test-1"}
  }'

# Expected response: 200 OK with AI response
# Test from multiple IPs to verify CORS
```

### 3. Monitoring Setup

```bash
# Verify CloudWatch alarms
aws cloudwatch describe-alarms \
  --alarm-name-prefix alfred-${ENV} \
  --query 'MetricAlarms[].AlarmName'

# Enable detailed monitoring
aws cloudwatch put-metric-alarm \
  --alarm-name alfred-${ENV}-errors \
  --alarm-description "Lambda errors alarm" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold
```

---

## Rollback Procedure

### If Deployment Fails

```bash
# 1. Identify what went wrong
aws cloudformation describe-stack-events \
  --stack-name alfred-${ENV} \
  --query 'StackEvents[?ResourceStatus==`CREATE_FAILED`]'

# 2. Review Lambda logs
aws logs tail /aws/lambda/alfred-handler-${ENV} --since 5m --follow

# 3. Option A: Rollback to previous state
terraform destroy -auto-approve
git checkout HEAD~1
make deploy ENV=${ENV}

# 4. Option B: Fix and redeploy
# Make necessary fixes in code/config
make deploy ENV=${ENV}
```

### If Production Issues Arise

```bash
# 1. Immediate: Reduce traffic / enable circuit breaker
aws apigateway update-stage \
  --rest-api-id ${API_ID} \
  --stage-name prod \
  --patch-operations op=replace,path=/throttle/rateLimit,value=100

# 2. Check logs for root cause
aws logs tail /aws/lambda/alfred-handler-prod --follow

# 3. Roll back if necessary
cd terraform && terraform apply -var="version=previous-stable"

# 4. Communicate status
# Post incident report to team
```

---

## Deployment Checklist

```
# Pre-Deployment
☐ Code review completed
☐ Tests passing (99/99)
☐ Terraform plan reviewed
☐ Knowledge base updated
☐ Team notified of deployment window
☐ Runbook reviewed

# During Deployment
☐ Terraform apply completed successfully
☐ Lambda function verified active
☐ Health checks passed
☐ Smoke tests passed
☐ Monitoring alerts configured
☐ Team notified of progress

# Post-Deployment
☐ Production traffic normal
☐ Error rates within baseline
☐ Response latency normal
☐ Cost metrics normal
☐ Documentation updated
☐ Runbook recorded in log

# Sign Off
Deployed by: _________________ Date: ________
Reviewed by: _________________ Date: ________
```

---

## Common Issues & Solutions

### Issue: Terraform State Lock Timeout

**Solution**:

```bash
# Check lock
terraform force-unlock ${LOCK_ID}

# Or wait for lock timeout (300s default)
sleep 300
```

### Issue: Lambda Layer Build Fails

**Solution**:

```bash
# Rebuild from scratch
rm -rf lambda_layer/python/
make build

# Verify Docker is running
docker ps
```

### Issue: Knowledge Base S3 Upload Fails

**Solution**:

```bash
# Verify S3 bucket exists and is accessible
aws s3 ls s3://alfred-knowledge-bucket-${ENV}/

# Check IAM permissions
aws sts get-caller-identity

# Retry upload
aws s3 cp knowledge_base.json s3://alfred-knowledge-bucket-${ENV}/
```

---

## Monitoring Post-Deployment

### See Also

- [OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md) — Daily monitoring procedures
- [COSTS_ANALYSIS.md](COSTS_ANALYSIS.md) — Expected costs to monitor

### Key Metrics to Watch

- Lambda invocation count
- Lambda error rate (should be <1%)
- Average response latency (should be <2 seconds)
- DynamoDB read/write capacity
- S3 request count
- Bedrock token usage
- Cost per request

---

**Last Updated**: March 2026  
**Deployment Window**: 30-45 minutes  
**Rollback Time**: 15-20 minutes  
**Next Review**: June 2026
