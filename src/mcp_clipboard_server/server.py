"""Main MCP server implementation."""

import sys
import logging
import threading
from typing import Dict, Any, Optional

from .protocol import (
    parse_json_rpc_message, create_success_response, create_error_response,
    ErrorCodes, JsonRpcRequest
)
from .mcp_handler import MCPHandler
from .logging_config import setup_logging, log_request, log_response
from .errors import create_error_response_for_exception
from .validators import safe_json_parse, ValidationException

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
            
            # Read line from stdin with timeout to allow checking shutdown event
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
            
            # Parse and handle the request - wrap in comprehensive error handling
            try:
                # Enhanced JSON parsing with validation
                parsed_data = safe_json_parse(line)
                request = parse_json_rpc_message(line)
                response = server.handle_request(request)
                
                if response is not None:
                    logger.debug(f"Sending: {response}")
                    sys.stdout.write(response + '\n')
                    sys.stdout.flush()  # Critical for STDIO communication
                    
            except ValidationException as e:
                # Enhanced validation error handling
                logger.error(f"Validation error: {e}")
                try:
                    error_response = create_error_response(
                        None, ErrorCodes.INVALID_PARAMS, str(e)
                    )
                    sys.stdout.write(error_response + '\n')
                    sys.stdout.flush()
                except Exception as write_error:
                    logger.error(f"Failed to send validation error response: {write_error}")
                    
            except ValueError as e:
                # JSON parsing or other validation error - recoverable
                logger.error(f"Parse error: {e}")
                try:
                    error_response = create_error_response(
                        None, ErrorCodes.PARSE_ERROR, str(e)
                    )
                    sys.stdout.write(error_response + '\n')
                    sys.stdout.flush()
                except Exception as write_error:
                    logger.error(f"Failed to send error response: {write_error}")
                
            except Exception as e:
                # Unexpected error - recoverable, log and continue
                logger.error(f"Unexpected error processing request: {e}", exc_info=True)
                try:
                    error_response = create_error_response(
                        None, ErrorCodes.INTERNAL_ERROR, "Internal server error"
                    )
                    sys.stdout.write(error_response + '\n')
                    sys.stdout.flush()
                except Exception as write_error:
                    logger.error(f"Failed to send error response: {write_error}")
    
    except Exception as e:
        logger.error(f"Fatal error in server loop: {e}", exc_info=True)
        raise
    
    logger.info("MCP clipboard server shutdown complete")
