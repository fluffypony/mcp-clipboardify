# MCP Clipboard Server - Development Guide

---
Last Updated: 2025-07-16
Version: 1.0.0
Verified Against: Current implementation
Test Sources: tests/, .github/workflows/, pyproject.toml
---

## Overview

This guide provides comprehensive instructions for setting up a development environment, understanding the codebase, contributing changes, and maintaining the MCP Clipboard Server.

## Development Environment Setup

### Prerequisites

- **Python 3.8.1 or higher** (required for development toolchain compatibility)
- **Poetry** for dependency management
- **Git** for version control
- **Platform-specific clipboard utilities** for testing

### Initial Setup

<!-- SOURCE: README.md:254-274 -->
<!-- VERIFIED: 2025-07-16 -->
1. **Clone the repository:**
   ```bash
   git clone https://github.com/fluffypony/mcp-clipboardify.git
   cd mcp-clipboardify
   ```

2. **Install Poetry** (if not already installed):
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. **Install dependencies:**
   ```bash
   poetry install
   ```

4. **Activate virtual environment:**
   ```bash
   poetry shell
   ```

### Development Dependencies

<!-- SOURCE: pyproject.toml development dependencies -->
<!-- VERIFIED: 2025-07-16 -->
The project includes a comprehensive development toolchain:

```toml
[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"                 # Testing framework
pytest-cov = "^4.1.0"            # Coverage reporting
pytest-timeout = "^2.1.0"        # Test timeout support
black = "^23.0.0"                 # Code formatting
flake8 = "^6.0.0"                 # Linting
isort = "^5.12.0"                 # Import sorting
mypy = "^1.5.0"                   # Type checking
```

### Platform-Specific Setup

#### Linux Development
```bash
# Install clipboard utilities for testing
sudo apt-get install xclip xsel wl-clipboard  # Ubuntu/Debian
sudo dnf install xclip xsel wl-clipboard      # Fedora
sudo pacman -S xclip xsel wl-clipboard        # Arch
```

#### macOS Development
```bash
# No additional setup required
# Verify clipboard tools are available
which pbcopy && which pbpaste
```

#### Windows Development
```cmd
REM No additional setup required
REM Verify Python and Poetry installation
python --version
poetry --version
```

## Project Structure

```
src/mcp_clipboard_server/     # Main package source code
├── __init__.py              # Package initialization with dynamic version loading
├── __main__.py              # Module entry point (python -m mcp_clipboard_server)
├── cli.py                   # Command-line interface with signal handling
├── server.py                # Main server loop with batch processing support
├── protocol.py              # JSON-RPC 2.0 message handling with batch support
├── tools.py                 # Tool implementations using centralized schemas
├── clipboard.py             # Cross-platform clipboard operations with Wayland support
├── _mcp_handler.py          # PRIVATE: MCP protocol implementation with JSON Schema validation
├── _protocol_types.py       # PRIVATE: TypedDict definitions for MCP protocol data structures
├── _tool_schemas.py         # PRIVATE: JSON Schema definitions (single source of truth)
├── _errors.py               # PRIVATE: Centralized error handling with ValidationException
├── _validators.py           # PRIVATE: Input validation utilities with comprehensive error handling
└── _logging_config.py       # PRIVATE: Structured logging with JSON formatter
```

### Module Privacy Convention

**Public Modules** (no underscore prefix):
- Intended for external use and import
- Stable public API
- Comprehensive documentation required
- Backwards compatibility maintained

**Private Modules** (underscore prefix):
- Internal implementation details
- Subject to change without notice
- Import only within package
- No external API guarantees

## Development Workflow

### Code Quality Tools

<!-- SOURCE: README.md:294-302 -->
<!-- VERIFIED: 2025-07-16 -->
Run quality checks before committing:

```bash
# Type checking
poetry run mypy src/

# Linting
poetry run flake8 src/

# Formatting
poetry run black src/ tests/

# Import sorting
poetry run isort src/ tests/
```

### Testing

<!-- SOURCE: README.md:278-289 -->
<!-- VERIFIED: 2025-07-16 -->
Run the comprehensive test suite:

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=mcp_clipboard_server

# Run specific test categories
poetry run pytest tests/test_unit.py
poetry run pytest tests/test_integration.py

# Run with timeout support (30s default)
poetry run pytest --timeout=60

# Run platform-specific tests only
poetry run pytest tests/test_platform_specific.py
```

### Running the Server

```bash
# Development mode
poetry run python -m mcp_clipboard_server

# With debug logging
poetry run python -c "
import os
os.environ['MCP_LOG_LEVEL'] = 'DEBUG'
os.environ['MCP_LOG_JSON'] = 'true'
" && poetry run python -m mcp_clipboard_server

# Direct module execution
poetry run mcp-clipboard-server

# With environment variables
MCP_LOG_LEVEL=DEBUG MCP_LOG_JSON=true poetry run mcp-clipboard-server
```

## Testing Strategy

### Test Categories

<!-- SOURCE: tests/ directory structure -->
<!-- VERIFIED: 2025-07-16 -->
The test suite is organized into distinct categories:

```
tests/
├── test_clipboard.py        # Unit tests for clipboard operations
├── test_integration.py      # Legacy integration tests
├── test_mcp_integration.py  # Comprehensive MCP protocol integration tests
├── test_protocol.py         # JSON-RPC protocol unit tests
├── test_server.py           # Server implementation unit tests
├── test_tools.py            # Tool implementation unit tests with schema validation
├── test_platform_specific.py # Platform-conditional tests
├── test_e2e.py              # End-to-end subprocess tests
└── fixtures/                # Sample JSON-RPC requests for testing
```

### Unit Tests

<!-- SOURCE: tests/test_tools.py:17-43 -->
<!-- VERIFIED: 2025-07-16 -->
Unit tests focus on individual module functionality:

```python
class TestToolDefinitions:
    """Test tool schema definitions."""

    def test_tools_defined(self):
        """Test that both required tools are defined."""
        tool_definitions = get_all_tool_definitions()
        assert "get_clipboard" in tool_definitions
        assert "set_clipboard" in tool_definitions

    def test_get_clipboard_schema(self):
        """Test get_clipboard tool schema."""
        tool_definitions = get_all_tool_definitions()
        tool = tool_definitions["get_clipboard"]
        assert tool["name"] == "get_clipboard"
        assert "description" in tool
        assert tool["inputSchema"]["type"] == "object"
        assert tool["inputSchema"]["properties"] == {}
```

### Integration Tests

<!-- SOURCE: tests/test_mcp_integration.py:40-86 -->
<!-- VERIFIED: 2025-07-16 -->
Integration tests verify full protocol flows:

```python
async def start_server(self) -> tuple[asyncio.StreamReader, asyncio.StreamWriter]:
    """
    Start the MCP server as a subprocess.

    Returns:
        Tuple of (reader, writer) for communication.
    """
    # Start server subprocess
    self.server_process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "mcp_clipboard_server",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=os.path.dirname(os.path.dirname(__file__)),  # Project root
    )

    return self.server_process.stdout, self.server_process.stdin
```

### Platform-Specific Tests

<!-- SOURCE: tests/test_platform_specific.py -->
<!-- VERIFIED: 2025-07-16 -->
Platform tests use conditional execution:

```python
import pytest
import platform

@pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific test")
def test_windows_clipboard():
    """Test Windows-specific clipboard functionality."""
    # Windows-specific test implementation

@pytest.mark.skipif(platform.system() != "Darwin", reason="macOS-specific test")  
def test_macos_clipboard():
    """Test macOS-specific clipboard functionality."""
    # macOS-specific test implementation

@pytest.mark.skipif(platform.system() != "Linux", reason="Linux-specific test")
def test_linux_clipboard():
    """Test Linux-specific clipboard functionality."""
    # Linux-specific test implementation
```

### End-to-End Tests

<!-- SOURCE: tests/test_e2e.py -->
<!-- VERIFIED: 2025-07-16 -->
E2E tests validate complete system behavior:

```python
class MCPServerProcess:
    """Context manager for MCP server subprocess testing."""
    
    def __enter__(self):
        """Start server process."""
        self.process = subprocess.Popen(
            [sys.executable, "-m", "mcp_clipboard_server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up server process."""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=5)
```

## Code Architecture

### Adding New Tools

To add a new MCP tool, follow these steps:

1. **Define the tool schema** in `_tool_schemas.py`:

```python
# Add new tool schema
NEW_TOOL_SCHEMA: ToolInputSchema = {
    "type": "object",
    "properties": {
        "parameter": {
            "type": "string",
            "description": "Parameter description",
        }
    },
    "required": ["parameter"],
    "additionalProperties": False,
}

# Add to TOOL_DEFINITIONS
TOOL_DEFINITIONS["new_tool"] = {
    "name": "new_tool",
    "description": "Description of the new tool",
    "inputSchema": NEW_TOOL_SCHEMA,
}
```

2. **Implement the tool logic** in `tools.py`:

```python
def execute_tool(tool_name: str, params: Dict[str, Any]) -> ToolCallResult:
    # Add validation for new tool
    if tool_name == "new_tool":
        parameter = params["parameter"]
        return execute_new_tool(parameter)
    
    # ... existing tool handling

def validate_tool_params(tool_name: str, params: Dict[str, Any]) -> None:
    # Add parameter validation for new tool
    if tool_name == "new_tool":
        if not params or "parameter" not in params:
            raise ValueError("new_tool requires 'parameter' parameter")
        # Additional validation logic
```

3. **Add tool implementation** (create new module if complex):

```python
# In tools.py or new module
def execute_new_tool(parameter: str) -> ToolCallResult:
    """
    Implement the new tool functionality.
    
    Args:
        parameter: Tool parameter
        
    Returns:
        ToolCallResult containing execution results
        
    Raises:
        ValueError: If parameter is invalid
        RuntimeError: If tool execution fails
    """
    try:
        # Tool implementation
        result = perform_tool_operation(parameter)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Tool result: {result}"
                }
            ]
        }
    except Exception as e:
        logger.error("New tool execution failed: %s", e)
        raise RuntimeError(f"Tool execution failed: {str(e)}") from e
```

4. **Add comprehensive tests** in `tests/test_tools.py`:

```python
class TestNewTool:
    """Test new tool functionality."""
    
    def test_new_tool_schema(self):
        """Test new tool schema definition."""
        tool_definitions = get_all_tool_definitions()
        tool = tool_definitions["new_tool"]
        assert tool["name"] == "new_tool"
        assert "parameter" in tool["inputSchema"]["properties"]
    
    def test_new_tool_execution(self):
        """Test new tool execution."""
        result = execute_tool("new_tool", {"parameter": "test"})
        assert result["content"][0]["type"] == "text"
        # Additional assertions
    
    def test_new_tool_validation(self):
        """Test new tool parameter validation."""
        with pytest.raises(ValueError, match="requires 'parameter'"):
            validate_tool_params("new_tool", {})
```

### Error Handling Patterns

Follow established error handling patterns:

```python
# In tool implementation
try:
    # Tool operation
    result = perform_operation()
    return format_success_result(result)
    
except ValidationException as e:
    # Parameter validation errors
    logger.error("Validation error: %s", e)
    raise ValueError(f"Invalid parameters: {str(e)}") from e
    
except SpecificOperationError as e:
    # Tool-specific errors
    logger.error("Operation failed: %s", e)
    raise RuntimeError(f"Operation failed: {str(e)}") from e
    
except Exception as e:
    # Unexpected errors
    logger.error("Unexpected error: %s", e)
    raise RuntimeError(f"Unexpected error: {str(e)}") from e
```

### Logging Best Practices

Use structured logging throughout the codebase:

```python
import logging

logger = logging.getLogger(__name__)

def some_operation():
    """Example of proper logging usage."""
    logger.info("Starting operation with parameter: %s", param)
    
    try:
        result = perform_operation(param)
        logger.debug("Operation completed successfully: %s", result)
        return result
        
    except Exception as e:
        logger.error("Operation failed: %s", e, exc_info=True)
        raise
```

## Contributing Guidelines

### Code Style Standards

**Python Style Guidelines:**
- Follow PEP 8, enforced by black and flake8
- Maximum line length: 100 characters
- Use type hints for all public functions
- Google-style docstrings for documentation

**Example Function Documentation:**
```python
def example_function(param1: str, param2: int = 10) -> Dict[str, Any]:
    """
    Brief description of the function.
    
    Longer description providing more context about the function's
    purpose and behavior.
    
    Args:
        param1: Description of the first parameter.
        param2: Description of the second parameter with default value.
        
    Returns:
        Description of the return value and its structure.
        
    Raises:
        ValueError: When param1 is empty or invalid.
        RuntimeError: When the operation fails unexpectedly.
        
    Example:
        >>> result = example_function("test", 20)
        >>> print(result["status"])
        "success"
    """
    if not param1:
        raise ValueError("param1 cannot be empty")
        
    try:
        # Implementation
        return {"status": "success", "value": param1 * param2}
    except Exception as e:
        raise RuntimeError(f"Operation failed: {e}") from e
```

### Type Safety Requirements

All public APIs must include comprehensive type hints:

```python
from typing import Any, Dict, List, Optional, Union
from ._protocol_types import ToolCallResult, ToolInputSchema

def typed_function(
    required_param: str,
    optional_param: Optional[int] = None,
    complex_param: Dict[str, Any] = None
) -> ToolCallResult:
    """Function with comprehensive type annotations."""
    if complex_param is None:
        complex_param = {}
        
    # Implementation with type safety
    return {
        "content": [
            {
                "type": "text", 
                "text": f"Result: {required_param}"
            }
        ]
    }
```

### Commit Message Convention

Use conventional commit format for clear version history:

```
type(scope): description

feat(tools): add new clipboard history tool
fix(server): handle malformed JSON gracefully  
docs(api): update protocol documentation with batch examples
test(integration): add cross-platform clipboard tests
style(format): apply black formatting to all modules
refactor(errors): consolidate error handling utilities
perf(clipboard): optimize platform detection logic
```

**Commit Types:**
- `feat`: New features
- `fix`: Bug fixes
- `docs`: Documentation updates
- `test`: Test additions/modifications
- `style`: Code formatting (no functional changes)
- `refactor`: Code restructuring (no functional changes)
- `perf`: Performance improvements
- `chore`: Maintenance tasks

### Pull Request Process

1. **Create Feature Branch:**
   ```bash
   git checkout -b feature/descriptive-name
   ```

2. **Make Changes** following established patterns:
   - Follow code style guidelines
   - Add comprehensive tests
   - Update documentation
   - Verify type safety

3. **Run Quality Checks:**
   ```bash
   # Format code
   poetry run black src/ tests/
   poetry run isort src/ tests/
   
   # Validate quality
   poetry run flake8 src/ tests/
   poetry run mypy src/
   
   # Run tests
   poetry run pytest --cov=mcp_clipboard_server
   ```

4. **Submit Pull Request** with:
   - Clear description of changes
   - Link to related issues
   - Test coverage evidence
   - Documentation updates
   - Breaking change notes (if applicable)

### Review Process

Pull requests must pass:
- **Automated CI/CD pipeline** (all platforms, Python versions)
- **Code quality checks** (formatting, linting, type checking)
- **Test coverage requirements** (>90% line coverage)
- **Documentation completeness** (all public APIs documented)
- **Backwards compatibility** (unless breaking change is justified)

## Release Management

### Version Management

The project follows semantic versioning (SemVer):

- **Major version** (X.0.0): Breaking changes
- **Minor version** (1.X.0): New features, backwards compatible
- **Patch version** (1.0.X): Bug fixes, backwards compatible

### Release Process

<!-- SOURCE: .github/workflows/release.yml -->
<!-- VERIFIED: 2025-07-16 -->

1. **Prepare Release:**
   ```bash
   # Update version in pyproject.toml
   poetry version patch  # or minor, major
   
   # Update CHANGELOG.md with changes
   # Commit version bump
   git add pyproject.toml CHANGELOG.md
   git commit -m "chore: bump version to 1.0.1"
   ```

2. **Create Release Tag:**
   ```bash
   git tag v1.0.1
   git push origin v1.0.1
   ```

3. **Automated Release Pipeline:**
   - GitHub Actions automatically builds packages
   - Runs comprehensive test suite across all platforms
   - Publishes to TestPyPI for validation
   - Publishes to production PyPI
   - Creates GitHub release with changelog

### Package Building

```bash
# Build packages locally for testing
poetry build

# Verify package contents
tar -tzf dist/mcp_clipboard_server-1.0.0.tar.gz
unzip -l dist/mcp_clipboard_server-1.0.0-py3-none-any.whl

# Test installation from built package
pip install dist/mcp_clipboard_server-1.0.0-py3-none-any.whl
```

## Debugging and Troubleshooting

### Debug Configuration

Enable comprehensive debugging:

```bash
# Environment variables for debugging
export MCP_LOG_LEVEL=DEBUG
export MCP_LOG_JSON=true

# Run with debug output
poetry run mcp-clipboard-server 2>debug.log

# Monitor debug output
tail -f debug.log
```

### Interactive Testing

Create test scripts for manual validation:

```python
#!/usr/bin/env python3
"""Interactive testing script for MCP server."""

import json
import subprocess
import sys

def test_manual_interaction():
    """Manual testing interface."""
    process = subprocess.Popen(
        [sys.executable, "-m", "mcp_clipboard_server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        while True:
            # Get user input
            request_input = input("Enter JSON request (or 'quit'): ")
            if request_input.lower() == 'quit':
                break
            
            # Send request
            process.stdin.write(request_input + '\n')
            process.stdin.flush()
            
            # Read response
            response = process.stdout.readline()
            print(f"Response: {response.strip()}")
            
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        process.terminate()

if __name__ == "__main__":
    test_manual_interaction()
```

### Common Development Issues

**Import Errors:**
```bash
# Verify package installation
poetry run python -c "import mcp_clipboard_server; print('OK')"

# Check import paths
poetry run python -c "import sys; print(sys.path)"
```

**Test Failures:**
```bash
# Run specific failing test with verbose output
poetry run pytest tests/test_specific.py::test_function -v -s

# Run with debugging information
poetry run pytest tests/test_specific.py::test_function --pdb

# Check test environment
poetry run python -c "import platform; print(platform.platform())"
```

**Platform Issues:**
```bash
# Check platform detection
poetry run python -c "
from mcp_clipboard_server.clipboard import detect_platform
print(detect_platform())
"

# Test clipboard utilities
# Linux
which xclip && echo 'xclip available'
which wl-copy && echo 'wl-copy available'

# macOS  
which pbcopy && echo 'pbcopy available'

# Windows
python -c "import win32clipboard; print('win32clipboard available')"
```

### Performance Profiling

Profile server performance during development:

```python
import cProfile
import pstats
from mcp_clipboard_server.server import MCPServer

def profile_server():
    """Profile server performance."""
    server = MCPServer()
    
    # Profile server operations
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run test operations
    test_requests = [
        '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05"}}',
        '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}',
        '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get_clipboard","arguments":{}}}',
    ]
    
    for request in test_requests:
        server.handle_request(request)
    
    profiler.disable()
    
    # Generate performance report
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)

if __name__ == "__main__":
    profile_server()
```

## Documentation Maintenance

### API Documentation

Keep API documentation synchronized with code:

```bash
# Verify all public APIs are documented
poetry run python -c "
import ast
import inspect
from mcp_clipboard_server import tools

for name, obj in inspect.getmembers(tools):
    if inspect.isfunction(obj) and not name.startswith('_'):
        if not obj.__doc__:
            print(f'Missing docstring: {name}')
"
```

### Documentation Testing

Validate documentation examples:

```python
# Test documentation examples
def test_documentation_examples():
    """Verify that documentation examples work correctly."""
    
    # Example from API documentation
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "get_clipboard",
            "arguments": {}
        }
    }
    
    # Validate example works
    from mcp_clipboard_server.tools import execute_tool
    result = execute_tool("get_clipboard", {})
    assert "content" in result
    assert result["content"][0]["type"] == "text"
```

---

This development guide provides everything needed to contribute effectively to the MCP Clipboard Server project. For additional information, refer to:

- [API Reference](api_reference.md) - Technical API documentation
- [Architecture Documentation](architecture.md) - Internal system design
- [Platform Guide](platform_guide.md) - Platform-specific setup
- [Troubleshooting Guide](troubleshooting.md) - Issue resolution
