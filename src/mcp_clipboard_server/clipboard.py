"""Cross-platform clipboard access module with platform-specific fallback handling."""

import logging
import os
import platform
import pyperclip
from typing import Optional
from .validators import validate_clipboard_text, ValidationException

# Configure logging
logger = logging.getLogger(__name__)


class ClipboardError(Exception):
    """Custom exception for clipboard operation failures."""
    pass


def _get_platform_info() -> str:
    """Get detailed platform information for error messages."""
    system = platform.system()
    if system == "Linux":
        if os.path.exists("/proc/version"):
            try:
                with open("/proc/version", "r") as f:
                    version = f.read().strip()
                    if "Microsoft" in version or "WSL" in version:
                        return "WSL (Windows Subsystem for Linux)"
            except Exception:
                pass
        if "DISPLAY" not in os.environ:
            return "Linux (headless)"
        return "Linux"
    elif system == "Darwin":
        return "macOS"
    elif system == "Windows":
        return "Windows"
    else:
        return f"{system} (unsupported)"


def _get_platform_guidance(error_msg: str) -> str:
    """Get platform-specific guidance for clipboard errors."""
    platform_info = _get_platform_info()
    
    if "Linux" in platform_info:
        if "headless" in platform_info:
            return (
                "Clipboard access requires a display server. "
                "On headless Linux systems, clipboard operations are not supported."
            )
        elif "xclip" in error_msg.lower() or "xsel" in error_msg.lower():
            return (
                "Missing clipboard utilities. Install with: "
                "sudo apt-get install xclip xsel (Ubuntu/Debian) or "
                "sudo yum install xclip xsel (RHEL/CentOS) or "
                "sudo pacman -S xclip xsel (Arch)"
            )
        elif "display" in error_msg.lower():
            return (
                "No display available. Ensure DISPLAY environment variable is set "
                "or run in a desktop environment."
            )
    elif "WSL" in platform_info:
        return (
            "WSL clipboard access may be limited. Try: "
            "1. Use WSL2 with Windows 10 build 19041+ "
            "2. Install wslu package for clip.exe integration "
            "3. Use Windows Terminal or enable clipboard sharing"
        )
    elif "macOS" in platform_info:
        return (
            "macOS clipboard access failed. This may be due to: "
            "1. Security permissions (check System Preferences > Privacy) "
            "2. Running in a sandboxed environment "
            "3. Insufficient user privileges"
        )
    elif "Windows" in platform_info:
        return (
            "Windows clipboard access failed. This may be due to: "
            "1. Another application holding clipboard lock "
            "2. Insufficient user privileges "
            "3. Antivirus software blocking access"
        )
    
    return f"Platform-specific guidance not available for {platform_info}"


def get_clipboard() -> str:
    """
    Get the current contents of the system clipboard with platform-specific fallback handling.
    
    Returns:
        str: The clipboard contents as a string. Returns empty string if clipboard is empty
             or if clipboard access fails gracefully.
        
    Raises:
        ClipboardError: If clipboard access fails critically.
    """
    try:
        content = pyperclip.paste()
        return content if content is not None else ""
    except Exception as e:
        error_msg = str(e)
        platform_info = _get_platform_info()
        guidance = _get_platform_guidance(error_msg)
        
        # Log detailed error information for debugging
        logger.error(
            f"Clipboard read failed on {platform_info}: {error_msg}\n"
            f"Platform guidance: {guidance}"
        )
        
        # For read operations, return empty string as per spec requirement
        # This allows the application to continue functioning gracefully
        logger.warning("Returning empty string due to clipboard read failure")
        return ""


def set_clipboard(text: str) -> None:
    """
    Set the system clipboard contents to the provided text with platform-specific fallback handling.
    
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
        logger.debug(f"Successfully set clipboard content: {len(text)} characters")
    except Exception as e:
        error_msg = str(e)
        platform_info = _get_platform_info()
        guidance = _get_platform_guidance(error_msg)
        
        # Log detailed error information
        logger.error(
            f"Clipboard write failed on {platform_info}: {error_msg}\n"
            f"Platform guidance: {guidance}"
        )
        
        # For write operations, raise ClipboardError with enhanced message
        raise ClipboardError(
            f"Failed to write to clipboard on {platform_info}: {error_msg}. "
            f"Solution: {guidance}"
        ) from e
