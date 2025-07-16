"""MCP protocol data structures using TypedDict for type safety."""

from typing import Any, Dict, List, Optional, Union

try:
    from typing import TypedDict
except ImportError:
    # Python 3.7 compatibility
    from typing_extensions import TypedDict

# Define JsonRpcError locally to avoid circular import


# Basic types
JsonRpcId = Union[str, int, None]


# Initialize request/response types
class ClientInfo(TypedDict, total=False):
    """Client information provided during initialization."""

    name: str
    version: str


class InitializeParams(TypedDict, total=False):
    """Parameters for initialize request."""

    protocolVersion: str
    clientInfo: ClientInfo


class ServerInfo(TypedDict):
    """Server information returned during initialization."""

    name: str
    version: str


class ToolsCapability(TypedDict, total=False):
    """Tools capability declaration."""

    listChanged: bool


class ResourcesCapability(TypedDict, total=False):
    """Resources capability declaration."""

    subscribe: bool
    listChanged: bool


class ServerCapabilities(TypedDict, total=False):
    """Server capabilities returned during initialization."""

    tools: ToolsCapability
    resources: ResourcesCapability


class InitializeResult(TypedDict):
    """Result of initialize request."""

    protocolVersion: str
    serverInfo: ServerInfo
    capabilities: ServerCapabilities


# Tool definition types
class ToolInputSchema(TypedDict):
    """JSON Schema for tool input parameters."""

    type: str
    properties: Dict[str, Any]
    required: List[str]
    additionalProperties: bool


class ToolDefinition(TypedDict):
    """MCP tool definition."""

    name: str
    description: str
    inputSchema: ToolInputSchema


class ToolsListResult(TypedDict):
    """Result of tools/list request."""

    tools: List[ToolDefinition]


# Tool call types
class ToolCallParams(TypedDict):
    """Parameters for tools/call request."""

    name: str
    arguments: Dict[str, Any]


class TextContent(TypedDict):
    """Text content block."""

    type: str  # Always "text"
    text: str


class ToolCallResult(TypedDict):
    """Result of tools/call request."""

    content: List[TextContent]


# JSON-RPC message types
class JsonRpcRequest(TypedDict):
    """JSON-RPC 2.0 request message."""

    jsonrpc: str  # Always "2.0"
    method: str
    id: JsonRpcId
    params: Optional[Dict[str, Any]]


class JsonRpcError(TypedDict):
    """JSON-RPC 2.0 error object."""

    code: int
    message: str
    data: Optional[Any]


class JsonRpcNotification(TypedDict):
    """JSON-RPC 2.0 notification message (no id field)."""

    jsonrpc: str  # Always "2.0"
    method: str
    params: Optional[Dict[str, Any]]


class JsonRpcSuccessResponse(TypedDict):
    """JSON-RPC 2.0 success response."""

    jsonrpc: str  # Always "2.0"
    id: JsonRpcId
    result: Any


class JsonRpcErrorResponse(TypedDict):
    """JSON-RPC 2.0 error response."""

    jsonrpc: str  # Always "2.0"
    id: JsonRpcId
    error: JsonRpcError


# Union types for convenience
JsonRpcMessage = Union[JsonRpcRequest, JsonRpcNotification]
JsonRpcResponse = Union[JsonRpcSuccessResponse, JsonRpcErrorResponse]
