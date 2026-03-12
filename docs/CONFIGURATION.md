# Configuration Guide

Complete reference for Alfred's configuration, environment variables, and settings.

---

## Configuration Hierarchy

Alfred loads configuration in this order (highest priority first):

1. **Environment Variables** (`.env` file or shell exports)
2. **Command-line Arguments** (if applicable)
3. **Config Files** (`src/shared/config.py`)
4. **Defaults** (hardcoded in code)

---

## Environment Variables

### AWS Configuration

```bash
# AWS Region
AWS_REGION=us-east-1
# Options: us-east-1, us-west-2, eu-west-1, ap-southeast-1, etc.
# Default: us-east-1

# AWS Profile (for local development)
AWS_PROFILE=default
# Looks up credentials from ~/.aws/credentials
# Default: default

# AWS Credentials (alternative to profile)
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_SESSION_TOKEN=...  # For temporary credentials
```

### Bedrock Configuration

```bash
# LLM Model ID (inference profile)
MODEL_ID=us.amazon.nova-lite-v1:0
# Production: us.amazon.nova-lite-v1:0 (Nova Lite, cost-effective)
# Alternative: us.anthropic.claude-3-5-sonnet-20241022-v2:0 (Claude, higher cost)
# Default: us.amazon.nova-lite-v1:0

# Model Max Tokens (output length)
MODEL_MAX_TOKENS=512
# Range: 1-4096
# Default: 512
# Note: Lower = faster & cheaper responses

# Model Temperature (creativity)
MODEL_TEMPERATURE=0.7
# Range: 0.0 - 1.0
# 0.0 = deterministic, always same response
# 1.0 = highly creative, variable responses
# Default: 0.7
```

### Storage Configuration

```bash
# S3 Knowledge Base Bucket
KNOWLEDGE_BUCKET=alfred-knowledge-bucket-prod
# Format: s3-bucket-name (no s3:// prefix)
# Must exist in same AWS region
# Default: alfred-knowledge-bucket-{environment}

# DynamoDB Conversation Cache Table
CACHE_TABLE_NAME=alfred-runtime-cache
# Default: alfred-runtime-cache

# DynamoDB Usage Tracker Table
USAGE_TABLE_NAME=alfred-usage-tracker
# Default: alfred-usage-tracker

# Cache TTL (time-to-live in seconds)
CACHE_TTL_SECONDS=2592000
# 2,592,000 = 30 days (default)
# Set to 0 to disable caching
```

### Application Configuration

```bash
# Rate Limiting: Max requests per user per day
RATE_LIMIT_DAILY=3
# Default: 3
# Set to 0 to disable rate limiting (development only)
# Typical values: 3 (prod), 10 (staging), unlimited (dev)

# Allowed Origins (CORS whitelist)
ALLOWED_ORIGINS=https://locle.dev,https://www.locle.dev,https://locleprojects.dev
# Comma-separated list of allowed origins
# If not set, CORS disabled (all origins rejected)
# Use * for development (insecure)

# Calendly URL (for scheduling requests)
CALENDLY_URL=https://calendly.com/locle/
# Default: https://calendly.com/locle/

# Environment Name
ENVIRONMENT=prod
# Options: dev, staging, prod
# Default: prod
# Used for logging and metrics tagging
```

### Logging Configuration

```bash
# Log Level
LOG_LEVEL=INFO
# Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
# Default: INFO (production) / DEBUG (development)
# DEBUG = verbose, tons of output (use in dev only)
# INFO = normal, key events
# WARNING = only problems
# ERROR = only errors
# CRITICAL = only critical errors

# CloudWatch Log Group
LOG_GROUP_NAME=/aws/lambda/alfred-assistant-handler
# Automatically created by Lambda
# Logs published here automatically

# Enable Structured Logging
STRUCTURED_LOGGING=true
# If true, logs are JSON (machine-readable)
# If false, logs are plain text (human-readable)
# Default: true (production)
```

### Optional Features

```bash
# Enable Response Caching
ENABLE_CACHE=true
# Default: true
# Set to false to bypass cache (slower, higher cost)

# Enable Usage Tracking
ENABLE_USAGE_TRACKING=true
# Default: true
# Set to false to disable rate limiting

# DynamoDB Endpoint (local testing)
DYNAMODB_ENDPOINT=http://localhost:8000
# For local DynamoDB (docker run amazon/dynamodb-local)
# If not set, uses AWS-managed DynamoDB

# Enable Debug Mode
DEBUG=false
# If true, more verbose error messages, profiling output
# Default: false
```

---

## Configuration Files

### .env File (Local Development)

Create `.env` in project root:

```bash
# AWS
AWS_REGION=us-east-1
AWS_PROFILE=default

# Bedrock
MODEL_ID=us.amazon.nova-lite-v1:0
MODEL_MAX_TOKENS=512
MODEL_TEMPERATURE=0.7

# Storage
KNOWLEDGE_BUCKET=alfred-knowledge-bucket-dev
CACHE_TABLE_NAME=alfred-runtime-cache
USAGE_TABLE_NAME=alfred-usage-tracker
CACHE_TTL_SECONDS=3600  # 1 hour for faster iteration

# Application
RATE_LIMIT_DAILY=10  # Higher for dev
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
CALENDLY_URL=https://calendly.com/locle/
ENVIRONMENT=dev

# Logging
LOG_LEVEL=DEBUG
STRUCTURED_LOGGING=false  # Human-readable in dev
DEBUG=true

# Options
ENABLE_CACHE=true
ENABLE_USAGE_TRACKING=false  # Disable for testing
```

### src/shared/config.py (Application Configuration)

```python
# System Prompt (defines Alfred's behavior)
ALFRED_SYSTEM_PROMPT = """
You are Alfred, an AI assistant specialized in answering questions about Loc Le - a backend-focused
Senior Cloud Software Engineer with 6+ years of experience in AWS, system design, and AI/LLM integrations.

IMPORTANT RULES:
1. Only answer questions about Loc Le using the provided knowledge base.
2. If a question is outside your knowledge base, politely decline and suggest contacting Loc directly.
3. Be concise but informative in your responses.
4. Do not make up information not in the knowledge base.
5. Maintain a professional and friendly tone.
"""

# Application Settings
RATE_LIMIT_DAILY = int(os.getenv('RATE_LIMIT_DAILY', '3'))
CACHE_TTL_SECONDS = int(os.getenv('CACHE_TTL_SECONDS', '2592000'))  # 30 days
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '').split(',')
CALENDLY_URL = os.getenv('CALENDLY_URL', 'https://calendly.com/locle/')

# AWS Configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
KNOWLEDGE_BUCKET = os.getenv('KNOWLEDGE_BUCKET', 'alfred-knowledge-bucket-prod')
CACHE_TABLE_NAME = os.getenv('CACHE_TABLE_NAME', 'alfred-runtime-cache')
USAGE_TABLE_NAME = os.getenv('USAGE_TABLE_NAME', 'alfred-usage-tracker')
DYNAMODB_ENDPOINT = os.getenv('DYNAMODB_ENDPOINT', None)  # None = use AWS endpoint

# Bedrock Configuration
MODEL_ID = os.getenv('MODEL_ID', 'us.amazon.nova-lite-v1:0')
MODEL_MAX_TOKENS = int(os.getenv('MODEL_MAX_TOKENS', '512'))
MODEL_TEMPERATURE = float(os.getenv('MODEL_TEMPERATURE', '0.7'))

# Feature Flags
ENABLE_CACHE = os.getenv('ENABLE_CACHE', 'true').lower() == 'true'
ENABLE_USAGE_TRACKING = os.getenv('ENABLE_USAGE_TRACKING', 'true').lower() == 'true'
```

---

## Environment Profiles

### Development Profile

```bash
# .env.dev
AWS_REGION=us-east-1
ENVIRONMENT=dev
LOG_LEVEL=DEBUG
STRUCTURED_LOGGING=false

RATE_LIMIT_DAILY=10
CACHE_TTL_SECONDS=3600

ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

ENABLE_CACHE=true
ENABLE_USAGE_TRACKING=false
DYNAMODB_ENDPOINT=http://localhost:8000
```

### Staging Profile

```bash
# .env.staging
AWS_REGION=us-east-1
AWS_PROFILE=staging
ENVIRONMENT=staging
LOG_LEVEL=INFO
STRUCTURED_LOGGING=true

RATE_LIMIT_DAILY=5
CACHE_TTL_SECONDS=604800  # 7 days

ALLOWED_ORIGINS=https://staging.locle.dev,https://staging-app.locle.dev

ENABLE_CACHE=true
ENABLE_USAGE_TRACKING=true
```

### Production Profile

```bash
# .env.prod
AWS_REGION=us-east-1
AWS_PROFILE=prod
ENVIRONMENT=prod
LOG_LEVEL=INFO
STRUCTURED_LOGGING=true

RATE_LIMIT_DAILY=3
CACHE_TTL_SECONDS=2592000  # 30 days

ALLOWED_ORIGINS=https://locle.dev,https://www.locle.dev,https://locleprojects.dev

ENABLE_CACHE=true
ENABLE_USAGE_TRACKING=true
```

---

## Loading Environment Variables

### Method 1: From .env File (Development)

```bash
# Install python-dotenv
pip install python-dotenv

# In your code
from dotenv import load_dotenv
import os

load_dotenv('.env')  # Loads .env into os.environ
model_id = os.getenv('MODEL_ID')
```

### Method 2: AWS Systems Manager Parameter Store

```bash
# Store in Parameter Store
aws ssm put-parameter \
  --name /alfred/prod/MODEL_ID \
  --value "us.amazon.nova-lite-v1:0" \
  --type String

# Retrieve in code
import boto3

ssm = boto3.client('ssm')
response = ssm.get_parameter(Name='/alfred/prod/MODEL_ID')
model_id = response['Parameter']['Value']
```

### Method 3: AWS Secrets Manager

```bash
# Store secret
aws secretsmanager create-secret \
  --name alfred/prod/config \
  --secret-string '{"BEDROCK_MODEL_ID":"us.amazon.nova-lite-v1:0"}'

# Retrieve in code
import boto3
import json

secrets = boto3.client('secretsmanager')
response = secrets.get_secret_value(SecretId='alfred/prod/config')
config = json.loads(response['SecretString'])
```

### Method 4: Lambda Environment Variables (Console)

```
In AWS Lambda console:
1. Select function: alfred-assistant-handler
2. Configuration tab → Environment variables
3. Edit environment variables
4. Add: MODEL_ID=us.amazon.nova-lite-v1:0
5. Save
```

---

## Configuration Validation

### Validate Configuration at Startup

```python
# src/shared/config.py
import os
import sys

def validate_config():
    """Validate all critical configuration at startup."""
    errors = []

    # Check required variables
    required = [
        'AWS_REGION',
        'MODEL_ID',
        'KNOWLEDGE_BUCKET',
        'CACHE_TABLE_NAME',
        'USAGE_TABLE_NAME',
    ]

    for var in required:
        if not os.getenv(var):
            errors.append(f"Missing required environment variable: {var}")

    # Validate values
    if os.getenv('RATE_LIMIT_DAILY'):
        try:
            limit = int(os.getenv('RATE_LIMIT_DAILY'))
            if limit < 0:
                errors.append("RATE_LIMIT_DAILY must be >= 0")
        except ValueError:
            errors.append("RATE_LIMIT_DAILY must be an integer")

    if errors:
        print("Configuration validation failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)

# Call at startup
validate_config()
```

---

## Secrets Management

### AWS Secrets Manager Best Practices

```bash
# 1. Store all secrets in AWS Secrets Manager
aws secretsmanager create-secret \
  --name alfred/prod/all-secrets \
  --secret-string '{
    "BEDROCK_MODEL_ID": "us.amazon.nova-lite-v1:0",
    "API_KEY": "sk-...",
    "OTHER_SECRET": "value"
  }'

# 2. Grant Lambda permission to read secret
aws iam attach-role-policy \
  --role-name alfred-lambda-role \
  --policy-arn arn:aws:iam::aws:policy/secretsmanager:GetSecretValue

# 3. Retrieve in code
import boto3
import json

def get_secrets():
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='alfred/prod/all-secrets')
    return json.loads(response['SecretString'])

secrets = get_secrets()
model_id = secrets['BEDROCK_MODEL_ID']
```

### Rotation Policy

```bash
# Enable automatic rotation every 30 days
aws secretsmanager rotate-secret \
  --secret-id alfred/prod/all-secrets \
  --rotation-rules AutomaticallyAfterDays=30
```

---

## Configuration Best Practices

1. **Use environment variables** for all environment-specific settings
2. **Never commit secrets** to version control (use .gitignore)
3. **Use AWS Secrets Manager** for sensitive data in production
4. **Validate configuration** at application startup
5. **Log configuration** (redact secrets) in debug logs
6. **Use different profiles** for dev/staging/prod
7. **Document all available options** (this file is a start!)
8. **Provide sensible defaults** for optional settings
9. **Use feature flags** for gradual rollouts
10. **Rotate secrets** regularly and automatically

---

## Troubleshooting Configuration Issues

### Issue: "Environment variable not found"

```bash
# Check if variable is exported
echo $MY_VAR

# Export it
export MY_VAR=value

# Or add to .env file
echo "MY_VAR=value" >> .env
```

### Issue: "Invalid configuration"

```bash
# Test configuration loading
python3 << 'EOF'
import os
from dotenv import load_dotenv

load_dotenv()
print(f"AWS_REGION={os.getenv('AWS_REGION')}")
print(f"MODEL_ID={os.getenv('MODEL_ID')}")
print(f"RATE_LIMIT={os.getenv('RATE_LIMIT_DAILY')}")
EOF
```

### Issue: "Secrets Manager access denied"

```bash
# Check IAM policy
aws iam get-role-policy --role-name alfred-lambda-role --policy-name secrets-access

# Add permission if missing
aws iam put-role-policy \
  --role-name alfred-lambda-role \
  --policy-name secrets-manager \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": "secretsmanager:GetSecretValue",
      "Resource": "arn:aws:secretsmanager:*:*:secret:alfred/*"
    }]
  }'
```

---

## Configuration as Code (Terraform)

```hcl
# terraform/variables.tf

variable "environment" {
  type = string
  description = "Environment (dev, staging, prod)"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Invalid environment"
  }
}

variable "rate_limit_daily" {
  type    = number
  default = 3
}

variable "cache_ttl_seconds" {
  type    = number
  default = 2592000  # 30 days
}

variable "model_id" {
  type    = string
  default = "us.amazon.nova-lite-v1:0"
}

# terraform/modules/lambda/main.tf

resource "aws_lambda_function" "assistant" {
  # ...
  environment {
    variables = {
      AWS_REGION           = var.aws_region
      MODEL_ID             = var.model_id
      RATE_LIMIT_DAILY     = var.rate_limit_daily
      CACHE_TTL_SECONDS    = var.cache_ttl_seconds
      KNOWLEDGE_BUCKET     = aws_s3_bucket.knowledge.bucket
      CACHE_TABLE_NAME     = aws_dynamodb_table.cache.name
      USAGE_TABLE_NAME     = aws_dynamodb_table.usage.name
      ENVIRONMENT          = var.environment
      # ... other variables
    }
  }
}
```

---

## Monitoring Configuration Changes

```bash
# Log all environment variable reads
# Add to logs for audit trail

# Track configuration changes in git
git log --all --oneline --grep="config"

# Compare configurations
diff <(aws ssm get-parameters-by-path --path /alfred/prod --query 'Parameters[].{Name:Name,Value:Value}') \
     <(aws ssm get-parameters-by-path --path /alfred/staging --query 'Parameters[].{Name:Name,Value:Value}')
```

---

**For configuration questions, check the examples or contact the team.**
