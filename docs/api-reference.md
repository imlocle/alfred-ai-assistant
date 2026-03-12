# API Reference

## Overview

Alfred exposes a single HTTP API endpoint for chat interactions. The API is built on AWS API Gateway (HTTP API) with Lambda integration and follows RESTful conventions.

**Base URL**: Provided by Terraform output (`api_endpoint_url`)

**Protocol**: HTTPS only

**Authentication**: None (rate limiting via IP address)

---

## Endpoints

### POST /ask

Submit a question to Alfred and receive an AI-generated response.

#### Request

**Method**: `POST`

**URL**: `{base_url}/ask`

**Headers**:

```
Content-Type: application/json
Origin: https://imlocle.com (or allowed origin)
```

**Body**:

```json
{
  "question": "string (required)"
}
```

**Parameters**:

- `question` (string, required): The user's question. Must not be empty.

**Example Request**:

```bash
curl -X POST https://api.example.com/ask \
  -H "Content-Type: application/json" \
  -H "Origin: https://imlocle.com" \
  -d '{"question": "What services does Loc offer?"}'
```

#### Response

**Success Response** (200 OK):

```json
{
  "reply": "string"
}
```

**Fields**:

- `reply` (string): The AI-generated response, may contain markdown formatting

**Example Success Response**:

```json
{
  "reply": "Loc offers three service packages:\n\n1. **MVP Core** ($2,500) - API endpoints, authentication, database setup, AWS deployment\n2. **MVP + AI** ($3,500) - Everything in MVP Core plus LLM integration\n3. **MVP + Support** ($4,000) - Everything in MVP Core plus 30 days post-launch support"
}
```

#### Error Responses

**400 Bad Request** - Invalid or empty question

```json
{
  "reply": "I am sorry, but that was an invalid question. Please ask another."
}
```

**403 Forbidden** - Unauthorized origin

```json
{
  "reply": "I am sorry, but you are chatting with me from a different place. Please continue this conversation through Loc's website."
}
```

**429 Too Many Requests** - Rate limit exceeded

```json
{
  "reply": "I apologize, but you have reached the limit for today. Please come back tomorrow."
}
```

**500 Internal Server Error** - Server error

```json
{
  "reply": "My apologies, I am currently unavailable. Please come back soon."
}
```

---

## CORS Configuration

The API supports Cross-Origin Resource Sharing (CORS) for browser-based clients.

**Allowed Origins**:

- `http://localhost:5173` (development)
- `https://imlocle.com` (production)
- `https://imlocle.github.io` (GitHub Pages)

**Allowed Methods**:

- `OPTIONS` (preflight)
- `POST`

**Allowed Headers**:

- `Content-Type`
- `X-Amz-Date`
- `Authorization`

**Max Age**: 3600 seconds (1 hour)

**Preflight Request Example**:

```bash
curl -X OPTIONS https://api.example.com/ask \
  -H "Origin: https://imlocle.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type"
```

**Preflight Response**:

```
Access-Control-Allow-Origin: https://imlocle.com
Access-Control-Allow-Methods: OPTIONS,POST
Access-Control-Allow-Headers: Content-Type,X-Amz-Date,Authorization
Access-Control-Max-Age: 3600
```

---

## Rate Limiting

**Limit**: 50 requests per day per IP address

**Identification**: Based on `x-forwarded-for` header (IP address)

**Reset**: Automatic at midnight UTC via DynamoDB TTL

**Behavior**:

- Requests 1-50: Normal processing
- Request 51+: HTTP 429 with error message
- Next day: Counter resets automatically

**Rate Limit Headers**: Not currently implemented (future enhancement)

---

## Special Behaviors

### Scheduling Detection

If the question contains keywords related to scheduling (schedule, book, meeting, call, appointment), Alfred returns a direct Calendly link:

**Example**:

```json
{
  "question": "Can I schedule a call with Loc?"
}
```

**Response**:

```json
{
  "reply": "You can schedule a meeting with Loc here: [Book a time with Loc on Calendly](https://calendly.com/loc-le/30-min-meeting)"
}
```

### Markdown Formatting

Responses may include markdown formatting:

- **Bold**: `**text**`
- _Italic_: `*text*`
- Lists: `1. item` or `- item`
- Links: `[text](url)`
- Code: `` `code` ``

Clients should render markdown appropriately.

---

## Request/Response Examples

### Example 1: Service Inquiry

**Request**:

```json
{
  "question": "What is the MVP Core package?"
}
```

**Response**:

```json
{
  "reply": "The MVP Core package is priced at $2,500 and is best for validating ideas quickly. It includes API endpoints, authentication, database setup, AWS deployment, and documentation with handoff."
}
```

### Example 2: Technical Question

**Request**:

```json
{
  "question": "Explain how Alfred works"
}
```

**Response**:

```json
{
  "reply": "Alfred is a production AI assistant built on AWS. The architecture follows this flow:\n\n1. User submits question through React frontend\n2. API Gateway routes to Lambda function\n3. Lambda checks rate limits in DynamoDB\n4. System prompt and knowledge base are injected\n5. AWS Bedrock (Nova model) generates response\n6. Usage counter is updated\n7. Response returns to frontend\n\nKey features include strict guardrails, rate limiting (50 requests/day), and cost-aware inference settings."
}
```

### Example 3: Out-of-Scope Question

**Request**:

```json
{
  "question": "How do I write a Python function?"
}
```

**Response**:

```json
{
  "reply": "I appreciate your question, but I am here specifically to assist with inquiries about Mr. Loc Le—his background, experience, projects, and services. For general programming assistance, I would recommend consulting Python documentation or developer communities."
}
```

### Example 4: Rate Limit Exceeded

**Request** (51st request of the day):

```json
{
  "question": "Tell me about Neptune"
}
```

**Response** (429):

```json
{
  "reply": "I apologize, but you have reached the limit for today. Please come back tomorrow."
}
```

---

## Error Handling

All errors return a consistent JSON structure with a `reply` field containing a user-friendly message.

**Error Response Structure**:

```json
{
  "reply": "string (error message)"
}
```

**HTTP Status Codes**:

- `200`: Success
- `400`: Bad request (invalid input)
- `403`: Forbidden (CORS violation)
- `429`: Too many requests (rate limit)
- `500`: Internal server error

**Client Recommendations**:

- Handle all error status codes gracefully
- Display error messages to users
- Implement retry logic with exponential backoff for 500 errors
- Do not retry 429 errors (wait until next day)
- Do not retry 403 errors (origin not allowed)

---

## Integration Guide

### JavaScript/TypeScript Example

```typescript
async function askAlfred(question: string): Promise<string> {
  const response = await fetch("https://api.example.com/ask", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.reply || "Request failed");
  }

  const data = await response.json();
  return data.reply;
}

// Usage
try {
  const reply = await askAlfred("What services does Loc offer?");
  console.log(reply);
} catch (error) {
  console.error("Error:", error.message);
}
```

### Python Example

```python
import requests

def ask_alfred(question: str) -> str:
    url = 'https://api.example.com/ask'
    headers = {'Content-Type': 'application/json'}
    payload = {'question': question}

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        return response.json()['reply']
    else:
        raise Exception(response.json()['reply'])

# Usage
try:
    reply = ask_alfred('What services does Loc offer?')
    print(reply)
except Exception as e:
    print(f'Error: {e}')
```

---

## Performance Characteristics

**Typical Response Time**: 2-5 seconds

- Cold start: 3-8 seconds (first request after idle period)
- Warm Lambda: 2-4 seconds

**Timeout**: 30 seconds (Lambda timeout)

**Payload Limits**:

- Request body: 10 MB (API Gateway limit)
- Response body: 10 MB (API Gateway limit)
- Practical question length: ~2000 characters

**Concurrency**: Unlimited (Lambda auto-scales)

---

## Monitoring and Debugging

CloudWatch Logs use structured JSON format with request correlation:

```json
{
  "timestamp": "2026-03-06T12:00:00.000Z",
  "level": "INFO",
  "message": "Question received",
  "module": "query_controller",
  "request_id": "abc-123",
  "user_id": "192.168.1.1",
  "question_length": 42
}
```

Debugging tips:

- Check CloudWatch logs for the Lambda function
- Filter by `request_id` to trace a single request end-to-end
- Verify CORS headers in browser developer tools
- Test with curl to isolate client-side issues
- Check DynamoDB for usage records

---

## Future API Enhancements

- Streaming responses via WebSocket or Server-Sent Events
- Rate limit headers (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`)
- Conversation history for multi-turn conversations
- Authentication for higher rate limits
- API versioning (`/v1/ask`, `/v2/ask`)
