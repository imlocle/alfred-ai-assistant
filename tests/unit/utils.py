"""Shared test utilities and helpers."""

import json
from typing import Any, Dict


def create_lambda_event(
    question: str,
    origin: str = "http://localhost:5173",
    user_id: str = "test-user",
    request_id: str = "test-123",
    time_epoch: int = 1678300800000,
) -> Dict[str, Any]:
    """Create a valid Lambda event for testing."""
    return {
        "headers": {
            "origin": origin,
            "x-forwarded-for": user_id,
        },
        "requestContext": {
            "requestId": request_id,
            "timeEpoch": time_epoch,
        },
        "body": json.dumps({"question": question}),
    }


def assert_response_valid(response: Dict[str, Any]) -> None:
    """Assert response has valid Lambda format."""
    assert "statusCode" in response
    assert "body" in response
    assert "headers" in response
    assert isinstance(response["statusCode"], int)
    assert isinstance(response["body"], str)
    assert isinstance(response["headers"], dict)
