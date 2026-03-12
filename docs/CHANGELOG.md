# Changelog

All notable changes to the Alfred AI Assistant project.

---

## [3.1.0] - 2026-03-06 - Bedrock Configuration Fix

### 🔧 Infrastructure Fixes

#### Bedrock IAM Policy Update

- **Fixed AccessDeniedException** - Updated IAM policy to allow access to foundation models and inference profiles
- **Cross-region support** - Policy now allows `bedrock:InvokeModel` on all regions (`arn:aws:bedrock:*::foundation-model/*` and `arn:aws:bedrock:*:*:inference-profile/*`)
- **Removed overly restrictive ARN** - Previous policy only allowed specific inference profile ARN

#### Bedrock Model ID Configuration

- **Fixed ValidationException** - Changed MODEL_ID from foundation model ID to inference profile format
- **Updated MODEL_ID** to `us.amazon.nova-lite-v1:0` (cross-region inference profile)
- **Bedrock requirement** - On-demand throughput requires inference profile ID, not direct model ID

#### Enhanced Error Logging

- **Added `exc_info=True`** to all LLM error logging for full stack traces
- **Improved debugging** - CloudWatch logs now show complete exception details
- **Better troubleshooting** - Full traceback helps identify root cause faster

### 📝 Documentation Updates

- Updated `infrastructure-and-deployment.md` with Bedrock troubleshooting section
- Updated `architecture-overview.md` with inference profile details
- Updated `README.md` with MODEL_ID format explanation
- Added troubleshooting entries for Bedrock AccessDenied and ValidationException errors

---

## [3.0.0] - 2026 - Enterprise SaaS Naming Refactor

### 🏗️ Architecture Refactoring (Agent-Centric Pattern)

Complete codebase rename following Enterprise SaaS / Agent-Centric naming conventions.

#### File Renames

| Old Path                                   | New Path                                      |
| ------------------------------------------ | --------------------------------------------- |
| `src/utils/constants.py`                   | `src/shared/config.py`                        |
| `src/utils/errors.py`                      | `src/shared/exceptions.py`                    |
| `src/utils/input_sanitizer.py`             | `src/shared/validators.py`                    |
| `src/utils/logger.py`                      | `src/shared/logging.py`                       |
| `src/utils/response_service.py`            | `src/shared/responses.py`                     |
| `src/aws/bedrock_service.py`               | `src/providers/llm_provider.py`               |
| `src/aws/dynamodb_service.py`              | `src/providers/storage_provider.py`           |
| `src/aws/s3_service.py`                    | `src/providers/knowledge_provider.py`         |
| `src/repositories/inference_repository.py` | `src/repositories/conversation_repository.py` |
| `src/services/inference_service.py`        | `src/services/assistant_service.py`           |
| `src/controllers/ask_controller.py`        | `src/controllers/query_controller.py`         |
| `src/handlers/ask_alfred.py`               | `src/handlers/assistant_handler.py`           |

#### Class Renames

| Old Name              | New Name                 |
| --------------------- | ------------------------ |
| `AskHandler`          | `AssistantHandler`       |
| `AskController`       | `QueryController`        |
| `InferenceService`    | `AssistantService`       |
| `InferenceRepository` | `ConversationRepository` |
| `BedrockService`      | `LLMProvider`            |
| `DynamodbService`     | `StorageProvider`        |
| `S3Service`           | `KnowledgeProvider`      |

#### Directory Changes

- `src/utils/` → `src/shared/` (shared utilities, config, exceptions)
- `src/aws/` → `src/providers/` (external service providers)
- Removed empty `src/utils/` and `src/aws/` directories

#### Terraform Updates

- Updated Lambda handler path to `handlers.assistant_handler.lambda_handler`

#### Terraform Renames

| Old                                          | New                                   |
| -------------------------------------------- | ------------------------------------- |
| `terraform/modules/lambda/ask_alfred/`       | `terraform/modules/lambda/assistant/` |
| Module `ask_alfred`                          | Module `assistant`                    |
| `lambda_name = "ask-alfred"`                 | `lambda_name = "assistant"`           |
| `alfred_usage_tracker_table_*` variables     | `usage_tracker_table_*` variables     |
| DynamoDB module `alfred_usage_tracker_table` | `usage_tracker_table`                 |
| Env var `ALFRED_USAGE_TRACKER_TABLE`         | `USAGE_TRACKER_TABLE`                 |

#### Remaining Print Statements

- Replaced remaining `print()` calls in providers with structured `logger` calls

### Breaking Changes

- Lambda handler path changed: `handlers.ask_alfred.lambda_handler` → `handlers.assistant_handler.lambda_handler`
- All import paths changed (see table above)
- All class names changed (see table above)

---

## [2.0.0] - 2024 - Major Improvements Release

### 🔒 Security Enhancements

#### IAM Permission Restrictions

- **Restricted Bedrock access** from wildcard (`*`) to specific Nova model ARN
- **Removed S3 write permissions** - Lambda now has read-only access to knowledge bucket
- **Added explicit AWS_REGION** environment variable for consistent configuration

#### Input Validation & Sanitization

- **Created `input_sanitizer.py`** module for centralized input validation
- **Removes control characters** to prevent injection attacks
- **Normalizes whitespace** for consistent processing
- **Enforces length limits** (2000 characters max)
- **Validates non-empty** questions after sanitization

### ⚡ Performance Improvements

#### Response Caching

- **Implemented in-memory cache** with configurable TTL (default: 1 hour)
- **MD5-based cache keys** from normalized questions
- **Automatic expiration** of stale cache entries
- **Cache hit/miss logging** for monitoring
- **Estimated 30-50% cost reduction** for repeated questions

### 📊 Observability Enhancements

#### Structured JSON Logging

- **Created `logger.py`** module with custom JSON formatter
- **Consistent log format** with timestamp, level, message, module, function, line
- **Request correlation** via request_id tracking
- **User tracking** via user_id in logs
- **Exception tracking** with full stack traces
- **CloudWatch Insights ready** for advanced queries

#### Request ID Tracking

- **End-to-end tracing** from API Gateway through all layers
- **Request correlation** across handler → controller → service → repository
- **Included in all log messages** for easy debugging
- **Extracted from API Gateway** event context

#### Replaced Print Statements

- **Removed all `print()` calls** in favor of structured logging
- **Added contextual information** (request_id, user_id, error details)
- **Consistent logging levels** (INFO, WARNING, ERROR)

### 🏗️ Infrastructure Improvements

#### DynamoDB Enhancements

- **Enabled point-in-time recovery** for data protection
- **Added backup tags** for compliance tracking
- **35-day recovery window** for disaster recovery

#### CloudWatch Log Management

- **Created explicit log group** with 30-day retention
- **Automatic log cleanup** to control costs
- **Tagged for organization** (Environment, Application)

#### CloudWatch Alarms

- **Lambda errors alarm** - triggers on >10 errors in 5 minutes
- **Lambda duration alarm** - triggers on >10 second average duration
- **Lambda throttles alarm** - triggers on >5 throttles in 5 minutes
- **Proactive monitoring** for faster incident response

### 🔧 Code Quality Improvements

#### Configuration Management

- **Extracted magic numbers** to constants
- **Added `CACHE_TTL_SECONDS`** (3600 = 1 hour)
- **Added `RATE_LIMIT_MAX_REQUESTS`** (50 per day)
- **Centralized configuration** in `constants.py`

#### Error Handling

- **Added try-catch blocks** in sanitization
- **Better error messages** with context
- **Graceful degradation** (cache failures don't break requests)
- **Detailed error logging** throughout

#### Type Safety

- **All files pass diagnostics** with zero errors
- **Proper type hints** throughout
- **Optional parameters** correctly typed

---

## [1.0.0] - 2024 - Bug Fixes Release

### 🐛 Critical Bug Fixes

#### DynamoDB Race Condition

- **Fixed incorrect ConditionExpression** that caused updates to fail after first request
- **Removed problematic condition** and added proper error handling
- **Added return value checking** with logging

#### S3 Knowledge Base Loading

- **Added error handling** for S3 fetch failures
- **Fallback to empty dict** if knowledge base unavailable
- **Prevents Lambda initialization crashes**

#### Streaming Implementation

- **Fixed broken `invoke_model_with_response_stream()`** method
- **Proper text accumulation** from stream chunks
- **Correct JSON parsing** of chunk data
- **Returns accumulated text** or fallback message

#### AWS Region Configuration

- **Fixed missing AWS_REGION** environment variable
- **Added fallback chain** to AWS_DEFAULT_REGION and us-west-1
- **Applied to both Bedrock and S3** clients

#### Type Hint Errors

- **Fixed lowercase `any`** to proper `Any` type
- **Fixed mutable default arguments** with Optional pattern
- **Added `cast()` for boto3** client/resource returns
- **Fixed DynamoDB return types** to generic Dict[str, Any]

### 🔧 High Priority Fixes

#### Question Length Validation

- **Added MAX_QUESTION_LENGTH** constant (2000 chars)
- **Validates before sending** to Bedrock
- **Prevents abuse** and unexpected costs

#### S3 Error Logging

- **Added detailed error messages** with bucket and key context
- **Improved exception chaining** with `raise ... from e`
- **Better debugging** information

#### DynamoDB Update Verification

- **Added return value checks** for update operations
- **Logs warnings** if update returns no result
- **Graceful failure** (doesn't break request if tracking fails)

### 🔨 Medium/Low Priority Fixes

#### Regex Replacement

- **Replaced regex pattern** with simple keyword list
- **Safer and faster** string matching
- **No regex on user input**

#### S3 Timeout Configuration

- **Added Config** with 5s connect, 10s read timeouts
- **3 retry attempts** for transient failures
- **Prevents indefinite hangs**

#### Mutable Default Arguments

- **Fixed classic Python bug** with `dict()` defaults
- **Changed to Optional[dict] = None** pattern
- **Proper null checking**

#### Rate Limit Logging

- **Added structured logging** when limits hit
- **Includes user_id, count, and date** for monitoring
- **Better security observability**

### 📝 Documentation

#### Created Documentation Files

- **`bug-report.md`** - Comprehensive list of all bugs found and fixed
- **`bug-fixes-applied.md`** - Detailed documentation of fixes
- **`improvements.md`** - Recommendations for enhancements
- **`improvements-applied.md`** - Documentation of improvements implemented
- **`streaming-vs-non-streaming.md`** - Technical guide on streaming options
- **`CHANGELOG.md`** - This file

---

## Summary Statistics

### Code Changes

- Files Created: `src/shared/validators.py`, `src/shared/logging.py`
- Files Modified: All `src/` files, `terraform/modules/lambda/assistant/main.tf`, `terraform/modules/dynamodb/main.tf`

### Bug Fixes

- **16 bugs fixed** (12 original + 4 type safety)
  - 5 Critical/High severity
  - 3 High priority
  - 4 Medium/Low priority
  - 4 Type safety issues

### Improvements

- **12 improvements implemented**
  - 2 Security enhancements
  - 1 Performance optimization
  - 4 Code quality improvements
  - 3 Infrastructure enhancements
  - 2 Configuration improvements

### Quality Metrics

- **Zero diagnostic errors** across all Python files
- **100% type hint coverage** in new code
- **Structured logging** throughout application
- **Comprehensive error handling** at all layers

---

## Migration Guide

### For Existing Deployments

#### 1. Update Dependencies

No new dependencies required - all changes use existing libraries.

#### 2. Review Configuration

Check and adjust these constants in `src/shared/config.py`:

```python
CACHE_TTL_SECONDS = 3600  # Adjust cache duration if needed
RATE_LIMIT_MAX_REQUESTS = 50  # Adjust rate limit if needed
```

#### 3. Deploy Infrastructure Changes

```bash
cd terraform
terraform plan  # Review changes
terraform apply  # Apply changes
```

#### 4. Deploy Application Code

```bash
make deploy  # Or your deployment command
```

#### 5. Verify Deployment

- Check CloudWatch Logs for JSON format
- Verify alarms are in OK state
- Test a few questions to verify caching
- Check DynamoDB PITR is enabled
- Verify log retention is 30 days

---

## Known Issues

None. All known issues have been resolved.

---

## Future Enhancements

See `docs/ideas-improvements.md` for the full roadmap including multi-agent platform evolution, agent framework, tool integration, and enterprise features.
