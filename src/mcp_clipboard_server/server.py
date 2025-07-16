"""Main MCP server implementation."""

import sys
import logging
import threading
from typing import Dict, Any, Optional, List, Union

from .protocol import (
    parse_json_rpc_message, create_success_response, create_error_response,
    create_batch_response, ErrorCodes, JsonRpcRequest
)
from ._mcp_handler import MCPHandler
from ._logging_config import setup_logging, log_request, log_response
from ._errors import create_error_response_for_exception
from ._validators import safe_json_parse, ValidationException

logger = logging.getLogger(__name__)


class MCPServer:
    """MCP clipboard server implementation."""
    
    def __init__(self):
        """Initialize the MCP server."""
        self.mcp_handler = MCPHandler()
    
    # Expose MCPHandler properties for backwards compatibility with tests
    @property
    def initialized(self):
        """Check if server is initialized."""
        return self.mcp_handler.initialized
    
    @initialized.setter
    def initialized(self, value):
        """Set initialization state."""
        self.mcp_handler.initialized = value
    
    @property
    def server_info(self):
        """Get server info."""
        return self.mcp_handler.get_server_info()
    
    @property
    def capabilities(self):
        """Get server capabilities."""
        return self.mcp_handler.get_server_capabilities()
    
    # Expose handler methods for backwards compatibility
    def handle_initialize(self, request: JsonRpcRequest) -> str:
        """Handle initialize request."""
        return self.mcp_handler.handle_initialize(request)
    
    def handle_tools_list(self, request: JsonRpcRequest) -> str:
        """Handle tools/list request."""
        return self.mcp_handler.handle_tools_list(request)
    
    def handle_tools_call(self, request: JsonRpcRequest) -> str:
        """Handle tools/call request."""
        return self.mcp_handler.handle_tools_call(request)
    
    def handle_ping(self, request: JsonRpcRequest) -> Optional[str]:
        """Handle ping notification."""
        return self.mcp_handler.handle_ping(request)
    
    def handle_request(self, request: JsonRpcRequest) -> Optional[str]:
        """
        Handle a JSON-RPC request and return the appropriate response.
        
        Args:
            request: Parsed JSON-RPC request.
            
        Returns:
            JSON response string, or None for notifications.
        """
        # Log the incoming request
        log_request(logger, request.method, request.params, request.id)
        
        try:
            # Delegate to MCP handler
            response = self.mcp_handler.handle_request(request)
            
            # Log successful response
            if response is not None:
                log_response(logger, request.method, True, request.id)
            
            return response
            
        except Exception as e:
            # Log error response
            log_response(logger, request.method, False, request.id, 
                        getattr(e, 'error_code', ErrorCodes.INTERNAL_ERROR))
            
            # Create error response for exception
            return create_error_response_for_exception(request.id, e)
    
    def handle_batch_requests(self, requests: List[JsonRpcRequest]) -> Optional[str]:
        """
        Handle a batch of JSON-RPC requests.
        
        Args:
            requests: List of parsed JSON-RPC requests.
            
        Returns:
            JSON batch response string, or None if all were notifications.
        """
        logger.info(f"Processing batch request with {len(requests)} items")
        
        responses = []
        for request in requests:
            try:
                response = self.handle_request(request)
                responses.append(response)
            except Exception as e:
                # Error handling for individual batch items
                error_response = create_error_response_for_exception(request.id, e)
                responses.append(error_response)
        
        return create_batch_response(responses)


def _read_stdin_line(shutdown_event: threading.Event | None = None) -> str | None:
    """Read a line from stdin with shutdown checking."""
    try:
        line = sys.stdin.readline()
        if not line:  # EOF
            logger.info("Received EOF, shutting down")
            return None
        
        line = line.strip()
        if not line:  # Empty line
            return ""
        
        logger.debug(f"Received: {line}")
        return line
        
    except (KeyboardInterrupt, EOFError):
        logger.info("Received interrupt or EOF, shutting down")
        return None


def _send_response(response: str) -> None:
    """Send response to stdout with error handling."""
    if response is not None:
        logger.debug(f"Sending: {response}")
        sys.stdout.write(response + '\n')
        sys.stdout.flush()  # Critical for STDIO communication


def _send_error_response(error_code: int, message: str) -> None:
    """Send error response with exception handling."""
    try:
        error_response = create_error_response(None, error_code, message)
        sys.stdout.write(error_response + '\n')
        sys.stdout.flush()
    except Exception as write_error:
        logger.error(f"Failed to send error response: {write_error}")


def _process_request(server: MCPServer, line: str) -> None:
    """Process a single request line."""
    try:
        parsed = parse_json_rpc_message(line)
        
        # Check if it's a batch request or single request
        if isinstance(parsed, list):
            response = server.handle_batch_requests(parsed)
        else:
            response = server.handle_request(parsed)
        
        _send_response(response)
        
    except ValidationException as e:
        logger.error(f"Validation error: {e}")
        _send_error_response(ErrorCodes.INVALID_PARAMS, str(e))
        
    except ValueError as e:
        logger.error(f"Parse error: {e}")
        _send_error_response(ErrorCodes.PARSE_ERROR, str(e))
        
    except Exception as e:
        logger.error(f"Unexpected error processing request: {e}", exc_info=True)
        _send_error_response(ErrorCodes.INTERNAL_ERROR, "Internal server error")


def run_server(shutdown_event: threading.Event | None = None):
    """
    Run the MCP server main loop.
    
    Reads JSON-RPC messages from stdin and writes responses to stdout.
    
    Args:
        shutdown_event: Optional event to signal graceful shutdown.
    """
    # Setup logging first
    setup_logging()
    
    server = MCPServer()
    logger.info("Starting MCP clipboard server")
    
    try:
        while True:
            # Check shutdown signal
            if shutdown_event and shutdown_event.is_set():
                logger.info("Shutdown requested, exiting gracefully")
                break
            
            # Read line from stdin
            line = _read_stdin_line(shutdown_event)
            if line is None:  # EOF or interrupt
                break
            if line == "":  # Empty line
                continue
            
            # Process the request
            _process_request(server, line)
    
    except Exception as e:
        logger.error(f"Fatal error in server loop: {e}", exc_info=True)
        raise
    
    logger.info("MCP clipboard server shutdown complete")
