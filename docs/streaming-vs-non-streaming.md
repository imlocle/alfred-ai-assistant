# Streaming vs Non-Streaming: Technical Guide

## Overview

This document explains the difference between `invoke_model()` and `invoke_model_with_response_stream()` in the Bedrock service, and provides guidance on when to use each.

---

## Current Implementation: Non-Streaming

### How It Works

```python
# In LLMProvider (src/providers/llm_provider.py)
def invoke_model(self, system_blocks, messages) -> str:
    response = self.client.invoke_model(...)
    result = json.loads(response["body"].read())
    # Returns complete response at once
    return answer
```

**Flow**:

1. Send request to Bedrock
2. Wait for complete response
3. Parse entire response
4. Return full answer to user

**User Experience**:

- User submits question
- Loading indicator shows
- Complete answer appears all at once

---

## Alternative: Streaming Implementation

### How It Works

```python
# In LLMProvider (src/providers/llm_provider.py)
def invoke_model_with_response_stream(self, system_blocks, messages) -> str:
    response = self.client.invoke_model_with_response_stream(...)

    accumulated_text = ""
    for event in response["body"]:
        chunk = json.loads(event["chunk"]["bytes"])
        if "contentBlockDelta" in chunk:
            delta = chunk["contentBlockDelta"].get("delta", {})
            if "text" in delta:
                accumulated_text += delta["text"]

    return accumulated_text
```

**Flow**:

1. Send request to Bedrock
2. Receive tokens as they're generated
3. Accumulate or stream tokens to user
4. Complete when all tokens received

**User Experience**:

- User submits question
- Answer appears word-by-word (like ChatGPT)
- Feels faster even if total time is similar

---

## Comparison

| Feature             | Non-Streaming (`invoke_model`)  | Streaming (`invoke_model_with_response_stream`) |
| ------------------- | ------------------------------- | ----------------------------------------------- |
| **Response Time**   | Wait for complete response      | See first tokens immediately                    |
| **Perceived Speed** | Slower (wait for everything)    | Faster (progressive display)                    |
| **Implementation**  | Simple                          | More complex                                    |
| **Infrastructure**  | REST API (current setup)        | Requires WebSocket or SSE                       |
| **Caching**         | Easy to cache complete response | Harder to cache partial responses               |
| **Error Handling**  | Simple (all or nothing)         | Complex (partial responses)                     |
| **User Experience** | Loading → Complete answer       | Progressive typing effect                       |
| **Best For**        | Short responses, APIs           | Long responses, conversational UIs              |

---

## When to Use Each

### Use Non-Streaming (Current) When:

✅ Using REST API (API Gateway HTTP API)  
✅ Responses are typically short (< 200 tokens)  
✅ Caching is important  
✅ Simplicity is preferred  
✅ Batch processing or background jobs  
✅ Mobile apps with limited connectivity

### Use Streaming When:

✅ Using WebSocket API  
✅ Responses are long (> 200 tokens)  
✅ User experience is critical  
✅ Building conversational UI  
✅ Want ChatGPT-like typing effect  
✅ Real-time feedback is important

---

## Infrastructure Requirements

### Current Setup (Non-Streaming)

```
User → API Gateway (HTTP) → Lambda → Bedrock
     ← Complete Response ←
```

**Requirements**:

- API Gateway HTTP API ✅ (already have)
- Lambda function ✅ (already have)
- Bedrock access ✅ (already have)

### Streaming Setup

```
User → API Gateway (WebSocket) → Lambda → Bedrock
     ← Token Stream ←
```

**Requirements**:

- API Gateway WebSocket API ❌ (need to add)
- Lambda with streaming support ❌ (need to modify)
- Client-side WebSocket handling ❌ (need to add)
- Connection management ❌ (need to add)

---

## Implementation Complexity

### Non-Streaming (Current)

```python
# Simple implementation
response = bedrock.invoke_model(...)
return parse_response(response)
```

**Complexity**: Low  
**Lines of Code**: ~20  
**Error Handling**: Simple

### Streaming

```python
# Complex implementation
response = bedrock.invoke_model_with_response_stream(...)

# Need to handle:
# - Connection management
# - Partial responses
# - Error recovery mid-stream
# - Client disconnection
# - Timeout handling
# - Buffering

for event in response["body"]:
    chunk = parse_chunk(event)
    yield chunk  # Send to client
    # Handle errors, timeouts, disconnections
```

**Complexity**: High  
**Lines of Code**: ~100+  
**Error Handling**: Complex

---

## Cost Considerations

### Token Costs

Both methods cost the same per token:

- Input tokens: Same price
- Output tokens: Same price

### Infrastructure Costs

**Non-Streaming**:

- API Gateway HTTP: $1.00 per million requests
- Lambda: Pay per invocation + duration
- **Total**: ~$1-2 per million requests

**Streaming**:

- API Gateway WebSocket: $1.00 per million messages + $0.25 per million connection minutes
- Lambda: Pay per invocation + duration (longer due to streaming)
- Connection management overhead
- **Total**: ~$2-4 per million requests (higher due to connection costs)

---

## Recommendation for Your Use Case

### Current Situation

- Using API Gateway HTTP API
- Responses are typically short (Alfred answers about Loc Le)
- Caching is valuable (same questions asked repeatedly)
- Simple infrastructure preferred

### Recommendation: **Stick with Non-Streaming**

**Reasons**:

1. ✅ Your responses are short (< 200 tokens typically)
2. ✅ Caching provides better performance than streaming
3. ✅ Current infrastructure is simpler and cheaper
4. ✅ No need for WebSocket complexity
5. ✅ Mobile-friendly (works with any HTTP client)

### When to Reconsider Streaming

Consider switching to streaming if:

- Responses become longer (> 500 tokens)
- User feedback indicates perceived slowness
- Building a conversational chat interface
- Want to add "typing" effect for better UX
- Have resources to implement WebSocket infrastructure

---

## Migration Path (If Needed)

If you decide to add streaming later:

### Phase 1: Prepare Backend

1. Keep current non-streaming endpoint
2. Add new WebSocket API Gateway
3. Create new Lambda for streaming
4. Test streaming implementation

### Phase 2: Update Frontend

1. Add WebSocket client library
2. Implement progressive rendering
3. Add fallback to non-streaming
4. Test with real users

### Phase 3: Gradual Rollout

1. A/B test streaming vs non-streaming
2. Monitor performance metrics
3. Collect user feedback
4. Decide on default behavior

### Estimated Effort

- Backend: 2-3 days
- Frontend: 2-3 days
- Testing: 1-2 days
- **Total**: 1-2 weeks

---

## Code Example: How to Add Streaming (Future)

If you want to add streaming later, here's the pattern:

### Backend (Lambda)

```python
def lambda_handler(event, context):
    request_type = event.get("requestContext", {}).get("eventType")

    if request_type == "CONNECT":
        return {"statusCode": 200}

    elif request_type == "MESSAGE":
        connection_id = event["requestContext"]["connectionId"]
        question = json.loads(event["body"])["question"]

        # Stream response
        for chunk in stream_answer(question):
            send_to_websocket(connection_id, chunk)

        return {"statusCode": 200}

    elif request_type == "DISCONNECT":
        return {"statusCode": 200}

def stream_answer(question):
    response = bedrock.invoke_model_with_response_stream(...)
    for event in response["body"]:
        chunk = parse_chunk(event)
        yield chunk
```

### Frontend (JavaScript)

```javascript
const ws = new WebSocket(
  "wss://your-api.execute-api.region.amazonaws.com/prod",
);

ws.onopen = () => {
  ws.send(JSON.stringify({ question: "Who is Loc Le?" }));
};

ws.onmessage = (event) => {
  const chunk = JSON.parse(event.data);
  appendToAnswer(chunk.text); // Progressive display
};

ws.onerror = (error) => {
  // Fallback to non-streaming
  fetchNonStreaming(question);
};
```

---

## Performance Comparison

### Scenario: 150-token response

**Non-Streaming**:

- Time to first byte: 2.5 seconds
- Time to complete: 2.5 seconds
- User perception: "Slow" (waiting 2.5s)

**Streaming**:

- Time to first byte: 0.3 seconds
- Time to complete: 2.5 seconds
- User perception: "Fast" (seeing progress immediately)

**With Caching (Non-Streaming)**:

- Time to first byte: 0.1 seconds
- Time to complete: 0.1 seconds
- User perception: "Instant"

**Winner**: Non-streaming with caching (which you now have!)

---

## Conclusion

For your Alfred chatbot:

- ✅ **Current approach (non-streaming) is optimal**
- ✅ **Caching provides better performance than streaming**
- ✅ **Simpler infrastructure is more maintainable**
- ✅ **Lower costs**
- ✅ **Better mobile support**

The streaming implementation is fixed and available if needed, but there's no compelling reason to use it for your use case. The response caching you now have provides better performance than streaming would.

---

## Additional Resources

- [AWS Bedrock Streaming Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/model-parameters-streaming.html)
- [API Gateway WebSocket APIs](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-websocket-api.html)
- [Lambda Streaming Response](https://aws.amazon.com/blogs/compute/introducing-aws-lambda-response-streaming/)
