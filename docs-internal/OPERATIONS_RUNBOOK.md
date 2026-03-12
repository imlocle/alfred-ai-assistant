# Operations Runbook

**Purpose**: Daily operations, monitoring, incident response, and troubleshooting procedures.  
**Audience**: DevOps engineers, SREs, on-call engineers  
**Updated**: March 2026

---

## Daily Operations

### Morning Checklist (5-10 minutes)

```bash
#!/bin/bash
# Run each morning to verify system health

REGION=us-west-1
ENV=prod

echo "📋 Alfred Daily Operations Checklist"
echo "Time: $(date -u)"
echo "Region: $REGION"
echo ""

# 1. Check service health
echo "✓ Lambda Function Status:"
aws lambda get-function --function-name alfred-handler-${ENV} \
  --query 'Configuration.LastUpdateStatus' --region $REGION

# 2. Check error rates (last hour)
echo "✓ Lambda Error Count (last hour):"
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=alfred-handler-${ENV} \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum \
  --region $REGION

# 3. Check DynamoDB table health
echo "✓ DynamoDB Usage Tracker Status:"
aws dynamodb describe-table \
  --table-name alfred-usage-tracker-${ENV} \
  --query 'Table.{Status:TableStatus, ConsumedCapacity:ProvisionedThroughput.ReadCapacityUnits}' \
  --region $REGION

# 4. Check recent logs
echo "✓ Recent Errors in CloudWatch:"
aws logs filter-log-events \
  --log-group-name /aws/lambda/alfred-handler-${ENV} \
  --filter-pattern "ERROR" \
  --start-time $(($(date +%s) - 3600))000 \
  --region $REGION | head -20

echo ""
echo "✅ Health check complete. See below for any anomalies."
```

### Weekly Review (30 minutes)

**Monday Morning:**

1. Review weekend incident logs
2. Check cost trends in AWS Cost Explorer
3. Review rate limit distribution across users
4. Update [VERSION_HISTORY.md](VERSION_HISTORY.md) if changes made

**Friday Afternoon:**

1. Prepare deployment summary
2. Verify all tests still passing
3. Review [ROADMAP.md](../docs/ROADMAP.md) for next week priorities

---

## Monitoring & Alerting

### Key Metrics

| Metric                    | Warning Threshold | Critical Threshold | Check Frequency |
| ------------------------- | ----------------- | ------------------ | --------------- |
| Lambda Error Rate         | > 1%              | > 5%               | 5 min           |
| Lambda Duration           | > 3s (95th %ile)  | > 5s (95th %ile)   | 5 min           |
| DynamoDB Read Throttling  | > 0 events        | > 10 events        | 1 min           |
| DynamoDB Write Throttling | > 0 events        | > 10 events        | 1 min           |
| API Gateway 4xx Errors    | > 2%              | > 10%              | 5 min           |
| API Gateway 5xx Errors    | > 0.1%            | > 1%               | 5 min           |
| Cost per Request          | > $0.005          | > $0.01            | Hourly          |

### Setting Up CloudWatch Alarms

```bash
# Lambda Error Rate Alarm
aws cloudwatch put-metric-alarm \
  --alarm-name alfred-lambda-errors-high \
  --alarm-description "Lambda error rate > 5%" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Average \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2 \
  --alarm-actions arn:aws:sns:us-west-1:${ACCOUNT_ID}:alerts

# DynamoDB Read Throttling Alarm
aws cloudwatch put-metric-alarm \
  --alarm-name alfred-dynamodb-read-throttle \
  --alarm-description "DynamoDB read throttling detected" \
  --metric-name ConsumedReadCapacityUnits \
  --namespace AWS/DynamoDB \
  --statistic Sum \
  --period 60 \
  --threshold 100 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-west-1:${ACCOUNT_ID}:alerts
```

---

## Incident Response

### Incident Severity Levels

| Severity          | Definition                         | Response Time | Escalation       |
| ----------------- | ---------------------------------- | ------------- | ---------------- |
| **P1 - Critical** | Complete outage, no responses      | < 5 min       | Director         |
| **P2 - High**     | Degraded service, error rate > 10% | < 15 min      | Engineering Lead |
| **P3 - Medium**   | Minor issues, error rate 1-10%     | < 1 hour      | On-call Engineer |
| **P4 - Low**      | Non-urgent improvements            | < 1 day       | Backlog          |

### Incident Response Playbook

#### Step 1: Immediate Response (First 5 minutes)

```bash
# IMMEDIATELY notify team on Slack
# Format: "🚨 [P${SEVERITY}] ${ISSUE_TITLE} - ${IMPACT}"

# Verify the issue
ENDPOINT=$(aws apigateway get-rest-apis --query 'items[0].id' --output text)
curl -w "\nStatus: %{http_code}\n" https://${ENDPOINT}.execute-api.us-west-1.amazonaws.com/prod/health

# Get logs
aws logs tail /aws/lambda/alfred-handler-prod --follow --since 5m

# Check metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --statistics Sum \
  --start-time $(date -u -d '15 min ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60
```

#### Step 2: Diagnosis (Next 10-15 minutes)

**Lambda Issues?**

```bash
# Check recent deployments
aws lambda get-function --function-name alfred-handler-prod

# Check environment variables
aws lambda get-function-configuration --function-name alfred-handler-prod \
  | jq '.Environment.Variables'

# Check logs for patterns
aws logs filter-log-events \
  --log-group-name /aws/lambda/alfred-handler-prod \
  --filter-pattern 'ERROR' \
  --start-time $(($(date +%s) - 600))000
```

**DynamoDB Issues?**

```bash
# Check table status
aws dynamodb describe-table --table-name alfred-usage-tracker-prod \
  | jq '.Table | { Status, ConsumedCapacity: .ProvisionedThroughput }'

# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=alfred-usage-tracker-prod \
  --statistics Sum \
  --start-time $(date -u -d '15 min ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60
```

**S3 Knowledge Base Issues?**

```bash
# Verify bucket is accessible
aws s3 ls s3://alfred-knowledge-bucket-prod/

# Check for corrupt knowledge base
aws s3 cp s3://alfred-knowledge-bucket-prod/knowledge_base.json - | jq . | head -50
```

#### Step 3: Mitigation (Immediate)

**Option A: Scale Up (If Under-Provisioned)**

```bash
# Increase Lambda concurrent executions
aws lambda put-function-concurrency \
  --function-name alfred-handler-prod \
  --reserved-concurrent-executions 100

# Increase DynamoDB capacity (if on provisioned mode)
aws dynamodb update-table \
  --table-name alfred-usage-tracker-prod \
  --provisioned-throughput ReadCapacityUnits=100,WriteCapacityUnits=100
```

**Option B: Rollback (If Recent Deployment)**

```bash
# Rollback to previous Lambda version
cd terraform
git checkout HEAD~1
terraform apply -auto-approve

# Verify rollback
aws lambda get-function --function-name alfred-handler-prod \
  | jq '.Configuration.LastModified'
```

**Option C: Circuit Breaker (If Overloaded)**

```bash
# Reduce API rate limit to shed load
aws apigateway update-stage \
  --rest-api-id ${API_ID} \
  --stage-name prod \
  --patch-operations op=replace,path=/throttle/rateLimit,value=10
```

#### Step 4: Incident Logging

```bash
# Document incident
cat > incident_${DATE}.md << EOF
# Incident Report: ${TITLE}

**Date**: $(date -u)
**Severity**: P${SEVERITY}
**Duration**: START_TIME to END_TIME
**Impact**: ${IMPACT_DESCRIPTION}

## Timeline
- START_TIME: Issue detected
- DIAGNOSIS_TIME: Root cause identified
- MITIGATION_TIME: Mitigation applied
- RESOLUTION_TIME: System recovered

## Root Cause
${ROOT_CAUSE_ANALYSIS}

## Mitigation Actions
1. Action 1
2. Action 2
3. Action 3

## Prevention (For Future)
${PREVENTION_STEPS}

## Owner
Incident Commander: ${NAME}
EOF
```

---

## Performance Tuning

### Latency Optimization

**Current Baseline**: ~1.5s (p95) from Lambda invocation to response

**Bottleneck Analysis**:

- Knowledge base S3 fetch: 200-300ms
- Bedrock inference: 800-1200ms
- Caching layer: -30-50% on cache hits
- DynamoDB writes: 50-100ms

**Optimization Steps**:

```bash
# 1. Enable S3 request caching
aws s3api put-bucket-versioning \
  --bucket alfred-knowledge-bucket-prod \
  --versioning-configuration Status=Enabled

# Monitor cache effectiveness
aws cloudwatch get-metric-statistics \
  --namespace AWS/S3 \
  --metric-name 4xxErrors \
  --start-time $(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum

# 2. Optimize DynamoDB queries
aws dynamodb describe-table --table-name alfred-usage-tracker-prod \
  | jq '.Table.GlobalSecondaryIndexes'

# 3. Monitor Bedrock latency
aws cloudwatch get-metric-statistics \
  --namespace AWS/Bedrock \
  --metric-name Duration \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 60 \
  --statistics Average,Maximum
```

### Cost Optimization

See [COST_OPTIMIZATION_GUIDE.md](COST_OPTIMIZATION_GUIDE.md) for detailed strategies.

Quick wins:

- Monitor cache hit rate (target: 40-60%)
- Review rate-limited requests (wasted API calls)
- Track inference token usage per query
- Monitor DynamoDB capacity vs. actual usage

---

## Troubleshooting Common Issues

### Issue: High Lambda Error Rate

**Symptoms**: Error rate > 5%, frequent 5xx responses

**Diagnosis**:

```bash
# Check logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/alfred-handler-prod \
  --filter-pattern 'ERROR' \
  --start-time $(($(date +%s) - 300))000

# Check if it's a knowledge base issue
aws s3 cp s3://alfred-knowledge-bucket-prod/knowledge_base.json - | jq '.version'

# Check if it's a Bedrock issue
# Try manual invocation
aws bedrock-runtime invoke-model \
  --model-id us.amazon.nova-lite-v1:0 \
  --body '{"messages":[{"role":"user","content":"Test"}]}' \
  response.json
```

**Resolution**:

1. Review recent Lambda changes
2. Check knowledge base integrity
3. Roll back if necessary
4. Increase logging level for detailed diagnostics

### Issue: DynamoDB Throttling

**Symptoms**: ProvisionedThroughputExceededException errors

**Diagnosis**:

```bash
aws dynamodb describe-table --table-name alfred-usage-tracker-prod \
  | jq '.Table.ProvisionedThroughput'
```

**Resolution**:

```bash
# Option 1: Scale up (provisioned mode)
aws dynamodb update-table \
  --table-name alfred-usage-tracker-prod \
  --provisioned-throughput ReadCapacityUnits=200,WriteCapacityUnits=100

# Option 2: Switch to on-demand mode
aws dynamodb update-table \
  --table-name alfred-usage-tracker-prod \
  --billing-mode PAY_PER_REQUEST
```

### Issue: S3 Knowledge Base Access Errors

**Symptoms**: "Failed to fetch knowledge base" error

**Diagnosis**:

```bash
# Check bucket exists
aws s3 ls s3://alfred-knowledge-bucket-prod/

# Check Lambda IAM role has S3 permissions
aws iam get-role-policy \
  --role-name alfred-lambda-role \
  --policy-name s3-access
```

**Resolution**:

```bash
# Re-upload knowledge base
aws s3 cp knowledge_base.json s3://alfred-knowledge-bucket-prod/

# Verify Lambda can read it
aws lambda invoke \
  --function-name alfred-handler-prod \
  --payload '{"body": "{\"question\": \"test\"}"}' \
  response.json
```

---

## Maintenance Tasks

### Weekly

- [ ] Review error logs
- [ ] Check cost trends
- [ ] Verify backups (if applicable)

### Monthly

- [ ] Dependency updates review
- [ ] Performance baseline check
- [ ] Security scan

### Quarterly

- [ ] Load testing
- [ ] Disaster recovery drill
- [ ] Architecture review

---

## See Also

- [DEPLOYMENT_RUNBOOK.md](DEPLOYMENT_RUNBOOK.md) — Deployment procedures
- [COSTS_ANALYSIS.md](COSTS_ANALYSIS.md) — Cost monitoring
- [INFRASTRUCTURE_DETAILS.md](INFRASTRUCTURE_DETAILS.md) — Infrastructure configuration

---

**Last Updated**: March 2026  
**Runbook Version**: 1.0  
**Next Review**: June 2026  
**On-Call Rotation**: Contact engineering lead for schedule
