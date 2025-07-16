"""Centralized error handling and code definitions for MCP server."""

import json
import logging
from typing import Any, Callable, Dict, Optional, Type, Union

from ._validators import ValidationException


class ClipboardError(Exception):
    """Custom exception for clipboard operation failures."""


logger = logging.getLogger(__name__)


class ErrorCodes:  # pylint: disable=too-few-public-methods
    """JSON-RPC 2.0 and MCP-specific error codes."""

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    SERVER_ERROR = -32000
    CLIPBOARD_ERROR = -32001


# MCP-specific error codes (extending JSON-RPC standard codes)
class MCPErrorCodes:  # pylint: disable=too-few-public-methods
    """Extended error codes for MCP-specific errors."""

    # Standard JSON-RPC 2.0 error codes
    PARSE_ERROR = ErrorCodes.PARSE_ERROR  # -32700
    INVALID_REQUEST = ErrorCodes.INVALID_REQUEST  # -32600
    METHOD_NOT_FOUND = ErrorCodes.METHOD_NOT_FOUND  # -32601
    INVALID_PARAMS = ErrorCodes.INVALID_PARAMS  # -32602
    INTERNAL_ERROR = ErrorCodes.INTERNAL_ERROR  # -32603

    # MCP server errors
    SERVER_ERROR = ErrorCodes.SERVER_ERROR  # -32000

    # Custom application errors (in the reserved range -32099 to -32000)
    CLIPBOARD_ERROR = -32001  # Clipboard operation failed
    VALIDATION_ERROR = -32002  # Parameter validation failed
    INITIALIZATION_ERROR = -32003  # Server not initialized


# Error code to message mapping
ERROR_MESSAGES: Dict[int, str] = {
    MCPErrorCodes.PARSE_ERROR: "Parse error",
    MCPErrorCodes.INVALID_REQUEST: "Invalid Request",
    MCPErrorCodes.METHOD_NOT_FOUND: "Method not found",
    MCPErrorCodes.INVALID_PARAMS: "Invalid params",
    MCPErrorCodes.INTERNAL_ERROR: "Internal error",
    MCPErrorCodes.SERVER_ERROR: "Server error",
    MCPErrorCodes.CLIPBOARD_ERROR: "Clipboard operation failed",
    MCPErrorCodes.VALIDATION_ERROR: "Parameter validation failed",
    MCPErrorCodes.INITIALIZATION_ERROR: "Server not initialized",
}


# Exception to error code mapping
EXCEPTION_TO_ERROR_CODE: Dict[
    Type[Exception], Union[int, Callable[[Exception], int]]
] = {
    ValueError: MCPErrorCodes.INVALID_PARAMS,
    ValidationException: MCPErrorCodes.INVALID_PARAMS,
    ClipboardError: MCPErrorCodes.CLIPBOARD_ERROR,
    TypeError: MCPErrorCodes.INVALID_PARAMS,
    KeyError: MCPErrorCodes.INVALID_PARAMS,
    AttributeError: MCPErrorCodes.INTERNAL_ERROR,
    RuntimeError: MCPErrorCodes.SERVER_ERROR,
}


def get_error_message(error_code: int, custom_message: Optional[str] = None) -> str:
    """
    Get a human-readable error message for an error code.

    Args:
        error_code: The JSON-RPC error code.
        custom_message: Optional custom message to use instead of default.

    Returns:
        Error message string.
    """
    if custom_message:
        return custom_message

    return ERROR_MESSAGES.get(error_code, "Unknown error")


def create_error_response_for_exception(request_id: Any, exception: Exception) -> str:
    """
    Create a JSON-RPC error response for an exception.

    Args:
        request_id: The ID from the original request.
        exception: The exception that occurred.

    Returns:
        JSON-encoded error response.
    """
    error_code = get_error_code_for_exception(exception)
    error_message = str(exception) or get_error_message(error_code)

    # Log the error for debugging
    logger.error("Error %s: %s", error_code, error_message, exc_info=exception)

    # Create error response locally to avoid circular import
    response = {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": error_code, "message": error_message},
    }
    return json.dumps(response)


def safe_execute(
    request_id: Any, operation: Callable[..., Any], *args, **kwargs
) -> str:
    """
    Safely execute an operation and return appropriate response.

    Args:
        request_id: The ID from the original request.
        operation: The operation to execute.
        *args: Positional arguments for the operation.
        **kwargs: Keyword arguments for the operation.

    Returns:
        Either a success response or a JSON error response.
    """
    try:
        result = operation(*args, **kwargs)
        logger.debug("Operation executed successfully")
        # Create success response locally to avoid circular import
        response = {"jsonrpc": "2.0", "id": request_id, "result": result}
        return json.dumps(response)
    except Exception as e:  # pylint: disable=broad-except
        return create_error_response_for_exception(request_id, e)


class MCPError(Exception):
    """Base exception class for MCP-specific errors."""

    def __init__(self, message: str, error_code: int = MCPErrorCodes.SERVER_ERROR):
        """
        Initialize MCP error.

        Args:
            message: Error message.
            error_code: JSON-RPC error code.
        """
        super().__init__(message)
        self.error_code = error_code


class InitializationError(MCPError):
    """Raised when server is not properly initialized."""

    def __init__(self, message: str = "Server not initialized"):
        super().__init__(message, MCPErrorCodes.INITIALIZATION_ERROR)


class ValidationError(MCPError):
    """Raised when parameter validation fails."""

    def __init__(self, message: str):
        super().__init__(message, MCPErrorCodes.VALIDATION_ERROR)


# Update exception mapping to include custom exceptions
EXCEPTION_TO_ERROR_CODE.update(
    {
        MCPError: lambda e: getattr(e, "error_code", MCPErrorCodes.SERVER_ERROR),
        InitializationError: MCPErrorCodes.INITIALIZATION_ERROR,
        ValidationError: MCPErrorCodes.VALIDATION_ERROR,
    }
)


def get_error_code_for_exception(exception: Exception) -> int:
    """
    Map an exception to the appropriate JSON-RPC error code.
    Updated to handle custom MCP exceptions.

    Args:
        exception: The exception that occurred.

    Returns:
        Appropriate JSON-RPC error code.
    """
    exception_type = type(exception)

    # Handle custom MCP exceptions with error_code attribute
    if hasattr(exception, "error_code"):
        return exception.error_code

    # Check for exact type match first
    if exception_type in EXCEPTION_TO_ERROR_CODE:
        error_code_or_func = EXCEPTION_TO_ERROR_CODE[exception_type]
        # Handle callable mappings
        if callable(error_code_or_func):
            return error_code_or_func(exception)  # pylint: disable=not-callable
        return error_code_or_func

    # Check for inheritance (e.g., custom ValueError subclasses)
    for exc_type, error_code_or_func in EXCEPTION_TO_ERROR_CODE.items():
        if isinstance(exception, exc_type):
            # Handle callable mappings
            if callable(error_code_or_func):
                return error_code_or_func(exception)  # pylint: disable=not-callable
            return error_code_or_func

    # Default to internal error for unknown exceptions
    logger.warning("Unknown exception type: %s", exception_type.__name__)
    return MCPErrorCodes.INTERNAL_ERROR
