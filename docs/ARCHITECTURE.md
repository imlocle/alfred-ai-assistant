# Architecture Overview

This document provides a comprehensive technical overview of Alfred's system design, data flows, and component responsibilities.

## System Architecture

### High-Level Request Flow

```
Client Browser / Frontend
    ↓
API Gateway (HTTP API)
    ↓
Lambda Function (AssistantHandler)
    ↓
QueryController (Validation, CORS)
    ↓
AssistantService (Orchestration)
    ├─ ConversationRepository (Usage tracking, caching)
    ├─ AssistantAgent (AI logic)
    │   ├─ LLMProvider (Bedrock → Claude)
    │   └─ KnowledgeProvider (S3)
    └─ StorageProvider (DynamoDB)
    ↓
Response → Client
```

## Component Architecture

### 1. **Handler Layer** (`src/handlers/assistant_handler.py`)

**Purpose**: Lambda entry point and error handling

**Responsibilities**:

- Receives HTTP events from API Gateway
- Delegates to QueryController for processing
- Catches and transforms exceptions into HTTP responses
- Returns standardized success/error responses
- Logs all requests with correlation IDs

**Key Features**:

- Exception mapping (InvalidQuestionError → 400, RateLimitError → 429, etc.)
- CORS error handling with custom headers
- Request correlation tracking
- Structured logging

---

### 2. **Controller Layer** (`src/controllers/query_controller.py`)

**Purpose**: Request validation and routing

**Responsibilities**:

- Validates incoming HTTP requests
- Extracts query parameters (question, userId, currentDate, origin)
- Implements CORS validation
- Enforces input constraints
- Routes validated requests to AssistantService

**Key Features**:

- CORS origin whitelisting
- Input sanitization and validation
- Request parameter extraction
- Error propagation with context

---

### 3. **Service Layer** (`src/services/assistant_service.py`)

**Purpose**: Business logic orchestration

**Responsibilities**:

- Coordinates between Agent, Repository, and Providers
- Enforces rate limiting checks
- Manages response caching
- Tracks usage per user
- Orchestrates the request lifecycle

**Key Features**:

- Usage tracking per user per day
- Response caching for performance
- Rate limit enforcement (e.g., 3 requests/day)
- Atomic database operations

**Request Lifecycle**:

1. Check rate limits (via ConversationRepository)
2. Check cache for existing response
3. If cached, return immediately
4. Otherwise, invoke AssistantAgent
5. Cache the response
6. Update usage metrics
7. Return response

---

### 4. **Agent Layer** (`src/agents/assistant_agent.py`)

**Purpose**: AI logic, prompt construction, and routing

**Responsibilities**:

- Loads and maintains knowledge base in memory
- Routes scheduling requests separately
- Constructs system prompts dynamically
- Invokes LLM via Bedrock
- Returns AI-generated responses

**Key Features**:

- **Scheduling Request Detection**: Identifies scheduling keywords and routes to Calendly
- **System Prompt Injection**: Builds safety guardrails and knowledge context
- **Knowledge Augmentation**: Injects knowledge base into each request
- **Error Resilience**: Gracefully handles knowledge base loading failures

**Request Routing**:

```
Question
├─ Is it a scheduling request? (contains: schedule, book, meeting, call, appointment)
│  └─ Return Calendly link
└─ Not a scheduling request
   ├─ Build system context (prompt + knowledge)
   ├─ Invoke Bedrock Claude model
   └─ Return AI response
```

---

### 5. **Provider Layer** (`src/providers/`)

#### **LLMProvider** (`llm_provider.py`)

- **Responsibility**: Interfaces with AWS Bedrock
- **Model**: Amazon Nova Lite via inference profiles for cost efficiency
- **Features**:
  - Cross-region inference profiles (`us.amazon.nova-lite-v1:0`)
  - Automatic error handling and logging
  - Token streaming support (optional)
  - Cost-aware configuration

#### **KnowledgeProvider** (`knowledge_provider.py`)

- **Responsibility**: Loads knowledge base from S3
- **Storage**: S3 bucket containing `knowledge_base.json`
- **Features**:
  - Caches knowledge in memory during Lambda execution
  - TTL-based refresh (respects Lambda warm starts)
  - Fallback to empty knowledge if S3 unavailable

#### **StorageProvider** (`storage_provider.py`)

- **Responsibility**: Manages DynamoDB operations
- **Operations**:
  - Conversation caching (responses keyed by question hash)
  - Usage tracking (daily per-user request counts)
  - TTL on cache entries (configurable, default: 30 days)

---

### 6. **Repository Layer** (`src/repositories/conversation_repository.py`)

**Purpose**: Data access abstraction for conversations and usage tracking

**Responsibilities**:

- **Usage Tracking**: Records daily request counts per user
- **Rate Limiting**: Enforces daily request quotas
- **Response Caching**: Stores and retrieves cached responses
- **TTL Management**: Handles cache expiration

**Operations**:

```python
check_usage(user_id: str, current_date: str)
  # Verify user hasn't exceeded daily limit
  # Raises RateLimitError if quota exhausted

update_usage(user_id: str, current_date: str)
  # Increment daily request counter for user

get_cached_response(question: str) -> Optional[str]
  # Retrieve cached response or None

cache_response(question: str, response: str)
  # Store response with TTL
```

---

### 7. **Shared Utilities** (`src/shared/`)

#### **config.py**

- System prompts and guardrails
- Model configurations
- Feature flags and feature toggles
- Service URLs (Calendly, etc.)

#### **exceptions.py**

- Custom exception hierarchy
- Domain-specific errors:
  - `InvalidQuestionError`: Malformed or empty questions
  - `RateLimitError`: Daily quota exceeded
  - `CORSOriginError`: Unauthorized origin
  - `ChatbotProcessingError`: General processing failures

#### **logging.py**

- Structured logging setup
- CloudWatch integration
- Request correlation tracking
- Performance monitoring hooks

#### **responses.py**

- HTTP response builders
- CORS header management
- Error response formatting

#### **validators.py**

- Input validation rules
- Question cleanliness checks
- Origin validation against whitelist

---

## Data Models

### DynamoDB Tables

#### **Conversation Cache Table**

```
PK: question_hash (String)
SK: N/A
Attributes:
  - response (String): Cached AI response
  - timestamp (Number): Unix timestamp
  - TTL (Number): Expiration time (30 days)
```

#### **Usage Tracker Table**

```
PK: user_id (String)
SK: date (String, format: YYYY-MM-DD)
Attributes:
  - request_count (Number): Daily requests
  - TTL (Number): Expiration time (90 days)
```

### Knowledge Base Schema (S3)

```json
{
  "version": "2.3.0",
  "metadata": {
    "created_date": "2025-09-09",
    "last_updated": "2026-02-03",
    "source": "Personal profile data + live website",
    "description": "Loc Le's profile and professional background"
  },
  "personal_info": {
    "full_name": "Loc Le",
    "role": "Senior Cloud Software Engineer",
    "experience": "6+ years",
    "...": "Other attributes"
  }
}
```

---

## AWS Infrastructure

### Compute

- **AWS Lambda**: Serverless function running Python 3.12+
- **Function**: `{project_name}-assistant-handler`
- **Memory**: 512 MB (configurable)
- **Timeout**: 60 seconds (configurable)

### Networking

- **API Gateway (HTTP API)**: REST endpoint for client requests
- **Route**: `POST /chat`
- **CORS**: Configured for whitelisted origins only

### Storage

- **S3 Bucket**: `{project_name}-knowledge-bucket`
  - Stores `knowledge_base.json`
  - Versioning enabled for rollback capability
- **DynamoDB Tables**:
  - Conversation cache (provisioned with autoscaling)
  - Usage tracker (provisioned with autoscaling)

### AI/ML

- **AWS Bedrock**: Managed LLM inference service
- **Model**: Amazon Nova Lite (cross-region inference profile)
- **Inference Profile**: `us.amazon.nova-lite-v1:0`
- **Cost Model**: On-demand pricing

### Monitoring & Logging

- **CloudWatch**: All Lambda logs and metrics
- **X-Ray** (optional): Distributed tracing

---

## Guardrails & Safety

### 1. **System Prompt Injection**

- Enforces strict scope: "Only answer questions about Loc Le"
- Refusal templates for out-of-scope questions
- Instruction: "Do not provide information outside your knowledge base"

### 2. **Rate Limiting**

- Daily per-user quota (configurable, default: 3 requests/day)
- Returns 429 (Too Many Requests) when exceeded
- Usage tracked in DynamoDB

### 3. **CORS Protection**

- Origin whitelist validation
- Rejects requests from unauthorized domains
- Custom error headers for debugging

### 4. **Input Validation**

- Question must not be empty
- Minimum length: 3 characters
- Sanitizes special characters and potential injection attempts

### 5. **Knowledge Base Isolation**

- Only knowledge about Loc Le is injected into prompts
- LLM cannot access external data, only provided knowledge
- Knowledge base updates require redeployment or S3 refresh

---

## Performance Characteristics

### Latency

- **Warm Start**: 100-300ms (LLM invoke: 800-2000ms)
- **Cold Start**: 2-5s (first Lambda invocation, includes dependencies load)
- **Cache Hit**: <50ms (instant response return)

### Throughput

- **Concurrent Executions**: Limited by Lambda concurrency quota (account-level)
- **DynamoDB**: Autoscaled read/write capacity
- **API Gateway**: Default quota of 10,000 requests/second

### Storage

- **Knowledge Base**: ~5-50 MB (typical)
- **Lambda Package**: ~150 MB (with dependencies)
- **Cache Size**: Grows with unique questions (each response ~1-5 KB)

---

## Scalability

### Horizontal Scaling

- Lambda automatically scales to handle concurrent requests
- DynamoDB autoscaling manages traffic spikes
- API Gateway handles routing without manual intervention

### Vertical Scaling

- Lambda memory adjustable (128 MB - 10,240 MB)
- Higher memory = more CPU and faster LLM inference
- Recommended: 512-1024 MB

### Limitations & Bottlenecks

- **Bedrock Quota**: May have rate limits per inference profile
- **DynamoDB**: Can hit hot partition for heavily used knowledge
- **S3**: Knowledge base refresh latency (typical: <100ms)

---

## Deployment Architecture

### Infrastructure-as-Code (Terraform)

```
terraform/
├── main.tf              # Root configuration
├── variables.tf         # Variable definitions
├── outputs.tf          # Output values
├── backend.tf          # State backend (S3)
└── modules/
    ├── api/            # API Gateway setup
    ├── lambda/         # Lambda function
    └── dynamodb/       # DynamoDB tables
```

### Deployment Pipeline

1. Code committed to repository
2. Terraform plan validates changes
3. Infrastructure provisioned (Terraform apply)
4. Lambda code packaged and deployed
5. Rollback available via S3 state management

---

## Error Handling & Recovery

### Exception Hierarchy

```
Exception
├── ChatbotProcessingError (5xx)
│   ├── InvalidQuestionError (400)
│   └── [Generic processing failures]
├── RateLimitError (429)
├── CORSOriginError (403)
└── [AWS service exceptions]
```

### Retry Strategy

- **Client-side**: Retry with exponential backoff (1s, 2s, 4s)
- **Lambda**: No automatic retries for 4xx errors, automatic retry for 5xx
- **Bedrock**: Automatic retry within Lambda with exponential backoff

### Circuit Breaker

- Knowledge base loading failure: Falls back to empty knowledge, returns degraded response
- Bedrock unavailable: Returns error response with 503 (Service Unavailable)

---

## Security Model

### IAM Permissions

- Lambda execution role has minimal permissions (least privilege)
- S3 permissions limited to knowledge bucket and specific keys
- DynamoDB permissions limited to specific tables
- Bedrock invoke permissions for inference profiles only

### Data Privacy

- No persistent user data beyond daily usage count
- Responses cached but can be cleared
- Knowledge base is read-only (immutable during runtime)

### Network

- All communication over HTTPS/TLS
- API Gateway enforces TLS 1.2+
- No data traverses public internet (AWS managed service)

---

## Monitoring & Observability

### Metrics

- **Lambda**: Invocations, duration, errors, throttles
- **DynamoDB**: Read/write capacity consumed, latency, throttles
- **API Gateway**: Request count, latency, 4xx/5xx errors
- **Bedrock**: Model invocations, token usage, latency

### Alarms

- Lambda error rate > 5% → PagerDuty alert
- Rate limit violations spike
- DynamoDB throttling detected
- Knowledge base unavailable

### Logging

- All requests logged with correlation IDs
- Full error stack traces in CloudWatch
- Performance metrics (latency, token usage)
- Audit trail of user requests (anonymized)

---

## Future Enhancements

1. **Multi-Model Support**: Support multiple LLMs (Claude 3.5, GPT-4, etc.)
2. **Conversation History**: Store multi-turn conversations, not just single Q&A
3. **Fine-tuning**: Domain-specific model fine-tuning for better responses
4. **Semantic Search**: Use embeddings to find relevant knowledge more accurately
5. **Custom Tools**: Integration with external APIs (email, calendar, Slack)
6. **A/B Testing**: Compare different prompts and model configurations
7. **Feedback Loop**: User feedback to improve guardrails and responses

---

## References

- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [AWS DynamoDB Documentation](https://docs.aws.amazon.com/dynamodb/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
