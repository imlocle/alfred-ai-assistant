# API Documentation

Complete specification for the Alfred AI Assistant HTTP API.

## Base URL

```
POST https://{api-endpoint}/chat
```

## Authentication

Currently **no authentication** required. Protection is enforced via:

- CORS origin whitelist
- Rate limiting (per user ID)
- Input validation

**Future**: API keys or OAuth authentication may be added.

---

## Endpoints

### Chat Endpoint

**Submit a question and receive an AI response**

#### Request

```http
POST /chat HTTP/1.1
Host: {api-endpoint}
Content-Type: application/json
Origin: https://locle.dev

{
  "question": "What are your main services?",
  "userId": "user123",
  "currentDate": "2026-03-12",
  "origin": "https://locle.dev"
}
```

#### Request Parameters

| Parameter     | Type   | Required | Description                                                                            |
| ------------- | ------ | -------- | -------------------------------------------------------------------------------------- |
| `question`    | string | ✓ Yes    | The question to ask Alfred. Min length: 3 characters                                   |
| `userId`      | string | ✓ Yes    | Unique user identifier for rate limiting and tracking                                  |
| `currentDate` | string | ✓ Yes    | Current date in `YYYY-MM-DD` format. Used for rate limit bucketing                     |
| `origin`      | string | ✗ No     | Request origin. Validated against CORS whitelist. Falls back to HTTP header if omitted |

#### Request Validation

```python
# Question validation
- Length: >= 3 characters
- Not empty or whitespace-only
- Not null

# userId validation
- Required and non-empty
- String format

# currentDate validation
- Format: YYYY-MM-DD
- Valid date (no 2026-13-45)

# origin validation
- Must match CORS whitelist (configured in environment)
- Example: https://locle.dev, https://locleprojects.dev
```

---

#### Response

**Success Response (200 OK)**

```json
{
  "body": {
    "reply": "I'm a backend-focused cloud engineer with 6+ years of experience designing scalable systems on AWS..."
  }
}
```

**Structure**:

```
{
  "body": {
    "reply": "string - AI-generated response"
  }
}
```

---

#### Error Responses

##### 400 Bad Request - Invalid Question

```json
{
  "error": "I am sorry, but that was an invalid question. Please ask another."
}
```

**Causes**:

- Question is empty or too short (< 3 characters)
- Question is whitespace-only
- Missing required parameter

---

##### 403 Forbidden - CORS Origin Error

```json
{
  "error": "I am sorry, but you are chatting with me from a different place. Please continue this conversation through Loc's website."
}
```

**Causes**:

- Request origin not in CORS whitelist
- Origin header missing and not provided in request body
- Origin validation failed

**Resolution**: Contact administrator to whitelist origin

---

##### 429 Too Many Requests - Rate Limit Exceeded

```json
{
  "error": "I am sorry, but you have too many queries. Please try again tomorrow."
}
```

**Causes**:

- Daily request quota exceeded for user ID
- Rate limit: 3 requests per user per day (configurable)

**Reset**: Limit resets at midnight UTC daily

**Tracking**: Based on `currentDate` parameter. If date changes, new quota applies.

---

##### 500 Internal Server Error

```json
{
  "error": "Something went wrong on our end. Please try again later."
}
```

**Causes**:

- Lambda processing error
- Bedrock service unavailable
- Knowledge base not accessible
- Unexpected exception in handlers

**Recovery**: Usually transient. Retry after 30 seconds.

---

##### 503 Service Unavailable

```json
{
  "error": "We are temporarily unavailable. Please try again later."
}
```

**Causes**:

- AWS Bedrock is down or overloaded
- DynamoDB throttling
- API Gateway throttling

**Recovery**: Retry with exponential backoff (1s, 2s, 4s, 8s)

---

## Examples

### Example 1: Simple Question

**Request**:

```bash
curl -X POST https://api.locle.dev/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is your experience?",
    "userId": "user-001",
    "currentDate": "2026-03-12"
  }'
```

**Response**:

```json
{
  "body": {
    "reply": "I'm a Senior Cloud Software Engineer with 6+ years of experience designing and building production-grade systems on AWS. My expertise spans backend architecture, cloud infrastructure, data engineering, and AI/LLM integrations. I've worked with scaling systems, cost optimization, and building systems that reliably serve millions of requests without constant firefighting."
  }
}
```

---

### Example 2: Scheduling Request

**Request**:

```bash
curl -X POST https://api.locle.dev/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Can I schedule a meeting with you?",
    "userId": "user-002",
    "currentDate": "2026-03-12"
  }'
```

**Response**:

```json
{
  "body": {
    "reply": "You can schedule a meeting with Loc here: [Book a time with Loc on Calendly](https://calendly.com/locle/)"
  }
}
```

---

### Example 3: Rate Limited

**Request** (4th request for user-001 on same day):

```bash
curl -X POST https://api.locle.dev/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "One more question",
    "userId": "user-001",
    "currentDate": "2026-03-12"
  }'
```

**Response** (429):

```json
{
  "error": "I am sorry, but you have too many queries. Please try again tomorrow."
}
```

---

### Example 4: Invalid Question

**Request**:

```bash
curl -X POST https://api.locle.dev/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Hi",
    "userId": "user-003",
    "currentDate": "2026-03-12"
  }'
```

**Response** (400):

```json
{
  "error": "I am sorry, but that was an invalid question. Please ask another."
}
```

---

### Example 5: CORS Origin Error

**Request** (from unauthorized origin):

```bash
curl -X POST https://api.locle.dev/chat \
  -H "Content-Type: application/json" \
  -H "Origin: https://unauthorized.com" \
  -d '{
    "question": "What is your experience?",
    "userId": "user-004",
    "currentDate": "2026-03-12"
  }'
```

**Response** (403):

```json
{
  "error": "I am sorry, but you are chatting with me from a different place. Please continue this conversation through Loc's website."
}
```

---

## Client Implementation

### JavaScript / TypeScript

```typescript
async function askAlfred(
  question: string,
  userId: string,
  currentDate: string,
  origin: string = window.location.origin,
): Promise<string> {
  const response = await fetch("https://api.locle.dev/chat", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question,
      userId,
      currentDate,
      origin,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || "Unknown error");
  }

  const data = await response.json();
  return data.body.reply;
}

// Usage
try {
  const reply = await askAlfred(
    "What are your main services?",
    "user-123",
    new Date().toISOString().split("T")[0],
  );
  console.log(reply);
} catch (error) {
  console.error("Failed to get response:", error.message);
}
```

---

### Python

```python
import requests
from datetime import date

def ask_alfred(question: str, user_id: str, current_date: str = None) -> str:
    """Ask Alfred a question."""
    if current_date is None:
        current_date = date.today().isoformat()

    response = requests.post(
        'https://api.locle.dev/chat',
        json={
            'question': question,
            'userId': user_id,
            'currentDate': current_date,
        },
        headers={
            'Content-Type': 'application/json',
        }
    )

    response.raise_for_status()
    return response.json()['body']['reply']

# Usage
try:
    reply = ask_alfred(
        'What are your main services?',
        'user-123'
    )
    print(reply)
except requests.exceptions.HTTPError as e:
    print(f'Error: {e.response.json()}')
```

---

## Rate Limiting

### Daily Quota

- **Default**: 3 requests per user per day
- **Reset**: Midnight UTC
- **Tracking**: Per `userId` per `currentDate`

### Quota Tracking Example

```
User ID: user-001
Date: 2026-03-12

Request 1: 09:00 AM → Success
Request 2: 02:00 PM → Success
Request 3: 05:00 PM → Success
Request 4: 09:00 PM → Rejected (429)

Date: 2026-03-13  ← New day, quota resets
Request 1: 08:00 AM → Success
```

### Headers

Response headers include rate limit information:

```
X-RateLimit-Limit: 3
X-RateLimit-Remaining: 1
X-RateLimit-Reset: 1678300800
```

---

## Caching

### Response Caching

- Identical questions return cached responses
- Cache TTL: 30 days
- Cache key: Hash of question string
- Benefits: Reduced latency, lower Bedrock costs

### Cache Invalidation

- Manual: Restart Lambda function
- Automatic: After TTL expires
- Scheduled: Clear cache nightly (if configured)

---

## CORS Configuration

### Whitelisted Origins

- `https://locle.dev`
- `https://www.locle.dev`
- `https://locleprojects.dev`
- `https://www.locleprojects.dev`
- (Others configured in `ALLOWED_ORIGINS` environment variable)

### CORS Headers

Request must include valid origin:

```
Origin: https://locle.dev
```

Response includes CORS headers:

```
Access-Control-Allow-Origin: https://locle.dev
Access-Control-Allow-Methods: POST
Access-Control-Allow-Headers: Content-Type
```

---

## Performance Considerations

### Latency

| Scenario          | Latency            |
| ----------------- | ------------------ |
| Cache hit         | <50ms              |
| Warm Lambda + LLM | 1000-2000ms        |
| Cold Lambda + LLM | 3000-5000ms        |
| Bedrock timeout   | 60,000ms (timeout) |

### Optimization Tips

1. **Reuse userId**: Ensures consistent rate limiting and caching
2. **Batch questions**: Space out requests to avoid rate limiting
3. **Improve questions**: Longer, more specific questions → better responses
4. **Cache locally**: Store responses in client for repeated questions

---

## Troubleshooting

### Common Issues

#### Q: Getting "Invalid Question" for valid questions

- **A**: Check question length (minimum 3 characters)
- **A**: Ensure no leading/trailing whitespace
- **A**: Verify special characters aren't being filtered

#### Q: Getting "Too Many Requests"

- **A**: Check `userId` - ensure you're using consistent ID per user
- **A**: Verify `currentDate` is correct (should be today's date)
- **A**: Wait until next day for quota reset (or contact admin)

#### Q: Getting CORS error

- **A**: Check `origin` parameter matches whitelisted domain
- **A**: Verify Origin header is being sent by client
- **A**: Contact admin to whitelist new origin

#### Q: Getting "Service Unavailable"

- **A**: Transient issue - retry with exponential backoff
- **A**: Check AWS status page for Bedrock region outages

---

## Rate Limits & Quotas

| Limit                       | Value                               |
| --------------------------- | ----------------------------------- |
| Daily requests per user     | 3                                   |
| Concurrent Lambda instances | Account-level quota (default: 1000) |
| API Gateway throttle        | 10,000 requests/second              |
| Bedrock token throughput    | Account-level quota                 |

---

## Response Headers

All responses include standard HTTP headers:

```
Content-Type: application/json
Content-Length: {size}
Date: {timestamp}
X-Amzn-RequestId: {correlation-id}
X-Amz-Apigw-Integration-Latency: {ms}
```

---

## Deprecated Endpoints

None at this time. All endpoints are production-ready.

---

## API Versioning

Currently at **v1** (implicit). Breaking changes will increment version number in URL path.

---

## Support

For API issues or questions:

- Email: support@locle.dev
- Documentation: https://docs.locle.dev
- Status: https://status.locle.dev
