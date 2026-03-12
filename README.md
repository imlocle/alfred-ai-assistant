# Alfred — AI Assistant Platform

Alfred is a **production-style AI assistant platform** built on AWS that demonstrates real-world GenAI system design, infrastructure-as-code, and strict LLM guardrails.

It is intentionally **not a general-purpose chatbot**.  
Alfred is constrained to answer questions only about a specific subject (Loc Le) using a controlled knowledge base, enforced refusal behavior, rate limiting, and cost-aware inference settings.

This project showcases how to build **safe, scalable, and low-cost AI systems** suitable for production environments.

## Why Alfred Exists

Most AI demos stop at "it works."

Alfred was built to demonstrate:

- **Production-ready GenAI architecture**
- **LLM guardrails and scope control**
- **Infrastructure-as-code with Terraform**
- **Cost-aware model selection and inference tuning**
- **Multi-user safety via rate limiting and usage tracking**

This mirrors the types of systems I've built professionally for enterprise and startup environments.

## Architecture Overview

**Request Flow**

```
Client
→ API Gateway (HTTP API)
→ Lambda (AssistantHandler)
→ QueryController (validation, CORS)
→ AssistantService (orchestration)
→ AssistantAgent (AI logic) + ConversationRepository (caching, usage tracking)
→ LLMProvider (Bedrock) + StorageProvider (DynamoDB) + KnowledgeProvider (S3)
```

**Project Structure**

```
src/
├── handlers/
│   └── assistant_handler.py          # Lambda entry point
├── controllers/
│   └── query_controller.py           # Request validation & routing
├── services/
│   └── assistant_service.py          # Business logic orchestration
├── agents/
│   └── assistant_agent.py            # AI logic: prompts, routing, LLM calls
├── repositories/
│   └── conversation_repository.py    # Caching & usage tracking
├── providers/
│   ├── llm_provider.py               # Bedrock wrapper
│   ├── storage_provider.py           # DynamoDB wrapper
│   └── knowledge_provider.py         # S3 wrapper
└── shared/
    ├── config.py                     # Constants
    ├── exceptions.py                 # Custom errors
    ├── validators.py                 # Input sanitization
    ├── logging.py                    # Structured JSON logging
    └── responses.py                  # HTTP response formatting
```

**Key Characteristics**

- Layered backend architecture with clear separation of concerns
- Agent-centric pattern: AI logic separated from data access
- Deterministic request/response flow
- Infrastructure fully managed via Terraform

## Guardrails & Safety

Alfred is intentionally constrained to prevent hallucinations and off-topic behavior.

### Guardrail Mechanisms

- **Strict system prompt** limiting scope to Loc Le only
- **Hard refusal pattern** for all unrelated questions
- **Knowledge base injected directly into system context**
- **Input sanitization** (control character removal, length limits)
- **Inference configuration tuned for stability**
  - `maxTokens: 200`
  - `temperature: 0.2`
- **Daily rate limiting**
  - Per-IP usage counters stored in DynamoDB
  - TTL-based reset (50 requests/day/IP)
- **Response caching** (1-hour TTL, 30-50% cost reduction)

This ensures predictable behavior, low cost, and safe public exposure.

## Model Strategy

Alfred currently uses **AWS Bedrock with Nova Lite**.

### Why Nova?

- Extremely low operating cost
- Suitable for constrained, deterministic assistants
- Ideal for experimentation without cost spikes

### Model Flexibility

The system is **model-agnostic**:

- Model ID is configuration-driven via environment variable (`MODEL_ID`)
- Uses Bedrock inference profile format (e.g., `us.amazon.nova-lite-v1:0`)
- **Can be swapped to Anthropic (Claude) or other Bedrock models without refactoring**
- IAM policy supports all foundation models and inference profiles across regions
- Architecture supports future multi-model routing

Nova is a **cost decision**, not a technical limitation.

## Technologies

- **Languages**: Python 3.13
- **AI / GenAI**:
  - AWS Bedrock
  - Nova Lite Foundation Model
  - Prompt Engineering
  - LLM Guardrails
- **Cloud & Infrastructure**:
  - AWS Lambda (serverless compute)
  - API Gateway (HTTP API)
  - DynamoDB (usage tracking with TTL)
  - S3 (knowledge base storage)
  - CloudWatch (structured JSON logging, alarms)
  - Terraform (infrastructure as code)
- **Architecture**:
  - Serverless
  - Layered backend design (Handler → Controller → Service → Agent/Repository → Providers)
  - Agent-centric pattern
  - IP-based rate limiting
  - Response caching

## Knowledge Base

Alfred consumes a structured knowledge base stored in S3.

### Uploading the Knowledge Base

```bash
aws s3 cp knowledge_base.json s3://alfred-knowledge-bucket/knowledge_base.json
```

### Example `knowledge_base.json`

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
  },
  "projects": [],
  "contact_info": {}
}
```

The knowledge base is injected directly into the LLM system context at inference time.

## Deployment

### Prerequisites

- AWS CLI configured with credentials
- Docker installed (for Lambda layer builds)
- Terraform installed
- S3 bucket for Terraform state: `alfred-terraform-state-bucket`

### Create Terraform State Bucket (First Time Only)

```bash
aws s3 mb s3://alfred-terraform-state-bucket --region us-west-1
aws s3api put-bucket-versioning \
  --bucket alfred-terraform-state-bucket \
  --versioning-configuration Status=Enabled
```

### Deploy

```bash
make clean && make deploy ENV=dev
```

This will:

1. Clean previous builds
2. Build Lambda layer using Docker (Amazon Linux 2 compatible)
3. Zip Lambda function code
4. Generate Terraform backend config
5. Initialize Terraform with remote state
6. Apply infrastructure changes

### Deploy to Different Environments

```bash
make deploy ENV=dev      # Development
make deploy ENV=staging  # Staging
make deploy ENV=prod     # Production
```

### Get API Endpoint

```bash
terraform -chdir=terraform output api_endpoint_url
```

### Upload Knowledge Base

```bash
aws s3 cp knowledge_base.json s3://alfred-knowledge-bucket/knowledge_base.json
```

## Testing

```bash
# Test the API
curl -X POST https://your-api-endpoint.execute-api.us-west-1.amazonaws.com/ask \
  -H "Content-Type: application/json" \
  -H "Origin: https://imlocle.com" \
  -d '{"question": "What services does Loc offer?"}'
```

## Monitoring

### CloudWatch Logs

Structured JSON logs with request correlation:

```bash
aws logs tail /aws/lambda/alfred-assistant-dev --follow
```

### CloudWatch Alarms

- Lambda errors: >10 errors in 5 minutes
- Lambda duration: >10 second average
- Lambda throttles: >5 throttles in 5 minutes

## Cost Optimization

- **Nova Lite**: Lowest-cost Bedrock model
- **Response caching**: 30-50% reduction in LLM calls
- **Token limits**: Max 200 tokens per response
- **Rate limiting**: Prevents abuse
- **Pay-per-request**: No idle costs
- **Log retention**: 30 days (prevents indefinite storage)

**Estimated cost**: ~$0.50-1.00/month for 1000 requests

## Extensibility & Next Steps

See `docs/ideas-improvements.md` for the full roadmap.

### Immediate Enhancements

- Add comprehensive unit tests
- Implement health check endpoint
- Add custom CloudWatch metrics
- Set up CI/CD pipeline

### Future Platform Evolution

- Multi-agent orchestration
- Streaming responses via WebSocket
- Conversation history and context
- Agent marketplace
- Enterprise features (multi-tenancy, RBAC)

## Documentation

- `docs/architecture-overview.md` - Detailed architecture
- `docs/api-reference.md` - API documentation
- `docs/infrastructure-and-deployment.md` - Ops guide
- `docs/CHANGELOG.md` - Version history
- `docs/ideas-improvements.md` - Future roadmap

## Resources

- [AWS Bedrock InvokeModel](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_InvokeModel.html)
- [AWS Bedrock Streaming Responses](https://docs.aws.amazon.com/bedrock/latest/userguide/model-streaming.html)
- [Nova Foundation Models](https://docs.aws.amazon.com/nova/latest/userguide/what-is-nova.html)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
