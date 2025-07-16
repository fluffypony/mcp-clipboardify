"""MCP Clipboard Server - A Model Context Protocol server for clipboard access."""

from ._version import __version__ as __version__

# Export main components
from ._protocol_types import (
    JsonRpcId as JsonRpcId,
    ClientInfo as ClientInfo,
    InitializeParams as InitializeParams,
    ServerInfo as ServerInfo,
    ToolsCapability as ToolsCapability,
    ResourcesCapability as ResourcesCapability,
    ServerCapabilities as ServerCapabilities,
    InitializeResult as InitializeResult,
    ToolInputSchema as ToolInputSchema,
    ToolDefinition as ToolDefinition,
    ToolsListResult as ToolsListResult,
    ToolCallParams as ToolCallParams,
    TextContent as TextContent,
    ToolCallResult as ToolCallResult,
    JsonRpcRequest as JsonRpcRequest,
    JsonRpcError as JsonRpcError,
    JsonRpcNotification as JsonRpcNotification,
    JsonRpcSuccessResponse as JsonRpcSuccessResponse,
    JsonRpcErrorResponse as JsonRpcErrorResponse,
    JsonRpcMessage as JsonRpcMessage,
    JsonRpcResponse as JsonRpcResponse,
)
from ._mcp_handler import MCPHandler as MCPHandler
from .server import run_server as run_server
from .clipboard import get_clipboard as get_clipboard, set_clipboard as set_clipboard
from ._errors import ClipboardError as ClipboardError
from ._errors import MCPError as MCPError, InitializationError as InitializationError, ValidationError as ValidationError
