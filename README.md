# Alfred — AI Assistant Platform

Alfred is a **production-style AI assistant platform** built on AWS that demonstrates real-world GenAI system design, infrastructure-as-code, and strict LLM guardrails.

It is intentionally **not a general-purpose chatbot**.  
Alfred is constrained to answer questions only about a specific subject (Loc Le) using a controlled knowledge base, enforced refusal behavior, rate limiting, and cost-aware inference settings.

This project showcases how to build **safe, scalable, and low-cost AI systems** suitable for production environments.

## Why Alfred Exists

Most AI demos stop at “it works.”

Alfred was built to demonstrate:

- **Production-ready GenAI architecture**
- **LLM guardrails and scope control**
- **Infrastructure-as-code with Terraform**
- **Cost-aware model selection and inference tuning**
- **Multi-user safety via rate limiting and usage tracking**

This mirrors the types of systems I’ve built professionally for enterprise and startup environments.

## Architecture Overview

**Request Flow**

Client
→ API Gateway
→ Lambda (Handler)
→ Controller
→ Service
→ Repository
→ DynamoDB (usage tracking)
→ AWS Bedrock (LLM inference)

**Key Characteristics**

- Layered backend architecture
- Deterministic request/response flow
- No async orchestration for chat (low-latency UX)
- Infrastructure fully managed via Terraform

## Guardrails & Safety

Alfred is intentionally constrained to prevent hallucinations and off-topic behavior.

### Guardrail Mechanisms

- **Strict system prompt** limiting scope to Loc Le only
- **Hard refusal pattern** for all unrelated questions
- **Knowledge base injected directly into system context**
- **Inference configuration tuned for stability**
  - `maxTokens: 200`
  - `temperature: 0.2`
- **Daily rate limiting**
  - Per-IP usage counters stored in DynamoDB
  - TTL-based reset (e.g. 50 requests/day/IP)

This ensures predictable behavior, low cost, and safe public exposure.

## Model Strategy

Alfred currently uses **AWS Bedrock with Nova**.

### Why Nova?

- Extremely low operating cost
- Suitable for constrained, deterministic assistants
- Ideal for experimentation without cost spikes

### Model Flexibility

The system is **model-agnostic**:

- Model ID is configuration-driven
- **Can be swapped to Anthropic (Claude) or other Bedrock models without refactoring**
- Architecture supports future multi-model routing

Nova is a **cost decision**, not a technical limitation.

## Technologies

- **Languages**: Python
- **AI / GenAI**:
  - AWS Bedrock
  - Nova Foundation Model
  - Prompt Engineering
  - LLM Guardrails
- **Cloud & Infrastructure**:
  - AWS Lambda
  - API Gateway
  - DynamoDB
  - S3
  - Terraform
- **Architecture**:
  - Serverless
  - Layered backend design
  - IP-based rate limiting

## Knowledge Base

Alfred consumes a structured knowledge base stored in S3.

### Uploading the Knowledge Base

```bash
aws s3 cp knowledge_base.json s3://<BUCKET_NAME>/knowledge_base.json
```

### Example `knowledge_base.json`

```
{
  "personal_info": {
    "first_name": "Loc",
    "last_name": "Le",
    "role": "Senior Cloud Software Engineer",
    "location": "Las Vegas, NV"
  },
  "projects": [],
  "services": [],
  "contact_info": {}
}
```

The knowledge base is injected directly into the LLM system context at inference time.

## Deployment

Alfred is deployed via Terraform and Make

```
make clean && make deploy ENV=dev
```

## Extensibility & Next Steps

### Planned Enhancements:

- Streaming responses using `invoke_model_with_response_stream`

- Multi-model routing (Nova vs Anthropic)

- Enhanced observability (token usage, latency)

- Reuse of this architecture for future product chatbots (e.g. Neptune)

## Resources

- [AWS Bedrock InvokeModel](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_InvokeModel.html)

- [AWS Bedrock Streaming Responses](https://docs.aws.amazon.com/bedrock/latest/userguide/model-streaming.html)

- [Nova Foundation Models](https://docs.aws.amazon.com/nova/latest/userguide/what-is-nova.html)
