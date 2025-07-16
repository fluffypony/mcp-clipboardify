"""MCP tool implementations for clipboard operations."""

import logging
from typing import Any, Dict

from .clipboard import get_clipboard, set_clipboard, ClipboardError
from .protocol import ErrorCodes
from ._tool_schemas import (
    get_all_tool_definitions,
    validate_tool_exists,
    get_tool_schema,
)

# Configure logging
logger = logging.getLogger(__name__)


def list_tools() -> Dict[str, Any]:
    """
    Return the list of available tools for MCP tools/list request.

    Returns:
        Dict containing the tools array.
    """
    tool_definitions = get_all_tool_definitions()
    return {"tools": list(tool_definitions.values())}


def validate_tool_params(tool_name: str, params: Dict[str, Any]) -> None:
    """
    Validate parameters for a tool call.

    Args:
        tool_name: Name of the tool being called.
        params: Parameters provided for the tool.

    Raises:
        ValueError: If parameters are invalid.
    """
    if not validate_tool_exists(tool_name):
        raise ValueError(f"Unknown tool: {tool_name}")

    _ = get_tool_schema(tool_name)

    if tool_name == "get_clipboard":
        # No parameters required
        if params and len(params) > 0:
            raise ValueError("get_clipboard does not accept parameters")

    elif tool_name == "set_clipboard":
        # Text parameter required
        if not params or "text" not in params:
            raise ValueError("set_clipboard requires 'text' parameter")

        text = params["text"]
        if not isinstance(text, str):
            raise ValueError("'text' parameter must be a string")

        # Additional parameters not allowed
        if len(params) > 1:
            extra_params = set(params.keys()) - {"text"}
            raise ValueError(f"Unexpected parameters: {list(extra_params)}")


def execute_tool(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a tool with the given parameters.

    Args:
        tool_name: Name of the tool to execute.
        params: Parameters for the tool.

    Returns:
        Dict containing the tool execution result.

    Raises:
        ValueError: If tool name is invalid or parameters are wrong.
        RuntimeError: If tool execution fails.
    """
    logger.info("Executing tool: %s", tool_name)

    # Validate parameters first
    validate_tool_params(tool_name, params)

    try:
        if tool_name == "get_clipboard":
            content = get_clipboard()
            logger.debug("Retrieved clipboard content: %s characters", len(content))
            return {"content": [{"type": "text", "text": content}]}

        if tool_name == "set_clipboard":
            text = params["text"]
            set_clipboard(text)
            logger.debug("Set clipboard content: %s characters", len(text))
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Successfully copied {len(text)} characters to clipboard",
                    }
                ]
            }

    except ClipboardError as e:
        logger.error("Clipboard operation failed: %s", e)
        raise RuntimeError(f"Clipboard operation failed: {str(e)}") from e
    except ValueError as e:
        logger.error("Invalid clipboard operation: %s", e)
        raise RuntimeError(f"Invalid operation: {str(e)}") from e
    except Exception as e:
        logger.error("Unexpected error in tool execution: %s", e)
        raise RuntimeError(f"Tool execution failed: {str(e)}") from e

    # This should never be reached
    raise ValueError(f"Unknown tool: {tool_name}")


def get_tool_error_code(error: Exception) -> int:
    """
    Map tool execution errors to JSON-RPC error codes.

    Args:
        error: The exception that occurred.

    Returns:
        Appropriate JSON-RPC error code.
    """
    if isinstance(error, ValueError):
        return ErrorCodes.INVALID_PARAMS
    return ErrorCodes.SERVER_ERROR
