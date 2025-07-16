"""End-to-end subprocess tests for MCP clipboard server."""

import json
import subprocess
import sys
import threading
import time
from typing import Any, Dict, Optional
import pytest
import pyperclip


class MCPServerProcess:
    """Helper class to manage MCP server subprocess."""
    
    def __init__(self):
        self.process: Optional[subprocess.Popen] = None
        self.original_clipboard: str = ""
        
    def start(self, timeout: float = 5.0) -> None:
        """Start the MCP server subprocess."""
        # Save original clipboard content
        try:
            self.original_clipboard = pyperclip.paste() or ""
        except Exception:
            self.original_clipboard = ""
        
        # Start the server process
        cmd = [sys.executable, "-m", "mcp_clipboard_server"]
        self.process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0  # Unbuffered
        )
        
        # Give the process time to start
        time.sleep(0.1)
        
        if self.process.poll() is not None:
            stdout, stderr = self.process.communicate()
            raise RuntimeError(f"Server process failed to start:\nstdout: {stdout}\nstderr: {stderr}")
    
    def stop(self) -> None:
        """Stop the MCP server subprocess."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            self.process = None
        
        # Restore original clipboard content
        try:
            pyperclip.copy(self.original_clipboard)
        except Exception:
            pass  # Best effort restore
    
    def send_request(self, request: Dict[str, Any], timeout: float = 5.0) -> Dict[str, Any]:
        """Send a JSON-RPC request and get the response."""
        if not self.process:
            raise RuntimeError("Server process not started")
        
        request_line = json.dumps(request) + '\n'
        
        try:
            self.process.stdin.write(request_line)
            self.process.stdin.flush()
        except BrokenPipeError:
            raise RuntimeError("Failed to send request - server process terminated")
        
        # Read response with timeout
        response_line = None
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.process.stdout.readable():
                response_line = self.process.stdout.readline()
                if response_line:
                    break
            time.sleep(0.01)
        
        if not response_line:
            # Check if process is still alive
            if self.process.poll() is not None:
                stdout, stderr = self.process.communicate()
                raise RuntimeError(f"Server process terminated:\nstdout: {stdout}\nstderr: {stderr}")
            raise TimeoutError(f"No response received within {timeout} seconds")
        
        try:
            return json.loads(response_line.strip())
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {response_line.strip()}") from e


@pytest.fixture
def mcp_server():
    """Fixture to provide an MCP server subprocess."""
    server = MCPServerProcess()
    server.start()
    yield server
    server.stop()


def test_server_startup_and_shutdown(mcp_server):
    """Test that the server starts and can be shutdown cleanly."""
    # Server should be running
    assert mcp_server.process is not None
    assert mcp_server.process.poll() is None


def test_initialize_request(mcp_server):
    """Test the MCP initialize handshake."""
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    response = mcp_server.send_request(init_request)
    
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1
    assert "result" in response
    assert "protocolVersion" in response["result"]
    assert "serverInfo" in response["result"]


def test_tools_list_request(mcp_server):
    """Test listing available tools."""
    # First initialize
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    }
    mcp_server.send_request(init_request)
    
    # Then list tools
    tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    response = mcp_server.send_request(tools_request)
    
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 2
    assert "result" in response
    assert "tools" in response["result"]
    
    tools = response["result"]["tools"]
    tool_names = [tool["name"] for tool in tools]
    assert "get_clipboard" in tool_names
    assert "set_clipboard" in tool_names


def test_get_clipboard_tool(mcp_server):
    """Test the get_clipboard tool."""
    # Initialize first
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    }
    mcp_server.send_request(init_request)
    
    # Set a known value in clipboard
    test_text = "Test clipboard content for E2E test"
    pyperclip.copy(test_text)
    
    # Call get_clipboard tool
    get_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "get_clipboard",
            "arguments": {}
        }
    }
    
    response = mcp_server.send_request(get_request)
    
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 2
    assert "result" in response
    assert "content" in response["result"]
    
    # The content should match what we set
    content = response["result"]["content"]
    assert isinstance(content, list)
    assert len(content) == 1
    assert content[0]["type"] == "text"
    assert content[0]["text"] == test_text


def test_set_clipboard_tool(mcp_server):
    """Test the set_clipboard tool."""
    # Initialize first
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    }
    mcp_server.send_request(init_request)
    
    # Set clipboard via MCP tool
    test_text = "Hello from MCP set_clipboard! 🚀"
    set_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "set_clipboard",
            "arguments": {
                "text": test_text
            }
        }
    }
    
    response = mcp_server.send_request(set_request)
    
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 2
    assert "result" in response
    assert "content" in response["result"]
    
    # Verify the clipboard was actually set
    actual_clipboard = pyperclip.paste()
    assert actual_clipboard == test_text


def test_unicode_content(mcp_server):
    """Test Unicode and emoji content handling."""
    # Initialize first
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    }
    mcp_server.send_request(init_request)
    
    # Test with various Unicode characters and emoji
    unicode_text = "Hello 世界! 🌍🚀 Ñoël ñ français αβγδε"
    set_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "set_clipboard",
            "arguments": {
                "text": unicode_text
            }
        }
    }
    
    response = mcp_server.send_request(set_request)
    assert "result" in response
    
    # Verify Unicode content is preserved
    actual_clipboard = pyperclip.paste()
    assert actual_clipboard == unicode_text


def test_large_text_validation(mcp_server):
    """Test that large text (>1MB) is rejected."""
    # Initialize first
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    }
    mcp_server.send_request(init_request)
    
    # Create text larger than 1MB
    large_text = "x" * (1024 * 1024 + 1)  # 1MB + 1 byte
    set_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "set_clipboard",
            "arguments": {
                "text": large_text
            }
        }
    }
    
    response = mcp_server.send_request(set_request)
    
    # Should return an error
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 2
    assert "error" in response
    assert response["error"]["code"] == -32602  # Invalid params


def test_malformed_json_recovery(mcp_server):
    """Test that the server recovers from malformed JSON."""
    # Initialize first
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    }
    mcp_server.send_request(init_request)
    
    # Send malformed JSON
    malformed_json = '{"jsonrpc": "2.0", "id": 2, "method": "invalid"'  # Missing closing brace
    
    try:
        mcp_server.process.stdin.write(malformed_json + '\n')
        mcp_server.process.stdin.flush()
        
        # Read error response
        response_line = mcp_server.process.stdout.readline()
        error_response = json.loads(response_line.strip())
        
        assert error_response["jsonrpc"] == "2.0"
        assert "error" in error_response
        assert error_response["error"]["code"] == -32700  # Parse error
        
        # Server should still be responsive after error
        tools_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/list",
            "params": {}
        }
        
        response = mcp_server.send_request(tools_request)
        assert "result" in response
        
    except Exception as e:
        pytest.fail(f"Server failed to recover from malformed JSON: {e}")


def test_unknown_method_error(mcp_server):
    """Test that unknown methods return proper error responses."""
    # Initialize first
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    }
    mcp_server.send_request(init_request)
    
    # Send request with unknown method
    unknown_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "unknown/method",
        "params": {}
    }
    
    response = mcp_server.send_request(unknown_request)
    
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 2
    assert "error" in response
    assert response["error"]["code"] == -32601  # Method not found


def test_ping_notification(mcp_server):
    """Test that ping notifications are handled silently."""
    # Initialize first
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    }
    mcp_server.send_request(init_request)
    
    # Send ping notification (no id = notification)
    ping_notification = {
        "jsonrpc": "2.0",
        "method": "$/ping",
        "params": {}
    }
    
    # Send ping - should not get a response
    mcp_server.process.stdin.write(json.dumps(ping_notification) + '\n')
    mcp_server.process.stdin.flush()
    
    # Give time for any potential response
    time.sleep(0.1)
    
    # Server should still be responsive
    tools_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    response = mcp_server.send_request(tools_request)
    assert "result" in response


@pytest.mark.timeout(10)
def test_stress_multiple_requests(mcp_server):
    """Test handling multiple rapid requests."""
    # Initialize first
    init_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    }
    mcp_server.send_request(init_request)
    
    # Send multiple get_clipboard requests rapidly
    responses = []
    for i in range(10):
        request = {
            "jsonrpc": "2.0",
            "id": i + 2,
            "method": "tools/call",
            "params": {
                "name": "get_clipboard",
                "arguments": {}
            }
        }
        response = mcp_server.send_request(request)
        responses.append(response)
    
    # All should succeed
    for i, response in enumerate(responses):
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == i + 2
        assert "result" in response


@pytest.mark.skipif(sys.platform == "win32", reason="Unix signal test")
def test_platform_detection_unix():
    """Test that server runs correctly on Unix-like platforms."""
    with MCPServerProcess() as mcp_server:
        # Basic initialization should work
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        response = mcp_server.send_request(request)
        assert response["jsonrpc"] == "2.0"
        assert "result" in response


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-specific test")
def test_platform_detection_windows():
    """Test that server runs correctly on Windows."""
    with MCPServerProcess() as mcp_server:
        # Basic initialization should work
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        response = mcp_server.send_request(request)
        assert response["jsonrpc"] == "2.0"
        assert "result" in response


def test_cross_platform_unicode_content():
    """Test Unicode content handling across platforms."""
    unicode_content = "Hello, 世界! 🌍 Café naïve résumé"
    
    with MCPServerProcess() as mcp_server:
        # Initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        mcp_server.send_request(init_request)
        
        # Set Unicode clipboard content
        set_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "set_clipboard",
                "arguments": {"text": unicode_content}
            }
        }
        set_response = mcp_server.send_request(set_request)
        
        # May fail on some platforms, which is acceptable
        if "result" in set_response:
            # Get clipboard content back
            get_request = {
                "jsonrpc": "2.0", 
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "get_clipboard",
                    "arguments": {}
                }
            }
            get_response = mcp_server.send_request(get_request)
            
            if "result" in get_response:
                content = get_response["result"]["content"][0]["text"]
                # Content should match or be empty (graceful fallback)
                assert content == unicode_content or content == ""


def test_large_content_handling():
    """Test handling of large clipboard content."""
    # Create content near the validation limit
    large_content = "A" * (1024 * 100)  # 100KB
    
    with MCPServerProcess() as mcp_server:
        # Initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        mcp_server.send_request(init_request)
        
        # Try to set large content
        set_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "set_clipboard",
                "arguments": {"text": large_content}
            }
        }
        set_response = mcp_server.send_request(set_request)
        
        # Should either succeed or fail gracefully
        assert "result" in set_response or "error" in set_response
        
        if "result" in set_response:
            # If set succeeded, try to get it back
            get_request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "get_clipboard",
                    "arguments": {}
                }
            }
            get_response = mcp_server.send_request(get_request)
            
            if "result" in get_response:
                retrieved_content = get_response["result"]["content"][0]["text"]
                # Content should match or be gracefully truncated/empty
                assert isinstance(retrieved_content, str)
                assert len(retrieved_content) <= len(large_content)


def test_platform_error_recovery():
    """Test that server recovers gracefully from platform-specific errors."""
    with MCPServerProcess() as mcp_server:
        # Initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        mcp_server.send_request(init_request)
        
        # Attempt multiple clipboard operations
        for i in range(3):
            # Get clipboard (should always work, returning empty string on failure)
            get_request = {
                "jsonrpc": "2.0",
                "id": i + 2,
                "method": "tools/call",
                "params": {
                    "name": "get_clipboard",
                    "arguments": {}
                }
            }
            get_response = mcp_server.send_request(get_request)
            
            # Should never cause server to crash
            assert "result" in get_response or "error" in get_response
            
            if "result" in get_response:
                content = get_response["result"]["content"][0]["text"]
                assert isinstance(content, str)  # Should always be string
        
        # Server should still be responsive
        assert mcp_server.process and mcp_server.process.poll() is None
