"""Main entry point for MCP clipboard server."""

import sys
import logging
from .server import run_server


def main():
    """Main entry point for the MCP clipboard server."""
    # Configure logging level from environment if needed
    import os
    log_level = os.environ.get('MCP_LOG_LEVEL', 'INFO').upper()
    
    try:
        numeric_level = getattr(logging, log_level)
    except AttributeError:
        numeric_level = logging.INFO
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr  # Log to stderr to keep stdout clean for JSON-RPC
    )
    
    try:
        run_server()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
