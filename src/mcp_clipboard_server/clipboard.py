"""Cross-platform clipboard access module."""

import pyperclip
from typing import Optional
from .validators import validate_clipboard_text, ValidationException


class ClipboardError(Exception):
    """Custom exception for clipboard operation failures."""
    pass


def get_clipboard() -> str:
    """
    Get the current contents of the system clipboard.
    
    Returns:
        str: The clipboard contents as a string. Returns empty string if clipboard is empty.
        
    Raises:
        ClipboardError: If clipboard access fails.
    """
    try:
        content = pyperclip.paste()
        return content if content is not None else ""
    except Exception as e:
        raise ClipboardError(f"Failed to read clipboard: {str(e)}") from e


def set_clipboard(text: str) -> None:
    """
    Set the system clipboard contents to the provided text.
    
    Args:
        text: The text to copy to the clipboard.
        
    Raises:
        ClipboardError: If clipboard access fails.
        ValueError: If text validation fails.
    """
    try:
        # Use enhanced validation
        validate_clipboard_text(text)
    except ValidationException as e:
        # Convert ValidationException to ValueError for backward compatibility
        raise ValueError(str(e)) from e
    
    try:
        pyperclip.copy(text)
    except Exception as e:
        raise ClipboardError(f"Failed to write to clipboard: {str(e)}") from e
