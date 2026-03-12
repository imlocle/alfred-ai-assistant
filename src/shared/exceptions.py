from shared.responses import get_headers


class InvalidQuestionError(Exception):
    """Raised when the user provides an invalid or empty question."""

    def __init__(
        self,
        message="Invalid or empty question provided",
        question=None,
    ):
        super().__init__(message)
        self.question = question
        self.http_status = 400
        self.headers = get_headers()


class ChatbotProcessingError(Exception):
    """Raised for general chatbot processing errors."""

    def __init__(self, message="Error processing chatbot request", details=None):
        super().__init__(message)
        self.details = details
        self.http_status = 500
        self.headers = get_headers()


class CORSOriginError(Exception):
    """Raised when the request origin is not allowed."""

    def __init__(self, message="Unauthorized origin", origin=None):
        super().__init__(message)
        self.origin = origin
        self.http_status = 403  # Forbidden
        self.headers = get_headers()


class RateLimitError(Exception):
    def __init__(self, message="Rate limit exceeded. Please try again tomorrow."):
        super().__init__(message)
        self.http_status = 429
        self.headers = get_headers()
