"""Unit tests for exceptions module."""

import pytest
from shared.exceptions import (
    InvalidQuestionError,
    ChatbotProcessingError,
    CORSOriginError,
    RateLimitError,
)


class TestInvalidQuestionError:
    """Test InvalidQuestionError exception."""

    def test_invalid_question_error_creation(self):
        """Test creating InvalidQuestionError."""
        error = InvalidQuestionError(message="Test error", question="test?")
        assert str(error) == "Test error"
        assert error.http_status == 400
        assert error.question == "test?"

    def test_invalid_question_error_has_headers(self):
        """Test that error includes CORS headers."""
        error = InvalidQuestionError()
        assert "Content-Type" in error.headers
        assert "Access-Control-Allow-Origin" in error.headers

    def test_invalid_question_error_default_message(self):
        """Test default error message."""
        error = InvalidQuestionError()
        assert "Invalid or empty question" in str(error)


class TestCORSOriginError:
    """Test CORSOriginError exception."""

    def test_cors_origin_error_creation(self):
        """Test creating CORSOriginError."""
        error = CORSOriginError(origin="https://evil.com")
        assert error.http_status == 403
        assert error.origin == "https://evil.com"

    def test_cors_origin_error_has_headers(self):
        """Test that CORS error includes headers."""
        error = CORSOriginError()
        assert "Content-Type" in error.headers
        assert error.http_status == 403

    def test_cors_origin_error_default_message(self):
        """Test default CORS error message."""
        error = CORSOriginError()
        assert "Unauthorized origin" in str(error)


class TestRateLimitError:
    """Test RateLimitError exception."""

    def test_rate_limit_error_creation(self):
        """Test creating RateLimitError."""
        error = RateLimitError()
        assert error.http_status == 429
        assert "Rate limit exceeded" in str(error)

    def test_rate_limit_error_default_message(self):
        """Test default rate limit message."""
        error = RateLimitError(message="Custom message")
        assert "Custom message" in str(error)

    def test_rate_limit_error_has_headers(self):
        """Test that error includes headers."""
        error = RateLimitError()
        assert "Content-Type" in error.headers


class TestChatbotProcessingError:
    """Test ChatbotProcessingError exception."""

    def test_chatbot_processing_error_creation(self):
        """Test creating ChatbotProcessingError."""
        error = ChatbotProcessingError(details="Something went wrong")
        assert error.http_status == 500
        assert error.details == "Something went wrong"

    def test_chatbot_processing_error_has_headers(self):
        """Test that error includes headers."""
        error = ChatbotProcessingError()
        assert "Content-Type" in error.headers
        assert error.http_status == 500

    def test_chatbot_processing_error_default_message(self):
        """Test default error message."""
        error = ChatbotProcessingError()
        assert "Error processing chatbot request" in str(error)
