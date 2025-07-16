"""Command-line interface for MCP clipboard server."""

import argparse
import io
import logging
import signal
import sys
import threading
from typing import NoReturn

try:
    from importlib.metadata import version, PackageNotFoundError
except ImportError:
    # Python < 3.8 fallback
    from importlib_metadata import version, PackageNotFoundError

from ._logging_config import configure_third_party_loggers, setup_logging
from .server import run_server

# Global shutdown event for clean exit
shutdown_event = threading.Event()


def signal_handler(signum: int, _frame) -> None:
    """Handle shutdown signals gracefully."""
    logger = logging.getLogger(__name__)
    logger.info("Received signal %s, initiating graceful shutdown", signum)
    shutdown_event.set()


def setup_signal_handlers() -> None:
    """Register signal handlers for graceful shutdown."""
    # Register SIGINT (Ctrl+C) and SIGTERM handlers
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, "SIGTERM"):  # Windows doesn't have SIGTERM
        signal.signal(signal.SIGTERM, signal_handler)


def get_package_version() -> str:
    """Get package version from metadata."""
    try:
        return version("mcp-clipboard-server")
    except PackageNotFoundError:
        return "0.1.0"  # Fallback version


def create_parser() -> argparse.ArgumentParser:
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="mcp-clipboard-server",
        description="MCP server providing clipboard access tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  mcp-clipboard-server                    # Start the server
  python -m mcp_clipboard_server          # Alternative startup method

Environment Variables:
  MCP_LOG_LEVEL    Set logging level (DEBUG, INFO, WARNING, ERROR)
  MCP_LOG_JSON     Use JSON logging format (true/false)
        """,
    )

    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {get_package_version()}"
    )

    return parser


def main(args: list[str] | None = None) -> NoReturn:
    """Main CLI entry point."""
    parser = create_parser()
    _ = parser.parse_args(args)

    # Force UTF-8 encoding on Windows to handle Unicode clipboard content
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

    # Setup logging and signal handlers
    setup_logging()
    configure_third_party_loggers()
    setup_signal_handlers()

    logger = logging.getLogger(__name__)
    logger.info("Starting MCP clipboard server")

    try:
        run_server(shutdown_event)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down")
        sys.exit(0)
    except Exception as e:
        logger.error("Fatal error: %s", e, exc_info=True)
        sys.exit(1)

    logger.info("Server shutdown complete")
    sys.exit(0)


if __name__ == "__main__":
    main()
