"""Main entry point for MCP clipboard server."""

import sys
import logging
from .server import run_server
from .logging_config import setup_logging, configure_third_party_loggers


def main():
    """Main entry point for the MCP clipboard server."""
    # Setup structured logging
    setup_logging()
    configure_third_party_loggers()
    
    logger = logging.getLogger(__name__)
    logger.info("Starting MCP clipboard server")
    
    try:
        run_server()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
