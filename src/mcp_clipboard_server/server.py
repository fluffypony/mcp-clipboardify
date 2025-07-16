"""Main MCP server implementation."""

import sys
import logging
from typing import Dict, Any, Optional

from .protocol import (
    parse_json_rpc_message, create_success_response, create_error_response,
    ErrorCodes, JsonRpcRequest
)
from .mcp_handler import MCPHandler
from .logging_config import setup_logging, log_request, log_response
from .errors import create_error_response_for_exception

logger = logging.getLogger(__name__)


class MCPServer:
    """MCP clipboard server implementation."""
    
    def __init__(self):
        """Initialize the MCP server."""
        self.mcp_handler = MCPHandler()
    
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


def run_server():
    """
    Run the MCP server main loop.
    
    Reads JSON-RPC messages from stdin and writes responses to stdout.
    """
    # Setup logging first
    setup_logging()
    
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
