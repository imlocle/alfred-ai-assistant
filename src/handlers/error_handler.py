"""
Error handling utilities for consistent error responses across the application.
"""

import json
import traceback
from typing import Dict, Any, Tuple

from shared.responses import CORS_HEADERS
from shared.exceptions import BaseError


def handle_error(error: Exception, include_traceback: bool = False) -> Tuple[int, str]:
    """
    Handle any exception and return appropriate HTTP status code and response body.

    Args:
        error: The exception to handle
        include_traceback: Whether to include stack trace in response (dev only)

    Returns:
        Tuple of (status_code, response_body_json)
    """
    if isinstance(error, BaseError):
        return _handle_base_error(error, include_traceback)
    else:
        return _handle_unknown_error(error, include_traceback)


def _handle_base_error(error: BaseError, include_traceback: bool) -> Tuple[int, str]:
    """Handle known BaseError exceptions"""
    response_body = error.to_dict()

    if include_traceback:
        response_body["traceback"] = traceback.format_exc()

    return error.http_status, json.dumps(response_body)


def _handle_unknown_error(error: Exception, include_traceback: bool) -> Tuple[int, str]:
    """Handle unknown exceptions"""
    response_body = {
        "error": "INTERNAL_SERVER_ERROR",
        "message": "An unexpected error occurred",
    }

    if include_traceback:
        response_body["details"] = {
            "error_type": error.__class__.__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
        }

    return 500, json.dumps(response_body)


def create_error_response(status_code: int, error_body: str) -> Dict[str, Any]:
    """
    Create a standardized Lambda response for errors.

    Args:
        status_code: HTTP status code
        error_body: JSON string of error details

    Returns:
        Lambda response dictionary
    """
    return {
        "statusCode": status_code,
        "headers": {**CORS_HEADERS},
        "body": error_body,
    }


def error_response(error: Exception, include_traceback: bool = False) -> Dict[str, Any]:
    """
    Convenience function to handle error and create Lambda response in one call.

    Args:
        error: The exception to handle
        include_traceback: Whether to include stack trace (dev only)

    Returns:
        Complete Lambda response dictionary
    """
    status_code, body = handle_error(error, include_traceback)
    return create_error_response(status_code, body)


# Context manager for error handling
class ErrorHandler:
    """Context manager for consistent error handling in Lambda functions"""

    def __init__(self, include_traceback: bool = False):
        self.include_traceback = include_traceback

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Log the error (in production, this would go to CloudWatch)
            print(f"Error occurred: {exc_type.__name__}: {exc_val}")
            if self.include_traceback:
                print(traceback.format_exc())
        return False  # Don't suppress the exception

    def handle(self, error: Exception) -> Dict[str, Any]:
        """Handle an error and return Lambda response"""
        return error_response(error, self.include_traceback)


# Decorator for Lambda handlers
def handle_errors(include_traceback: bool = False):
    """
    Decorator to automatically handle errors in Lambda handlers.

    Args:
        include_traceback: Whether to include stack traces in responses

    Usage:
        @handle_errors(include_traceback=True)  # Dev environment
        def lambda_handler(event, context):
            # Your handler code
            pass
    """

    def decorator(func):
        def wrapper(event, context):
            try:
                return func(event, context)
            except Exception as e:
                return error_response(e, include_traceback)

        return wrapper

    return decorator


# Error logging utilities
def log_error(error: Exception, context: Dict[str, Any] = None):
    """
    Log error with context for monitoring and debugging.

    Args:
        error: The exception that occurred
        context: Additional context (user_id, request_id, etc.)
    """
    error_info = {
        "error_type": error.__class__.__name__,
        "error_message": str(error),
        "context": context or {},
    }

    if isinstance(error, BaseError):
        error_info.update(
            {
                "error_code": error.error_code,
                "details": error.details,
                "http_status": error.http_status,
            }
        )

    # In production, this would use structured logging
    print(f"ERROR: {json.dumps(error_info, indent=2)}")


def log_error_with_context(
    error: Exception,
    user_id: str = None,
    request_id: str = None,
    operation: str = None,
    **kwargs,
):
    """
    Log error with common context fields.

    Args:
        error: The exception that occurred
        user_id: User who triggered the error
        request_id: Request identifier
        operation: Operation being performed
        **kwargs: Additional context fields
    """
    context = {
        "user_id": user_id,
        "request_id": request_id,
        "operation": operation,
        **kwargs,
    }
    # Remove None values
    context = {k: v for k, v in context.items() if v is not None}

    log_error(error, context)
