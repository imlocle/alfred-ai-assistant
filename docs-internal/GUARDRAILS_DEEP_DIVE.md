# Guardrails Deep Dive

**Purpose**: Comprehensive analysis of all safety mechanisms.  
**Audience**: Security, product, engineering  
**Updated**: March 2026

---

## Five-Layer Guardrail System

### Layer 1: CORS Validation

- Only allows requests from approved origins
- Current: `https://imlocle.com`, `http://localhost:5173`
- Rejects cross-origin requests from unknown domains

### Layer 2: Input Sanitization

- Removes control characters (null bytes, etc.)
- Normalizes whitespace
- Enforces max length (2,000 chars)
- See [Validators](../src/shared/validators.py)

### Layer 3: Rate Limiting

- 50 requests per IP per day
- DynamoDB TTL-based reset
- Returns HTTP 429 (Too Many Requests)

### Layer 4: System Prompt Injection

- Strict system message limiting scope to Loc Le
- Knowledge base injected at inference time
- Hard refusal pattern for off-topic questions

### Layer 5: Model Configuration

- Low temperature (0.2): Deterministic, focused responses
- Max tokens (200): Prevents verbose outputs
- Inference settings tuned for stability

## Effectiveness Analysis

**Test Coverage**: 99 unit tests validate all guardrails  
**Failure Rate**: 0% (all tests pass)  
**Real-World Validation**: Deployed in production with no breaches

---

See [DEVELOPMENT.md](../docs/DEVELOPMENT.md) for end-user safety features.

**Last Updated**: March 2026
