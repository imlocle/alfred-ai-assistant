# Architecture Overview

## Project Purpose

Alfred is a production-style AI assistant platform built on AWS that demonstrates real-world GenAI system design, infrastructure-as-code, and strict LLM guardrails. It is intentionally constrained to answer questions only about Loc Le using a controlled knowledge base, enforced refusal behavior, rate limiting, and cost-aware inference settings.

## High-Level Architecture

Alfred follows a serverless, event-driven architecture on AWS with a layered backend design:

```
Client (React/Vite)
    ↓
API Gateway (HTTP API)
    ↓
Lambda Function (Python)
    ↓
Handler → Controller → Service → Repository → Providers
    ↓
AWS Services (Bedrock, DynamoDB, S3)
```

## Project Structure

```
src/
├── handlers/
│   └── assistant_handler.py          # Lambda entry point
├── controllers/
│   └── query_controller.py           # Request validation & routing
├── services/
│   └── assistant_service.py          # Business logic orchestration
├── repositories/
│   └── conversation_repository.py    # Data access, caching, AI calls
├── providers/
│   ├── llm_provider.py               # Bedrock client wrapper
│   ├── storage_provider.py           # DynamoDB client wrapper
│   └── knowledge_provider.py         # S3 client wrapper
├── agents/
│   └── __init__.py                   # Reserved for future agent logic
└── shared/
    ├── config.py                     # Constants and configuration
    ├── exceptions.py                 # Custom exception classes
    ├── validators.py                 # Input sanitization
    ├── logging.py                    # Structured JSON logging
    └── responses.py                  # HTTP response formatting
```

## Core Components

### Frontend Layer

- Technology: React, TypeScript, Vite
- Hosting: GitHub Pages
- Responsibilities: Chat UI widget, markdown rendering, API communication

### API Layer

- Service: AWS API Gateway (HTTP API)
- Endpoint: `POST /ask`
- Features: CORS configuration, Lambda integration, auto-deployment

### Compute Layer

- Service: AWS Lambda
- Runtime: Python 3.13
- Timeout: 30 seconds
- Architecture Pattern: Layered design
  - Handler (`assistant_handler.py`): Entry point, error handling, response formatting
  - Controller (`query_controller.py`): Request validation, CORS checking, input parsing
  - Service (`assistant_service.py`): Business logic orchestration, usage enforcement
  - Repository (`conversation_repository.py`): Data access, caching, external service integration

### AI/ML Layer

- Service: AWS Bedrock
- Model: Amazon Nova Lite (via cross-region inference profile)
- Model ID: `us.amazon.nova-lite-v1:0`
- Configuration: Max tokens 200, Temperature 0.2, Top P 0.9, Top K 1
- Features: System prompt injection, knowledge base context injection

### Data Layer

#### DynamoDB

- Table: `alfred-usage-tracker-table`
- Purpose: Rate limiting and usage tracking
- Schema: Partition Key `pk` (user IP), Sort Key `sk` (date YYYY-MM-DD), Attributes `count`, `expires_at` (TTL)
- Billing: Pay-per-request
- Point-in-time recovery enabled

#### S3

- Bucket: `alfred-knowledge-bucket`
- Purpose: Store structured knowledge base (`knowledge_base.json`)
- Access: Read-only from Lambda

## Request Flow

1. User submits question through chat widget
2. Frontend sends POST request to API Gateway `/ask` endpoint
3. API Gateway validates CORS and routes to Lambda
4. `AssistantHandler` receives event and delegates to `QueryController`
5. `QueryController` validates origin, extracts user ID (IP), sanitizes input
6. `AssistantService` checks usage limits via `ConversationRepository`
7. `ConversationRepository` checks cache, constructs system prompt with knowledge base from S3
8. `LLMProvider` invokes Bedrock model with prompt and user question
9. Response cached and flows back through service → controller → handler
10. `StorageProvider` updates usage counter in DynamoDB
11. Lambda returns JSON response to API Gateway

## Infrastructure as Code

All AWS resources are managed via Terraform with a modular structure:

```
terraform/
├── main.tf                       # Root module orchestration
├── variables.tf                  # Input variables
├── outputs.tf                    # Outputs
├── backend.tf                    # Remote state config
└── modules/
    ├── api/                      # API Gateway
    ├── dynamodb/                 # Usage tracking table
    └── lambda/
        └── assistant/            # Lambda function, layer, IAM, alarms
```

### Deployment

```bash
make clean && make deploy ENV=dev
```

## Key Design Decisions

### Serverless Architecture

Cost-effective for variable traffic, no server management, automatic scaling. Trade-off: cold start latency (mitigated with 30s timeout).

### Layered Backend Pattern

Separation of concerns, testability, maintainability. Handler (I/O) → Controller (validation) → Service (orchestration) → Repository (data access).

### Provider Abstraction

AWS services wrapped in provider classes (`LLMProvider`, `StorageProvider`, `KnowledgeProvider`) to decouple business logic from infrastructure. Enables swapping providers without changing core logic.

### Nova Model Selection

Extremely low operating cost, suitable for constrained assistants. Model ID is configurable via environment variable.

### IP-Based Rate Limiting

Simple, no authentication required, prevents abuse. DynamoDB counter with TTL-based daily reset (50 requests/day).

### Response Caching

In-memory cache with configurable TTL (1 hour default). MD5-based cache keys from normalized questions. Estimated 30-50% cost reduction for repeated questions.

### Knowledge Base Injection

S3 JSON file loaded at runtime and injected into system context. Easy to update without code changes.

## Security & Guardrails

- CORS Protection: Allowed origins `localhost:5173`, `imlocle.com`, `imlocle.github.io`
- Rate Limiting: 50 requests/day per IP, enforced before model invocation
- Input Sanitization: Control character removal, whitespace normalization, length limits (2000 chars)
- Prompt Constraints: Strict system prompt limits scope to Loc Le only
- IAM Least Privilege: S3 read-only, Bedrock invoke on all foundation models and inference profiles (cross-region), DynamoDB Get/Update/Put only

## Observability

- Structured JSON Logging: Custom formatter with timestamp, level, module, request_id, user_id
- Request ID Tracking: End-to-end correlation from API Gateway through all layers
- CloudWatch Alarms: Lambda errors (>10/5min), duration (>10s avg), throttles (>5/5min)
- CloudWatch Log Retention: 30 days

## Cost Optimization

- Nova model: Lowest-cost Bedrock option
- Token limits: Max 200 tokens per response
- Response caching: 30-50% reduction in Bedrock calls
- Rate limiting: Prevents runaway costs
- Pay-per-request: No idle costs for DynamoDB or Lambda
- Log retention: 30 days prevents indefinite storage costs
