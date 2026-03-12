# Decision Log

**Purpose**: Record major architectural and technology decisions.  
**Audience**: All engineers  
**Updated**: March 2026  
**Format**: ADR (Architecture Decision Record) style

---

## ADR-001: Serverless Lambda Architecture

**Date**: March 2026  
**Status**: ACCEPTED  
**Context**: Need to deploy AI assistant with minimal operational overhead

**Decision**: Use AWS Lambda with API Gateway instead of containers/EC2

**Rationale**:

- ✅ Automatic scaling for variable load
- ✅ Pay-per-request pricing (cheap for low traffic)
- ✅ No server management overhead
- ✅ Integrated with other AWS services (S3, DynamoDB, Bedrock)

**Alternatives Considered**:

- ❌ EC2 with manual scaling: Too much ops overhead
- ❌ ECS Fargate: Overkill for this workload
- ❌ On-premise: No Bedrock integration

**Consequences**:

- ✅ Cold start latency (3-5s first invocation)
- ✅ 30s execution timeout limit
- ✅ Simplified deployment
- ✅ Cost-effective for current traffic

---

## ADR-002: Nova Lite Model Selection

**Date**: March 2026  
**Status**: ACCEPTED  
**Context**: Need reliable, cost-effective LLM for guardrail-heavy assistant

**Decision**: Use AWS Bedrock with Nova Lite (not Claude, GPT-4)

**Rationale**:

- ✅ 10x cheaper than Claude 3
- ✅ Fast token processing
- ✅ Suitable for deterministic, guardrailed responses
- ✅ Native AWS integration
- ✅ Model-agnostic architecture allows future swaps

**Alternatives Considered**:

- ❌ Claude 3: Too expensive ($0.80 input, $2.40 output per 1M tokens)
- ❌ GPT-4: Requires external API, higher latency
- ❌ Llama 2 (self-hosted): Too much ops overhead

**Consequences**:

- ✅ Lower quality for open-ended questions (acceptable for this use case)
- ✅ Requires careful prompt engineering
- ✅ Room to upgrade if needed

**Review Schedule**: Q3 2026 (evaluate performance vs. cost)

---

## ADR-003: In-Memory Caching with DynamoDB TTL

**Date**: March 2026  
**Status**: ACCEPTED  
**Context**: Need to reduce Bedrock costs for repeated questions

**Decision**: Implement two-level caching:

1. In-memory cache (Lambda execution)
2. DynamoDB TTL for distributed cache

**Rationale**:

- ✅ In-memory: Ultra-fast, no network latency
- ✅ DynamoDB TTL: Persistent, auto-cleanup, cheap (<$1/month on-demand)
- ✅ 40-60% cache hit rate expected
- ✅ 30-50% reduction in Bedrock costs

**Alternatives Considered**:

- ❌ Redis: Adds cost, complexity, operational overhead
- ❌ ElastiCache: Minimum cost ~$15/month, overkill for this scale
- ❌ S3 caching: Too slow for this workload

**Consequences**:

- ✅ When knowledge base updates, cached responses become stale
- ✅ In-memory cache lost on Lambda container recycle
- ✅ Significant cost reduction

**Mitigation**: 1-hour TTL balances freshness and cost

---

## ADR-004: Rate Limiting by IP Address

**Date**: March 2026  
**Status**: ACCEPTED  
**Context**: Need to prevent abuse and control costs

**Decision**: IP-based rate limiting (50 requests/day per IP)

**Rationale**:

- ✅ Simple to implement (DynamoDB ID = IP)
- ✅ No authentication required
- ✅ Prevents obvious abuse
- ✅ Works with public URLs

**Alternatives Considered**:

- ❌ User-based (requires login): Friction for new users
- ❌ API key-based: Complex key management
- ❌ No rate limiting: Cost explosion risk

**Consequences**:

- ✅ Mobile users behind shared NAT may share limit
- ✅ Can be bypassed by VPN/proxy
- ✅ Simple, effective for this use case

**Future Enhancement**: User-based rate limiting (ADR-TBD)

---

## ADR-005: Infrastructure-as-Code with Terraform

**Date**: March 2026  
**Status**: ACCEPTED  
**Context**: Need reproducible, versionable infrastructure

**Decision**: Terraform for all AWS resources

**Rationale**:

- ✅ Version control for infrastructure
- ✅ Repeatable deployments
- ✅ Multi-environment support
- ✅ State management with S3 + DynamoDB

**Alternatives Considered**:

- ❌ CloudFormation: AWS-only, less readable
- ❌ Pulumi: Good but less adoption
- ❌ Manual AWS Console: No version control

**Consequences**:

- ✅ Terraform state must be backed up
- ✅ Requires Terraform knowledge
- ✅ State locks prevent concurrent deployments

---

## ADR-006: GitHub as Version Control (Implied)

**Date**: March 2026  
**Status**: ACCEPTED  
**Context**: Need collaborative, auditable code history

**Decision**: GitHub for all code and infrastructure

**Review Cycle**: Quarterly (ADR reviews)

---

**Last Updated**: March 2026  
**Total ADRs**: 6  
**Status**: All ACCEPTED
