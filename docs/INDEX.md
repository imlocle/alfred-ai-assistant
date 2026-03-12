# Documentation Index

**Complete documentation for the Alfred AI Assistant project.**

---

## 📚 Documentation Overview

This is your comprehensive guide to understanding, developing, deploying, and operating Alfred.

---

## 🚀 Getting Started

**New to Alfred?** Start here:

1. **[README.md](../README.md)** (5 min read)
   - Project overview and purpose
   - Quick feature list
   - Why Alfred exists

2. **[ARCHITECTURE.md](ARCHITECTURE.md)** (15 min read)
   - System design and components
   - Data flow
   - AWS services used

3. **[API.md](API.md)** (10 min read)
   - How to use the API
   - Request/response examples
   - Error handling

---

## 👨‍💻 For Developers

**Want to develop locally or contribute?**

1. **[DEVELOPMENT.md](DEVELOPMENT.md)** (30 min + setup)
   - Local environment setup
   - Running tests
   - Development workflow
   - IDE configuration
   - Debugging tips

2. **[CONTRIBUTING.md](CONTRIBUTING.md)** (10 min read)
   - How to contribute
   - Code style guidelines
   - PR process
   - Branch naming conventions

---

## 🔧 For DevOps / Infrastructure

**Need to deploy or maintain infrastructure?**

1. **[DEPLOYMENT.md](DEPLOYMENT.md)** (45 min read)
   - Infrastructure overview
   - Step-by-step deployment
   - Rollback procedures
   - Scaling strategies
   - Monitoring and alarms

2. **[CONFIGURATION.md](CONFIGURATION.md)** (15 min read)
   - Environment variables
   - Configuration files
   - Different profiles (dev/staging/prod)
   - Secrets management

3. **[COST-OPTIMIZATION.md](COST-OPTIMIZATION.md)** (20 min read)
   - Cost breakdown
   - Optimization strategies
   - Model selection
   - Caching optimization
   - Monitoring costs

---

## 🔒 Security & Operations

**Security conscious? Need to understand safeguards?**

1. **[GUARDRAILS.md](GUARDRAILS.md)** (20 min read)
   - System prompt guardrails
   - Rate limiting mechanisms
   - CORS protection
   - Input validation
   - Prompt injection prevention
   - Audit logging

2. **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** (Reference)
   - Common errors and solutions
   - Lambda errors
   - Bedrock issues
   - DynamoDB problems
   - Performance troubleshooting

---

## 📋 Quick Reference

### Commands

```bash
# Development
make format              # Format code
make lint               # Check linting
make type-check         # Type checking
make test               # Run tests
make check              # All checks

# Deployment
terraform init          # Initialize
terraform plan          # Dry-run
terraform apply         # Deploy

# Monitoring
aws logs tail /aws/lambda/alfred-assistant-handler --follow
aws lambda get-function --function-name alfred-assistant-handler
```

### Environment Variables

```bash
AWS_REGION=us-east-1
MODEL_ID=us.amazon.nova-lite-v1:0
RATE_LIMIT_DAILY=3
LOG_LEVEL=INFO
ALLOWED_ORIGINS=https://locle.dev
```

### Key Files

```
src/
  handlers/assistant_handler.py      # Lambda entry point
  controllers/query_controller.py    # Validation & routing
  services/assistant_service.py      # Business logic
  agents/assistant_agent.py          # AI logic
  repositories/                      # Data access
  providers/                         # External services
  shared/config.py                   # Configuration

terraform/
  main.tf                            # Infrastructure
  modules/
    api/                             # API Gateway
    lambda/                          # Lambda config
    dynamodb/                        # Database tables
```

---

## 📊 Architecture at a Glance

```
Client
  ↓
API Gateway (HTTP)
  ↓
Lambda (Python)
  ├─ QueryController (validate)
  ├─ AssistantService (orchestrate)
  │   ├─ AssistantAgent (AI logic)
  │   ├─ LLMProvider (Bedrock)
  │   └─ StorageProvider (DynamoDB)
  └─ Error handling
  ↓
Response
```

---

## 🔄 Common Tasks

### I want to...

| Goal                  | Document                                                              | Time    |
| --------------------- | --------------------------------------------------------------------- | ------- |
| Understand the system | [ARCHITECTURE.md](ARCHITECTURE.md)                                    | 15 min  |
| Set up locally        | [DEVELOPMENT.md](DEVELOPMENT.md)                                      | 30 min  |
| Deploy to AWS         | [DEPLOYMENT.md](DEPLOYMENT.md)                                        | 45 min  |
| Add a feature         | [DEVELOPMENT.md](DEVELOPMENT.md) + [CONTRIBUTING.md](CONTRIBUTING.md) | 1+ hr   |
| Fix a bug             | [TROUBLESHOOTING.md](TROUBLESHOOTING.md)                              | 15+ min |
| Optimize costs        | [COST-OPTIMIZATION.md](COST-OPTIMIZATION.md)                          | 30 min  |
| Understand security   | [GUARDRAILS.md](GUARDRAILS.md)                                        | 20 min  |
| Configure environment | [CONFIGURATION.md](CONFIGURATION.md)                                  | 10 min  |
| Call the API          | [API.md](API.md)                                                      | 10 min  |

---

## 📱 API Quick Start

```bash
# Call the API
curl -X POST https://api.locle.dev/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is your experience?",
    "userId": "user-123",
    "currentDate": "2026-03-12"
  }'

# Expected response
{
  "body": {
    "reply": "I am a Senior Cloud Software Engineer..."
  }
}
```

See [API.md](API.md) for full documentation.

---

## 🛠️ Setup Quick Start

```bash
# Clone and setup
git clone https://github.com/locle/alfred-ai-assistant.git
cd alfred-ai-assistant

# Create environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install deps
pip install -r src/requirements.txt -r requirements-dev.txt

# Verify
make verify

# Run tests
make test

# Start developing!
```

See [DEVELOPMENT.md](DEVELOPMENT.md) for full details.

---

## 🚀 Deployment Quick Start

```bash
# Configure
export AWS_REGION=us-east-1
export ENVIRONMENT=prod

# Plan
cd terraform
terraform plan

# Deploy
terraform apply

# Verify
aws lambda invoke \
  --function-name alfred-assistant-handler \
  --payload '{"question":"Hello"}' \
  response.json
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for full details.

---

## 🔍 Troubleshooting Quick Reference

| Error                                        | Solution                                  |
| -------------------------------------------- | ----------------------------------------- |
| "AccessDeniedException: bedrock:InvokeModel" | Check Lambda IAM policy                   |
| "ValidationException: invalid model ID"      | Use correct inference profile ID          |
| "ResourceNotFoundException: table not found" | Run `terraform apply` to create tables    |
| "Too many requests"                          | Rate limit exceeded (3/day), try tomorrow |
| "CORS error"                                 | Add origin to ALLOWED_ORIGINS             |

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for full guide.

---

## 📞 Support & Help

### Before Asking for Help

1. Check the relevant documentation above
2. Search [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
3. Review CloudWatch logs
4. Check GitHub issues

### Getting Help

- **Slack**: #alfred-support
- **Email**: support@locle.dev
- **GitHub Issues**: Create an issue with details
- **Documentation**: Check the index above

---

## 📈 Documentation Maintenance

Last updated: **2026-03-12**

Version: **3.1.0** (see [../CHANGELOG.md](../CHANGELOG.md) for history)

Maintainers:

- Loc Le (@locle)

---

## 🎯 Next Steps

1. **New user?** → Start with [README.md](../README.md)
2. **Developer?** → Go to [DEVELOPMENT.md](DEVELOPMENT.md)
3. **DevOps?** → Go to [DEPLOYMENT.md](DEPLOYMENT.md)
4. **API user?** → Go to [API.md](API.md)
5. **Stuck?** → Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

**Happy learning! 📚**

---

## 📚 Full Document List

| Document                                     | Purpose                    | Audience                 | Time     |
| -------------------------------------------- | -------------------------- | ------------------------ | -------- |
| [README.md](../README.md)                    | Project overview           | Everyone                 | 5 min    |
| [ARCHITECTURE.md](ARCHITECTURE.md)           | System design              | Developers, Ops          | 15 min   |
| [API.md](API.md)                             | API specification          | API users, Frontend devs | 10 min   |
| [DEVELOPMENT.md](DEVELOPMENT.md)             | Local development          | Developers               | 30+ min  |
| [DEPLOYMENT.md](DEPLOYMENT.md)               | Infrastructure, deployment | DevOps, SREs             | 45+ min  |
| [CONFIGURATION.md](CONFIGURATION.md)         | Environment setup          | DevOps, Ops              | 10 min   |
| [GUARDRAILS.md](GUARDRAILS.md)               | Security, safety           | Security, Ops            | 20 min   |
| [COST-OPTIMIZATION.md](COST-OPTIMIZATION.md) | Cost management            | Finance, Ops             | 30 min   |
| [TROUBLESHOOTING.md](TROUBLESHOOTING.md)     | Problem solving            | Everyone                 | Variable |
| [CONTRIBUTING.md](CONTRIBUTING.md)           | Contributing               | Contributors             | 10 min   |
| [INDEX.md](INDEX.md)                         | This file                  | Navigation               | 5 min    |

---

**Questions? Check the docs above or reach out to the team. 🚀**
