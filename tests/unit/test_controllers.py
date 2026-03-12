"""Unit tests for the query controller."""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from controllers.query_controller import QueryController
from shared.exceptions import InvalidQuestionError, CORSOriginError


class TestQueryController:
    """Test QueryController request handling."""

    def test_handle_valid_event(self, valid_lambda_event, monkeypatch_config):
        """Test handling a valid Lambda event."""
        mock_service = Mock()
        mock_service.ask = Mock(return_value="Test response")

        controller = QueryController(assistant_service=mock_service)
        result = controller.handle_event(valid_lambda_event, "test-123")

        assert result == "Test response"
        mock_service.ask.assert_called_once()
        # ask(user_id, question, current_date, request_id)
        assert (
            mock_service.ask.call_args[0][1] == "What is your experience?"
        )  # question is 2nd positional arg

    def test_handle_event_cors_validation_success(
        self, valid_lambda_event, monkeypatch_config
    ):
        """Test that valid origin passes CORS validation."""
        mock_service = Mock()
        mock_service.ask = Mock(return_value="Response")

        controller = QueryController(assistant_service=mock_service)
        result = controller.handle_event(valid_lambda_event, "test-123")

        assert result == "Response"

    def test_handle_event_cors_validation_failure(self, invalid_origin_event):
        """Test that invalid origin raises CORSOriginError."""
        controller = QueryController()

        with pytest.raises(CORSOriginError) as exc_info:
            controller.handle_event(invalid_origin_event, "test-124")

        assert exc_info.value.origin == "https://malicious.com"
        assert exc_info.value.http_status == 403

    def test_handle_event_invalid_question(
        self, invalid_question_event, monkeypatch_config
    ):
        """Test that invalid question raises InvalidQuestionError."""
        controller = QueryController()

        with pytest.raises(InvalidQuestionError) as exc_info:
            controller.handle_event(invalid_question_event, "test-125")

        assert exc_info.value.http_status == 400

    def test_handle_event_extracts_user_id_from_headers(
        self, valid_lambda_event, monkeypatch_config
    ):
        """Test that user_id is extracted from x-forwarded-for header."""
        mock_service = Mock()
        mock_service.ask = Mock(return_value="Response")

        controller = QueryController(assistant_service=mock_service)
        controller.handle_event(valid_lambda_event, "test-123")

        # ask(user_id, question, current_date, request_id) - user_id is 1st arg
        assert mock_service.ask.call_args[0][0] == "192.168.1.1"

    def test_handle_event_sanitizes_question(
        self, valid_lambda_event, monkeypatch_config
    ):
        """Test that question is sanitized."""
        mock_service = Mock()
        mock_service.ask = Mock(return_value="Response")

        # Modify event with extra whitespace
        event = valid_lambda_event.copy()
        event["body"] = json.dumps({"question": "  What  is  your  experience?  "})

        controller = QueryController(assistant_service=mock_service)
        controller.handle_event(event, "test-123")

        # ask(user_id, question, current_date, request_id) - question is 2nd arg
        # Question should be normalized (no double spaces)
        assert mock_service.ask.call_args[0][1] == "What is your experience?"

    def test_handle_event_extracts_date_from_epoch(
        self, valid_lambda_event, monkeypatch_config
    ):
        """Test that current_date is extracted from timeEpoch."""
        mock_service = Mock()
        mock_service.ask = Mock(return_value="Response")

        controller = QueryController(assistant_service=mock_service)
        controller.handle_event(valid_lambda_event, "test-123")

        # ask(user_id, question, current_date, request_id) - current_date is 3rd arg
        # timeEpoch: 1678300800000 ms = 1678300800 s = 2023-03-08
        assert mock_service.ask.call_args[0][2] == "2023-03-08"

    def test_handle_event_passes_request_id(
        self, valid_lambda_event, monkeypatch_config
    ):
        """Test that request_id is passed to service."""
        mock_service = Mock()
        mock_service.ask = Mock(return_value="Response")

        controller = QueryController(assistant_service=mock_service)
        controller.handle_event(valid_lambda_event, "custom-request-id")

        # ask(user_id, question, current_date, request_id) - request_id is 4th arg
        assert mock_service.ask.call_args[0][3] == "custom-request-id"

    def test_handle_event_parses_json_body(
        self, valid_lambda_event, monkeypatch_config
    ):
        """Test that JSON body is parsed correctly."""
        mock_service = Mock()
        mock_service.ask = Mock(return_value="Response")

        controller = QueryController(assistant_service=mock_service)
        result = controller.handle_event(valid_lambda_event, "test-123")

        assert result == "Response"

    def test_handle_event_with_dict_body(self, valid_lambda_event, monkeypatch_config):
        """Test handling event with dict body (not JSON string)."""
        mock_service = Mock()
        mock_service.ask = Mock(return_value="Response")

        event = valid_lambda_event.copy()
        event["body"] = {"question": "What are your skills?"}  # Already dict

        controller = QueryController(assistant_service=mock_service)
        result = controller.handle_event(event, "test-123")

        assert result == "Response"
        # ask(user_id, question, current_date, request_id) - question is 2nd arg
        assert mock_service.ask.call_args[0][1] == "What are your skills?"

    def test_handle_event_default_user_id_anonymous(
        self, valid_lambda_event, monkeypatch_config
    ):
        """Test that default user_id is 'anonymous' if header missing."""
        mock_service = Mock()
        mock_service.ask = Mock(return_value="Response")

        event = valid_lambda_event.copy()
        event["headers"] = {"origin": "http://localhost:5173"}  # No x-forwarded-for

        controller = QueryController(assistant_service=mock_service)
        controller.handle_event(event, "test-123")

        # ask(user_id, question, current_date, request_id) - user_id is 1st arg
        assert mock_service.ask.call_args[0][0] == "anonymous"


class TestQueryControllerInit:
    """Test QueryController initialization."""

    def test_init_with_default_service(self):
        """Test initialization with default service."""
        controller = QueryController()
        assert controller.assistant_service is not None

    def test_init_with_custom_service(self):
        """Test initialization with custom service."""
        mock_service = Mock()
        controller = QueryController(assistant_service=mock_service)
        assert controller.assistant_service == mock_service
