from shared.responses import get_headers


class BaseError(Exception):
    """Base class for all application errors with HTTP status and headers."""

    def __init__(self, message: str, error_code: str = None, http_status: int = 500):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.http_status = http_status
        self.headers = get_headers()

    def to_dict(self):
        """Convert error to dictionary for JSON response."""
        return {
            "error": self.error_code,
            "message": self.message,
        }


class InvalidQuestionError(BaseError):
    """Raised when the user provides an invalid or empty question."""

    def __init__(
        self,
        message="Invalid or empty question provided",
        question=None,
    ):
        super().__init__(message, error_code="INVALID_QUESTION", http_status=400)
        self.question = question


class ChatbotProcessingError(BaseError):
    """Raised for general chatbot processing errors."""

    def __init__(self, message="Error processing chatbot request", details=None):
        super().__init__(message, error_code="CHATBOT_ERROR", http_status=500)
        self.details = details

    def to_dict(self):
        """Include details in error response if available."""
        result = super().to_dict()
        if self.details:
            result["details"] = self.details
        return result


class CORSOriginError(BaseError):
    """Raised when the request origin is not allowed."""

    def __init__(self, message="Unauthorized origin", origin=None):
        super().__init__(message, error_code="CORS_ERROR", http_status=403)
        self.origin = origin


class RateLimitError(BaseError):
    """Raised when the rate limit has been exceeded."""

    def __init__(self, message="Rate limit exceeded. Please try again tomorrow."):
        super().__init__(message, error_code="RATE_LIMIT_EXCEEDED", http_status=429)
