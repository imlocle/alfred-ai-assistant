"""
Base handler class with common functionality for all Lambda handlers.
Uses shared RequestContext for context extraction.
"""

import os
from typing import Dict, Any, Callable
from .error_handler import handle_errors
from shared.request_context import RequestContext


class BaseHandler:
    """
    Base class for all Lambda handlers.

    Uses RequestContext for:
    - Error logging context
    - Request metadata

    The RequestContext is shared with Controllers to avoid duplicate extraction.
    """

    def __init__(self, event: Dict[str, Any]):
        self.event = event
        self.request_context = RequestContext(event)

    @property
    def context(self) -> RequestContext:
        """Alias for request_context for convenience"""
        return self.request_context

    def log_error(self, error: Exception, operation: str, **additional_context):
        """Log error with full request context"""
        self.request_context.log_error(error, operation, **additional_context)

    def handle_with_logging(self, operation: str, handler_func: Callable):
        """
        Execute handler function with automatic error logging.

        Args:
            operation: Name of the operation (for logging)
            handler_func: Function to execute

        Returns:
            Result of handler_func

        Raises:
            Any exception from handler_func (after logging)
        """
        try:
            return handler_func()
        except Exception as e:
            self.log_error(e, operation)
            raise


def lambda_handler_with_errors(operation_name: str):
    """
    Decorator factory for Lambda handlers with automatic error handling.

    Args:
        operation_name: Name of the operation (for logging)

    Usage:
        @lambda_handler_with_errors("create_todo")
        def lambda_handler(event, context):
            return MyHandler(event).handler()
    """

    def decorator(handler_func: Callable):
        @handle_errors(include_traceback=os.environ.get("ENVIRONMENT", "prod") == "dev")
        def wrapper(event, context):
            return handler_func(event, context)

        return wrapper

    return decorator
