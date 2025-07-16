"""Integration tests for MCP clipboard server."""

import json
import subprocess
import sys
import time
from typing import Any, Dict, Optional

import pyperclip
import pytest


class MCPIntegrationTest:
    """Integration test helper for MCP server."""

    def __init__(self):
        """Initialize integration test."""
        self.process: Optional[subprocess.Popen] = None
        self.original_clipboard = None

    def start_server(self):
        """Start the MCP server as a subprocess."""
        self.process = subprocess.Popen(
            [sys.executable, "-m", "mcp_clipboard_server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=0,  # Unbuffered for real-time communication
        )

        # Give the server a moment to start
        time.sleep(0.1)

        if self.process.poll() is not None:
            stderr_output = self.process.stderr.read()
            raise RuntimeError(f"Server failed to start: {stderr_output}")

    def stop_server(self):
        """Stop the MCP server."""
        if self.process:
            self.process.stdin.close()
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()

    def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a JSON-RPC request and get the response.

        Args:
            request: JSON-RPC request dictionary.

        Returns:
            JSON-RPC response dictionary.
        """
        if not self.process:
            raise RuntimeError("Server not started")

        # Send request
        request_json = json.dumps(request) + "\n"
        self.process.stdin.write(request_json)
        self.process.stdin.flush()

        # Read response
        response_line = self.process.stdout.readline()
        if not response_line:
            raise RuntimeError("No response from server")

        return json.loads(response_line.strip())

    def setup_clipboard_backup(self):
        """Backup current clipboard content."""
        try:
            self.original_clipboard = pyperclip.paste()
        except Exception:
            self.original_clipboard = ""

    def restore_clipboard_backup(self):
        """Restore original clipboard content."""
        if self.original_clipboard is not None:
            try:
                pyperclip.copy(self.original_clipboard)
            except Exception:
                pass  # Best effort restore

    def __enter__(self):
        """Context manager entry."""
        self.setup_clipboard_backup()
        self.start_server()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_server()
        self.restore_clipboard_backup()


def test_mcp_handshake():
    """Test complete MCP handshake sequence."""
    with MCPIntegrationTest() as test:
        # 1. Initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "0.8.0",
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        }

        init_response = test.send_request(init_request)
        assert init_response["jsonrpc"] == "2.0"
        assert init_response["id"] == 1
        assert "result" in init_response
        assert "serverInfo" in init_response["result"]
        assert init_response["result"]["serverInfo"]["name"] == "mcp-clipboardify"
        assert "capabilities" in init_response["result"]

        # 2. List tools
        list_request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}

        list_response = test.send_request(list_request)
        assert list_response["jsonrpc"] == "2.0"
        assert list_response["id"] == 2
        assert "result" in list_response
        assert "tools" in list_response["result"]

        tools = list_response["result"]["tools"]
        assert len(tools) == 2
        tool_names = [tool["name"] for tool in tools]
        assert "get_clipboard" in tool_names
        assert "set_clipboard" in tool_names


@pytest.mark.serial
def test_clipboard_operations():
    """Test actual clipboard read/write operations."""
    test_text = "Integration test content 🚀"

    with MCPIntegrationTest() as test:
        # Initialize first
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "0.8.0"},
        }
        test.send_request(init_request)

        # Set clipboard content
        set_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "set_clipboard", "arguments": {"text": test_text}},
        }

        set_response = test.send_request(set_request)
        assert set_response["jsonrpc"] == "2.0"
        assert set_response["id"] == 2
        assert "result" in set_response
        assert "content" in set_response["result"]

        # Verify clipboard was actually set by reading it directly
        actual_clipboard = pyperclip.paste()
        assert actual_clipboard == test_text

        # Get clipboard content via MCP
        get_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "get_clipboard", "arguments": {}},
        }

        get_response = test.send_request(get_request)
        assert get_response["jsonrpc"] == "2.0"
        assert get_response["id"] == 3
        assert "result" in get_response
        assert "content" in get_response["result"]

        content = get_response["result"]["content"][0]
        assert content["type"] == "text"
        assert content["text"] == test_text


def test_error_handling():
    """Test error handling in integration scenario."""
    with MCPIntegrationTest() as test:
        # Try to call tool before initialization
        premature_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "get_clipboard", "arguments": {}},
        }

        response = test.send_request(premature_request)
        assert "error" in response
        assert response["error"]["code"] == -32000  # Server error

        # Initialize
        init_request = {"jsonrpc": "2.0", "id": 2, "method": "initialize", "params": {}}
        test.send_request(init_request)

        # Call unknown tool
        unknown_tool_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "unknown_tool", "arguments": {}},
        }

        response = test.send_request(unknown_tool_request)
        assert "error" in response
        assert response["error"]["code"] == -32602  # Invalid params

        # Invalid parameters for set_clipboard
        invalid_params_request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "set_clipboard", "arguments": {"wrong_param": "value"}},
        }

        response = test.send_request(invalid_params_request)
        assert "error" in response
        assert response["error"]["code"] == -32602  # Invalid params


def test_malformed_json():
    """Test handling of malformed JSON."""
    with MCPIntegrationTest() as test:
        # Send malformed JSON
        if test.process:
            test.process.stdin.write('{"malformed": json}\n')
            test.process.stdin.flush()

            response_line = test.process.stdout.readline()
            if response_line:
                response = json.loads(response_line.strip())
                assert "error" in response
                assert response["error"]["code"] == -32700  # Parse error


def test_unknown_method():
    """Test handling of unknown methods."""
    with MCPIntegrationTest() as test:
        # Initialize first
        init_request = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        test.send_request(init_request)

        # Call unknown method
        unknown_method_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "unknown/method",
            "params": {},
        }

        response = test.send_request(unknown_method_request)
        assert "error" in response
        assert response["error"]["code"] == -32601  # Method not found


def test_notification_handling():
    """Test handling of JSON-RPC notifications."""
    with MCPIntegrationTest() as test:
        # Initialize first
        init_request = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        test.send_request(init_request)

        # Send ping notification (no ID)
        ping_notification = {"jsonrpc": "2.0", "method": "$/ping"}

        if test.process:
            notification_json = json.dumps(ping_notification) + "\n"
            test.process.stdin.write(notification_json)
            test.process.stdin.flush()

            # Brief wait to ensure notification is processed
            time.sleep(0.1)

            # Send a regular request to verify server is still responsive
            status_request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}

            response = test.send_request(status_request)
            assert response["id"] == 2
            assert "result" in response


@pytest.mark.serial
def test_unicode_clipboard_content():
    """Test handling of Unicode content in clipboard."""
    unicode_text = "Hello 🌍 こんにちは 🚀 مرحبا"

    with MCPIntegrationTest() as test:
        # Initialize
        init_request = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        test.send_request(init_request)

        # Set Unicode content
        set_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "set_clipboard", "arguments": {"text": unicode_text}},
        }

        set_response = test.send_request(set_request)
        assert "result" in set_response

        # Get Unicode content back
        get_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "get_clipboard", "arguments": {}},
        }

        get_response = test.send_request(get_request)
        assert "result" in get_response

        content = get_response["result"]["content"][0]
        assert content["text"] == unicode_text


# Note: These tests require an actual environment with clipboard access
# They may need to be skipped in headless CI environments
def test_server_startup_and_shutdown():
    """Test that server starts and shuts down cleanly."""
    test = MCPIntegrationTest()

    # Test startup
    test.start_server()
    assert test.process is not None
    assert test.process.poll() is None  # Should be running

    # Test shutdown
    test.stop_server()
    assert test.process.poll() is not None  # Should have terminated


if __name__ == "__main__":
    # Run tests individually for debugging
    print("Running MCP integration tests...")

    try:
        test_server_startup_and_shutdown()
        print("✓ Server startup/shutdown test passed")

        test_mcp_handshake()
        print("✓ MCP handshake test passed")

        test_clipboard_operations()
        print("✓ Clipboard operations test passed")

        test_error_handling()
        print("✓ Error handling test passed")

        test_unicode_clipboard_content()
        print("✓ Unicode content test passed")

        print("\nAll integration tests passed! 🎉")

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
