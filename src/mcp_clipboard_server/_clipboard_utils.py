"""Shared utilities for clipboard operations."""

import logging
from typing import Dict, Any

from .clipboard import get_clipboard, set_clipboard

logger = logging.getLogger(__name__)


def execute_get_clipboard() -> Dict[str, Any]:
    """
    Execute get_clipboard operation and return standardized result.
    
    Returns:
        Dict containing the clipboard content in MCP format.
    """
    content = get_clipboard()
    logger.debug("Retrieved clipboard content: %s characters", len(content))
    return {"content": [{"type": "text", "text": content}]}


def execute_set_clipboard(text: str) -> Dict[str, Any]:
    """
    Execute set_clipboard operation and return standardized result.
    
    Args:
        text: Text to set in clipboard.
        
    Returns:
        Dict containing success message in MCP format.
    """
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
