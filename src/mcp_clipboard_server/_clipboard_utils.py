"""Shared utilities for clipboard operations."""

import logging

from ._protocol_types import ToolCallResult
from .clipboard import get_clipboard, set_clipboard

logger = logging.getLogger(__name__)


def execute_get_clipboard() -> ToolCallResult:
    """
    Execute get_clipboard operation and return standardized result.

    Returns:
        ToolCallResult containing the clipboard content in MCP format.
    """
    content = get_clipboard()
    logger.debug("Retrieved clipboard content: %s characters", len(content))
    return {"content": [{"type": "text", "text": content}]}


def execute_set_clipboard(text: str) -> ToolCallResult:
    """
    Execute set_clipboard operation and return standardized result.

    Args:
        text: Text to set in clipboard.

    Returns:
        ToolCallResult containing success message in MCP format.
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
