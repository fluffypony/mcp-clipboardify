# MCP Clipboard Server

A Model Context Protocol (MCP) server that provides clipboard access tools for AI assistants and other clients.

## Features

- Cross-platform clipboard access (Windows, macOS, Linux)
- Standard MCP protocol compliance
- Simple JSON-RPC 2.0 interface over STDIO
- Two core tools: `get_clipboard` and `set_clipboard`

## Installation

```bash
pip install mcp-clipboard-server
```

## Usage

The server communicates via STDIO using JSON-RPC 2.0 messages:

```bash
python -m mcp_clipboard_server
```

## Development

1. Install Poetry
2. Clone this repository
3. Install dependencies: `poetry install`
4. Run tests: `poetry run pytest`

## Requirements

- Python 3.11 or higher
- Cross-platform clipboard support through pyperclip
