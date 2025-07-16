"""JSON Schema definitions for MCP tool input parameters."""

from typing import Dict, Any, List
from .protocol_types import ToolDefinition


# Schema for get_clipboard tool (no parameters)
GET_CLIPBOARD_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {},
    "required": [],
    "additionalProperties": False
}

# Schema for set_clipboard tool
SET_CLIPBOARD_SCHEMA: Dict[str, Any] = {
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

# Complete tool definitions with schemas
TOOL_DEFINITIONS: Dict[str, ToolDefinition] = {
    "get_clipboard": {
        "name": "get_clipboard",
        "description": "Get the current text content from the system clipboard",
        "inputSchema": GET_CLIPBOARD_SCHEMA
    },
    "set_clipboard": {
        "name": "set_clipboard",
        "description": "Set the system clipboard to the provided text content",
        "inputSchema": SET_CLIPBOARD_SCHEMA
    }
}


def get_tool_schema(tool_name: str) -> Dict[str, Any]:
    """
    Get the JSON schema for a specific tool.
    
    Args:
        tool_name: Name of the tool.
        
    Returns:
        Dict containing the JSON schema.
        
    Raises:
        KeyError: If tool name is not found.
    """
    if tool_name not in TOOL_DEFINITIONS:
        raise KeyError(f"Unknown tool: {tool_name}")
    
    return TOOL_DEFINITIONS[tool_name]["inputSchema"]


def get_all_tool_definitions() -> Dict[str, ToolDefinition]:
    """
    Get all tool definitions.
    
    Returns:
        Dict mapping tool names to their definitions.
    """
    return TOOL_DEFINITIONS.copy()


def validate_tool_exists(tool_name: str) -> bool:
    """
    Check if a tool exists.
    
    Args:
        tool_name: Name of the tool to check.
        
    Returns:
        True if tool exists, False otherwise.
    """
    return tool_name in TOOL_DEFINITIONS


def get_tool_names() -> List[str]:
    """
    Get list of all available tool names.
    
    Returns:
        List of tool names.
    """
    return list(TOOL_DEFINITIONS.keys())
