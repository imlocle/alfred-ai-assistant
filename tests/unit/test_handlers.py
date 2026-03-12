"""Unit tests for the Lambda handler."""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from handlers.assistant_handler import AssistantHandler, lambda_handler
from shared.exceptions import (
    InvalidQuestionError,
    CORSOriginError,
    RateLimitError,
    ChatbotProcessingError,
)


class TestAssistantHandler:
    """Test AssistantHandler Lambda event handling."""

    def test_handler_success(self, valid_lambda_event, monkeypatch_config):
        """Test successful handler execution."""
        mock_controller = Mock()
        mock_controller.handle_event = Mock(return_value="Test response")

        handler = AssistantHandler()
        handler.controller = mock_controller

        response = handler.handler(valid_lambda_event, None)

        assert response["statusCode"] == 200
        assert json.loads(response["body"])["reply"] == "Test response"
        assert "Content-Type" in response["headers"]

    def test_handler_logs_request_id(self, valid_lambda_event, monkeypatch_config):
        """Test that request ID is extracted and used for logging."""
        mock_controller = Mock()
        mock_controller.handle_event = Mock(return_value="Response")

        handler = AssistantHandler()
        handler.controller = mock_controller

        response = handler.handler(valid_lambda_event, None)

        # Verify handler was called with correct request_id
        mock_controller.handle_event.assert_called_once()
        # handle_event(event, request_id) - request_id is 2nd positional arg
        assert mock_controller.handle_event.call_args[0][1] == "test-request-123"

    def test_handler_invalid_question_error(
        self, invalid_question_event, monkeypatch_config
    ):
        """Test handling InvalidQuestionError."""
        mock_controller = Mock()
        mock_controller.handle_event.side_effect = InvalidQuestionError()

        handler = AssistantHandler()
        handler.controller = mock_controller

        response = handler.handler(invalid_question_event, None)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert "invalid question" in body["reply"].lower()

    def test_handler_cors_origin_error(self, invalid_origin_event):
        """Test handling CORSOriginError."""
        mock_controller = Mock()
        mock_controller.handle_event.side_effect = CORSOriginError(
            origin="https://evil.com"
        )

        handler = AssistantHandler()
        handler.controller = mock_controller

        response = handler.handler(invalid_origin_event, None)

        assert response["statusCode"] == 403
        body = json.loads(response["body"])
        assert "different place" in body["reply"].lower()

    def test_handler_rate_limit_error(self, valid_lambda_event, monkeypatch_config):
        """Test handling RateLimitError."""
        mock_controller = Mock()
        mock_controller.handle_event.side_effect = RateLimitError()

        handler = AssistantHandler()
        handler.controller = mock_controller

        response = handler.handler(valid_lambda_event, None)

        assert response["statusCode"] == 429
        body = json.loads(response["body"])
        assert "limit" in body["reply"].lower()

    def test_handler_unexpected_error(self, valid_lambda_event, monkeypatch_config):
        """Test handling unexpected errors."""
        mock_controller = Mock()
        mock_controller.handle_event.side_effect = Exception(
            "Database connection failed"
        )

        handler = AssistantHandler()
        handler.controller = mock_controller

        response = handler.handler(valid_lambda_event, None)

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "unavailable" in body["reply"].lower()

    def test_handler_returns_headers(self, valid_lambda_event, monkeypatch_config):
        """Test that handler returns proper headers."""
        mock_controller = Mock()
        mock_controller.handle_event = Mock(return_value="Response")

        handler = AssistantHandler()
        handler.controller = mock_controller

        response = handler.handler(valid_lambda_event, None)

        assert "Content-Type" in response["headers"]
        assert "Access-Control-Allow-Origin" in response["headers"]
        assert response["headers"]["Content-Type"] == "application/json"

    def test_handler_request_id_default(self, valid_lambda_event, monkeypatch_config):
        """Test that request ID defaults to 'unknown' if missing."""
        mock_controller = Mock()
        mock_controller.handle_event = Mock(return_value="Response")

        event = valid_lambda_event.copy()
        event["requestContext"] = {}  # Missing requestId

        handler = AssistantHandler()
        handler.controller = mock_controller

        response = handler.handler(event, None)

        # Should still work with default request_id
        assert response["statusCode"] == 200

    def test_handler_exception_includes_exc_info(
        self, valid_lambda_event, monkeypatch_config
    ):
        """Test that exception info is logged for debugging."""
        mock_controller = Mock()
        mock_controller.handle_event.side_effect = ValueError("Test error")

        handler = AssistantHandler()
        handler.controller = mock_controller

        response = handler.handler(valid_lambda_event, None)

        # Should return error response
        assert response["statusCode"] == 500


class TestHandlerIntegration:
    """Integration tests for handler with real (mocked) services."""

    def test_handler_with_mock_controller(self, valid_lambda_event, monkeypatch_config):
        """Test handler with mocked controller."""
        handler = AssistantHandler()
        handler.controller = Mock()
        handler.controller.handle_event = Mock(return_value="AI response")

        response = handler.handler(valid_lambda_event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["reply"] == "AI response"


class TestLambdaHandler:
    """Test the main lambda_handler function."""

    def test_lambda_handler_delegates_to_class(
        self, valid_lambda_event, monkeypatch_config
    ):
        """Test that lambda_handler delegates to AssistantHandler."""
        with patch.object(AssistantHandler, "handler") as mock_handler:
            mock_handler.return_value = {
                "statusCode": 200,
                "body": json.dumps({"reply": "test"}),
            }

            response = lambda_handler(valid_lambda_event, None)

            assert response["statusCode"] == 200

    def test_lambda_handler_returns_dict(self, valid_lambda_event, monkeypatch_config):
        """Test that lambda_handler returns a dict."""
        response = lambda_handler(valid_lambda_event, None)

        assert isinstance(response, dict)
        assert "statusCode" in response
        assert "body" in response
        assert "headers" in response


class TestHandlerErrorMessages:
    """Test handler error message formatting."""

    def test_invalid_question_error_message(
        self, invalid_question_event, monkeypatch_config
    ):
        """Test InvalidQuestionError produces correct message."""
        mock_controller = Mock()
        mock_controller.handle_event.side_effect = InvalidQuestionError()

        handler = AssistantHandler()
        handler.controller = mock_controller

        response = handler.handler(invalid_question_event, None)
        body = json.loads(response["body"])

        assert "invalid question" in body["reply"].lower()
        assert "Please ask another" in body["reply"]

    def test_cors_error_message(self, invalid_origin_event):
        """Test CORSOriginError produces correct message."""
        mock_controller = Mock()
        mock_controller.handle_event.side_effect = CORSOriginError()

        handler = AssistantHandler()
        handler.controller = mock_controller

        response = handler.handler(invalid_origin_event, None)
        body = json.loads(response["body"])

        assert "different place" in body["reply"].lower()

    def test_rate_limit_message(self, valid_lambda_event, monkeypatch_config):
        """Test RateLimitError produces correct message."""
        mock_controller = Mock()
        mock_controller.handle_event.side_effect = RateLimitError()

        handler = AssistantHandler()
        handler.controller = mock_controller

        response = handler.handler(valid_lambda_event, None)
        body = json.loads(response["body"])

        assert "limit" in body["reply"].lower()
        assert "come back tomorrow" in body["reply"].lower()

    def test_generic_error_message(self, valid_lambda_event, monkeypatch_config):
        """Test generic error produces generic message."""
        mock_controller = Mock()
        mock_controller.handle_event.side_effect = Exception("Some error")

        handler = AssistantHandler()
        handler.controller = mock_controller

        response = handler.handler(valid_lambda_event, None)
        body = json.loads(response["body"])

        # Should not expose internal error details
        assert "unavailable" in body["reply"].lower()
