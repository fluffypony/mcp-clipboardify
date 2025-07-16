"""MCP tool implementations for clipboard operations."""

import logging
from typing import Any, Dict, List

from .clipboard import get_clipboard, set_clipboard, ClipboardError
from .protocol import ErrorCodes

# Configure logging
logger = logging.getLogger(__name__)

# Tool definitions following MCP schema
TOOLS = {
    "get_clipboard": {
        "name": "get_clipboard",
        "description": "Get the current text content from the system clipboard",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
    },
    "set_clipboard": {
        "name": "set_clipboard", 
        "description": "Set the system clipboard to the provided text content",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text content to copy to the clipboard",
                    "maxLength": 1048576  # 1MB limit
                }
            },
            "required": ["text"],
            "additionalProperties": False
        }
    }
}


def list_tools() -> Dict[str, Any]:
    """
    Return the list of available tools for MCP tools/list request.
    
    Returns:
        Dict containing the tools array.
    """
    return {"tools": list(TOOLS.values())}


def validate_tool_params(tool_name: str, params: Dict[str, Any]) -> None:
    """
    Validate parameters for a tool call.
    
    Args:
        tool_name: Name of the tool being called.
        params: Parameters provided for the tool.
        
    Raises:
        ValueError: If parameters are invalid.
    """
    if tool_name not in TOOLS:
        raise ValueError(f"Unknown tool: {tool_name}")
    
    tool_schema = TOOLS[tool_name]["inputSchema"]
    
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
    logger.info(f"Executing tool: {tool_name}")
    
    # Validate parameters first
    validate_tool_params(tool_name, params)
    
    try:
        if tool_name == "get_clipboard":
            content = get_clipboard()
            logger.debug(f"Retrieved clipboard content: {len(content)} characters")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": content
                    }
                ]
            }
            
        elif tool_name == "set_clipboard":
            text = params["text"]
            set_clipboard(text)
            logger.debug(f"Set clipboard content: {len(text)} characters")
            return {
                "content": [
                    {
                        "type": "text", 
                        "text": f"Successfully copied {len(text)} characters to clipboard"
                    }
                ]
            }
            
    except ClipboardError as e:
        logger.error(f"Clipboard operation failed: {e}")
        raise RuntimeError(f"Clipboard operation failed: {str(e)}") from e
    except ValueError as e:
        logger.error(f"Invalid clipboard operation: {e}")
        raise RuntimeError(f"Invalid operation: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error in tool execution: {e}")
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
    else:
        return ErrorCodes.SERVER_ERROR
