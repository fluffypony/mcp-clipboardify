"""MCP Clipboard Server - A Model Context Protocol server for clipboard access."""

from ._version import __version__

# Export main components
from ._protocol_types import *
from ._mcp_handler import MCPHandler
from .server import run_server
from .clipboard import get_clipboard, set_clipboard
from ._errors import ClipboardError
from ._errors import MCPError, InitializationError, ValidationError
