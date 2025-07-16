"""Version information for MCP Clipboard Server."""

import importlib.metadata

try:
    # Try to get version from package metadata
    __version__ = importlib.metadata.version("mcp-clipboard-server")
except importlib.metadata.PackageNotFoundError:
    # Fallback version if package not installed
    __version__ = "1.0.0-dev"
