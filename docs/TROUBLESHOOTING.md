# Troubleshooting Guide

Common issues, error messages, and solutions.

---

## Table of Contents

1. [Lambda Errors](#lambda-errors)
2. [Bedrock Errors](#bedrock-errors)
3. [DynamoDB Errors](#dynamodb-errors)
4. [API Errors](#api-errors)
5. [Performance Issues](#performance-issues)
6. [Deployment Issues](#deployment-issues)

---

## Lambda Errors

### Error: "AccessDeniedException: User is not authorized to perform: bedrock:InvokeModel"

**Cause**: Lambda IAM role lacks Bedrock permissions

**Solution**:

```bash
# Check current policy
aws iam get-role-policy \
  --role-name alfred-lambda-role \
  --policy-name bedrock-access

# Add permission (if missing)
aws iam put-role-policy \
  --role-name alfred-lambda-role \
  --policy-name bedrock-access \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:*:*:foundation-model/*",
        "arn:aws:bedrock:*:*:inference-profile/*"
      ]
    }]
  }'

# Redeploy Lambda
terraform -chdir=terraform apply
```

---

### Error: "Unable to locate credentials"

**Cause**: AWS credentials not configured for Lambda

**Solution**:

```bash
# Verify Lambda role has correct assume policy
aws iam get-role --role-name alfred-lambda-role

# Should trust Lambda service:
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Service": "lambda.amazonaws.com"
    },
    "Action": "sts:AssumeRole"
  }]
}

# If missing, add it:
aws iam update-assume-role-policy-document \
  --role-name alfred-lambda-role \
  --policy-document file://trust-policy.json
```

---

### Error: "Timeout waiting for response"

**Cause**: Lambda timeout (60s default) too short

**Check**: Look for slow Bedrock calls in logs

```bash
aws logs filter-log-events \
  --log-group-name /aws/lambda/alfred-assistant-handler \
  --filter-pattern "Duration"
```

**Solution**:

```bash
# Increase timeout to 120 seconds
aws lambda update-function-configuration \
  --function-name alfred-assistant-handler \
  --timeout 120

# Or in Terraform:
# timeout = 120  # in lambda module
terraform apply
```

---

### Error: "RequestLimitExceeded: Rate exceeded"

**Cause**: Lambda concurrency limit hit

**Solution**:

```bash
# Increase reserved concurrency
aws lambda put-function-concurrency \
  --function-name alfred-assistant-handler \
  --reserved-concurrent-executions 500

# Check current metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name ConcurrentExecutions \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Maximum
```

---

### Error: "Module not found: boto3"

**Cause**: Dependencies not included in Lambda package

**Solution**:

```bash
# Rebuild Lambda with dependencies
make build  # Creates zip with all dependencies

# Or manually:
pip install -r src/requirements.txt -t lambda_package/
zip -r lambda-function.zip src/ lambda_package/

# Verify size
ls -lh lambda-function.zip  # Should be < 250 MB

# Redeploy
aws lambda update-function-code \
  --function-name alfred-assistant-handler \
  --zip-file fileb://lambda-function.zip
```

---

## Bedrock Errors

### Error: "ValidationException: Provided model identifier is invalid"

**Cause**: MODEL_ID format incorrect or model doesn't exist

**Solution**:

```bash
# List available models
aws bedrock list-foundation-models

# Correct format for inference profiles:
# us.amazon.nova-lite-v1:0  ✓
# anthropic.claude-3-5-sonnet-20241022-v2:0  ✓
# amazon.titan-text-lite-v1:0  ✓

# Update environment variable
export MODEL_ID=us.amazon.nova-lite-v1:0

# Redeploy
terraform apply -var="model_id=us.amazon.nova-lite-v1:0"
```

---

### Error: "ThrottlingException: Rate exceeded"

**Cause**: Too many concurrent Bedrock requests

**Solution**:

```bash
# Check provisioned throughput
aws bedrock describe-provisioned-model-throughput

# For on-demand (recommended), no action needed
# AWS will automatically handle scale

# Monitor usage
aws cloudwatch get-metric-statistics \
  --namespace AWS/Bedrock \
  --metric-name InvokeModelCount \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

---

### Error: "ModelStreamingOutputNotReadable"

**Cause**: Response streaming configuration issue (if enabled)

**Solution**:

```python
# Check if streaming is disabled (recommended)
response = bedrock_client.invoke_model(
    modelId=MODEL_ID,
    body=request_body,
    # responseStream=False  # Make sure it's not True
)
```

---

### Error: "ContentFilteredException"

**Cause**: Bedrock content filter blocked the response

**Solution**:

```python
# This is a safety feature. Examples of blocked content:
# - Hate speech
# - Violence
# - Sexual content

# Options:
# 1. Rephrase question (if user's question triggered it)
# 2. Review system prompt for policy violations
# 3. Re-run (might succeed next time due to model randomness)
```

---

## DynamoDB Errors

### Error: "ResourceNotFoundException: Requested resource not found"

**Cause**: Table doesn't exist

**Solution**:

```bash
# List tables
aws dynamodb list-tables

# Create table if missing
terraform apply  # Creates all tables

# Or manually create:
aws dynamodb create-table \
  --table-name alfred-runtime-cache \
  --attribute-definitions AttributeName=question_hash,AttributeType=S \
  --key-schema AttributeName=question_hash,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

---

### Error: "ValidationException: One or more parameter values were invalid"

**Cause**: Invalid item attributes or types

**Solution**:

```python
# Verify item has correct structure:
item = {
    'question_hash': 'abc123',      # String ✓
    'response': 'Answer text',      # String ✓
    'timestamp': 1678300800,        # Number ✓
    'TTL': 1680892800,              # Number ✓
}

# Common mistakes to avoid:
# ❌ item = {'key': {'nested': 'value'}}  # No nested objects
# ❌ item = {'key': None}                 # No null values
# ❌ item = {'key': []}                   # Empty lists forbidden
```

---

### Error: "ProvisionedThroughputExceededException"

**Cause**: Table throughput exceeded (provisioned capacity)

**Solution**:

```bash
# Switch to on-demand (recommended for Alfred)
aws dynamodb update-table \
  --table-name alfred-runtime-cache \
  --billing-mode PAY_PER_REQUEST

# Or increase provisioned capacity
aws dynamodb update-table \
  --table-name alfred-runtime-cache \
  --provisioned-throughput ReadCapacityUnits=25,WriteCapacityUnits=25
```

---

### Error: "ConditionalCheckFailedException"

**Cause**: Conditional update/put failed

**Solution**:

```python
# Example error scenario:
table.put_item(
    Item={'id': '123', 'value': 'data'},
    ConditionExpression='attribute_not_exists(id)'  # Fails if 'id' already exists
)

# Fix: Remove condition or adjust logic
table.put_item(Item={'id': '123', 'value': 'data'})  # No condition
# or
table.update_item(Key={'id': '123'}, UpdateExpression='SET #v = :val', ...)  # Update instead
```

---

## API Errors

### Error 400: "I am sorry, but that was an invalid question"

**Cause**: Question validation failed

**Solution**:

```
Check that:
- Question length >= 3 characters
- Question contains alphanumeric characters
- No null bytes or control characters
- Question is not empty or whitespace-only

Example:
✓ "What is your experience?"
✗ "Hi"  (too short)
✗ ""    (empty)
✗ "   " (whitespace only)
```

---

### Error 403: "You are chatting with me from a different place"

**Cause**: CORS origin not whitelisted

**Solution**:

```bash
# Check current whitelist
echo $ALLOWED_ORIGINS

# Add new origin
export ALLOWED_ORIGINS="https://locle.dev,https://new-domain.com"

# Redeploy
terraform apply

# Verify in Lambda environment
aws lambda get-function-configuration \
  --function-name alfred-assistant-handler | grep ALLOWED_ORIGINS
```

---

### Error 429: "You have too many queries"

**Cause**: Rate limit exceeded

**Solution**:

```
Rate limit is 3 requests per user per day.

Steps to test if limit resets:
1. Note current day: 2026-03-12
2. Check when quota resets: midnight UTC
3. Wait until next day or:
   - Use different userId
   - Use different date in request (currentDate)
```

---

### Error 500: "Something went wrong on our end"

**Cause**: Internal Lambda error

**Solution**:

```bash
# Check Lambda logs
aws logs tail /aws/lambda/alfred-assistant-handler --follow

# Look for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/alfred-assistant-handler \
  --filter-pattern "ERROR\|Exception\|Traceback"

# Common causes:
# - Knowledge base not accessible (S3 error)
# - Bedrock invocation failed
# - DynamoDB throttling
# - Unhandled Python exception
```

---

### Error 503: "We are temporarily unavailable"

**Cause**: Bedrock or AWS service temporarily down

**Solution**:

```bash
# Check AWS status
curl https://status.aws.amazon.com/

# Monitor Bedrock availability
aws bedrock describe-foundation-models \
  --query 'modelSummaries[0]'

# Retry with exponential backoff (1s, 2s, 4s, 8s)
# Wait 30-60 seconds and try again
```

---

## Performance Issues

### Issue: High Latency (>5 seconds)

**Diagnosis**:

```bash
# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --start-time $(date -d '1 hour ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average,Maximum

# Check Bedrock latency
aws logs filter-log-events \
  --log-group-name /aws/lambda/alfred-assistant-handler \
  --filter-pattern "bedrock_latency"
```

**Solutions**:

1. **Increase Lambda memory**:

```bash
aws lambda update-function-configuration \
  --function-name alfred-assistant-handler \
  --memory-size 1024
```

2. **Enable caching** (if not already):

```python
# In AssistantService
cached = self.repository.get_cached_response(question)
if cached:
    return cached  # Fast path
```

3. **Warm up Lambda** (use provisioned concurrency):

```bash
aws lambda put-provisioned-concurrent-executions \
  --function-name alfred-assistant-handler \
  --provisioned-concurrent-executions 5
```

---

### Issue: Occasional Slow Requests (Cold Starts)

**Cause**: Lambda container initialization (first request or after idle time)

**Check**:

```bash
# Look for cold start indicator in logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/alfred-assistant-handler \
  --filter-pattern "INIT_START"
```

**Solutions**:

1. **Use provisioned concurrency** (warmup):

```bash
aws lambda put-provisioned-concurrent-executions \
  --function-name alfred-assistant-handler \
  --provisioned-concurrent-executions 1  # $0.015/hr
```

2. **Reduce function size** (faster initialization):

- Remove unused dependencies
- Use Lambda layers for shared code

3. **Optimize imports** (faster startup):

```python
# SLOW: Import at top level
import pandas as pd  # 100ms to load
import numpy as np    # 50ms to load

# FAST: Import only when needed
if needs_pandas:
    import pandas as pd  # Lazy load
```

---

### Issue: High DynamoDB Costs

**Diagnosis**:

```bash
# Check consumed capacity
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedWriteCapacityUnits \
  --dimensions Name=TableName,Value=alfred-runtime-cache \
  --start-time $(date -d '1 day ago' -u +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum
```

**Solutions**:

1. **Switch to on-demand**:

```bash
aws dynamodb update-table \
  --table-name alfred-runtime-cache \
  --billing-mode PAY_PER_REQUEST
```

2. **Reduce cache TTL**:

```python
# Shorter TTL = fewer items stored
CACHE_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days (from 30)
```

3. **Improve cache hit rate** (less DynamoDB writes):

```bash
# Monitor cache hit rate
aws logs filter-log-events \
  --log-group-name /aws/lambda/alfred-assistant-handler \
  --filter-pattern "cache_hit"
```

---

## Deployment Issues

### Error: "Terraform: resource already exists"

**Cause**: Terraform state out of sync with AWS

**Solution**:

```bash
# Option 1: Refresh state
terraform refresh

# Option 2: Import existing resource
terraform import aws_lambda_function.assistant alfred-assistant-handler

# Option 3: Recreate resource
terraform destroy -target aws_lambda_function.assistant
terraform apply
```

---

### Error: "Insufficient permissions to assume role"

**Cause**: IAM user lacks permission to create/modify roles

**Solution**:

```bash
# Verify IAM policy
aws iam get-user-policy --user-name your-user --policy-name inline-policy

# Need these permissions:
# - iam:CreateRole
# - iam:AttachRolePolicy
# - iam:UpdateAssumeRolePolicy
# - iam:PutRolePolicy

# Contact admin to add these permissions
```

---

### Error: "S3 bucket does not exist"

**Cause**: Knowledge bucket not created

**Solution**:

```bash
# Create manually
aws s3 mb s3://alfred-knowledge-bucket-prod --region us-east-1

# Or let Terraform create it
terraform apply

# Upload knowledge base
aws s3 cp knowledge_base.json s3://alfred-knowledge-bucket-prod/

# Verify
aws s3 ls s3://alfred-knowledge-bucket-prod/
```

---

## Getting Help

### Information to Gather Before Asking for Help

1. **Error message**: Full quote exact error
2. **Context**: When did error occur? What was the user doing?
3. **Logs**: CloudWatch log excerpts
4. **Recent changes**: What changed before the error?
5. **Environment**: dev, staging, or prod?
6. **Reproducibility**: Can you reproduce consistently?

### Where to Ask

- **Slack**: #alfred-support channel
- **Email**: support@locle.dev
- **GitHub Issues**: Create issue with details
- **Incident Report**: For production issues

### Debugging Checklist

- [ ] Check CloudWatch logs
- [ ] Check Lambda memory/timeout
- [ ] Check AWS credentials
- [ ] Check IAM permissions
- [ ] Check environment variables
- [ ] Check knowledge base in S3
- [ ] Check DynamoDB tables exist
- [ ] Verify Bedrock access
- [ ] Test Lambda locall (SAM)
- [ ] Check recent Terraform changes

---

**Still stuck? Reach out to the team or check docs/FAQ.md**
