"""
Shared RequestContext for extracting and managing Lambda event context.
Used by handlers for error logging and request metadata.
"""

import json
from typing import Dict, Any, Optional


class RequestContext:
    """
    Shared context object that extracts and caches relevant data from Lambda events.

    Features:
    - Lazy loading: Data extracted only when accessed
    - Caching: Each property extracted once per request
    """

    def __init__(self, event: Dict[str, Any]):
        self.event = event
        self._claims_cache: Optional[Dict[str, Any]] = None
        self._body_cache: Optional[Dict[str, Any]] = None

    @property
    def claims(self) -> Dict[str, Any]:
        """JWT claims from the authorizer"""
        if self._claims_cache is None:
            self._claims_cache = (
                self.event.get("requestContext", {})
                .get("authorizer", {})
                .get("jwt", {})
                .get("claims", {})
            ) or {}
        return self._claims_cache

    @property
    def body(self) -> Dict[str, Any]:
        """Parsed request body"""
        if self._body_cache is None:
            raw_body = self.event.get("body") or "{}"
            try:
                parsed = json.loads(raw_body)
                self._body_cache = parsed if isinstance(parsed, dict) else {}
            except json.JSONDecodeError:
                self._body_cache = {}
        return self._body_cache

    @property
    def raw_body(self) -> Optional[str]:
        """Raw request body string"""
        return self.event.get("body")

    @property
    def path_params(self) -> Dict[str, Any]:
        """Path parameters"""
        return self.event.get("pathParameters") or {}

    @property
    def query_params(self) -> Dict[str, Any]:
        """Query string parameters"""
        return self.event.get("queryStringParameters") or {}

    @property
    def user_id(self) -> Optional[str]:
        """User ID from JWT claims"""
        return self.claims.get("sub")

    @property
    def email(self) -> Optional[str]:
        """Email from JWT claims"""
        return self.claims.get("email")

    @property
    def request_id(self) -> Optional[str]:
        """AWS request ID"""
        return self.event.get("requestContext", {}).get("requestId")

    @property
    def http_method(self) -> Optional[str]:
        """HTTP method (GET, POST, etc.)"""
        return self.event.get("httpMethod") or self.event.get("requestContext", {}).get(
            "http", {}
        ).get("method")

    @property
    def path(self) -> Optional[str]:
        """Request path"""
        return self.event.get("requestContext", {}).get("path") or self.event.get(
            "rawPath"
        )

    @property
    def logging_context(self) -> Dict[str, Any]:
        """
        Context dictionary optimized for logging.
        Includes all relevant request information.
        """
        context = {
            "user_id": self.user_id,
            "email": self.email,
            "request_id": self.request_id,
            "http_method": self.http_method,
            "path": self.path,
        }

        # Add query params if present
        if self.query_params:
            context["query_params"] = self.query_params

        # Add body length for POST/PUT
        if self.raw_body:
            context["request_body_length"] = len(self.raw_body)

        # Remove None values
        return {k: v for k, v in context.items() if v is not None}

    def log_error(self, error: Exception, operation: str, **additional_context):
        """
        Log error with full request context.

        Args:
            error: The exception to log
            operation: Name of the operation that failed
            **additional_context: Extra context to include
        """
        context = {**self.logging_context, **additional_context}
        from handlers.error_handler import log_error_with_context

        log_error_with_context(error, operation=operation, **context)
