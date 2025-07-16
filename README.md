# MCP Clipboard Server

A [Model Context Protocol (MCP)](https://spec.modelcontextprotocol.io/) server that provides clipboard access tools for AI assistants and automation workflows. Seamlessly integrate clipboard operations into your AI-powered applications.

[![PyPI version](https://badge.fury.io/py/mcp-clipboardify.svg)](https://badge.fury.io/py/mcp-clipboardify)
[![Python Support](https://img.shields.io/pypi/pyversions/mcp-clipboardify.svg)](https://pypi.org/project/mcp-clipboardify/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📚 Quick Navigation

- [🚀 Quick Start](#-quick-start) - Get up and running in minutes
- [✨ Features](#-features) - Full feature overview
- [📋 Tools](#-tools) - Available clipboard operations
- [🔧 Usage Examples](#-usage-examples) - JSON-RPC protocol examples
- [🏗️ Installation & Setup](#-installation--setup) - Platform-specific instructions
- [🔍 Troubleshooting](#-troubleshooting) - Platform support and common issues
- [📖 Technical Reference](#-protocol-details--technical-reference) - Protocol details
- [🤝 Contributing](#-contributing) - Development and contribution guidelines

## 🚀 Quick Start

Install the server:

```bash
pip install mcp-clipboardify
```

Start the server:

```bash
mcp-clipboardify
# or alternatively:
python -m mcp_clipboard_server
```

## ✨ Features

- **Cross-platform clipboard access** - Works on Windows, macOS, and Linux with platform-specific fallback handling
- **MCP protocol compliance** - Full JSON-RPC 2.0 over STDIO implementation with batch request support
- **JSON Schema validation** - Comprehensive parameter validation with detailed error messages
- **Two core tools**:
  - `get_clipboard` - Retrieve current clipboard content
  - `set_clipboard` - Set clipboard to provided text
- **Enhanced error handling** - Platform-specific guidance for troubleshooting clipboard issues
- **Graceful degradation** - Fails safely with empty string on read errors, detailed error messages on write failures
- **Size limits** - 1MB text limit to prevent memory issues
- **Unicode support** - Full UTF-8 support for international text and emoji
- **Type safety** - Built with TypedDict for reliable protocol compliance
- **Production ready** - Comprehensive testing across platforms with CI/CD pipeline

## 📋 Tools

### `get_clipboard`
Retrieves the current text content from the system clipboard.

**Parameters:** None

**Returns:** Current clipboard content as a string

### `set_clipboard`
Sets the system clipboard to the provided text content.

**Parameters:**
- `text` (string, required): The text content to copy to the clipboard
  - Maximum size: 1MB (1,048,576 bytes)
  - Supports Unicode text and emoji

**Returns:** Success confirmation

## 🔧 Usage Examples

### Basic MCP Client Communication

The server uses JSON-RPC 2.0 over STDIO. Here are example request/response patterns:

#### Initialize the connection:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "example-client",
      "version": "1.0.0"
    }
  }
}
```

#### List available tools:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

#### Get clipboard content:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "get_clipboard",
    "arguments": {}
  }
}
```

#### Set clipboard content:
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "set_clipboard",
    "arguments": {
      "text": "Hello, World! 🌍"
    }
  }
}
```

#### Batch Requests (JSON-RPC 2.0)
The server supports batch requests for processing multiple operations in a single call:
```json
[
  {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "get_clipboard",
      "arguments": {}
    }
  },
  {
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "set_clipboard",
      "arguments": {
        "text": "Batch operation result"
      }
    }
  }
]
```

## 🔧 JSON-RPC 2.0 Compliance

This server implements full JSON-RPC 2.0 specification with the following features:

### Supported Features
- ✅ **Single requests** - Standard request/response pattern
- ✅ **Batch requests** - Process multiple requests in one call
- ✅ **Notifications** - Fire-and-forget messages (e.g., `$/ping`)
- ✅ **Error handling** - Comprehensive error codes and messages
- ✅ **Parameter validation** - JSON Schema-based validation with detailed error reports

### Schema Validation
All tool parameters are validated against JSON schemas with helpful error messages:
- **Type validation** - Ensures parameters are correct types
- **Required fields** - Validates all required parameters are present
- **Size limits** - Enforces 1MB text size limit for clipboard operations
- **Additional properties** - Rejects unexpected parameters

### Error Codes
The server uses standard JSON-RPC 2.0 error codes plus MCP-specific extensions:
- `-32700` Parse error (invalid JSON)
- `-32600` Invalid Request (malformed JSON-RPC)
- `-32601` Method not found
- `-32602` Invalid params (schema validation failures)
- `-32603` Internal error
- `-32000` Server error (MCP-specific errors)

### Integration with MCP Clients

This server works with any MCP-compatible client. Example integration:

```python
import subprocess
import json

# Start the server
process = subprocess.Popen(
    ["mcp-clipboardify"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    text=True
)

# Send initialize request
init_request = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2024-11-05",
        "capabilities": {},
        "clientInfo": {"name": "my-client", "version": "1.0.0"}
    }
}

process.stdin.write(json.dumps(init_request) + '\n')
process.stdin.flush()

# Read response
response = json.loads(process.stdout.readline())
print(response)
```

## 🏗️ Installation & Setup

### System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **Dependencies**: pyperclip for cross-platform clipboard access

### Platform-Specific Setup

#### Linux
You may need to install additional packages for clipboard support:

```bash
# Ubuntu/Debian
sudo apt-get install xclip
# or
sudo apt-get install xsel

# Fedora/RHEL
sudo dnf install xclip
```

#### Windows & macOS
No additional setup required - clipboard access works out of the box.

### Install from PyPI

```bash
pip install mcp-clipboardify
```

### Install from Source

```bash
git clone https://github.com/fluffypony/mcp-clipboardify.git
cd mcp-clipboardify
poetry install
```

## 🧪 Development

### Setup Development Environment

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

4. **Run the server in development:**
   ```bash
   poetry run python -m mcp_clipboard_server
   ```

### Testing

Run the test suite:

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=mcp_clipboard_server

# Run specific test categories
poetry run pytest tests/test_unit.py
poetry run pytest tests/test_integration.py
```

### Code Quality

```bash
# Type checking
poetry run mypy src/

# Linting
poetry run flake8 src/

# Formatting
poetry run black src/ tests/
```

## 🔍 Troubleshooting

### Platform Support

The MCP Clipboard Server provides comprehensive cross-platform support with intelligent fallback handling:

#### ✅ Windows
- **Requirements**: No additional dependencies
- **Supported**: Windows 10/11, Windows Server 2019+
- **Features**: Full Unicode support, CRLF line ending handling
- **Notes**: May require clipboard access permissions in some enterprise environments

#### ✅ macOS
- **Requirements**: macOS 10.15+ recommended
- **Supported**: Intel and Apple Silicon Macs
- **Features**: Full Unicode support, RTF content fallback to plain text
- **Notes**: Security permissions may be required (System Preferences > Privacy & Security)

#### ✅ Linux
- **Requirements**: X11 display server and clipboard utilities
- **Installation**:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install xclip xsel

  # RHEL/CentOS/Fedora
  sudo yum install xclip xsel

  # Arch Linux
  sudo pacman -S xclip xsel
  ```
- **Supported Distributions**: Ubuntu, Debian, RHEL, CentOS, Fedora, Arch Linux
- **Features**: Full Unicode support, headless environment detection
- **Notes**: Requires DISPLAY environment variable for GUI clipboard access

#### 🔧 WSL (Windows Subsystem for Linux)
- **Requirements**: WSL2 with Windows 10 build 19041+
- **Installation**:
  ```bash
  sudo apt-get install wslu  # For clip.exe integration
  ```
- **Features**: Clipboard sharing with Windows host
- **Notes**: Use Windows Terminal or enable clipboard sharing in WSL configuration

#### 🚫 Headless/Server Environments
- **Behavior**: Graceful degradation - read operations return empty string
- **Use Case**: Automated testing, CI/CD environments
- **Notes**: Write operations will fail with descriptive error messages

### Platform-Specific Guidance

The server automatically detects your platform and provides specific guidance when clipboard operations fail:

#### Linux Troubleshooting
```bash
# Missing utilities error
sudo apt-get install xclip xsel

# No display error
export DISPLAY=:0  # or run in desktop environment

# Headless system
# Read operations return empty string (graceful)
# Write operations fail with clear error message
```

#### WSL Troubleshooting
```bash
# Install Windows integration
sudo apt-get install wslu

# Enable clipboard sharing in ~/.wslconfig
[wsl2]
guiApplications=true
```

#### macOS Troubleshooting
```bash
# Security permissions
# Go to System Preferences > Privacy & Security > Input Monitoring
# Add Terminal or your application

# Sandboxed applications
# May have limited clipboard access
```

#### Windows Troubleshooting
```cmd
REM Antivirus blocking
REM Add exception for clipboard access

REM Enterprise policies
REM Check with IT administrator for clipboard permissions
```

### Common Issues

#### Platform Detection Issues
**Symptoms**: Unexpected platform-specific errors
**Solution**: The server automatically detects your environment. Check logs with `MCP_LOG_LEVEL=DEBUG` for detailed platform information.

#### Unicode Content Problems
**Symptoms**: International text or emoji not displaying correctly
**Solution**: Ensure your terminal/application supports UTF-8 encoding. The server handles Unicode correctly on all platforms.

#### Large Content Handling
**Solution**: The server enforces a 1MB limit. Split large content into smaller chunks.

#### Server Not Responding
**Solution**: Check that the client is sending proper JSON-RPC 2.0 formatted messages.

### Debugging

Enable debug logging:

```bash
# Set environment variable for detailed logs
export MCP_LOG_LEVEL=DEBUG
export MCP_LOG_JSON=true
mcp-clipboardify
```

### Getting Help

- **Platform Guide**: [Platform-specific setup instructions](docs/platform_guide.md)
- **Troubleshooting**: [Common issues and solutions](docs/troubleshooting.md)
- **Issues**: [GitHub Issues](https://github.com/fluffypony/mcp-clipboardify/issues)
- **Discussions**: [GitHub Discussions](https://github.com/fluffypony/mcp-clipboardify/discussions)
- **MCP Specification**: [Model Context Protocol](https://spec.modelcontextprotocol.io/)

### Installation Verification

After installation, verify everything works:

```bash
# Quick verification
mcp-clipboardify --help

# Comprehensive verification (requires download)
curl -sSL https://raw.githubusercontent.com/fluffypony/mcp-clipboardify/main/scripts/verify_installation.sh | bash

# Or with Python script
python -c "from scripts.verify_installation import InstallationVerifier; InstallationVerifier().run_all_tests()"
```

## 📖 Protocol Details & Technical Reference

### MCP Compliance

This server implements the [Model Context Protocol](https://spec.modelcontextprotocol.io/) specification:

- **Transport**: JSON-RPC 2.0 over STDIO
- **Required methods**: `initialize`, `tools/list`, `tools/call`
- **Optional methods**: Ping notifications for keep-alive
- **Error handling**: Standard JSON-RPC error codes

### Message Format

All messages are line-delimited JSON objects:

```
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{...}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
```

### Error Codes

The server returns standard JSON-RPC 2.0 error codes:

- `-32700`: Parse error (invalid JSON)
- `-32600`: Invalid request (malformed JSON-RPC)
- `-32601`: Method not found
- `-32602`: Invalid params
- `-32603`: Internal error

## 🤝 Contributing

We welcome contributions! Please see our [Development Guide](docs/development_guide.md) for contributing guidelines and workflow details.

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Add tests for new functionality
5. Run the test suite: `poetry run pytest`
6. Commit your changes: `git commit -am 'Add my feature'`
7. Push to the branch: `git push origin feature/my-feature`
8. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Model Context Protocol](https://spec.modelcontextprotocol.io/) specification
- [pyperclip](https://pypi.org/project/pyperclip/) for cross-platform clipboard access
- The Python community for excellent tooling and libraries

---

**Made with ❤️ for the AI and automation community**
