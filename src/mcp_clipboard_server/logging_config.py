"""Logging configuration for MCP clipboard server."""

import logging
import os
import sys
import json
from typing import Any, Dict
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: The log record to format.
            
        Returns:
            JSON-formatted log string.
        """
        # Create base log entry
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add request ID if available (for correlation)
        if hasattr(record, 'request_id') and record.request_id:
            log_entry["request_id"] = record.request_id
        
        # Add thread info if available
        if hasattr(record, 'thread') and record.thread:
            log_entry["thread"] = record.thread
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add any extra fields
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry, ensure_ascii=False)


def setup_logging(log_level: str = None) -> None:
    """
    Configure logging for the MCP server.
    
    Args:
        log_level: Override log level (DEBUG, INFO, WARNING, ERROR).
                  If None, uses MCP_LOG_LEVEL env var or defaults to INFO.
    """
    # Determine log level
    if log_level is None:
        log_level = os.getenv("MCP_LOG_LEVEL", "INFO").upper()
    
    # Validate log level
    numeric_level = getattr(logging, log_level, None)
    if not isinstance(numeric_level, int):
        print(f"Invalid log level: {log_level}, using INFO", file=sys.stderr)
        numeric_level = logging.INFO
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear any existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create stderr handler
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(numeric_level)
    
    # Use JSON formatter if requested, otherwise use simple format
    use_json = os.getenv("MCP_LOG_JSON", "false").lower() in ("true", "1", "yes")
    
    if use_json:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    stderr_handler.setFormatter(formatter)
    root_logger.addHandler(stderr_handler)
    
    # Log initial setup
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured: level={log_level}, json={use_json}")


def get_logger_with_request_id(name: str, request_id: str = None) -> logging.LoggerAdapter:
    """
    Get a logger adapter that includes request ID in all log messages.
    
    Args:
        name: Logger name.
        request_id: Request ID for correlation.
        
    Returns:
        LoggerAdapter with request ID context.
    """
    logger = logging.getLogger(name)
    
    class RequestIDAdapter(logging.LoggerAdapter):
        """Logger adapter that adds request ID to log records."""
        
        def process(self, msg, kwargs):
            """Add request ID to log record."""
            # Add request_id as extra data
            extra = kwargs.get('extra', {})
            if self.extra.get('request_id'):
                extra['request_id'] = self.extra['request_id']
            kwargs['extra'] = extra
            return msg, kwargs
    
    return RequestIDAdapter(logger, {'request_id': request_id})


def log_request(logger: logging.Logger, method: str, params: Any = None, request_id: str = None) -> None:
    """
    Log an incoming request.
    
    Args:
        logger: Logger instance.
        method: Request method name.
        params: Request parameters.
        request_id: Request ID for correlation.
    """
    extra_fields = {
        "request_method": method,
        "request_id": request_id
    }
    
    if params is not None:
        # Don't log sensitive parameters like clipboard content
        if method == "tools/call" and isinstance(params, dict):
            tool_name = params.get("name")
            if tool_name == "set_clipboard":
                # Log only the length of text, not the content
                args = params.get("arguments", {})
                if "text" in args:
                    safe_params = params.copy()
                    safe_params["arguments"] = args.copy()
                    safe_params["arguments"]["text"] = f"<{len(args['text'])} chars>"
                    extra_fields["request_params"] = safe_params
                else:
                    extra_fields["request_params"] = params
            else:
                extra_fields["request_params"] = params
        else:
            extra_fields["request_params"] = params
    
    # Create a log record with extra fields
    record = logger.makeRecord(
        logger.name, logging.INFO, "", 0,
        f"Incoming request: {method}",
        (), None
    )
    record.extra_fields = extra_fields
    logger.handle(record)


def log_response(logger: logging.Logger, method: str, success: bool, 
                request_id: str = None, error_code: int = None) -> None:
    """
    Log a response.
    
    Args:
        logger: Logger instance.
        method: Request method name.
        success: Whether the request was successful.
        request_id: Request ID for correlation.
        error_code: Error code if request failed.
    """
    extra_fields = {
        "response_method": method,
        "response_success": success,
        "request_id": request_id
    }
    
    if error_code is not None:
        extra_fields["error_code"] = error_code
    
    level = logging.INFO if success else logging.ERROR
    message = f"Response: {method} - {'success' if success else 'error'}"
    
    # Create a log record with extra fields
    record = logger.makeRecord(
        logger.name, level, "", 0, message, (), None
    )
    record.extra_fields = extra_fields
    logger.handle(record)


def configure_third_party_loggers() -> None:
    """Configure logging for third-party libraries."""
    # Reduce noise from pyperclip and other dependencies
    logging.getLogger("pyperclip").setLevel(logging.WARNING)
    
    # Set urllib3 to WARNING to reduce HTTP noise
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    # Set requests to WARNING
    logging.getLogger("requests").setLevel(logging.WARNING)


def get_log_level_from_env() -> str:
    """
    Get log level from environment variable.
    
    Returns:
        Log level string (DEBUG, INFO, WARNING, ERROR).
    """
    return os.getenv("MCP_LOG_LEVEL", "INFO").upper()


def is_debug_enabled() -> bool:
    """
    Check if debug logging is enabled.
    
    Returns:
        True if debug logging is enabled.
    """
    return get_log_level_from_env() == "DEBUG"
