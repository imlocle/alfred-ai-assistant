"""Shared pytest fixtures and configuration."""

import pytest
import json
import os
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any


# ===== Fixtures for AWS/External Services =====


@pytest.fixture
def mock_dynamodb():
    """Mock DynamoDB storage provider."""
    with patch("repositories.conversation_repository.StorageProvider") as mock:
        storage = Mock()
        storage.get = Mock(return_value={"count": 0})
        storage.update = Mock(return_value={"count": 1})
        mock.return_value = storage
        yield storage


@pytest.fixture
def mock_bedrock():
    """Mock Bedrock LLM provider."""
    with patch("providers.llm_provider.boto3.client") as mock:
        client = Mock()
        client.invoke_model = Mock(
            return_value={
                "body": Mock(
                    read=Mock(
                        return_value=json.dumps(
                            {"content": [{"text": "Test response from Alfred"}]}
                        ).encode()
                    )
                )
            }
        )
        mock.return_value = client
        yield client


@pytest.fixture
def mock_s3():
    """Mock S3 knowledge base provider."""
    with patch("providers.knowledge_provider.boto3.client") as mock:
        client = Mock()
        client.get_object = Mock(
            return_value={
                "Body": Mock(
                    read=Mock(
                        return_value=json.dumps(
                            {
                                "personal_info": {
                                    "full_name": "Loc Le",
                                    "role": "Senior Cloud Software Engineer",
                                }
                            }
                        ).encode()
                    )
                )
            }
        )
        mock.return_value = client
        yield client


# ===== Fixtures for Test Data =====


@pytest.fixture
def valid_lambda_event():
    """Valid Lambda event from API Gateway."""
    return {
        "headers": {
            "origin": "http://localhost:5173",
            "x-forwarded-for": "192.168.1.1",
        },
        "requestContext": {
            "requestId": "test-request-123",
            "timeEpoch": 1678300800000,  # March 8, 2023
        },
        "body": json.dumps({"question": "What is your experience?"}),
    }


@pytest.fixture
def invalid_origin_event():
    """Lambda event with invalid origin."""
    return {
        "headers": {
            "origin": "https://malicious.com",
            "x-forwarded-for": "192.168.1.1",
        },
        "requestContext": {"requestId": "test-request-124", "timeEpoch": 1678300800000},
        "body": json.dumps({"question": "What is your experience?"}),
    }


@pytest.fixture
def invalid_question_event():
    """Lambda event with invalid question."""
    return {
        "headers": {
            "origin": "http://localhost:5173",
            "x-forwarded-for": "192.168.1.1",
        },
        "requestContext": {"requestId": "test-request-125", "timeEpoch": 1678300800000},
        "body": json.dumps({"question": ""}),  # Empty question
    }


@pytest.fixture
def current_date_string():
    """Current date as string YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")


@pytest.fixture
def sample_user_id():
    """Sample user ID for testing."""
    return "test-user-123"


@pytest.fixture
def sample_question():
    """Sample valid question."""
    return "What is your experience with AWS?"


@pytest.fixture
def sample_response():
    """Sample LLM response."""
    return "I am a Senior Cloud Software Engineer with 6+ years of experience designing and building production-grade systems on AWS."


# ===== Fixtures for Service Dependencies =====


@pytest.fixture
def mock_assistant_agent():
    """Mock AssistantAgent."""
    agent = Mock()
    agent.answer = Mock(return_value="Test response from agent")
    return agent


@pytest.fixture
def mock_conversation_repository():
    """Mock ConversationRepository."""
    repo = Mock()
    repo.check_usage = Mock()  # Doesn't raise by default
    repo.get_cached_response = Mock(return_value=None)
    repo.cache_response = Mock()
    repo.update_usage = Mock()
    return repo


@pytest.fixture
def mock_knowledge_provider():
    """Mock KnowledgeProvider."""
    provider = Mock()
    provider.fetch_knowledge = Mock(
        return_value={
            "personal_info": {
                "full_name": "Loc Le",
                "role": "Senior Cloud Software Engineer",
            }
        }
    )
    return provider


@pytest.fixture
def mock_llm_provider():
    """Mock LLMProvider."""
    provider = Mock()
    provider.invoke_model = Mock(return_value="Generated response")
    return provider


# ===== Environment Setup =====


@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    """Set environment variables for testing and patch boto3."""
    # Set environment variables FIRST
    env_vars = {
        "AWS_REGION": "us-west-1",
        "USAGE_TRACKER_TABLE": "test-usage-table",
        "LOG_LEVEL": "DEBUG",
        "MODEL_ID": "us.amazon.nova-lite-v1:0",
        "KNOWLEDGE_BASE_KEY": "test-knowledge",
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    # Mock AWS boto3 at module level to prevent real AWS client creation
    with patch("boto3.resource") as mock_resource, patch(
        "boto3.client"
    ) as mock_client, patch("boto3.Session") as mock_session:

        # Mock DynamoDB resource
        mock_ddb = Mock()
        mock_ddb.Table = Mock(return_value=Mock())
        mock_resource.return_value = mock_ddb

        # Mock S3 client
        mock_s3_client = Mock()
        mock_s3_client.get_object = Mock(
            return_value={
                "Body": Mock(
                    read=Mock(
                        return_value=json.dumps(
                            {"personal_info": {"full_name": "Loc Le"}}
                        ).encode()
                    )
                )
            }
        )

        # Mock Bedrock client
        mock_bedrock_client = Mock()
        mock_bedrock_client.invoke_model = Mock(
            return_value={
                "body": Mock(
                    read=Mock(
                        return_value=json.dumps(
                            {"content": [{"text": "Test response"}]}
                        ).encode()
                    )
                )
            }
        )

        # Route different service calls to appropriate mocks
        def client_side_effect(service_name, *args, **kwargs):
            if service_name == "s3":
                return mock_s3_client
            elif service_name == "bedrock-runtime":
                return mock_bedrock_client
            return mock_client

        mock_client.side_effect = client_side_effect

        yield


@pytest.fixture
def monkeypatch_config(monkeypatch):
    """Make ALLOWED_ORIGINS mutable for testing."""
    from shared import config

    monkeypatch.setattr(
        config, "ALLOWED_ORIGINS", ["http://localhost:5173", "https://imlocle.com"]
    )
    return monkeypatch
