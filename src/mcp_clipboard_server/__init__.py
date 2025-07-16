"""MCP Clipboard Server - A Model Context Protocol server for clipboard access."""

import importlib.metadata

try:
    # Try to get version from package metadata
    __version__ = importlib.metadata.version("mcp-clipboard-server")
except importlib.metadata.PackageNotFoundError:
    # Fallback version if package not installed
    __version__ = "1.0.0-dev"

# Export main components
from .protocol_types import *
from .mcp_handler import MCPHandler
from .server import run_server
from .clipboard import get_clipboard, set_clipboard, ClipboardError
from .errors import MCPError, InitializationError, ValidationError
