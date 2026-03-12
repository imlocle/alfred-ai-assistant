# Infrastructure Details

**Purpose**: Deep dive into Terraform configuration and AWS resource setup.  
**Audience**: DevOps engineers, infrastructure architects  
**Updated**: March 2026

---

## Terraform Structure

```
terraform/
├── main.tf              # Resource definitions
├── variables.tf         # Input variables
├── outputs.tf           # Output values (endpoints, IDs)
├── backend.tf           # State backend configuration
├── backend.auto.hcl     # State bucket (environment-specific)
├── modules/
│   ├── api/             # API Gateway
│   ├── lambda/          # Lambda function
│   ├── dynamodb/        # DynamoDB tables
│   └── iam/             # IAM roles and policies
```

### Backend Configuration

State is stored in S3 with DynamoDB locking:

```hcl
terraform {
  backend "s3" {
    bucket         = "alfred-terraform-state"
    key            = "alfred/terraform.tfstate"
    region         = "us-west-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

## AWS Resources

### 1. API Gateway (HTTP API)

```
Endpoint: https://api-id.execute-api.us-west-1.amazonaws.com/prod

POST /chat → Lambda
GET /health → Lambda

Features:
- CORS enabled
- Auto-response format handling
- Request validation
```

### 2. Lambda Function

```
Name: alfred-handler-${ENV}
Runtime: Python 3.13
Memory: 256 MB
Timeout: 30 seconds
Layers: lambda_layer/ (dependencies)
```

### 3. DynamoDB Tables

- `alfred-usage-tracker-${ENV}`: Request usage tracking with TTL

### 4. S3 Buckets

- `alfred-knowledge-bucket-${ENV}`: Knowledge base versioning

## IAM Structure

Lambda execution role has permissions for:

- DynamoDB read/write (`alfred-usage-tracker-*`)
- S3 get object (`alfred-knowledge-bucket-*`)
- Bedrock invoke model
- CloudWatch logs

See Terraform IAM module for complete policy.

---

See [OPERATIONS_RUNBOOK.md](OPERATIONS_RUNBOOK.md) for operational details.

**Last Updated**: March 2026
