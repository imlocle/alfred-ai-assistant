# Cost Optimization Guide

**Purpose**: Tactical recommendations for reducing operational costs.  
**Audience**: Finance, engineering, product  
**Updated**: March 2026

---

## Quick Wins (Implement Immediately)

### 1. Enable CloudWatch Log Filtering

**Current**: All logs ingested (3 MB/month)  
**Optimization**: Sample 10% of logs
**Cost Savings**: 90% of CloudWatch ingestion (~$0.72/month)

```bash
# Filter non-ERROR logs
aws logs put-subscription-filter \
  --log-group-name /aws/lambda/alfred-handler-prod \
  --filter-pattern '[ERROR]'
```

### 2. Reduce System Prompt Size

**Current**: ~500 tokens/request  
**Optimization**: Compress to 300 tokens  
**Cost Savings**: 30% of Bedrock costs (~$1.65/month)

### 3. Increase Cache TTL

**Current**: 1 hour  
**Optimization**: 4 hours  
**Cost Savings**: 50% of Bedrock costs (~$2.75/month with cache)

### 4. Reduce Max Output Tokens

**Current**: 200 tokens  
**Optimization**: 150 tokens (if response quality acceptable)  
**Cost Savings**: 15% of Bedrock outputs (~$0.33/month)

---

## Medium-Term Optimizations (Q2-Q3 2026)

- DynamoDB DAX for caching (saves ~20-30%)
- Lambda memory optimization (if acceptable latency)
- Reserved capacity for Bedrock (20-30% discount at scale)

---

See [COSTS_ANALYSIS.md](COSTS_ANALYSIS.md) for full cost breakdown.

**Last Updated**: March 2026
