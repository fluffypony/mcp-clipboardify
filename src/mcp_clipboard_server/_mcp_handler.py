"""MCP-specific request handler extending JSON-RPC base functionality."""

import logging
from typing import Dict, Any, Optional, Callable
from ._version import __version__
from ._protocol_types import (
    InitializeResult,
    ToolsListResult,
    ToolCallResult,
    ServerCapabilities,
    ServerInfo,
)
from .protocol import (
    JsonRpcRequest,
    create_success_response,
    create_error_response,
)
from ._errors import ErrorCodes
from ._tool_schemas import (
    get_all_tool_definitions,
    validate_tool_exists,
    get_tool_schema,
)
from ._validators import validate_with_json_schema
from ._clipboard_utils import execute_get_clipboard, execute_set_clipboard
from ._errors import safe_execute

logger = logging.getLogger(__name__)


class MCPHandler:
    """MCP protocol handler for processing MCP-specific requests."""

    def __init__(self) -> None:
        """Initialize the MCP handler."""
        self.initialized = False
        self.client_info: Optional[Dict[str, Any]] = None

        # Method dispatch table for MCP methods
        self.method_handlers: Dict[str, Callable[[JsonRpcRequest], Optional[str]]] = {
            "initialize": self.handle_initialize,
            "tools/list": self.handle_tools_list,
            "tools/call": self.handle_tools_call,
            "$/ping": self.handle_ping,
        }

    def get_server_info(self) -> ServerInfo:
        """
        Get server information for initialize response.

        Returns:
            ServerInfo dictionary.
        """
        return {"name": "mcp-clipboard-server", "version": __version__}

    def get_server_capabilities(self) -> ServerCapabilities:
        """
        Get server capabilities for initialize response.

        Returns:
            ServerCapabilities dictionary.
        """
        return {"tools": {}}

    def handle_initialize(self, request: JsonRpcRequest) -> str:
        """
        Handle MCP initialize request.

        Args:
            request: The JSON-RPC request.

        Returns:
            JSON response string.
        """
        logger.info("Handling initialize request")

        # Extract and store client info if provided
        if request.params:
            self.client_info = request.params.get("clientInfo", {})
            protocol_version = request.params.get("protocolVersion", "unknown")
            logger.info(
                "Client info: %s, protocol version: %s",
                self.client_info,
                protocol_version,
            )

        # Mark as initialized
        self.initialized = True

        # Build initialize result
        result: InitializeResult = {
            "protocolVersion": "2024-11-05",  # Current MCP protocol version
            "serverInfo": self.get_server_info(),
            "capabilities": self.get_server_capabilities(),
        }

        logger.debug("Initialization complete, returning: %s", result)
        return create_success_response(request.id, result)

    def handle_tools_list(self, request: JsonRpcRequest) -> str:
        """
        Handle tools/list request.

        Args:
            request: The JSON-RPC request.

        Returns:
            JSON response string.
        """

        if not self.initialized:
            logger.warning("tools/list called before initialization")
            return create_error_response(
                request.id,
                ErrorCodes.SERVER_ERROR,
                "Server not initialized. Call initialize first.",
            )

        logger.debug("Handling tools/list request")

        # Get all tool definitions
        tool_definitions = get_all_tool_definitions()
        result: ToolsListResult = {"tools": list(tool_definitions.values())}

        logger.debug("Returning %s tools", len(result["tools"]))
        return create_success_response(request.id, result)

    def handle_tools_call(self, request: JsonRpcRequest) -> str:
        """
        Handle tools/call request.

        Args:
            request: The JSON-RPC request.

        Returns:
            JSON response string.
        """

        if not self.initialized:
            logger.warning("tools/call called before initialization")
            return create_error_response(
                request.id,
                ErrorCodes.SERVER_ERROR,
                "Server not initialized. Call initialize first.",
            )

        if not request.params:
            logger.warning("tools/call missing parameters")
            return create_error_response(
                request.id,
                ErrorCodes.INVALID_PARAMS,
                "Missing parameters for tool call",
            )

        # Extract tool call parameters
        tool_name = request.params.get("name")
        arguments = request.params.get("arguments", {})

        if not tool_name:
            logger.warning("tools/call missing tool name")
            return create_error_response(
                request.id, ErrorCodes.INVALID_PARAMS, "Missing 'name' parameter"
            )

        logger.info("Handling tools/call for: %s", tool_name)

        # Validate tool exists
        if not validate_tool_exists(tool_name):
            logger.warning("Unknown tool requested: %s", tool_name)
            return create_error_response(
                request.id, ErrorCodes.INVALID_PARAMS, f"Unknown tool: {tool_name}"
            )

        # Execute the tool using centralized error handling
        return safe_execute(request.id, self._execute_tool, tool_name, arguments)

    def handle_ping(self, _request: JsonRpcRequest) -> Optional[str]:
        """
        Handle $/ping notification.

        Args:
            request: The JSON-RPC request.

        Returns:
            None (notifications don't get responses).
        """
        logger.debug("Received ping notification")

    def _execute_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> ToolCallResult:
        """
        Execute a specific tool with given arguments.

        Args:
            tool_name: Name of the tool to execute.
            arguments: Arguments for the tool.

        Returns:
            ToolCallResult containing the execution result.

        Raises:
            ValidationException: If parameters are invalid.
            ClipboardError: If clipboard operation fails.
        """
        # Validate arguments against tool schema
        schema = get_tool_schema(tool_name)
        validate_with_json_schema(arguments, dict(schema))

        if tool_name == "get_clipboard":
            return execute_get_clipboard()

        if tool_name == "set_clipboard":
            text = arguments["text"]
            return execute_set_clipboard(text)

        # This should not happen if validate_tool_exists was called
        raise ValueError(f"Unknown tool: {tool_name}")

    def handle_request(self, request: JsonRpcRequest) -> Optional[str]:
        """
        Handle an MCP request by dispatching to the appropriate handler.

        Args:
            request: Parsed JSON-RPC request.

        Returns:
            JSON response string, or None for notifications.
        """
        method = request.method

        # Check if we have a handler for this method
        if method in self.method_handlers:
            handler = self.method_handlers[method]
            return handler(request)

        # Unknown method
        if request.id is not None:
            # It's a request, return error
            logger.warning("Unknown method requested: %s", method)
            return create_error_response(
                request.id, ErrorCodes.METHOD_NOT_FOUND, f"Method not found: {method}"
            )

        # It's a notification, ignore silently
        logger.debug("Ignoring unknown notification: %s", method)
        return None
