# MCP Clipboard Server

A [Model Context Protocol (MCP)](https://spec.modelcontextprotocol.io/) server that provides clipboard access tools for AI assistants and automation workflows. Seamlessly integrate clipboard operations into your AI-powered applications.

[![PyPI version](https://badge.fury.io/py/mcp-clipboard-server.svg)](https://badge.fury.io/py/mcp-clipboard-server)
[![Python Support](https://img.shields.io/pypi/pyversions/mcp-clipboard-server.svg)](https://pypi.org/project/mcp-clipboard-server/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 Quick Start

Install the server:

```bash
pip install mcp-clipboard-server
```

Start the server:

```bash
mcp-clipboard-server
# or alternatively:
python -m mcp_clipboard_server
```

## ✨ Features

- **Cross-platform clipboard access** - Works on Windows, macOS, and Linux
- **MCP protocol compliance** - Full JSON-RPC 2.0 over STDIO implementation
- **Two core tools**:
  - `get_clipboard` - Retrieve current clipboard content
  - `set_clipboard` - Set clipboard to provided text
- **Robust error handling** - Graceful degradation and comprehensive logging
- **Size limits** - 1MB text limit to prevent memory issues
- **Unicode support** - Full UTF-8 support for international text and emoji
- **Type safety** - Built with TypedDict for reliable protocol compliance

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

### Integration with MCP Clients

This server works with any MCP-compatible client. Example integration:

```python
import subprocess
import json

# Start the server
process = subprocess.Popen(
    ["mcp-clipboard-server"],
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
pip install mcp-clipboard-server
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

### Common Issues

#### "No clipboard support" error on Linux
**Solution:** Install xclip or xsel:
```bash
sudo apt-get install xclip
```

#### Permission denied errors
**Solution:** Ensure the process has access to the clipboard system.

#### Large text causing memory issues
**Solution:** The server enforces a 1MB limit. Split large content into smaller chunks.

#### Server not responding
**Solution:** Check that the client is sending proper JSON-RPC 2.0 formatted messages.

### Debugging

Enable debug logging:

```bash
# Set environment variable for detailed logs
export MCP_LOG_LEVEL=DEBUG
export MCP_LOG_JSON=true
mcp-clipboard-server
```

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/fluffypony/mcp-clipboardify/issues)
- **Discussions**: [GitHub Discussions](https://github.com/fluffypony/mcp-clipboardify/discussions)
- **MCP Specification**: [Model Context Protocol](https://spec.modelcontextprotocol.io/)

## 📖 Protocol Details

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

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

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
