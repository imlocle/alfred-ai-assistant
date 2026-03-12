# Cost Optimization Guide

Strategies and best practices for minimizing operational costs while maintaining performance and reliability.

---

## Cost Breakdown

### Monthly Cost Estimate (100 requests/day)

| Service           | Monthly Cost     | Notes                                                 |
| ----------------- | ---------------- | ----------------------------------------------------- |
| **Bedrock**       | $0.15            | Nova Lite: 500 input + 150 output tokens/request      |
| **Lambda**        | $0.02            | 512 MB, 1.5s average execution                        |
| **DynamoDB**      | $1.00            | On-demand billing, 3 tables (cache + usage + backups) |
| **API Gateway**   | $0.01            | HTTP API, $0.035/million requests                     |
| **S3**            | $0.05            | Knowledge base storage + versioning                   |
| **CloudWatch**    | $0.50            | Logs ingestion and storage                            |
| **Data Transfer** | $0.10            | Minimal, mostly within AWS                            |
|                   |                  |                                                       |
| **TOTAL**         | **~$1.83/month** | Conservative estimate                                 |

### Scaling Costs (1,000 requests/day)

```
Bedrock: $1.50/month
Lambda:  $0.20/month
DynamoDB: $5.00/month
Other: $0.50/month

TOTAL: ~$7.20/month
```

---

## Bedrock Optimization

### 1. Use Amazon Nova Lite (Not Claude)

**Cost Comparison** (per million tokens):

| Model                 | Input Cost  | Output Cost | Notes               |
| --------------------- | ----------- | ----------- | ------------------- |
| **Nova Lite**         | $0.00000375 | $0.00032    | Best value          |
| **Claude 3.5 Sonnet** | $0.00008    | $0.00024    | 20x+ more expensive |
| **Claude 3 Opus**     | $0.000015   | $0.00075    | Most expensive      |

**Recommendation**: Use Nova Lite for constrained QA (like Alfred). Switch to Claude only if quality becomes a problem.

### 2. Optimize Token Usage

```python
# BEFORE: Verbose system prompt
system_prompt = """
You are Alfred. You answer questions about Loc Le.
You must only use the provided knowledge base.
You should be professional and helpful.
... (long explanation)
"""  # 250+ tokens

# AFTER: Concise system prompt
system_prompt = """
You answer questions about Loc Le using provided knowledge only.
Be professional and helpful. Decline out-of-scope questions.
"""  # 40 tokens
```

**Savings**: 210 tokens × $0.00000375 = $0.00079 per request

For 1,000 requests/day:

- Annual savings: 1,000 × 210 × 365 × $0.00000375 = **$288/year**

### 3. Control Maximum Output Tokens

```python
# BEFORE: 1024 max tokens (overkill)
max_tokens = 1024
avg_output = 800 tokens → $0.000256 per response

# AFTER: 512 max tokens (sufficient)
max_tokens = 512
avg_output = 400 tokens → $0.000128 per response
```

**Savings**: 50% reduction in token-based costs

### 4. Inference Profiles vs Foundation Models

**Inference Profiles** (recommended):

```
us.amazon.nova-lite-v1:0  ← Use this for cross-region, on-demand
```

- Cross-region availability
- On-demand throughput (pay per use)
- Better cost for variable traffic
- No provisioning overhead

**Foundation Models** (avoid):

```
anthropic.claude-3-5-sonnet-20241022-v2  ← Higher cost
```

- Requires provisioned throughput
- Higher base cost
- Better for consistent high-volume

### 5. Implement Caching Aggressively

```python
# Cache responses to avoid re-invoking LLM
cache_key = hashlib.md5(question.encode()).hexdigest()

cached = repository.get_cached_response(cache_key)
if cached:
    return cached  # Free! No Bedrock call

# Store in DynamoDB with 30-day TTL
response = llm_provider.invoke_model(...)
repository.cache_response(cache_key, response)
```

**Impact**:

- Common questions: 100% hit rate → 0 Bedrock calls
- Average case: 40-60% hit rate → 40-60% cost reduction

### Cost Per Type

| Scenario                 | Cost Per Request |
| ------------------------ | ---------------- |
| Cache hit                | $0.00            |
| First request (uncached) | $0.0002          |
| High cache rate (60%)    | $0.000080        |

---

## Lambda Optimization

### 1. Right-Size Memory

```python
# Memory affects both cost AND performance

# BEFORE: 128 MB (cheap but slow)
memory_mb = 128
price_per_gb_sec = 0.0000166667
duration_sec = 3.5  # Very slow due to CPU throttling
cost = (128/1024) * 3.5 * price_per_gb_sec = $0.000059

# AFTER: 512 MB (balanced)
memory_mb = 512
duration_sec = 1.5  # Faster CPU, better performance
cost = (512/1024) * 1.5 * price_per_gb_sec = $0.000081

# BETTER: 1024 MB (performance-focused)
memory_mb = 1024
duration_sec = 1.0
cost = (1024/1024) * 1.0 * price_per_gb_sec = $0.0000167
```

**Recommendation**: 512-1024 MB balances cost and performance

### 2. Connection Pooling (Don't Recreate Clients)

```python
# ANTI-PATTERN: Create new client on every invocation
def handler(event, context):
    import boto3
    bedrock = boto3.client('bedrock-runtime')  # Expensive!
    # ... use bedrock
```

```python
# PATTERN: Reuse client (Lambda keeps warm)
import boto3
bedrock = boto3.client('bedrock-runtime')  # Created once, reused

def handler(event, context):
    # ... use bedrock
    # Client reused on warm starts!
```

**Savings**: 50-100ms per invocation

### 3. Provisioned Concurrency (For Consistent Traffic)

```bash
# NO provisioned concurrency
# - First request = 3-5s cold start
# - Subsequent = 100-300ms
# - Variable cost, unpredictable latency

# YES provisioned concurrency
aws lambda put-provisioned-concurrent-executions \
  --function-name alfred-assistant-handler \
  --provisioned-concurrent-executions 5

# Costs:
# - 5 × $0.015/hour = $0.075/hour = $54/month
# - Always warm, predictable latency
```

**Recommendation**: Use only if SLA requires <500ms latency

### 4. Lambda Layer Benefits

Use Lambda layers for dependencies:

```bash
# Package dependencies in layer
mkdir python
pip install -r requirements.txt -t python/

zip -r lambda-layer.zip python/

aws lambda publish-layer-version \
  --layer-name alfred-deps \
  --zip-file fileb://lambda-layer.zip \
  --compatible-runtimes python3.12
```

**Benefits**:

- Share dependencies across multiple functions
- Smaller function package
- Faster deployment

---

## DynamoDB Optimization

### 1. Use On-Demand Billing

```bash
# On-demand (recommended for Alfred)
aws dynamodb update-table \
  --table-name alfred-runtime-cache \
  --billing-mode PAY_PER_REQUEST

# Cost: $1.25 per million reads + $6.25 per million writes
# Good for: Variable, unpredictable traffic
```

```bash
# Provisioned (for predictable traffic)
aws dynamodb update-table \
  --table-name alfred-runtime-cache \
  --billing-mode PROVISIONED \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5

# Cost: $0.09 per read unit + $0.47 per write unit per month
# Better for: Consistent high-volume traffic
```

### 2. TTL for Automatic Cleanup

```python
# Set TTL on cache to auto-delete old entries
# Saves storage costs

cache_ttl_seconds = 30 * 24 * 60 * 60  # 30 days

table.put_item(
    Item={
        'question_hash': question_hash,
        'response': response,
        'TTL': int(time.time()) + cache_ttl_seconds,
    }
)
```

### 3. Key Selection

```python
# EFFICIENT: Small primary keys
question_hash = hashlib.md5(question.encode()).hexdigest()  # 32 bytes

# INEFFICIENT: Large primary keys
question_text = question  # Potentially 1000+ bytes
```

### 4. Query Optimization

```python
# Index usage for efficient queries
# Create GSI (Global Secondary Index) if querying by non-primary key

aws dynamodb update-table \
  --table-name alfred-runtime-cache \
  --attribute-definitions AttributeName=user_id,AttributeType=S \
  --global-secondary-indexes '
    [{"IndexName": "user_id-index", "Keys": [{"name": "user_id"}]}]
  '

# Query by user_id (using GSI)
response = table.query(
    IndexName='user_id-index',
    KeyConditionExpression='user_id = :uid',
    ExpressionAttributeValues={':uid': user_id}
)
```

---

## API Gateway Optimization

### 1. Use HTTP API (Not REST API)

```
HTTP API:    $0.035 per million requests
REST API:    $3.50 per million requests
            (100x more expensive!)
```

**Alfred uses HTTP API** ✅ (Good choice)

### 2. Caching at API Gateway

```python
# Enable caching to reduce Lambda invocations
aws apigateway put-stage \
  --rest-api-id abc123 \
  --stage-name prod \
  --caching-enabled \
  --cache-cluster-enabled \
  --cache-cluster-size '0.5'

# Cache TTL: 300 seconds (5 minutes)
# Cache hit = no Lambda invocation needed
```

### 3. Regional Endpoints

```bash
# Regional (recommended)
https://api.us-east-1.locle.dev

# Edge-optimized (more expensive)
https://api.locle.dev  # Uses CloudFront globally
```

---

## S3 Optimization

### 1. Intelligent Tiering

```bash
# Auto-move frequent/infrequent data
aws s3api put-bucket-intelligent-tiering-configuration \
  --bucket alfred-knowledge-bucket-prod \
  --id auto-tiering \
  --intelligent-tiering-configuration '
    {
      "Id": "auto-tiering",
      "Filter": {"Prefix": ""},
      "Status": "Enabled",
      "Tierings": [
        {"Days": 90, "AccessTier": "ARCHIVE_ACCESS"},
        {"Days": 180, "AccessTier": "DEEP_ARCHIVE_ACCESS"}
      ]
    }
  '

# Immediate: $0.023 per GB
# Infrequent (90+ days): $0.0125 per GB
# Archive (180+ days): $0.004 per GB
```

### 2. Deletion Policy

```python
# Delete old versions to save storage
aws s3 put-bucket-lifecycle-configuration \
  --bucket alfred-knowledge-bucket-prod \
  --lifecycle-configuration '
    {
      "Rules": [
        {
          "Id": "delete-old-versions",
          "Status": "Enabled",
          "NoncurrentVersionExpiration": {"NoncurrentDays": 30}
        }
      ]
    }
  '
```

### 3. CloudFront (For Frequent Accesses)

If knowledge base is accessed frequently:

```bash
# Only enable if cache miss rate is high
aws cloudfront create-distribution \
  --origin-domain-name alfred-knowledge-bucket-prod.s3.amazonaws.com \
  --default-cache-behavior ...

# Cost: $0.085 per GB (first 10TB)
# Saves: S3 GET requests ($0.0004 per 1000 requests)
# Benefit: Faster access for end-users globally
```

---

## Overall Cost Reduction Strategy

### Phase 1: Immediate (0-1 week)

- [ ] Switch to Nova Lite (if not already)
- [ ] Reduce max tokens to 512
- [ ] Enable response caching (if not already)
- [ ] Set DynamoDB TTL to 14 days initially

**Expected savings**: 30-40%

### Phase 2: Medium-term (1-4 weeks)

- [ ] Right-size Lambda memory (benchmark first)
- [ ] Analyze cache hit rate and optimize
- [ ] Optimize system prompt (remove redundancy)
- [ ] Implement knowledge base versioning

**Expected savings**: 20-30% additional

### Phase 3: Long-term (1-3 months)

- [ ] Set up cost anomaly detection
- [ ] Implement detailed usage analytics
- [ ] Consider scaling model (if traffic increases)
- [ ] Regular optimization reviews

**Expected savings**: 10-20% additional

---

## Monitoring & Alerts

### AWS Budgets

```bash
# Alert when spending exceeds $5/month
aws budgets create-budget \
  --account-id 123456789 \
  --budget file://budget.json

# budget.json:
{
  "BudgetName": "alfred-monthly",
  "BudgetLimit": {"Amount": "5", "Unit": "USD"},
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST",
  "NotificationsWithSubscribers": [
    {
      "Notification": {
        "NotificationType": "FORECASTED",
        "ComparisonOperator": "GREATER_THAN",
        "Threshold": 100,  # 100% of budget
        "ThresholdType": "PERCENTAGE"
      },
      "Subscribers": [{"SubscriptionType": "EMAIL", "Address": "ops@locle.dev"}]
    }
  ]
}
```

### Cost Anomaly Detection

```bash
# Automatically detect unusual spending patterns
aws ce create-anomaly-monitor \
  --anomaly-monitor '{
    "MonitorName": "alfred-anomaly",
    "MonitorType": "DIMENSIONAL",
    "MonitorDimension": "SERVICE",
    "MonitorSpecification": "Service==\"Amazon Bedrock\""
  }'
```

### Analyze Costs

```bash
# Get daily costs
aws ce get-cost-and-usage \
  --time-period Start=2026-03-01,End=2026-03-31 \
  --granularity DAILY \
  --metrics "BlendedCost" \
  --group-by Type=DIMENSION,Key=SERVICE

# Get cost by operation
aws ce get-cost-and-usage \
  --time-period Start=2026-03-01,End=2026-03-31 \
  --granularity MONTHLY \
  --metrics "BlendedCost" \
  --group-by Type=DIMENSION,Key=OPERATION
```

---

## Cost Optimization Checklist

- [ ] Bedrock: Using Nova Lite?
- [ ] Bedrock: Max tokens ≤ 512?
- [ ] Bedrock: Response caching enabled?
- [ ] Lambda: Memory right-sized (512-1024 MB)?
- [ ] Lambda: Clients reused (no recreation)?
- [ ] DynamoDB: Using on-demand billing?
- [ ] DynamoDB: TTL enabled for auto-cleanup?
- [ ] S3: Unneeded versions deleted?
- [ ] API Gateway: Using HTTP API (not REST)?
- [ ] Monitoring: Cost alerts configured?

---

## Example Optimization

### Before Optimization

```
Scenario: 500 requests/day

Bedrock: 500 × 1.5 tokens × $0.00000375 = $0.003/day = $0.09/month
Lambda: 500 × 1.5s × 512MB/1024 = 375 GB-sec = $0.006/day = $0.18/month
DynamoDB: $3/month (provisioned, over-provisioned)
Other: $1/month

TOTAL: $4.27/month
Cache hit rate: 20%
```

### After Optimization

```
Scenario: 500 requests/day

Bedrock: With 60% cache hit rate:
  500 × 0.4 × 0.8 tokens × $0.00000375 = $0.0006/day = $0.018/month
Lambda: 500 × 1.0s × 512MB/1024 = 250 GB-sec = $0.004/day = $0.12/month
DynamoDB: $1.50/month (on-demand, right-sized)
Other: $0.50/month

TOTAL: $2.14/month (50% reduction!)
Cache hit rate: 60%
```

---

## References

- [AWS Pricing Calculator](https://calculator.aws/)
- [AWS Cost Optimization Best Practices](https://aws.amazon.com/architecture/cost-optimization-pillar/)
- [Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/)
- [Lambda Pricing](https://aws.amazon.com/lambda/pricing/)

---

**Track costs closely and optimize continuously. Every service has cost-saving opportunities.**
