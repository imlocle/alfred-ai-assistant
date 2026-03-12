# Alfred AI Assistant - Comprehensive Technical Summary

**Project**: Alfred AI Assistant Platform  
**Purpose**: Production-style AI assistant demonstrating GenAI system design, infrastructure-as-code, and LLM guardrails  
**Status**: Complete - PHASE_1_COMPLETE  
**Last Updated**: March 12, 2026

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Core Components](#core-components)
4. [Data Flow](#data-flow)
5. [Design Patterns](#design-patterns)
6. [Configuration & Environment](#configuration--environment)
7. [Dependencies](#dependencies)
8. [Error Handling](#error-handling)
9. [Safety & Guardrails](#safety--guardrails)
10. [Testing & Quality](#testing--quality)
11. [Infrastructure (Terraform)](#infrastructure-terraform)
12. [Deployment & Operations](#deployment--operations)

---

## Project Overview

Alfred is a **constrained, production-ready AI assistant** built on AWS that serves as a personal assistant for answering questions about a specific subject (Loc Le) using a controlled knowledge base.

### Key Characteristics

- **Scope-Limited**: Only answers questions about a specific subject
- **Knowledge-Based**: Uses injected knowledge base instead of general training
- **Cost-Aware**: Optimized for low operational costs with model selection and caching
- **Safe**: Multiple layers of guardrails and rate limiting
- **Infrastructure-as-Code**: 100% Terraform-managed AWS resources
- **Production-Ready**: Proper error handling, structured logging, monitoring-ready

### Problem Statement

Most AI demos stop at "it works." Alfred demonstrates:

- Production-ready GenAI architecture with proper layering
- Scope control and refusal mechanisms for LLMs
- Cost-optimization strategies for AI systems
- Multi-user safety via rate limiting and usage tracking
- Real-world system design patterns

---

## Architecture

### High-Level Request Flow

```
┌─────────────────────┐
│  Client Browser     │
│  (Frontend App)     │
└──────────┬──────────┘
           │ HTTP POST
           ↓
┌─────────────────────────────────┐
│     AWS API Gateway             │
│     (HTTP API - Regional)       │
└──────────┬──────────────────────┘
           │
           ↓
┌──────────────────────────────────────────┐
│   AWS Lambda: AssistantHandler           │
│   (Request: event, context)              │
└──────────┬───────────────────────────────┘
           │
           ↓
┌──────────────────────────────────────────┐
│  QueryController                         │
│  - Validate origin (CORS)                │
│  - Extract user_id, date, question       │
│  - Sanitize input                        │
│  - Route to service                      │
└──────────┬───────────────────────────────┘
           │
           ↓
┌──────────────────────────────────────────┐
│  AssistantService (Orchestration)        │
│  1. Check usage limits                   │
│  2. Check response cache                 │
│  3. If miss: invoke agent                │
│  4. Cache result                         │
│  5. Update usage metrics                 │
└──────────┬───────────────────────────────┘
           │
      ┌────┴─────────────────────┬───────────────────┐
      │                          │                   │
      ↓                          ↓                   ↓
┌──────────────────────  ┌──────────────────  ┌──────────────────
│ AssistantAgent         │ ConversationRepo   │ StorageProvider
│ - Route scheduling req │ - Get cache        │ - DynamoDB
│ - Build system context │ - Update usage     │ - Usage tracking
│ - Inject knowledge     │ - Check limits     │
│ - Invoke LLM           │                    │
└──────────┬───────────────────────────────────────────┘
           │
      ┌────┴─────────────────┬────────────────────┐
      │                      │                    │
      ↓                      ↓                    ↓
┌─────────────────┐  ┌─────────────────┐  ┌──────────────────
│  LLMProvider    │  │ KnowledgeProvider│  │ StorageProvider
│  - Bedrock API  │  │ - S3 bucket      │  │ - DynamoDB tables
│  - Nova Lite    │  │ - knowledge.json │  │
└─────────────────┘  └──────────────────┘  └──────────────────
           │
           ↓
┌──────────────────────────────────────────┐
│        Response                          │
│  HTTP 200: {"reply": "..."}              │
│  HTTP 429: Rate limited                  │
│  HTTP 403: CORS origin denied            │
│  HTTP 400: Invalid question              │
│  HTTP 500: Internal error                │
└──────────────────────────────────────────┘
```

### Project Structure

```
alfred-ai-assistant/
├── src/                           # Application source code
│   ├── handlers/
│   │   └── assistant_handler.py   # Lambda entry point (70 lines)
│   │
│   ├── controllers/
│   │   └── query_controller.py    # Request validation & routing (50 lines)
│   │
│   ├── services/
│   │   └── assistant_service.py   # Business logic orchestration (20 lines)
│   │
│   ├── agents/
│   │   └── assistant_agent.py     # AI logic: prompts, LLM calls (45 lines)
│   │
│   ├── repositories/
│   │   └── conversation_repository.py  # Caching & usage tracking (90 lines)
│   │
│   ├── providers/
│   │   ├── llm_provider.py        # Bedrock wrapper (100 lines)
│   │   ├── knowledge_provider.py  # S3 wrapper (25 lines)
│   │   └── storage_provider.py    # DynamoDB wrapper (75 lines)
│   │
│   └── shared/
│       ├── config.py              # Constants and configuration (40 lines)
│       ├── exceptions.py          # Custom exception classes (40 lines)
│       ├── validators.py          # Input sanitization (30 lines)
│       ├── logging.py             # Structured JSON logging (60 lines)
│       ├── responses.py           # HTTP response formatting (20 lines)
│       └── __init__.py
│
├── tests/                         # Test suite
│   ├── conftest.py               # Shared pytest fixtures
│   ├── unit/
│   │   ├── test_handlers.py
│   │   ├── test_controllers.py
│   │   ├── test_services.py
│   │   ├── test_agents.py
│   │   ├── test_repositories.py
│   │   ├── test_validators.py
│   │   ├── test_exceptions.py
│   │   └── utils.py
│   └── integration/
│
├── terraform/                     # Infrastructure-as-Code
│   ├── main.tf                   # Main resource definitions
│   ├── variables.tf              # Input variables
│   ├── outputs.tf                # Output values
│   ├── backend.tf                # Backend configuration
│   └── modules/
│       ├── api/                  # API Gateway module
│       ├── lambda/               # Lambda function module
│       └── dynamodb/             # DynamoDB module
│
├── lambda_layer/                 # Lambda Layer (dependencies)
│   └── python/
│       ├── boto3/
│       ├── botocore/
│       ├── mypy_boto3_*          # Type stubs
│       └── [other AWS dependencies]
│
├── docs/                         # Documentation
│   ├── ARCHITECTURE.md           # Detailed architecture
│   ├── API.md                    # API specification
│   ├── CONFIGURATION.md          # Configuration guide
│   ├── DEPLOYMENT.md             # Deployment procedures
│   ├── DEVELOPMENT.md            # Development guide
│   ├── GUARDRAILS.md             # Safety mechanisms
│   ├── PRODUCTION-READINESS.md   # Readiness assessment
│   ├── COST-OPTIMIZATION.md      # Cost optimization strategies
│   ├── TROUBLESHOOTING.md        # Troubleshooting guide
│   └── TESTING.md                # Testing documentation
│
├── knowledge_base.json           # Content knowledge base
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development dependencies
├── pytest.ini                    # Pytest configuration
├── makefile                      # Build and deployment automation
├── run_tests.sh                  # Test runner script
├── PHASE_1_COMPLETE.md           # Phase 1 completion status
├── TESTING_SUMMARY.md            # Testing summary
└── README.md                     # Project overview
```

---

## Core Components

### 1. Handler Layer: AssistantHandler

**File**: `src/handlers/assistant_handler.py` (72 lines)

**Purpose**: Lambda entry point - receives AWS API Gateway events and returns HTTP responses

**Key Responsibilities**:

- Extract request ID for correlation logging
- Delegate to QueryController for business logic
- Catch all exceptions and transform into HTTP responses
- Return standardized JSON responses

**Exception Mapping**:
| Exception | HTTP Status | Message |
|-----------|-------------|---------|
| `InvalidQuestionError` | 400 | "Invalid question. Please ask another." |
| `CORSOriginError` | 403 | "You are chatting from a different place..." |
| `RateLimitError` | 429 | "Reached limit for today. Come back tomorrow." |
| Generic `Exception` | 500 | "Currently unavailable. Please come back soon." |

**Pseudo-Code Flow**:

```python
@lambda_handler(event, context)
  request_id = event["requestContext"]["requestId"]
  try:
    result = controller.handle_event(event, request_id)
    return success_response(body={"reply": result})
  except SpecificException as e:
    return error_response(message=formatted_msg, status_code=e.http_status)
  except Exception as e:
    return error_response(message=generic_msg, status_code=500)
```

---

### 2. Controller Layer: QueryController

**File**: `src/controllers/query_controller.py` (52 lines)

**Purpose**: Request validation and routing - single entry point for all business logic

**Key Responsibilities**:

- Validate CORS origin against whitelist
- Extract user ID from `x-forwarded-for` header
- Parse current date from Lambda event timestamp
- Sanitize and validate question input
- Route to AssistantService

**CORS Validation**:

```python
ALLOWED_ORIGINS = [
    "https://imlocle.com",      # Production domain
    "http://localhost:5173"      # Local development
]
```

**Input Pipeline**:

```
Raw Question
  ↓ [sanitize_question()]
    - Remove control characters
    - Normalize whitespace
    - Enforce length limit (2000 chars)
  ↓
Sanitized Question
  ↓ [raise InvalidQuestionError if empty]
  ↓
Valid Question → AssistantService
```

---

### 3. Service Layer: AssistantService

**File**: `src/services/assistant_service.py` (20 lines)

**Purpose**: Business logic orchestration - coordinates Agent, Repository, and Providers

**Key Responsibilities**:

- Check rate limits (via ConversationRepository)
- Check response cache
- Invoke AssistantAgent if cache miss
- Cache response
- Update usage metrics

**Request Lifecycle**:

```
1. check_usage(user_id, current_date)
   → Raises RateLimitError if limit exceeded

2. cached = get_cached_response(question)
   → Returns if found and TTL valid

3. response = agent.answer(question)
   → Only called on cache miss

4. cache_response(question, response)
   → Store in in-memory MRU cache

5. update_usage(user_id, current_date)
   → Increment DynamoDB usage counter

6. return response
```

**Key Design Pattern**: Dependency Injection via constructor

```python
def __init__(
    self,
    assistant_agent: Optional[AssistantAgent] = None,
    conversation_repository: Optional[ConversationRepository] = None
):
```

---

### 4. Agent Layer: AssistantAgent

**File**: `src/agents/assistant_agent.py` (45 lines)

**Purpose**: Core AI logic - prompt construction, knowledge injection, and response routing

**Key Responsibilities**:

- Load knowledge base from S3
- Detect scheduling requests (keyword matching)
- Build system context with prompt + knowledge
- Invoke LLM via Bedrock
- Handle AI errors gracefully

**Question Routing Logic**:

```python
SCHEDULING_KEYWORDS = ["schedule", "book", "meeting", "call", "appointment"]

if _is_scheduling_request(question):
    return f"Book at {CALENDLY_URL}"
else:
    return invoke_llm_with_knowledge_context()
```

**System Context Construction**:

```python
system_blocks = [
    {"text": ALFRED_SYSTEM_PROMPT},
    {"text": f"Knowledge Base:\n{self.knowledge}"}
]
```

**System Prompt** (detailed guardrail):

```
You are Alfred, a formal and courteous AI butler inspired by Alfred Pennyworth.
Your responsibility: assist visitors in learning about Loc Le using ONLY provided knowledge.

MUST NOT:
- Provide general programming help unrelated to Loc Le
- Explain scientific concepts beyond knowledge base
- Write code/algorithms unless describing Loc's work
- Speculate beyond knowledge base

If question falls outside knowledge base:
- Respond politely and concisely
- Decline the request
- Redirect conversation to Loc Le
```

---

### 5. Repository Layer: ConversationRepository

**File**: `src/repositories/conversation_repository.py` (95 lines)

**Purpose**: Data access abstraction - manages caching and usage tracking

**Key Responsibilities**:

- In-memory response caching (question → response)
- Rate limit checking per user per day
- Usage tracking in DynamoDB
- Cache key generation via MD5 hashing

**Caching Strategy**:

- **Cache Key**: MD5 hash of normalized question (lowercase, trimmed)
- **TTL**: 3600 seconds (1 hour)
- **Storage**: In-memory dictionary `Dict[str, Tuple[str, float]]`
- **Hit Rate Impact**: 30-50% cost reduction for repeated questions

**Cache Lifecycle**:

```python
question → normalize → hash → check_cache → return if TTL valid
```

**Rate Limiting Strategy**:

- **Limit**: 50 requests per user per day
- **Identifier**: IP via `x-forwarded-for` header
- **Storage**: DynamoDB with TTL
- **Key Structure**: `pk=user_id`, `sk=YYYY-MM-DD`
- **Expiry**: 24 hours via TTL-based deletion

**DynamoDB Queries**:
| Operation | Purpose | Key |
|-----------|---------|-----|
| `get_item` | Check usage count | (user_id, date) |
| `update_item` | Increment counter | (user_id, date) |

---

### 6. Provider Layer

#### 6a. LLMProvider

**File**: `src/providers/llm_provider.py` (100 lines)

**Purpose**: Wrapper around AWS Bedrock for Claude model invocation

**Bedrock Configuration**:

- **Model**: AWS Bedrock (configurable via `MODEL_ID` env var)
- **Model Used**: Nova Lite (low-cost, suitable for constrained tasks)
- **Region**: `us-west-1` (configurable)
- **Timeout**: 3600s (1 hour) for read/connect
- **Retries**: 3 automatic retries on failure

**Inference Configuration**:

```json
{
  "maxTokens": 200, // Limit response length
  "temperature": 0.2, // Low temperature = deterministic
  "topP": 0.9, // Nucleus sampling parameter
  "topK": 1, // Consider only top-1 token (greedy)
  "stopSequences": [] // No stop sequences
}
```

**Why These Settings**:

- **maxTokens: 200**: Ensures concise, relevant responses; reduces cost
- **temperature: 0.2**: Low variability = consistent behavior; reduces hallucinations
- **topK: 1**: Greedy decoding = most likely token; reduces randomness

**API Methods**:

```python
invoke_model(system_blocks, messages) → str
  Response format: {"output": {"message": {"content": [{"text": "..."}]}}}

invoke_model_with_response_stream(system_blocks, messages) → str
  Streams chunks and accumulates into response
```

**Error Handling**:

- Catches all exceptions
- Logs with error details
- Returns fallback response: "Sorry, Alfred is unavailable right now."

#### 6b. KnowledgeProvider

**File**: `src/providers/knowledge_provider.py` (25 lines)

**Purpose**: Loads knowledge base from AWS S3

**Configuration**:

- **Bucket**: From `KNOWLEDGE_BUCKET` environment variable
- **Key**: `knowledge_base.json` (default)
- **Format**: JSON
- **Timeout**: 5s connect, 10s read
- **Retries**: 3

**Knowledge Base Structure**:

```json
{
  "personal_info": {
    "full_name": "Loc Le",
    "role": "Senior Cloud Software Engineer",
    "experience": "6+ years",
    "skills": [...],
    "bio": "..."
  },
  "services": [...],
  "case_studies": [...],
  "achievements": [...]
}
```

**Error Handling**:

- Logs with bucket/key info
- Raises exception with S3 path for debugging
- Agent catches and handles gracefully

#### 6c. StorageProvider

**File**: `src/providers/storage_provider.py` (80 lines)

**Purpose**: Generic DynamoDB client wrapper with type hints

**Features**:

- Type-safe DynamoDB operations
- Support for: get, put, update, query, scan, delete, batch_get
- Error handling for ClientError
- Request enhancement with defaults

**Operations**:

```python
get(request) → Dict                    # Single item retrieval
put(request) → Optional[ResponseMetadata]  # Item insertion
update(request) → Optional[ResponseMetadata] # Item update
query(request) → {"items": [...], "lastEvaluatedKey": ...}
scan(request) → {"items": [...], "lastEvaluatedKey": ...}
delete(request) → Dict
batch_get(request) → List[Dict]
```

**Type Hints**:
Uses `mypy_boto3_dynamodb` type definitions for IDE autocomplete

---

### 7. Shared Utilities

#### 7a. Configuration (config.py)

**File**: `src/shared/config.py` (40 lines)

**Key Constants**:

```python
# CORS & Endpoints
DOMAIN_URL = "https://imlocle.com"
LOCAL_HOST = "http://localhost:5173"
ALLOWED_ORIGINS = [LOCAL_HOST, DOMAIN_URL]
CALENDLY_URL = "https://calendly.com/loc-le/30-min-meeting"

# Constraints
MAX_QUESTION_LENGTH = 2000           # Input limit
CACHE_TTL_SECONDS = 3600             # 1-hour cache
RATE_LIMIT_MAX_REQUESTS = 50         # 50 requests/day/user

# System Prompt (detailed guardrail ~300 lines)
ALFRED_SYSTEM_PROMPT = """..."""
```

#### 7b. Exceptions (exceptions.py)

**File**: `src/shared/exceptions.py` (45 lines)

**Exception Hierarchy**:

```python
Exception (built-in)
├── InvalidQuestionError (400)
│   ├── message: str
│   ├── question: str
│   ├── http_status: int
│   └── headers: Dict
│
├── ChatbotProcessingError (500)
│   ├── message: str
│   ├── details: str
│   ├── http_status: int
│   └── headers: Dict
│
├── CORSOriginError (403)
│   ├── message: str
│   ├── origin: str
│   ├── http_status: int
│   └── headers: Dict
│
└── RateLimitError (429)
    ├── message: str
    ├── http_status: int
    └── headers: Dict
```

#### 7c. Input Validation (validators.py)

**File**: `src/shared/validators.py` (30 lines)

**Sanitization Pipeline**:

```
Raw Input
  ↓ [Check if empty]
  ↓ [Remove control characters: \x00-\x1f except \n\t]
  ↓ [Normalize whitespace: collapse to single spaces]
  ↓ [Strip leading/trailing whitespace]
  ↓ [Enforce length limit: 2000 chars]
  ↓ [Final empty check]
  ↓
Sanitized Output
```

**Regex Patterns**:

- Remove control chars: `r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]'`
- Normalize whitespace: Using Python's `.split()` and `' '.join()`

**Raises**: `ValueError` with descriptive message

#### 7d. Structured Logging (logging.py)

**File**: `src/shared/logging.py` (65 lines)

**JSON Log Format**:

```json
{
  "timestamp": "2026-03-12T15:30:45.123456+00:00",
  "level": "INFO",
  "message": "Processing request",
  "module": "assistant_handler",
  "function": "handler",
  "line": 25,
  "request_id": "test-request-123",
  "user_id": "192.168.1.1",
  "error": "...", // If applicable
  "exception": "..." // If exc_info=True
}
```

**Key Features**:

- ISO 8601 timestamps with UTC timezone
- Request correlation via `request_id`
- User tracking via `user_id`
- Exception stack traces included
- CloudWatch-compatible format

**Usage**:

```python
logger = get_logger(__name__)
logger.info("Message", extra={"request_id": "123", "key": "value"})
```

#### 7e. HTTP Responses (responses.py)

**File**: `src/shared/responses.py` (20 lines)

**Response Formats**:

```python
success_response(body, status_code=200) → {
  "statusCode": 200,
  "headers": {...CORS headers...},
  "body": JSON string
}

error_response(message, headers, status_code=400) → {
  "statusCode": 400,
  "headers": {...with CORS...},
  "body": {"reply": message}
}
```

---

## Data Flow

### Complete Request-to-Response Flow

```
1. CLIENT REQUEST
   POST /ask HTTP/1.1
   Origin: https://imlocle.com
   x-forwarded-for: 192.168.1.100
   {
     "question": "What is Loc's experience?"
   }

2. API GATEWAY
   - Routes to Lambda
   - Provides event context with:
     - requestContext.requestId
     - requestContext.timeEpoch
     - headers (origin, x-forwarded-for)

3. LAMBDA HANDLER (AssistantHandler)
   ├─ Extract request_id from event
   ├─ Call QueryController.handle_event()
   └─ Catch exceptions and return responses

4. QUERY CONTROLLER (QueryController)
   ├─ Extract origin → validate against ALLOWED_ORIGINS
   │  └─ FAIL? Raise CORSOriginError(403)
   ├─ Extract user_id from x-forwarded-for header
   ├─ Extract current_date from timeEpoch
   ├─ Parse question from body
   ├─ Sanitize question with sanitize_question()
   │  └─ FAIL? Raise InvalidQuestionError(400)
   ├─ Call AssistantService.ask()
   └─ Return response string

5. ASSISTANT SERVICE (AssistantService)
   ├─ Check rate limits
   │  └─ check_usage(user_id=192.168.1.100, date=2026-03-12)
   │     ├─ Query DynamoDB(pk=192.168.1.100, sk=2026-03-12)
   │     ├─ Get count from response
   │     └─ If count >= 50 → Raise RateLimitError(429)
   │
   ├─ Check cache
   │  └─ cache_key = MD5(question.lower().strip())
   │     ├─ If in memory AND not expired → return cached response
   │     └─ EARLY EXIT: Skip steps 6-8
   │
   ├─ Invoke AssistantAgent (cache miss)
   │  └─ [Continue to step 6...]
   │
   ├─ Cache response
   │  └─ cache[cache_key] = (response, now_timestamp)
   │
   └─ Update usage
      └─ update_usage(pk=192.168.1.100, sk=2026-03-12)
         - Increment count in DynamoDB
         - Set TTL to tomorrow

6. ASSISTANT AGENT (AssistantAgent)
   ├─ Load knowledge base from S3
   │  └─ KnowledgeProvider.fetch_knowledge()
   │     - S3 GetObject(alfred-knowledge-bucket, knowledge_base.json)
   │
   ├─ Check if scheduling request
   │  └─ if any keyword in ["schedule", "book", "meeting", ...]:
   │     └─ Return direct Calendly link
   │
   ├─ Build system context
   │  └─ system_blocks = [
   │       {"text": ALFRED_SYSTEM_PROMPT},
   │       {"text": f"Knowledge Base:\n{knowledge_json}"}
   │     ]
   │
   └─ Invoke LLM
      └─ [Continue to step 7...]

7. LLM PROVIDER (LLMProvider)
   ├─ Prepare payload
   │  └─ {
   │       "system": system_blocks,
   │       "messages": [{"role": "user", "content": [{"text": question}]}],
   │       "inferenceConfig": {
   │         "maxTokens": 200,
   │         "temperature": 0.2,
   │         "topP": 0.9,
   │         "topK": 1
   │       }
   │     }
   │
   ├─ Invoke AWS Bedrock
   │  └─ bedrock_runtime_client.invoke_model(
   │       modelId="aws.nova-lite-v1:0",
   │       body=json.dumps(payload)
   │     )
   │
   ├─ Parse response
   │  └─ response["output"]["message"]["content"][0]["text"]
   │
   └─ Return response text

8. LOGGING
   ├─ request_id: test-request-123
   ├─ user_id: 192.168.1.100
   ├─ action: cache_hit | llm_invoked
   ├─ latency: 150ms | 2000ms
   └─ [All structured as JSON]

9. HANDLER RESPONSE
   HTTP 200 OK
   Content-Type: application/json
   Access-Control-Allow-Origin: https://imlocle.com
   {
     "statusCode": 200,
     "headers": {...CORS...},
     "body": "{\"reply\": \"Loc has 6+ years of experience...\"}"
   }

10. CLIENT RECEIVES
    Parse JSON response
    Display reply to user
```

### Cache Hit vs Miss Latency

**Cache Hit Flow** (typical: 10-50ms):

```
Client → API Gateway → Lambda → Controller → Service
  → Check Cache (HIT) → Return
```

**Cache Miss Flow** (typical: 1500-3000ms):

```
Client → API Gateway → Lambda → Controller → Service
  → Check Cache (MISS)
  → Agent: Load Knowledge (1000ms)
  → Agent: Build System Context (10ms)
  → Agent: Invoke Bedrock (1500ms)
  → Bedrock: Generate Response (500-1000ms)
  → Parse Response (10ms)
  → Cache Response (5ms)
  → Return
```

**Cost Impact**: 1-hour cache saves ~30-50% of Bedrock invocation costs

---

## Design Patterns

### 1. **Dependency Injection**

Used throughout for testability:

```python
# Pattern: Constructor injection with defaults
def __init__(self,
    llm_provider: Optional[LLMProvider] = None,
    knowledge_provider: Optional[KnowledgeProvider] = None
):
    self.llm_provider = llm_provider or LLMProvider()
    self.knowledge_provider = knowledge_provider or KnowledgeProvider()
```

**Benefits**:

- Easy mocking in tests
- Flexible swapping of implementations
- Clear interface contracts
- Decoupling of concerns

### 2. **Provider Pattern**

Abstracts external services behind clean interfaces:

```
┌───────────────────────────────────────┐
│         AssistantAgent                │
└───────────────────────────────────────┘
          ↓                ↓
┌──────────────────┐  ┌───────────────────────┐
│  LLMProvider     │  │  KnowledgeProvider    │
│ (Bedrock)        │  │ (S3)                  │
└──────────────────┘  └───────────────────────┘
```

**Benefits**:

- Loose coupling from external services
- Easy service switching
- Centralized error handling
- Configuration isolation

### 3. **Repository Pattern**

Abstracts data access:

```python
class ConversationRepository:
    - get_cached_response()     # In-memory
    - cache_response()          # In-memory
    - check_usage()             # DynamoDB
    - update_usage()            # DynamoDB
```

**Benefits**:

- Clear separation of data concerns
- Consistent interface for storage operations
- Mockable for testing
- Supports multiple storage backends

### 4. **Handler Pattern (AWS Lambda)**

Entry point with exception transformation:

```python
def lambda_handler(event, context):
    handler = AssistantHandler()
    return handler.handler(event, context)
```

**Benefits**:

- Decouples Lambda infrastructure from business logic
- Enables unit testing without AWS SDK
- Centralized exception handling
- Clean error responses

### 5. **Decorator Pattern (Fixtures)**

Pytest fixtures provide test infrastructure:

```python
@pytest.fixture
def mock_dynamodb():
    """Mock DynamoDB storage provider."""
    with patch(...) as mock:
        yield mock

# Usage:
def test_handler(mock_dynamodb):
    # mock_dynamodb is auto-injected
```

**Benefits**:

- Reusable test setup
- Readable test code
- Centralized mock management

### 6. **Strategy Pattern (Routing)**

AssistantAgent routes based on question type:

```python
if _is_scheduling_request(question):
    strategy = ReturnCalendlyLink()
else:
    strategy = InvokeLLMWithKnowledge()
```

**Benefits**:

- Extensible routing logic
- Clear code path separation
- Easy to add new strategies

### 7. **Singleton Pattern (AWS Clients)**

Reuse AWS clients across requests:

```python
_bedrock_runtime_client: BedrockRuntimeClient | None = None

def get_bedrock_runtime_client() -> BedrockRuntimeClient:
    global _bedrock_runtime_client
    if _bedrock_runtime_client is None:
        _bedrock_runtime_client = boto3.client(...)
    return _bedrock_runtime_client
```

**Benefits**:

- Less connection overhead
- Reuses connection pools
- Module-level initialization
- Cold start optimization

### 8. **Template Method Pattern (Error Handling)**

Exceptions follow consistent contract:

```python
class BaseException(Exception):
    def __init__(self, message, details=None):
        super().__init__(message)
        self.details = details
        self.http_status = 500  # Override in subclass
        self.headers = get_headers()
```

**Benefits**:

- Consistent HTTP response format
- Easy handler mapping
- Extensible for new exception types

---

## Configuration & Environment

### Environment Variables

**Required Variables**:

| Variable              | Value               | Purpose                 | Example                   |
| --------------------- | ------------------- | ----------------------- | ------------------------- |
| `MODEL_ID`            | Bedrock Model ID    | LLM selection           | `aws.nova-lite-v1:0`      |
| `KNOWLEDGE_BUCKET`    | S3 bucket name      | Knowledge base location | `alfred-knowledge-bucket` |
| `USAGE_TRACKER_TABLE` | DynamoDB table name | Usage tracking storage  | `alfred-usage-tracker`    |
| `AWS_REGION`          | AWS region          | Lambda/SDK region       | `us-west-1`               |

**Optional Variables**:

| Variable             | Default     | Purpose         |
| -------------------- | ----------- | --------------- |
| `AWS_DEFAULT_REGION` | `us-west-1` | Fallback region |

### Configuration Management

**Local Development** (`.env` file):

```bash
MODEL_ID=aws.nova-lite-v1:0
KNOWLEDGE_BUCKET=alfred-knowledge-bucket-dev
USAGE_TRACKER_TABLE=alfred-usage-tracker-dev
AWS_REGION=us-west-1
```

**Terraform Variables** (`terraform/variables.tf`):

```hcl
variable "aws_region" {
  type    = string
  default = "us-west-1"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "project_name" {
  type    = string
  default = "alfred"
}

variable "runtime" {
  type    = string
  default = "python3.13"
}
```

### Configuration via AWS Secrets Manager (Optional)

For production, store secrets:

```json
{
  "MODEL_ID": "aws.nova-lite-v1:0",
  "KNOWLEDGE_BUCKET": "alfred-knowledge-bucket-prod",
  "OPENAI_API_KEY": "sk-..."
}
```

---

## Dependencies

### Production Dependencies

**File**: `requirements.txt`

```
boto3>=1.42.30
- AWS SDK for Python
- Core dependency for Bedrock, S3, DynamoDB

mypy-boto3-dynamodb>=1.42.3
- Type stubs for DynamoDB
- Enables IDE autocomplete and mypy type checking

mypy-boto3-bedrock-runtime>=1.42.3
- Type stubs for Bedrock Runtime
- Enables IDE support for invoke_model()
```

**Why These?**

- **boto3**: Only official AWS SDK; required for all AWS service interactions
- **Type stubs**: Development-time for IDE support; included in Lambda layer for runtime type checking

### Development Dependencies

**File**: `requirements-dev.txt`

```
Testing Framework:
- pytest==7.4.3              # Test runner
- pytest-cov==4.1.0          # Code coverage
- pytest-mock==3.12.0        # Mocking utilities
- moto==4.2.10               # AWS service mocking
- responses==0.24.1          # HTTP mocking

Code Quality:
- black==23.12.0             # Code formatter
- pylint==3.0.3              # Linter
- mypy==1.7.1                # Static type checker

Utilities:
- python-dotenv==1.0.0       # .env file support
- ipython==8.18.1            # Enhanced REPL

AWS:
- boto3>=1.42.30
- mypy-boto3-dynamodb>=1.42.3
- mypy-boto3-bedrock-runtime>=1.42.3
```

### Lambda Layer Dependencies

**File**: `lambda_layer/python/`

Contains pre-built AWS SDK and dependencies for Lambda functions:

```
boto3-1.42.62/
botocore-1.42.62/
s3transfer/
jmespath/
dateutil/
urllib3/
six/
mypy_boto3_bedrock_runtime/
mypy_boto3_dynamodb/
```

**Built via Docker**: `make zip-layer` uses Amazon Linux 2 container to build

---

## Error Handling

### Exception Hierarchy & HTTP Mapping

```
User Request
    ↓
Business Logic
    ↓
Exception Raised
    ↓
Handler Catches
    ↓
Transform to HTTP Response
    ↓
Return to Client
```

### Exception Classes

| Exception                | HTTP Status | Trigger                           | Message                              |
| ------------------------ | ----------- | --------------------------------- | ------------------------------------ |
| `InvalidQuestionError`   | 400         | Empty question after sanitization | "Invalid or empty question provided" |
| `CORSOriginError`        | 403         | Origin not in `ALLOWED_ORIGINS`   | "Unauthorized origin"                |
| `RateLimitError`         | 429         | Usage count >= 50/day             | "Rate limit exceeded"                |
| `ChatbotProcessingError` | 500         | Unexpected exception              | "Error processing chatbot request"   |

### Error Response Format

```json
HTTP/1.1 400 Bad Request
Content-Type: application/json
Access-Control-Allow-Origin: https://imlocle.com

{
  "statusCode": 400,
  "headers": {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "https://imlocle.com",
    "Access-Control-Allow-Methods": "OPTIONS,POST",
    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization"
  },
  "body": "{\"reply\": \"I am sorry, but that was an invalid question. Please ask another.\"}"
}
```

### Logging on Errors

All exceptions are logged with context:

```json
{
  "timestamp": "2026-03-12T15:30:45.123456+00:00",
  "level": "ERROR",
  "message": "Unexpected error processing request",
  "module": "assistant_handler",
  "request_id": "test-request-123",
  "user_id": "192.168.1.1",
  "error": "Database connection failed",
  "exception": "[Full stack trace]"
}
```

---

## Safety & Guardrails

### Multi-Layer Guardrails

```
┌─────────────────────────────────────────┐
│  1. CORS Origin Validation              │
│     - Whitelist allowed domains         │
│     - Reject cross-origin requests      │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  2. Input Sanitization                  │
│     - Remove control characters         │
│     - Enforce length limits             │
│     - Normalize whitespace              │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  3. Rate Limiting                       │
│     - 50 requests/day per user          │
│     - DynamoDB-backed tracking          │
│     - 24-hour TTL reset                 │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  4. System Prompt Guardrails            │
│     - Scope limited to Loc Le           │
│     - No general AI assistance          │
│     - Refusal patterns for out-of-scope │
│     - Knowledge base injection          │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│  5. LLM Inference Tuning                │
│     - Low temperature (0.2)             │
│     - Greedy decoding (topK=1)          │
│     - Limited tokens (200)              │
│     - Deterministic responses           │
└─────────────────────────────────────────┘
```

### CORS Whitelist

```python
ALLOWED_ORIGINS = [
    "https://imlocle.com",      # Production
    "http://localhost:5173"      # Local dev
]
```

**Enforcement**:

```python
origin = headers.get("origin", "")
if origin not in ALLOWED_ORIGINS:
    raise CORSOriginError(origin=origin)  # 403 Forbidden
```

### Input Sanitization

**Attack Vectors Prevented**:

1. **Prompt Injection**: Control characters removed
2. **Buffer Overflow**: Length limited (2000 chars)
3. **Null Bytes**: Control chars excluded
4. **Unicode Exploits**: Whitespace normalized

**Sanitization Steps**:

```python
1. Remove control characters: \x00-\x1f except \n\t
2. Normalize whitespace: collapse to single space
3. Strip leading/trailing whitespace
4. Enforce length limit (2000 chars)
5. Raise ValueError if empty
```

### Rate Limiting

**Strategy**: Token bucket per user per day

**How It Works**:

```
User: 192.168.1.100
Date: 2026-03-12

DynamoDB Item:
{
  "pk": "192.168.1.100",
  "sk": "2026-03-12",
  "count": 45,                    // Requests today
  "expires_at": 1678387200       // Tomorrow timestamp
}

On Request:
1. Get item from DynamoDB
2. If count >= 50 → Raise RateLimitError (429)
3. Otherwise → Process request
4. Increment count via atomic UpdateExpression
5. Set expires_at to tomorrow
```

**Configuration**:

```python
RATE_LIMIT_MAX_REQUESTS = 50  # requests per day per user
```

**TTL-Based Cleanup**: DynamoDB automatically deletes items after 24 hours

### System Prompt Guardrails

**Core Principle**: Knowledge base injection prevents hallucinations

**Prompt Structure**:

```
System: "You are Alfred..."
Knowledge: "Knowledge Base: {json of approved info}"
User: "What is Loc's experience?"
```

**Refusal Patterns**:

- "I'm specialized in answering questions about Loc Le..."
- "For general {topic} help, I'd recommend..."
- "If you have questions about Loc's specific {topic}..."

**Example Refusal**:

```
User: "How do I build a React app?"

Alfred: "I'm specialized in answering questions about Loc Le's
experience and services. For general React development questions,
I'd recommend checking out the official React documentation.
If you have questions about Loc's specific React projects or
experience, I'd be happy to help!"
```

### LLM Inference Configuration

**Why Low Temperature?**

- Reduces randomness
- Prevents hallucinations
- Consistent behavior
- Aligned with guardrail system prompt

```python
inferenceConfig = {
    "maxTokens": 200,      # Concise responses
    "temperature": 0.2,    # Deterministic (0.0 = greedy, 1.0 = creative)
    "topP": 0.9,           # Nucleus sampling cutoff
    "topK": 1,             # Sample only top token (greedy decoding)
}
```

---

## Testing & Quality

### Testing Framework

**Framework**: pytest 7.4.3

**Configuration** (`pytest.ini`):

```ini
[pytest]
minversion = 7.0
python_files = test_*.py
python_classes = Test*
python_functions = test_*
testpaths = tests
pythonpath = src
```

### Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── unit/
│   ├── test_handlers.py     # Handler tests
│   ├── test_controllers.py  # Controller tests
│   ├── test_services.py     # Service tests
│   ├── test_agents.py       # Agent tests
│   ├── test_repositories.py # Repository tests
│   ├── test_validators.py   # Validator tests
│   ├── test_exceptions.py   # Exception tests
│   └── utils.py             # Test utilities
└── integration/             # Integration tests (placeholder)
```

### Fixtures (conftest.py)

**AWS Service Mocks**:

```python
@pytest.fixture
def mock_dynamodb():
    """Mock DynamoDB storage provider."""
    # Returns mocked StorageProvider

@pytest.fixture
def mock_bedrock():
    """Mock Bedrock LLM provider."""
    # Returns mocked Bedrock client

@pytest.fixture
def mock_s3():
    """Mock S3 knowledge base provider."""
    # Returns mocked S3 client
```

**Test Data**:

```python
@pytest.fixture
def valid_lambda_event():
    """Valid Lambda event from API Gateway."""
    # Returns event dict with valid data

@pytest.fixture
def invalid_origin_event():
    """Lambda event with invalid origin."""
    # Returns event dict with malicious origin
```

### Test Coverage Areas

| Component    | Tests | Coverage                              |
| ------------ | ----- | ------------------------------------- |
| Handlers     | 8+    | Exception mapping, logging            |
| Controllers  | 6+    | CORS, input validation                |
| Services     | 8+    | Caching, rate limiting, orchestration |
| Agents       | 4+    | Routing, LLM invocation               |
| Repositories | 6+    | Cache ops, usage tracking             |
| Validators   | 4+    | Sanitization edge cases               |
| Exceptions   | 2+    | HTTP status codes                     |

### Running Tests

**All tests**:

```bash
pytest tests/ -v
```

**Unit tests only**:

```bash
pytest tests/unit/ -v
```

**With coverage**:

```bash
pytest tests/ --cov=src --cov-report=html
```

**Specific test**:

```bash
pytest tests/unit/test_handlers.py::TestAssistantHandler::test_handler_success -v
```

### Code Quality Tools

**Formatting**:

```bash
black src/ tests/
```

**Linting**:

```bash
pylint src/
```

**Type Checking**:

```bash
mypy src/
```

---

## Infrastructure (Terraform)

### Architecture Diagram

```
┌────────────────────────────────────────────────────────┐
│                    AWS Account                         │
├────────────────────────────────────────────────────────┤
│                                                        │
│  ┌──────────────┐                                      │
│  │ API Gateway  │ (HTTP API - Regional)               │
│  │ Endpoint     │                                      │
│  └──────┬───────┘                                      │
│         │                                              │
│         ↓                                              │
│  ┌──────────────────────────────────────────┐          │
│  │         Lambda Function                  │          │
│  │  Runtime: Python 3.13                   │          │
│  │  Handler: assistant_handler.lambda_handler          │
│  │  Memory: 128-512 MB (configurable)      │          │
│  │  Timeout: 10-60 seconds                 │          │
│  └──────┬──────────────────────────────────┘          │
│         │                                              │
│    ┌────┴────────────────────┬───────────────────┐    │
│    │                         │                   │    │
│    ↓                         ↓                   ↓    │
│  ┌────────┐        ┌─────────────────┐  ┌──────────┐ │
│  │   S3   │        │    DynamoDB     │  │ Bedrock  │ │
│  │ Bucket │        │  Usage Tracker  │  │  API     │ │
│  │(Know.) │        │  Table          │  │(Claude)  │ │
│  └────────┘        └─────────────────┘  └──────────┘ │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │    CloudWatch Logs / Metrics                     │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
└────────────────────────────────────────────────────────┘
```

### Terraform Modules

**File Structure**:

```
terraform/
├── main.tf              # Root module (202 lines)
├── variables.tf         # Input variables (15 lines)
├── outputs.tf           # Output values
├── backend.tf           # Backend configuration
└── modules/
    ├── api/             # API Gateway module
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    │
    ├── lambda/          # Lambda function module
    │   ├── main.tf
    │   ├── variables.tf
    │   ├── outputs.tf
    │   └── function.zip (built by makefile)
    │
    └── dynamodb/        # DynamoDB table module
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

### Main Terraform Configuration

**`terraform/main.tf`**:

```hcl
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region  # us-west-1
}

# S3 Bucket for knowledge base
resource "aws_s3_bucket" "knowledge_bucket" {
  bucket = "${var.project_name}-knowledge-bucket"
}

# DynamoDB Tables (via module)
module "dynamodb" {
  source       = "./modules/dynamodb"
  project_name = var.project_name
  environment  = var.environment
}

# API Gateway (via module)
module "api" {
  source       = "./modules/api"
  environment  = var.environment
  project_name = var.project_name
}

# Lambda Function (via module)
module "lambda" {
  source                   = "./modules/lambda"
  environment              = var.environment
  aws_region               = var.aws_region
  project_name             = var.project_name
  api_id                   = module.api.api_id
  api_execution_arn        = module.api.api_execution_arn
  knowledge_bucket         = aws_s3_bucket.knowledge_bucket.bucket
  usage_tracker_table_arn  = module.dynamodb.usage_tracker_table_arn
  usage_tracker_table_name = module.dynamodb.usage_tracker_table_name
}
```

### Resource Details

#### API Gateway

**Type**: HTTP API (newer, faster, cheaper than REST API)

**Configuration**:

- Protocol: HTTP/2
- Endpoint: Regional
- CORS enabled with whitelist
- Integration: Lambda

#### Lambda Function

**Configuration**:

- **Runtime**: Python 3.13 (latest)
- **Memory**: 256 MB (configurable)
- **Timeout**: 30 seconds (for Bedrock)
- **Ephemeral Storage**: 512 MB
- **Environment Variables**: MODEL_ID, KNOWLEDGE_BUCKET, USAGE_TRACKER_TABLE, AWS_REGION
- **VPC**: Optional (for private DB access)
- **Log Group**: /aws/lambda/alfred-assistant-{environment}
- **Layers**: Python dependencies layer

**IAM Permissions** (Least Privilege):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": "arn:aws:s3:::alfred-knowledge-bucket/*"
    },
    {
      "Effect": "Allow",
      "Action": ["dynamodb:GetItem", "dynamodb:UpdateItem"],
      "Resource": "arn:aws:dynamodb:us-west-1:ACCOUNT:table/alfred-usage-tracker"
    },
    {
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel"],
      "Resource": "arn:aws:bedrock:us-west-1:ACCOUNT:foundation-model/aws.nova-lite-v1:0"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:us-west-1:ACCOUNT:log-group:/aws/lambda/alfred-*"
    }
  ]
}
```

#### DynamoDB Table

**Configuration** (Usage Tracker):

- **Partition Key (pk)**: User ID (String)
- **Sort Key (sk)**: Date (String, format: YYYY-MM-DD)
- **TTL Attribute**: expires_at (auto-deletes after 24 hours)
- **Billing Mode**: Pay-per-request (automatic scaling)
- **Attributes**:
  - `pk`: User ID
  - `sk`: Date
  - `count`: Number of requests today
  - `expires_at`: TTL timestamp

**Sample Item**:

```json
{
  "pk": "192.168.1.100",
  "sk": "2026-03-12",
  "count": 25,
  "expires_at": 1678387200
}
```

#### S3 Bucket (Knowledge Base)

**Configuration**:

- **Bucket Name**: alfred-knowledge-bucket
- **Versioning**: Optional
- **Encryption**: Optional (SSE-S3)
- **Public Access**: Blocked
- **Object**: knowledge_base.json

**Sample Content**:

```json
{
  "personal_info": {
    "full_name": "Loc Le",
    "role": "Senior Cloud Software Engineer",
    "experience": "6+ years"
  }
}
```

### Backend State Management

**`terraform/backend.auto.hcl`** (generated by makefile):

```hcl
bucket = "alfred-terraform-state-bucket"
key    = "alfred/dev/terraform.tfstate"
region = "us-west-1"
```

**State Locking**: DynamoDB table (optional, for team collaboration)

---

## Deployment & Operations

### Build & Deployment Process

**Makefile** (`makefile` - 81 lines):

```makefile
TARGET: Build Outputs
├─ zip-layer      # Build Python dependencies layer (Docker)
├─ zip-assistant  # Zip Lambda function code
├─ terraform-init # Initialize Terraform
├─ terraform-apply # Deploy resources
└─ deploy          # Run all above

COMMANDS:
$ make clean              # Remove build artifacts
$ make zip-all            # Zip layer and lambdas
$ make terraform-init     # Init Terraform
$ make terraform-apply    # Deploy
$ make deploy             # Full deployment

ENVIRONMENT:
ENV ?= dev                # Environment (dev/prod/staging)
REGION = us-west-1        # AWS region
```

### Deployment Steps

**Step 1: Build**:

```bash
make clean         # Clean old artifacts
make zip-all       # Build layer + lambda zips
```

**Step 2: Generate Config**:

```bash
make generate-backend-config  # Create backend config
```

**Step 3: Initialize**:

```bash
make terraform-init  # Initialize Terraform
```

**Step 4: Deploy**:

```bash
make terraform-apply  # Apply Terraform changes
```

**Full Deployment** (one command):

```bash
make deploy ENV=dev
```

### Docker Layer Building

**Why Docker?**: Ensures dependencies are built for Amazon Linux 2 (Lambda runtime)

```bash
docker run --rm \
  --platform linux/amd64 \
  -v $(CURDIR)/src:/var/task \
  -v $(CURDIR)/lambda_layer/python:/lambda/python \
  public.ecr.aws/sam/build-python3.13 \
  /bin/sh -c "pip3 install -r /var/task/requirements.txt \
              -t /lambda/python --no-cache-dir"
```

**Output**: `lambda_layer/python/` directory with compiled dependencies

### Local Development

**Setup**:

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt

# Create .env file
cat > .env << EOF
MODEL_ID=aws.nova-lite-v1:0
KNOWLEDGE_BUCKET=alfred-knowledge-bucket-dev
USAGE_TRACKER_TABLE=alfred-usage-tracker-dev
AWS_REGION=us-west-1
EOF

# Load environment
set -a && source .env && set +a
```

**Running Tests**:

```bash
pytest tests/unit/ -v
pytest tests/unit/ --cov=src --cov-report=html
```

**Local Lambda Testing** (using moto):

```bash
pytest tests/unit/test_handlers.py -v
```

### Monitoring & Observability

**CloudWatch Logs**:

- Log Group: `/aws/lambda/alfred-assistant-{environment}`
- Log Stream: Per Lambda invocation
- JSON format with request_id correlation

**CloudWatch Metrics** (optional):

- Invocations
- Duration
- Errors
- Throttles

**X-Ray Tracing** (optional):

- Request flow visualization
- Latency breakdown
- Error tracking

---

## Summary Table

| Aspect                   | Details                                                                          |
| ------------------------ | -------------------------------------------------------------------------------- |
| **Language**             | Python 3.13                                                                      |
| **Framework**            | AWS Lambda (serverless)                                                          |
| **Architecture**         | Layered (Handler → Controller → Service → Agent → Providers)                     |
| **LLM**                  | AWS Bedrock (Nova Lite)                                                          |
| **Database**             | DynamoDB (usage tracking)                                                        |
| **Storage**              | S3 (knowledge base)                                                              |
| **Caching**              | In-memory (1-hour TTL)                                                           |
| **Rate Limiting**        | 50 requests/day/user                                                             |
| **Latency (Cache Hit)**  | ~10-50ms                                                                         |
| **Latency (Cache Miss)** | ~1500-3000ms                                                                     |
| **Cost Model**           | Pay-per-invocation + Bedrock usage                                               |
| **Testing**              | pytest with mocking                                                              |
| **Infrastructure**       | Terraform (IaC)                                                                  |
| **Deployment**           | Makefile + Terraform                                                             |
| **Error Handling**       | Custom exceptions → HTTP responses                                               |
| **Logging**              | Structured JSON → CloudWatch                                                     |
| **Guardrails**           | 5-layer safety: CORS, validation, rate limiting, system prompt, inference tuning |

---

## Key Files at a Glance

| File                                          | Lines | Purpose                     |
| --------------------------------------------- | ----- | --------------------------- |
| `src/handlers/assistant_handler.py`           | 72    | Lambda entry point          |
| `src/controllers/query_controller.py`         | 52    | Request validation          |
| `src/services/assistant_service.py`           | 20    | Business logic              |
| `src/agents/assistant_agent.py`               | 45    | AI logic                    |
| `src/repositories/conversation_repository.py` | 95    | Data access (cache + usage) |
| `src/providers/llm_provider.py`               | 100   | Bedrock wrapper             |
| `src/shared/config.py`                        | 40    | Configuration constants     |
| `src/shared/exceptions.py`                    | 45    | Custom exceptions           |
| `src/shared/logging.py`                       | 65    | JSON logging                |
| `src/shared/validators.py`                    | 30    | Input sanitization          |
| `tests/conftest.py`                           | 80    | Test fixtures               |
| `terraform/main.tf`                           | 202   | Infrastructure              |
| `makefile`                                    | 81    | Build automation            |

---

## Next Steps & Recommendations

### For Production Deployment

1. **Set up CI/CD pipeline** (GitHub Actions, GitLab CI)
2. **Add integration tests** for AWS services
3. **Configure monitoring** (CloudWatch alarms, SNS notifications)
4. **Set up log analysis** (CloudWatch Insights queries)
5. **Implement more guardrails** (additional validation layers)
6. **Add analytics** (tracking queries, usage patterns)

### For Scaling

1. **Multi-region deployment** using Terraform workspaces
2. **Caching layer** (ElastiCache for distributed cache)
3. **Queue-based processing** (SQS for async responses)
4. **API versioning** (header-based or path-based)

### For Cost Optimization

1. **Reserved capacity** for predictable usage
2. **Query parameter caching** beyond 1 hour for common questions
3. **Regional endpoint selection** based on latency
4. **Lambda provisioned concurrency** for consistent performance

---

**Document Generated**: March 12, 2026  
**Status**: Complete - Comprehensive Technical Summary
