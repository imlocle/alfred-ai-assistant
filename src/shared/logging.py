import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add dynamic fields passed via extra={}
        request_id = getattr(record, "request_id", None)
        if request_id is not None:
            log_data["request_id"] = request_id
        
        user_id = getattr(record, "user_id", None)
        if user_id is not None:
            log_data["user_id"] = user_id
        
        extra_data = getattr(record, "extra_data", None)
        if extra_data is not None:
            log_data.update(extra_data)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with JSON formatting.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only add handler if not already configured
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
    
    return logger


def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    **kwargs: Any
) -> None:
    """
    Log a message with additional context.
    
    Args:
        logger: Logger instance
        level: Log level (INFO, WARNING, ERROR, etc.)
        message: Log message
        request_id: Optional request ID for correlation
        user_id: Optional user ID
        **kwargs: Additional fields to include in log
    """
    extra: Dict[str, Any] = {}
    
    if request_id:
        extra["request_id"] = request_id
    if user_id:
        extra["user_id"] = user_id
    if kwargs:
        extra["extra_data"] = kwargs
    
    log_method = getattr(logger, level.lower(), logger.info)
    log_method(message, extra=extra)
