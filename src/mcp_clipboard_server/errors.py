"""Centralized error handling and code definitions for MCP server."""

import logging
from typing import Dict, Type, Any
from .protocol import ErrorCodes
from .clipboard import ClipboardError

logger = logging.getLogger(__name__)


# MCP-specific error codes (extending JSON-RPC standard codes)
class MCPErrorCodes:
    """Extended error codes for MCP-specific errors."""
    
    # Standard JSON-RPC 2.0 error codes
    PARSE_ERROR = ErrorCodes.PARSE_ERROR           # -32700
    INVALID_REQUEST = ErrorCodes.INVALID_REQUEST   # -32600
    METHOD_NOT_FOUND = ErrorCodes.METHOD_NOT_FOUND # -32601
    INVALID_PARAMS = ErrorCodes.INVALID_PARAMS     # -32602
    INTERNAL_ERROR = ErrorCodes.INTERNAL_ERROR     # -32603
    
    # MCP server errors
    SERVER_ERROR = ErrorCodes.SERVER_ERROR         # -32000
    
    # Custom application errors (in the reserved range -32099 to -32000)
    CLIPBOARD_ERROR = -32001                       # Clipboard operation failed
    VALIDATION_ERROR = -32002                      # Parameter validation failed
    INITIALIZATION_ERROR = -32003                  # Server not initialized


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
EXCEPTION_TO_ERROR_CODE: Dict[Type[Exception], int] = {
    ValueError: MCPErrorCodes.INVALID_PARAMS,
    ClipboardError: MCPErrorCodes.CLIPBOARD_ERROR,
    TypeError: MCPErrorCodes.INVALID_PARAMS,
    KeyError: MCPErrorCodes.INVALID_PARAMS,
    AttributeError: MCPErrorCodes.INTERNAL_ERROR,
    RuntimeError: MCPErrorCodes.SERVER_ERROR,
}


def get_error_code_for_exception(exception: Exception) -> int:
    """
    Map an exception to the appropriate JSON-RPC error code.
    
    Args:
        exception: The exception that occurred.
        
    Returns:
        Appropriate JSON-RPC error code.
    """
    exception_type = type(exception)
    
    # Check for exact type match first
    if exception_type in EXCEPTION_TO_ERROR_CODE:
        return EXCEPTION_TO_ERROR_CODE[exception_type]
    
    # Check for inheritance (e.g., custom ValueError subclasses)
    for exc_type, error_code in EXCEPTION_TO_ERROR_CODE.items():
        if isinstance(exception, exc_type):
            return error_code
    
    # Default to internal error for unknown exceptions
    logger.warning(f"Unknown exception type: {exception_type.__name__}")
    return MCPErrorCodes.INTERNAL_ERROR


def get_error_message(error_code: int, custom_message: str = None) -> str:
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
    from .protocol import create_error_response
    
    error_code = get_error_code_for_exception(exception)
    error_message = str(exception) or get_error_message(error_code)
    
    # Log the error for debugging
    logger.error(f"Error {error_code}: {error_message}", exc_info=exception)
    
    return create_error_response(request_id, error_code, error_message)


def safe_execute(request_id: Any, operation: callable, *args, **kwargs) -> str:
    """
    Safely execute an operation and return appropriate error response if it fails.
    
    Args:
        request_id: The ID from the original request.
        operation: The operation to execute.
        *args: Positional arguments for the operation.
        **kwargs: Keyword arguments for the operation.
        
    Returns:
        Either the operation result or a JSON error response.
    """
    try:
        return operation(*args, **kwargs)
    except Exception as e:
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
EXCEPTION_TO_ERROR_CODE.update({
    MCPError: lambda e: e.error_code,
    InitializationError: MCPErrorCodes.INITIALIZATION_ERROR,
    ValidationError: MCPErrorCodes.VALIDATION_ERROR,
})


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
    if hasattr(exception, 'error_code'):
        return exception.error_code
    
    # Check for exact type match first
    if exception_type in EXCEPTION_TO_ERROR_CODE:
        error_code = EXCEPTION_TO_ERROR_CODE[exception_type]
        # Handle callable mappings
        if callable(error_code):
            return error_code(exception)
        return error_code
    
    # Check for inheritance (e.g., custom ValueError subclasses)
    for exc_type, error_code in EXCEPTION_TO_ERROR_CODE.items():
        if isinstance(exception, exc_type):
            if callable(error_code):
                return error_code(exception)
            return error_code
    
    # Default to internal error for unknown exceptions
    logger.warning(f"Unknown exception type: {exception_type.__name__}")
    return MCPErrorCodes.INTERNAL_ERROR
