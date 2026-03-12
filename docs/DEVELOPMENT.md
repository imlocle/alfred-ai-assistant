# Development Guide

Complete setup and development workflow for Alfred AI Assistant.

## Prerequisites

### System Requirements

- **Python**: 3.12+
- **Node.js**: 18+ (for infrastructure tools)
- **Git**: 2.0+
- **AWS CLI**: v2 (for AWS interactions)
- **Terraform**: 1.0+
- **Make**: 3.81+ (optional, for commands)

### AWS Account Setup

- AWS account with permissions to create Lambda, API Gateway, DynamoDB, S3, Bedrock
- AWS credentials configured locally (`~/.aws/credentials`)
- IAM role with appropriate permissions

### Development Tools

- VS Code or similar IDE with Python support
- Postman or cURL for API testing
- DynamoDB local for local testing (optional)

---

## Local Setup

### 1. Clone Repository

```bash
git clone https://github.com/locle/alfred-ai-assistant.git
cd alfred-ai-assistant
```

### 2. Create Virtual Environment

```bash
# Using venv
python3.12 -m venv .venv

# Activate
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate      # Windows

# Verify
python --version  # Should be 3.12+
```

### 3. Install Dependencies

```bash
# Install source code dependencies
pip install -r src/requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt  # pytest, black, pylint, mypy, etc.

# Verify installations
pip list | grep -E "boto3|pytest|black"
```

### 4. Configure Environment

Create `.env` file in project root:

```bash
# AWS Configuration
AWS_REGION=us-east-1
AWS_PROFILE=default

# Bedrock Configuration
MODEL_ID=us.amazon.nova-lite-v1:0
KNOWLEDGE_BUCKET=alfred-knowledge-bucket-dev

# Application Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8080
RATE_LIMIT_DAILY=10  # Higher for development
CACHE_TTL_SECONDS=3600

# Logging
LOG_LEVEL=DEBUG  # Use DEBUG in development

# DynamoDB (local testing)
DYNAMODB_ENDPOINT=http://localhost:8000  # If using local DynamoDB
```

### 5. Verify Setup

```bash
make verify  # Or run directly:
python -c "import boto3; import botocore; print('AWS SDKs OK')"
python -c "from src.handlers.assistant_handler import AssistantHandler; print('Source code OK')"
```

---

## Project Structure

```
alfred-ai-assistant/
├── src/
│   ├── handlers/              # Lambda entry points
│   │   └── assistant_handler.py
│   ├── controllers/           # Request routing & validation
│   │   └── query_controller.py
│   ├── services/              # Business logic
│   │   └── assistant_service.py
│   ├── agents/                # AI logic
│   │   └── assistant_agent.py
│   ├── repositories/          # Data access layer
│   │   └── conversation_repository.py
│   ├── providers/             # External service clients
│   │   ├── llm_provider.py
│   │   ├── knowledge_provider.py
│   │   └── storage_provider.py
│   ├── shared/                # Utilities & configs
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   ├── logging.py
│   │   ├── responses.py
│   │   └── validators.py
│   └── requirements.txt
├── terraform/                 # Infrastructure-as-Code
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── backend.tf
│   └── modules/
├── tests/                     # Automated tests
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docs/                      # Documentation
├── makefile                   # Common commands
├── .env                       # Environment config (not in git)
├── .venv/                     # Virtual environment
├── .gitignore                 # Git exclusions
├── README.md                  # Project overview
└── requirements-dev.txt       # Dev dependencies
```

---

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/my-feature
# or
git checkout -b bugfix/my-bug
```

### 2. Make Changes

```bash
# Example: Edit a file
vim src/agents/assistant_agent.py

# Keep dependencies updated if you add new packages
pip freeze > requirements-dev.txt  # For dev deps
pip freeze | grep -v "-e" > src/requirements.txt  # For prod deps
```

### 3. Run Tests Locally

```bash
# Run all tests
make test  # or: pytest tests/

# Run specific test file
pytest tests/unit/test_agent.py

# Run with coverage
pytest --cov=src tests/

# Run specific test
pytest tests/unit/test_agent.py::test_answer_scheduling_request
```

### 4. Format & Lint Code

```bash
# Format code (Black)
make format  # or: black src/

# Check linting (Pylint)
make lint    # or: pylint src/

# Type checking (mypy)
make type-check  # or: mypy src/

# All three
make check
```

### 5. Test Against Local Lambda

```bash
# Use AWS SAM to test locally
sam local start-api

# In another terminal, invoke the endpoint:
curl -X POST http://localhost:3000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is your experience?",
    "userId": "test-user",
    "currentDate": "2026-03-12"
  }'
```

### 6. Manual Integration Testing

```bash
# Set active AWS profile
export AWS_PROFILE=default

# Invoke Lambda directly (if deployed)
aws lambda invoke \
  --function-name alfred-assistant-handler \
  --payload file://test-event.json \
  response.json

# Test API endpoint
curl -X POST https://api.dev.locle.dev/chat \
  -H "Content-Type: application/json" \
  -d '{...}'
```

### 7. Commit & Push

```bash
git add src/
git commit -m "feat: add feature description"
git push origin feature/my-feature
```

### 8. Create Pull Request

- Push to GitHub
- Create PR with description
- Reference related issues (#123)
- Wait for CI/CD checks to pass
- Request code review

---

## Testing

### Test Structure

```
tests/
├── unit/                      # Unit tests (no external deps)
│   ├── test_handlers.py
│   ├── test_controllers.py
│   ├── test_services.py
│   ├── test_agents.py
│   ├── test_repositories.py
│   └── test_providers.py
├── integration/               # Integration tests (with AWS)
│   ├── test_dynamodb.py
│   ├── test_s3.py
│   └── test_bedrock.py
└── e2e/                       # End-to-end tests
    ├── test_full_flow.py
    └── test_api_endpoints.py
```

### Unit Testing Example

```python
# tests/unit/test_agents.py
import pytest
from unittest.mock import Mock, patch
from src.agents.assistant_agent import AssistantAgent

def test_answer_scheduling_request():
    """Test that scheduling requests are routed to Calendly."""
    agent = AssistantAgent(
        llm_provider=Mock(),
        knowledge_provider=Mock()
    )

    result = agent.answer("Can I schedule a meeting?")

    assert "Calendly" in result
    assert "schedule" not in result.lower() or "calendly" in result.lower()

def test_answer_normal_question():
    """Test that normal questions invoke the LLM."""
    mock_llm = Mock()
    mock_llm.invoke_model.return_value = "Expected response"

    agent = AssistantAgent(
        llm_provider=mock_llm,
        knowledge_provider=Mock()
    )

    result = agent.answer("What is your experience?")

    assert result == "Expected response"
    mock_llm.invoke_model.assert_called_once()
```

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_agents.py

# Run specific test function
pytest tests/unit/test_agents.py::test_answer_scheduling_request

# Run with coverage report
pytest --cov=src --cov-report=html tests/

# Run tests matching pattern
pytest -k "scheduling"

# Stop on first failure
pytest -x
```

### Test Coverage Target

- **Unit tests**: 80%+ coverage
- **Integration tests**: Required for critical paths
- **E2E tests**: Key user workflows

---

## Debugging

### Enable Debug Logging

Set in `.env`:

```
LOG_LEVEL=DEBUG
```

Or at runtime:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Add Breakpoints

```python
# In any Python file
import pdb; pdb.set_trace()

# Modern Python 3.7+
breakpoint()
```

### View CloudWatch Logs

```bash
# Tail Lambda logs
aws logs tail /aws/lambda/alfred-assistant-handler --follow

# View specific time range
aws logs filter-log-events \
  --log-group-name /aws/lambda/alfred-assistant-handler \
  --start-time $(date -d '1 hour ago' +%s)000
```

### Inspect DynamoDB

```bash
# Using AWS CLI
aws dynamodb scan --table-name alfred-runtime-cache

# Using DynamoDB local
aws dynamodb scan \
  --table-name alfred-runtime-cache \
  --endpoint-url http://localhost:8000
```

### X-Ray Tracing

```bash
# View traces in console
aws xray get-trace-summaries --start-time $(date -d '1 hour ago' +%s)

# View specific trace
aws xray get-trace --trace-id {trace-id}
```

---

## Common Development Tasks

### Adding a New Environment Variable

1. Update `.env`:

   ```
   MY_NEW_VAR=value
   ```

2. Add to `src/shared/config.py`:

   ```python
   MY_NEW_VAR = os.getenv('MY_NEW_VAR', 'default_value')
   ```

3. Update documentation in `CONFIGURATION.md`

### Adding a New Endpoint

1. Create handler in `src/controllers/`
2. Add routing in API Gateway (Terraform)
3. Add tests in `tests/unit/`
4. Document in `API.md`

### Adding a New Dependency

```bash
# Install package
pip install new-package==1.2.3

# Update requirements
pip freeze > src/requirements.txt

# (Or requirements-dev.txt for dev-only packages)

# Commit both
git add src/requirements.txt setup.py
git commit -m "chore: add new-package for feature X"
```

### Running Locally with Mock AWS Services

```bash
# Start DynamoDB local
docker run -p 8000:8000 amazon/dynamodb-local

# In another terminal, set endpoint
export DYNAMODB_ENDPOINT=http://localhost:8000

# Run your code
python -m src.handlers.assistant_handler
```

---

## Performance Profiling

### Profile Function Timing

```python
import time

start = time.time()
result = expensive_function()
elapsed = time.time() - start
print(f"Took {elapsed:.2f}s")
```

### Profile Memory Usage

```python
import tracemalloc

tracemalloc.start()
result = expensive_function()
current, peak = tracemalloc.get_traced_memory()
print(f"Current: {current / 1024 / 1024:.1f}MB; Peak: {peak / 1024 / 1024:.1f}MB")
tracemalloc.stop()
```

### Lambda Cost Estimation

```bash
# Estimate monthly cost based on invocations
# Formula: (GB-seconds × 0.0000166667) + (requests × 0.0000002)
# Where GB-seconds = memory_mb × execution_time_seconds / 1024 × invocations

python3 << 'EOF'
memory_mb = 512
execution_time_s = 1.5
daily_requests = 1000
monthly_requests = daily_requests * 30

gb_seconds = (memory_mb / 1024) * execution_time_s * (monthly_requests / 1000)
compute_cost = gb_seconds * 0.0000166667
request_cost = monthly_requests * 0.0000002

print(f"Monthly compute cost: ${compute_cost:.2f}")
print(f"Monthly request cost: ${request_cost:.2f}")
print(f"Total: ${compute_cost + request_cost:.2f}")
EOF
```

---

## CI/CD Integration

### GitHub Actions

Example workflow (`.github/workflows/test.yml`):

```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.12"
      - run: pip install -r src/requirements.txt -r requirements-dev.txt
      - run: make check
      - run: make test
```

---

## Deployment from Development

### To Staging Environment

```bash
# Build Lambda package
make build

# Deploy to staging
terraform -chdir=terraform apply -var-file=staging.tfvars

# Run smoke tests
make test-staging
```

### To Production

```bash
# Build Lambda package
make build

# Plan changes
terraform -chdir=terraform plan -var-file=prod.tfvars

# Apply changes (requires approval)
terraform -chdir=terraform apply -var-file=prod.tfvars

# Verify deployment
make test-prod
```

---

## Troubleshooting Development Issues

### ModuleNotFoundError

```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r src/requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

### AWS Credentials Not Found

```bash
# Configure AWS CLI
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
export AWS_DEFAULT_REGION=us-east-1
```

### Bedrock Access Denied

```bash
# Check IAM permissions
aws iam get-user-policy --user-name my-user --policy-name inline-policy

# Ensure policy includes:
# - bedrock:InvokeModel
# - Inference profile ARN: arn:aws:bedrock:*:*:inference-profile/*
```

---

## IDE Configuration

### VS Code Settings

`.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "ms-python.python"
}
```

### PyCharm Configuration

1. Project → Python Interpreter → Add Interpreter → Existing Environment
2. Select `.venv/bin/python`
3. Tools → Python Integrated Tools → Testing → pytest
4. Preferences → Editor → Code Style → Python → Target version 3.12

---

## Resources

- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/latest/dg/)
- [Boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
- [Pytest Documentation](https://docs.pytest.org/)
- [Black Code Formatter](https://black.readthedocs.io/)
- [Terraform Documentation](https://www.terraform.io/docs/)

---

## Got Stuck?

1. Check existing issues on GitHub
2. Review logging output (CloudWatch or local logs)
3. Check AWS service health dashboard
4. Contact team on Slack or email
5. Create an issue with reproduction steps

---

**Happy coding! 🚀**
