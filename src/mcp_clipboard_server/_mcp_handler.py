"""MCP-specific request handler extending JSON-RPC base functionality."""

import logging
from typing import Dict, Any, Optional, Callable
from ._protocol_types import (
    JsonRpcId, InitializeParams, InitializeResult, ToolsListResult,
    ToolCallParams, ToolCallResult, ServerCapabilities, ServerInfo
)
from .protocol import JsonRpcRequest, ErrorCodes
from ._tool_schemas import get_all_tool_definitions, validate_tool_exists, get_tool_schema
from ._validators import validate_with_json_schema, ValidationException
from .clipboard import get_clipboard, set_clipboard, ClipboardError

logger = logging.getLogger(__name__)


class MCPHandler:
    """MCP protocol handler for processing MCP-specific requests."""
    
    def __init__(self):
        """Initialize the MCP handler."""
        self.initialized = False
        self.client_info: Optional[Dict[str, Any]] = None
        
        # Method dispatch table for MCP methods
        self.method_handlers: Dict[str, Callable[[JsonRpcRequest], Optional[str]]] = {
            "initialize": self.handle_initialize,
            "tools/list": self.handle_tools_list,
            "tools/call": self.handle_tools_call,
            "$/ping": self.handle_ping
        }
    
    def get_server_info(self) -> ServerInfo:
        """
        Get server information for initialize response.
        
        Returns:
            ServerInfo dictionary.
        """
        from ._version import __version__
        
        return {
            "name": "mcp-clipboard-server",
            "version": __version__
        }
    
    def get_server_capabilities(self) -> ServerCapabilities:
        """
        Get server capabilities for initialize response.
        
        Returns:
            ServerCapabilities dictionary.
        """
        return {
            "tools": {}
        }
    
    def handle_initialize(self, request: JsonRpcRequest) -> str:
        """
        Handle MCP initialize request.
        
        Args:
            request: The JSON-RPC request.
            
        Returns:
            JSON response string.
        """
        from .protocol import create_success_response
        
        logger.info("Handling initialize request")
        
        # Extract and store client info if provided
        if request.params:
            self.client_info = request.params.get("clientInfo", {})
            protocol_version = request.params.get("protocolVersion", "unknown")
            logger.info(f"Client info: {self.client_info}, protocol version: {protocol_version}")
        
        # Mark as initialized
        self.initialized = True
        
        # Build initialize result
        result: InitializeResult = {
            "protocolVersion": "2024-11-05",  # Current MCP protocol version
            "serverInfo": self.get_server_info(),
            "capabilities": self.get_server_capabilities()
        }
        
        logger.debug(f"Initialization complete, returning: {result}")
        return create_success_response(request.id, result)
    
    def handle_tools_list(self, request: JsonRpcRequest) -> str:
        """
        Handle tools/list request.
        
        Args:
            request: The JSON-RPC request.
            
        Returns:
            JSON response string.
        """
        from .protocol import create_success_response, create_error_response
        
        if not self.initialized:
            logger.warning("tools/list called before initialization")
            return create_error_response(
                request.id, ErrorCodes.SERVER_ERROR,
                "Server not initialized. Call initialize first."
            )
        
        logger.debug("Handling tools/list request")
        
        # Get all tool definitions
        tool_definitions = get_all_tool_definitions()
        result: ToolsListResult = {
            "tools": list(tool_definitions.values())
        }
        
        logger.debug(f"Returning {len(result['tools'])} tools")
        return create_success_response(request.id, result)
    
    def handle_tools_call(self, request: JsonRpcRequest) -> str:
        """
        Handle tools/call request.
        
        Args:
            request: The JSON-RPC request.
            
        Returns:
            JSON response string.
        """
        from .protocol import create_success_response, create_error_response
        
        if not self.initialized:
            logger.warning("tools/call called before initialization")
            return create_error_response(
                request.id, ErrorCodes.SERVER_ERROR,
                "Server not initialized. Call initialize first."
            )
        
        if not request.params:
            logger.warning("tools/call missing parameters")
            return create_error_response(
                request.id, ErrorCodes.INVALID_PARAMS,
                "Missing parameters for tool call"
            )
        
        # Extract tool call parameters
        tool_name = request.params.get("name")
        arguments = request.params.get("arguments", {})
        
        if not tool_name:
            logger.warning("tools/call missing tool name")
            return create_error_response(
                request.id, ErrorCodes.INVALID_PARAMS,
                "Missing 'name' parameter"
            )
        
        logger.info(f"Handling tools/call for: {tool_name}")
        
        # Validate tool exists
        if not validate_tool_exists(tool_name):
            logger.warning(f"Unknown tool requested: {tool_name}")
            return create_error_response(
                request.id, ErrorCodes.INVALID_PARAMS,
                f"Unknown tool: {tool_name}"
            )
        
        # Execute the tool using centralized error handling
        from ._errors import safe_execute
        return safe_execute(request.id, self._execute_tool, tool_name, arguments)
    
    def handle_ping(self, request: JsonRpcRequest) -> Optional[str]:
        """
        Handle $/ping notification.
        
        Args:
            request: The JSON-RPC request.
            
        Returns:
            None (notifications don't get responses).
        """
        logger.debug("Received ping notification")
        return None  # Notifications don't get responses
    
    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> ToolCallResult:
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
        validate_with_json_schema(arguments, schema)
        
        if tool_name == "get_clipboard":
            content = get_clipboard()
            logger.debug(f"Retrieved clipboard content: {len(content)} characters")
            
            return {
                "content": [{
                    "type": "text",
                    "text": content
                }]
            }
            
        elif tool_name == "set_clipboard":
            text = arguments["text"]
            set_clipboard(text)
            logger.debug(f"Set clipboard content: {len(text)} characters")
            
            return {
                "content": [{
                    "type": "text",
                    "text": f"Successfully copied {len(text)} characters to clipboard"
                }]
            }
        
        else:
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
        from .protocol import create_error_response
        
        method = request.method
        
        # Check if we have a handler for this method
        if method in self.method_handlers:
            handler = self.method_handlers[method]
            return handler(request)
        else:
            # Unknown method
            if request.id is not None:
                # It's a request, return error
                logger.warning(f"Unknown method requested: {method}")
                return create_error_response(
                    request.id, ErrorCodes.METHOD_NOT_FOUND,
                    f"Method not found: {method}"
                )
            else:
                # It's a notification, ignore silently
                logger.debug(f"Ignoring unknown notification: {method}")
                return None
