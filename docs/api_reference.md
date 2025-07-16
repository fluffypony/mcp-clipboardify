# MCP Clipboard Server - API Reference

---
Last Updated: 2025-07-16
Version: 1.0.0
Verified Against: Current implementation
Test Sources: tests/test_mcp_integration.py, tests/test_tools.py
Implementation: src/mcp_clipboard_server/
---

## Overview

The MCP Clipboard Server implements the [Model Context Protocol](https://spec.modelcontextprotocol.io/) specification over JSON-RPC 2.0 via STDIO transport. This document provides a complete technical reference for all supported methods, data structures, and error codes.

## Protocol Compliance

- **Protocol Version**: `2024-11-05`
- **Transport**: JSON-RPC 2.0 over STDIO
- **Message Format**: Line-delimited JSON
- **Character Encoding**: UTF-8
- **Batch Requests**: Supported

## Request/Response Flow

### 1. Initialize Connection

```json
REQUEST:
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "clientInfo": {
      "name": "example-client",
      "version": "1.0.0"
    },
    "capabilities": {}
  }
}

RESPONSE:
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "serverInfo": {
      "name": "mcp-clipboardify",
      "version": "1.0.0"
    },
    "capabilities": {
      "tools": {}
    }
  }
}
```

### 2. Discover Available Tools

```json
REQUEST:
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}

RESPONSE:
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "get_clipboard",
        "description": "Get the current text content from the system clipboard",
        "inputSchema": {
          "type": "object",
          "properties": {},
          "required": [],
          "additionalProperties": false
        }
      },
      {
        "name": "set_clipboard",
        "description": "Set the system clipboard to the provided text content",
        "inputSchema": {
          "type": "object",
          "properties": {
            "text": {
              "type": "string",
              "description": "The text content to copy to the clipboard",
              "maxLength": 1048576
            }
          },
          "required": ["text"],
          "additionalProperties": false
        }
      }
    ]
  }
}
```

## Methods

### initialize

Establishes the MCP session and negotiates protocol version and capabilities.

**Request Parameters:**
- `protocolVersion` (string, optional): Protocol version (server responds with `"2024-11-05"`)
- `clientInfo` (object, optional): Client identification
  - `name` (string): Client name
  - `version` (string): Client version
- `capabilities` (object, optional): Client capabilities (unused by this server)

**Response:**
- `protocolVersion` (string): Always `"2024-11-05"` (server's supported version)
- `serverInfo` (object): Server identification
  - `name` (string): Always `"mcp-clipboardify"`
  - `version` (string): Server version
- `capabilities` (object): Server capabilities
  - `tools` (object): Empty object indicating tool support

**Note:** The server accepts any protocol version from clients and always responds with its supported version `"2024-11-05"`. No validation is performed on the client's protocol version.

### tools/list

Returns the list of available clipboard tools.

**Request Parameters:** None

**Response:**
- `tools` (array): List of tool definitions (see Tool Definitions section)

**Errors:** None (always succeeds after initialization)

### tools/call

Executes a clipboard tool with specified parameters.

**Request Parameters:**
- `name` (string, required): Tool name (`"get_clipboard"` or `"set_clipboard"`)
- `arguments` (object, required): Tool-specific parameters

**Response:**
- `content` (array): Array containing a single text content object
  - `type` (string): Always `"text"`
  - `text` (string): Result text

**Errors:**
- `-32601` Method not found: Unknown tool name
- `-32602` Invalid params: Invalid tool parameters
- `-32001` Clipboard error: Platform clipboard access failed

## Tools

### get_clipboard

Retrieves current text content from the system clipboard.

<!-- SOURCE: tests/test_mcp_integration.py:92-102 -->
<!-- VERIFIED: 2025-07-16 -->
**Example Request:**
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

**Parameters:**
- None (empty object or omitted)

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Hello, World!"
      }
    ]
  }
}
```

**Empty Clipboard Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": ""
      }
    ]
  }
}
```

**Error Conditions:**
- Platform clipboard access failure
- Headless environment without display server

### set_clipboard

Sets the system clipboard to specified text content.

<!-- SOURCE: tests/test_mcp_integration.py:105-117 -->
<!-- VERIFIED: 2025-07-16 -->
**Example Request:**
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

**Parameters:**
- `text` (string, required): Text content to copy to clipboard
  - Maximum length: 1,048,576 characters (1MB)
  - Supports full Unicode including emoji
  - Line endings preserved as provided

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Text copied to clipboard"
      }
    ]
  }
}
```

**Error Conditions:**
- Text parameter missing or invalid type
- Text exceeds 1MB size limit
- Platform clipboard access failure
- Additional unexpected parameters provided

## Batch Requests

The server supports JSON-RPC 2.0 batch requests for processing multiple operations.

<!-- SOURCE: tests/test_mcp_integration.py:120-144 -->
<!-- VERIFIED: 2025-07-16 -->
**Example Batch Request:**
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

**Batch Response:**
```json
[
  {
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
      "content": [
        {
          "type": "text",
          "text": "Previous clipboard content"
        }
      ]
    }
  },
  {
    "jsonrpc": "2.0",
    "id": 2,
    "result": {
      "content": [
        {
          "type": "text",
          "text": "Text copied to clipboard"
        }
      ]
    }
  }
]
```

**Batch Processing Rules:**
- Empty batches return error `-32600` Invalid Request
- Individual request failures don't abort the entire batch
- Responses maintain the same order as requests
- Each request/response pair is processed independently

## Error Codes

### Standard JSON-RPC 2.0 Errors

| Code | Message | Description |
|------|---------|-------------|
| `-32700` | Parse error | Invalid JSON received |
| `-32600` | Invalid Request | Malformed JSON-RPC request |
| `-32601` | Method not found | Unknown method or tool name |
| `-32602` | Invalid params | Parameter validation failed |
| `-32603` | Internal error | Server internal error |

### MCP-Specific Errors

| Code | Message | Description |
|------|---------|-------------|
| `-32000` | Server error | General server error |
| `-32001` | Clipboard error | Platform clipboard operation failed |

### Detailed Error Responses

**Unknown Tool:**
```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "error": {
    "code": -32601,
    "message": "Method not found",
    "data": {
      "details": "Unknown tool: invalid_tool"
    }
  }
}
```

**Invalid Parameters:**
```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": {
      "details": "set_clipboard requires 'text' parameter"
    }
  }
}
```

**Text Size Limit Exceeded:**
```json
{
  "jsonrpc": "2.0",
  "id": 7,
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": {
      "details": "Text content exceeds maximum size of 1048576 characters"
    }
  }
}
```

**Clipboard Access Failed:**
```json
{
  "jsonrpc": "2.0",
  "id": 8,
  "error": {
    "code": -32001,
    "message": "Clipboard error",
    "data": {
      "details": "Failed to access system clipboard: No display environment available"
    }
  }
}
```

## Data Types

### JSON Schema Definitions

**Tool Input Schema:**
```typescript
interface ToolInputSchema {
  type: "object";
  properties: Record<string, any>;
  required: string[];
  additionalProperties: boolean;
}
```

**Tool Definition:**
```typescript
interface ToolDefinition {
  name: string;
  description: string;
  inputSchema: ToolInputSchema;
}
```

**Text Content:**
```typescript
interface TextContent {
  type: "text";
  text: string;
}
```

**Tool Call Result:**
```typescript
interface ToolCallResult {
  content: TextContent[];
}
```

## Implementation Notes

### Schema Validation

The server performs comprehensive JSON Schema validation on all tool parameters:

<!-- SOURCE: src/mcp_clipboard_server/_tool_schemas.py:16-27 -->
<!-- VERIFIED: 2025-07-16 -->
```python
SET_CLIPBOARD_SCHEMA: ToolInputSchema = {
    "type": "object",
    "properties": {
        "text": {
            "type": "string",
            "description": "The text content to copy to the clipboard",
            "maxLength": 1048576,  # 1MB limit
        }
    },
    "required": ["text"],
    "additionalProperties": False,
}
```

### Error Handling Strategy

<!-- SOURCE: tests/test_tools.py:101-121 -->
<!-- VERIFIED: 2025-07-16 -->
The server maps exceptions to appropriate JSON-RPC error codes:

- `ValueError` → `-32602` Invalid params
- `ClipboardError` → `-32001` Clipboard error  
- `ValidationException` → `-32602` Invalid params
- `RuntimeError` → `-32000` Server error

### Unicode Support

The server provides full UTF-8 support for international text and emoji:

<!-- SOURCE: tests/test_mcp_integration.py:20-25 -->
<!-- VERIFIED: 2025-07-16 -->
```python
test_data = {
    "unicode_text": "Hello 世界 🌍 emoji test ñ",
    "short_text": "Hello, World!",
    "long_text": "A" * 1000,  # 1KB text
    "empty_text": "",
}
```

### Size Limits

- **Maximum text size**: 1,048,576 characters (1MB)
- **Validation**: Performed before clipboard operations
- **Error response**: `-32602` Invalid params with size details

### Platform Detection

The server automatically detects platform capabilities and provides appropriate error guidance:

- **Windows**: Uses native Win32 clipboard APIs
- **macOS**: Uses Pasteboard APIs  
- **Linux X11**: Requires `xclip` or `xsel`
- **Linux Wayland**: Uses `wl-clipboard` tools
- **WSL**: Integrates with Windows clipboard
- **Headless**: Graceful degradation with informative errors

## Transport Details

### Message Format

All messages are line-delimited JSON objects:

```
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{...}}\n
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}\n
```

### STDIO Protocol

- **Input**: Read from `stdin`
- **Output**: Write to `stdout` 
- **Errors**: Log to `stderr`
- **Buffering**: Explicit flush after each response
- **Encoding**: UTF-8

### Connection Lifecycle

1. **Start**: Launch server process
2. **Initialize**: Send initialize request
3. **Operate**: Send tool requests
4. **Terminate**: Send SIGTERM or close stdin

### Graceful Shutdown

The server handles shutdown signals gracefully:

- **SIGTERM**: Clean shutdown (Unix/Linux/macOS)
- **SIGINT**: Interrupt handling (Ctrl+C)  
- **EOF**: Stdin closure detection
- **Windows**: Polling-based shutdown detection

## Client Integration Examples

### Python Client

<!-- SOURCE: README.md:179-208 -->
<!-- VERIFIED: 2025-07-16 -->
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

### Async Python Client

<!-- SOURCE: tests/test_mcp_integration.py:40-86 -->
<!-- VERIFIED: 2025-07-16 -->
```python
import asyncio
import json
import sys

async def async_mcp_client():
    # Start server subprocess
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "mcp_clipboard_server",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    
    reader, writer = process.stdout, process.stdin
    
    # Send request
    request = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "id": "test-id",
        "params": {
            "protocolVersion": "2024-11-05",
            "clientInfo": {"name": "test", "version": "1.0"}
        }
    }
    
    request_line = json.dumps(request) + "\n"
    writer.write(request_line.encode())
    await writer.drain()
    
    # Read response
    response_line = await reader.readline()
    response = json.loads(response_line.decode())
    
    return response
```

## Testing and Validation

### Minimal Test Case

<!-- SOURCE: tests/test_mcp_integration.py:400-425 -->
<!-- VERIFIED: 2025-07-16 -->
For testing clipboard functionality:

```python
async def test_clipboard_roundtrip():
    """Test setting and getting clipboard content."""
    reader, writer = await start_server()
    
    # Initialize
    await send_request(writer, "initialize", {
        "protocolVersion": "2024-11-05"
    })
    await read_response(reader)
    
    # Set clipboard
    await send_request(writer, "tools/call", {
        "name": "set_clipboard",
        "arguments": {"text": "test content"}
    })
    set_response = await read_response(reader)
    
    # Get clipboard
    await send_request(writer, "tools/call", {
        "name": "get_clipboard",
        "arguments": {}
    })
    get_response = await read_response(reader)
    
    assert get_response["result"]["content"][0]["text"] == "test content"
```

### Platform Testing

The server includes platform-specific tests for:

- Windows native clipboard APIs
- macOS Pasteboard integration  
- Linux X11 clipboard utilities
- Wayland wl-clipboard support
- WSL clipboard bridging
- Headless environment graceful degradation

## Security Considerations

### Access Control

- **No Authentication**: Server assumes authorized client context
- **Process Isolation**: Runs in separate process from client
- **Limited Scope**: Only clipboard access, no file system access
- **No Persistence**: No storage of clipboard content

### Resource Limits

- **Text Size**: 1MB maximum to prevent memory exhaustion
- **Request Timeout**: Individual operations timeout after 5 seconds
- **Single Threading**: No concurrent request processing
- **Memory Bounded**: Text size limits prevent unbounded growth

### Privacy

- **No Logging**: Clipboard content never logged or stored
- **Ephemeral**: Content only in memory during operation
- **Process Boundary**: Content doesn't persist after tool execution

## Troubleshooting API Issues

### Common Integration Problems

**Invalid JSON Format:**
- Ensure proper JSON formatting
- Use line-delimited messages (each ending with `\n`)
- Verify UTF-8 encoding

**Protocol Version Mismatch:**
- Use exactly `"2024-11-05"` as protocol version
- Check server compatibility

**Missing Required Fields:**
- Include all required JSON-RPC 2.0 fields: `jsonrpc`, `method`, `id`
- Validate tool parameters against schemas

**Buffer Management:**
- Always flush stdout after writing requests
- Handle EOF conditions properly
- Implement timeout handling for responses

### Debug Mode

Enable detailed protocol logging:

```bash
export MCP_LOG_LEVEL=DEBUG
export MCP_LOG_JSON=true  
mcp-clipboardify
```

This provides:
- Request/response message tracing
- Tool execution details
- Platform operation logging
- Error stack traces

## Version History

### 1.0.0 (Current)
- Full MCP 2024-11-05 protocol compliance
- JSON-RPC 2.0 batch request support
- Cross-platform clipboard operations
- Enhanced error handling and validation
- Comprehensive JSON Schema validation
- Platform-specific fallback handling

---

For implementation examples, platform-specific guidance, and troubleshooting, see:
- [Platform Guide](platform_guide.md)
- [Troubleshooting Guide](troubleshooting.md)
- [Main README](../README.md)
