"""Main MCP server implementation."""

import sys
import logging
from typing import Dict, Any, Optional

from .protocol import (
    parse_json_rpc_message, create_success_response, create_error_response,
    ErrorCodes, JsonRpcRequest
)
from .tools import list_tools, execute_tool, get_tool_error_code

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MCPServer:
    """MCP clipboard server implementation."""
    
    def __init__(self):
        """Initialize the MCP server."""
        self.initialized = False
        self.server_info = {
            "name": "mcp-clipboard-server",
            "version": "0.1.0"
        }
        self.capabilities = {
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
        logger.info("Initializing MCP server")
        
        # Extract client info if provided
        client_info = {}
        if request.params:
            client_info = request.params.get("clientInfo", {})
            logger.info(f"Client info: {client_info}")
        
        self.initialized = True
        
        result = {
            "serverInfo": self.server_info,
            "capabilities": self.capabilities
        }
        
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
            return create_error_response(
                request.id, ErrorCodes.SERVER_ERROR, 
                "Server not initialized"
            )
        
        logger.debug("Listing available tools")
        result = list_tools()
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
            return create_error_response(
                request.id, ErrorCodes.SERVER_ERROR,
                "Server not initialized"
            )
        
        if not request.params:
            return create_error_response(
                request.id, ErrorCodes.INVALID_PARAMS,
                "Missing parameters for tool call"
            )
        
        tool_name = request.params.get("name")
        arguments = request.params.get("arguments", {})
        
        if not tool_name:
            return create_error_response(
                request.id, ErrorCodes.INVALID_PARAMS,
                "Missing tool name"
            )
        
        try:
            result = execute_tool(tool_name, arguments)
            return create_success_response(request.id, result)
        except Exception as e:
            error_code = get_tool_error_code(e)
            return create_error_response(
                request.id, error_code, str(e)
            )
    
    def handle_ping(self, request: JsonRpcRequest) -> Optional[str]:
        """
        Handle ping notification.
        
        Args:
            request: The JSON-RPC request.
            
        Returns:
            None for notifications (no response).
        """
        logger.debug("Received ping")
        return None  # Notifications don't get responses
    
    def handle_request(self, request: JsonRpcRequest) -> Optional[str]:
        """
        Handle a JSON-RPC request and return the appropriate response.
        
        Args:
            request: Parsed JSON-RPC request.
            
        Returns:
            JSON response string, or None for notifications.
        """
        method = request.method
        
        # Handle MCP methods
        if method == "initialize":
            return self.handle_initialize(request)
        elif method == "tools/list":
            return self.handle_tools_list(request)
        elif method == "tools/call":
            return self.handle_tools_call(request)
        elif method == "$/ping":
            return self.handle_ping(request)
        else:
            # Unknown method - return error if it's a request (has ID)
            if request.id is not None:
                return create_error_response(
                    request.id, ErrorCodes.METHOD_NOT_FOUND,
                    f"Method not found: {method}"
                )
            else:
                # Ignore unknown notifications
                logger.debug(f"Ignoring unknown notification: {method}")
                return None


def run_server():
    """
    Run the MCP server main loop.
    
    Reads JSON-RPC messages from stdin and writes responses to stdout.
    """
    server = MCPServer()
    logger.info("Starting MCP clipboard server")
    
    try:
        while True:
            # Read line from stdin
            try:
                line = sys.stdin.readline()
                if not line:  # EOF
                    logger.info("Received EOF, shutting down")
                    break
                
                line = line.strip()
                if not line:  # Empty line
                    continue
                
                logger.debug(f"Received: {line}")
                
            except KeyboardInterrupt:
                logger.info("Received interrupt, shutting down")
                break
            except EOFError:
                logger.info("Received EOF, shutting down")
                break
            
            # Parse and handle the request
            try:
                request = parse_json_rpc_message(line)
                response = server.handle_request(request)
                
                if response is not None:
                    logger.debug(f"Sending: {response}")
                    sys.stdout.write(response + '\n')
                    sys.stdout.flush()  # Critical for STDIO communication
                    
            except ValueError as e:
                # JSON parsing or validation error
                logger.error(f"Parse error: {e}")
                error_response = create_error_response(
                    None, ErrorCodes.PARSE_ERROR, str(e)
                )
                sys.stdout.write(error_response + '\n')
                sys.stdout.flush()
                
            except Exception as e:
                # Unexpected error
                logger.error(f"Unexpected error: {e}")
                error_response = create_error_response(
                    None, ErrorCodes.INTERNAL_ERROR, "Internal server error"
                )
                sys.stdout.write(error_response + '\n')
                sys.stdout.flush()
    
    except Exception as e:
        logger.error(f"Fatal error in server loop: {e}")
        sys.exit(1)
    
    logger.info("MCP clipboard server shutdown complete")
