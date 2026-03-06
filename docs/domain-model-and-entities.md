# Domain Model and Entities

## Overview

Alfred's domain model is intentionally simple, focusing on three core entities: User Requests, Usage Tracking, and Knowledge Base. The system is designed for stateless request/response interactions with minimal data persistence.

## Core Entities

### 1. User Request

Represents an incoming question from a user through the chat interface.

**Attributes:**

- `question` (string, required): The user's question text
- `user_id` (string, derived): IP address from `x-forwarded-for` header
- `current_date` (string, derived): Request date in `YYYY-MM-DD` format
- `origin` (string, derived): Request origin from headers

**Validation Rules:**

- Question must not be empty
- Origin must be in allowed list
- User must not exceed daily rate limit

**Lifecycle:**

1. Received via API Gateway
2. Validated by controller
3. Processed by service
4. Sent to Bedrock for inference
5. Response returned to client

**Example:**

```json
{
  "question": "What services does Loc offer?",
  "user_id": "192.168.1.1",
  "current_date": "2026-02-12",
  "origin": "https://imlocle.com"
}
```

---

### 2. Usage Record

Tracks daily request counts per user for rate limiting purposes.

**DynamoDB Schema:**

- `pk` (string, partition key): User identifier (IP address)
- `sk` (string, sort key): Date in `YYYY-MM-DD` format
- `count` (number): Number of requests made on this date
- `expires_at` (number, TTL): Unix timestamp for automatic deletion

**Access Patterns:**

- **Check usage**: Get item by `pk` and `sk`
- **Update usage**: Increment `count` atomically
- **Auto-cleanup**: TTL deletes records after 24 hours

**Business Rules:**

- Maximum 50 requests per user per day
- Counter resets automatically via TTL
- First request creates record with count=1
- Subsequent requests increment counter

**DynamoDB Operations:**

```python
# Check usage
get_params = {
    "Key": {"pk": user_id, "sk": current_date}
}

# Update usage
update_params = {
    "Key": {"pk": user_id, "sk": current_date},
    "UpdateExpression": "SET #count = if_not_exists(#count, :start) + :inc, #expires_at = :expires_at",
    "ExpressionAttributeValues": {
        ":start": 0,
        ":inc": 1,
        ":expires_at": int((datetime.now() + timedelta(days=1)).timestamp())
    }
}
```

**Example Record:**

```json
{
  "pk": "192.168.1.1",
  "sk": "2026-02-12",
  "count": 15,
  "expires_at": 1739404800
}
```

---

### 3. Knowledge Base

Structured JSON document containing all information about Loc Le that Alfred can reference.

**Storage:**

- Location: S3 bucket (`alfred-knowledge-bucket`)
- File: `knowledge_base.json`
- Size: ~15KB
- Format: Nested JSON structure

**Top-Level Sections:**

- `version`: Knowledge base version number
- `metadata`: Creation date, last updated, description
- `personal_info`: Name, role, location, bio, education
- `professional_focus`: Positioning, offerings, target clients
- `services`: Service packages, pricing, deliverables
- `technical_skills`: Languages, cloud, backend, data, frontend
- `case_studies`: Detailed project descriptions (Alfred, Neptune, etc.)
- `projects`: Project summaries with technologies
- `website`: URL and sections
- `contact_info`: LinkedIn, GitHub, Calendly
- `ai_chatbot_info`: Alfred's self-description and behavior rules
- `alfred_architecture`: Detailed architecture documentation
- `hobbies`: Personal interests
- `fun_facts`: Interesting background information

**Usage Pattern:**

1. Lambda cold start loads knowledge base from S3
2. Cached in memory for subsequent invocations
3. Injected into Bedrock system context on each request
4. Updated manually by uploading new JSON to S3

**Example Structure:**

```json
{
  "version": "2.3.0",
  "personal_info": {
    "full_name": "Loc Le",
    "main_role": "Senior Cloud Software Engineer",
    "location": "Las Vegas, NV"
  },
  "services": {
    "pricing": {
      "packages": [
        {
          "name": "MVP Core",
          "price": 2500,
          "includes": ["API endpoints", "Authentication", "Database setup"]
        }
      ]
    }
  }
}
```

---

### 4. AI Response

The generated response from AWS Bedrock based on the user's question and knowledge base.

**Attributes:**

- `reply` (string): The AI-generated answer
- `model_id` (string): Bedrock model identifier
- `usage` (object): Token consumption metrics (optional)

**Generation Process:**

1. System prompt defines Alfred's behavior and constraints
2. Knowledge base injected as context
3. User question appended as user message
4. Bedrock invoked with inference configuration
5. Response extracted from model output

**Inference Configuration:**

```python
{
    "maxTokens": 200,
    "temperature": 0.2,  # Low randomness
    "topP": 0.9,
    "topK": 1,
    "stopSequences": []
}
```

**Response Format:**

```json
{
  "reply": "Loc offers three service packages: MVP Core ($2,500), MVP + AI ($3,500), and MVP + Support ($4,000). Each package includes backend development, authentication, and AWS deployment."
}
```

---

## Entity Relationships

```
User Request
    ├─> Usage Record (check/update)
    ├─> Knowledge Base (read)
    └─> AI Response (generate)

Usage Record
    └─> User Request (rate limit enforcement)

Knowledge Base
    └─> AI Response (context injection)
```

## Data Flow

1. Request Ingestion: User submits question → API Gateway → Lambda (`AssistantHandler`)
2. Validation: `QueryController` validates CORS, sanitizes input
3. Usage Check: `ConversationRepository` checks DynamoDB for user's daily count
4. Cache Check: `ConversationRepository` checks in-memory cache
5. Context Assembly: Load knowledge base from S3 via `KnowledgeProvider`, construct system prompt
6. Inference: `LLMProvider` sends to Bedrock with context and question
7. Cache Store: Response cached in `ConversationRepository`
8. Usage Update: `StorageProvider` increments DynamoDB counter
9. Response Delivery: Return AI reply to client

## Persistence Strategy

### Ephemeral Data (Not Persisted)

- User questions (logged only)
- AI responses (logged only)
- Request metadata (headers, timestamps)

### Persistent Data

- **Usage records**: DynamoDB with 24-hour TTL
- **Knowledge base**: S3 (manually updated)

### Rationale

- No conversation history needed (stateless design)
- Privacy-friendly (no long-term user data storage)
- Cost-effective (minimal storage requirements)
- Compliance-friendly (automatic data deletion via TTL)

## Domain Constraints

### Business Rules

- One user = one IP address (no authentication)
- Daily limit: 50 requests per user
- Knowledge base is single source of truth
- Responses must be grounded in knowledge base

### Technical Constraints

- DynamoDB eventual consistency acceptable
- S3 knowledge base cached per Lambda instance
- No cross-request state sharing
- Maximum response time: 30 seconds (Lambda timeout)

## Error Handling

### Domain Exceptions

`InvalidQuestionError` (in `shared/exceptions.py`)

- Trigger: Empty or missing question
- HTTP Status: 400

`CORSOriginError` (in `shared/exceptions.py`)

- Trigger: Request from unauthorized origin
- HTTP Status: 403

`RateLimitError` (in `shared/exceptions.py`)

- Trigger: User exceeds 50 requests/day
- HTTP Status: 429

`ChatbotProcessingError` (in `shared/exceptions.py`)

- Trigger: Unexpected errors (Bedrock failures, etc.)
- HTTP Status: 500

## Future Entity Considerations

### Potential Additions

- **Conversation History**: Store multi-turn conversations
- **User Profiles**: Authenticated users with preferences
- **Feedback Records**: Track response quality ratings
- **Analytics Events**: Detailed usage metrics and patterns
- **Model Routing**: Track which model handled each request
