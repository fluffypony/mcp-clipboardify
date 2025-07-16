"""Integration tests for MCP clipboard server."""

import asyncio
import json
import os
import sys
import unittest
from typing import Any, Dict
import uuid


class MCPIntegrationTest(unittest.TestCase):
    """Integration tests that launch the server as a subprocess."""

    def setUp(self):
        """Set up test environment."""
        self.server_process = None
        self.test_data = {
            "short_text": "Hello, World!",
            "unicode_text": "Hello 世界 🌍 emoji test ñ",
            "long_text": "A" * 1000,  # 1KB text
            "empty_text": "",
        }

    def tearDown(self):
        """Clean up after each test."""
        if self.server_process:
            self.server_process.terminate()
            try:
                self.server_process.wait()  # asyncio subprocess doesn't have timeout parameter
            except Exception:
                self.server_process.kill()
                self.server_process.wait()

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

    async def send_request(
        self,
        writer: asyncio.StreamWriter,
        method: str,
        params: Dict[str, Any] = None,
        request_id: str = None,
    ) -> None:
        """
        Send a JSON-RPC request to the server.

        Args:
            writer: Stream writer to server.
            method: Request method.
            params: Request parameters.
            request_id: Request ID (generated if None).
        """
        if request_id is None:
            request_id = str(uuid.uuid4())

        request = {"jsonrpc": "2.0", "method": method, "id": request_id}

        if params is not None:
            request["params"] = params

        request_line = json.dumps(request) + "\n"
        writer.write(request_line.encode())
        await writer.drain()

    async def send_notification(
        self, writer: asyncio.StreamWriter, method: str, params: Dict[str, Any] = None
    ) -> None:
        """
        Send a JSON-RPC notification to the server.

        Args:
            writer: Stream writer to server.
            method: Notification method.
            params: Notification parameters.
        """
        notification = {"jsonrpc": "2.0", "method": method}

        if params is not None:
            notification["params"] = params

        notification_line = json.dumps(notification) + "\n"
        writer.write(notification_line.encode())
        await writer.drain()

    async def read_response(
        self, reader: asyncio.StreamReader, timeout: float = 5.0
    ) -> Dict[str, Any]:
        """
        Read a JSON-RPC response from the server.

        Args:
            reader: Stream reader from server.
            timeout: Timeout in seconds.

        Returns:
            Parsed JSON response.
        """
        try:
            response_line = await asyncio.wait_for(reader.readline(), timeout=timeout)
            if not response_line:
                raise RuntimeError("Server closed connection")

            return json.loads(response_line.decode().strip())
        except asyncio.TimeoutError:
            raise RuntimeError(f"No response received within {timeout}s")

    async def test_full_handshake(self):
        """Test complete MCP handshake sequence."""
        reader, writer = await self.start_server()

        # Send initialize request
        await self.send_request(
            writer,
            "initialize",
            {
                "protocolVersion": "1.0",
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
            "init-1",
        )

        # Read initialize response
        response = await self.read_response(reader)
        self.assertEqual(response["jsonrpc"], "2.0")
        self.assertEqual(response["id"], "init-1")
        self.assertIn("result", response)

        result = response["result"]
        self.assertIn("serverInfo", result)
        self.assertIn("capabilities", result)

        server_info = result["serverInfo"]
        self.assertEqual(server_info["name"], "mcp-clipboard-server")
        self.assertIn("version", server_info)

        # Test tools/list
        await self.send_request(writer, "tools/list", {}, "tools-1")
        response = await self.read_response(reader)

        self.assertEqual(response["id"], "tools-1")
        self.assertIn("result", response)
        tools = response["result"]["tools"]
        self.assertEqual(len(tools), 2)

        tool_names = [tool["name"] for tool in tools]
        self.assertIn("get_clipboard", tool_names)
        self.assertIn("set_clipboard", tool_names)

    async def test_clipboard_operations(self):
        """Test clipboard get and set operations."""
        reader, writer = await self.start_server()

        # Initialize
        await self.send_request(writer, "initialize", {}, "init-1")
        await self.read_response(reader)

        # Test set_clipboard
        await self.send_request(
            writer,
            "tools/call",
            {
                "name": "set_clipboard",
                "arguments": {"text": self.test_data["short_text"]},
            },
            "set-1",
        )

        response = await self.read_response(reader)
        self.assertEqual(response["id"], "set-1")
        self.assertIn("result", response)

        content = response["result"]["content"]
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]["type"], "text")
        self.assertIn("Successfully copied", content[0]["text"])

        # Test get_clipboard
        await self.send_request(
            writer, "tools/call", {"name": "get_clipboard", "arguments": {}}, "get-1"
        )

        response = await self.read_response(reader)
        self.assertEqual(response["id"], "get-1")
        self.assertIn("result", response)

        content = response["result"]["content"]
        self.assertEqual(len(content), 1)
        self.assertEqual(content[0]["type"], "text")
        self.assertEqual(content[0]["text"], self.test_data["short_text"])

    async def test_unicode_content(self):
        """Test clipboard operations with Unicode content."""
        reader, writer = await self.start_server()

        # Initialize
        await self.send_request(writer, "initialize", {}, "init-1")
        await self.read_response(reader)

        # Set Unicode text
        await self.send_request(
            writer,
            "tools/call",
            {
                "name": "set_clipboard",
                "arguments": {"text": self.test_data["unicode_text"]},
            },
            "set-unicode",
        )

        await self.read_response(reader)

        # Get Unicode text
        await self.send_request(
            writer,
            "tools/call",
            {"name": "get_clipboard", "arguments": {}},
            "get-unicode",
        )

        response = await self.read_response(reader)
        content = response["result"]["content"][0]["text"]
        self.assertEqual(content, self.test_data["unicode_text"])

    async def test_error_scenarios(self):
        """Test various error scenarios."""
        reader, writer = await self.start_server()

        # Test calling tools before initialization
        await self.send_request(writer, "tools/list", {}, "error-1")
        response = await self.read_response(reader)
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], -32000)  # Server error

        # Initialize first
        await self.send_request(writer, "initialize", {}, "init-1")
        await self.read_response(reader)

        # Test unknown method
        await self.send_request(writer, "unknown/method", {}, "error-2")
        response = await self.read_response(reader)
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], -32601)  # Method not found

        # Test invalid parameters for set_clipboard
        await self.send_request(
            writer,
            "tools/call",
            {
                "name": "set_clipboard",
                "arguments": {},  # Missing text parameter
            },
            "error-3",
        )

        response = await self.read_response(reader)
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], -32602)  # Invalid params

        # Test unknown tool
        await self.send_request(
            writer, "tools/call", {"name": "unknown_tool", "arguments": {}}, "error-4"
        )

        response = await self.read_response(reader)
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], -32602)  # Invalid params

    async def test_malformed_json(self):
        """Test server response to malformed JSON."""
        reader, writer = await self.start_server()

        # Send malformed JSON
        writer.write(b"{ invalid json }\n")
        await writer.drain()

        response = await self.read_response(reader)
        self.assertIn("error", response)
        self.assertEqual(response["error"]["code"], -32700)  # Parse error

    async def test_ping_notification(self):
        """Test ping notification handling."""
        reader, writer = await self.start_server()

        # Initialize
        await self.send_request(writer, "initialize", {}, "init-1")
        await self.read_response(reader)

        # Send ping notification
        await self.send_notification(writer, "$/ping", {})

        # Ping notifications should not generate responses
        # Send a regular request to ensure server is still responsive
        await self.send_request(writer, "tools/list", {}, "after-ping")
        response = await self.read_response(reader)
        self.assertEqual(response["id"], "after-ping")
        self.assertIn("result", response)

    async def test_large_content(self):
        """Test handling of large clipboard content."""
        reader, writer = await self.start_server()

        # Initialize
        await self.send_request(writer, "initialize", {}, "init-1")
        await self.read_response(reader)

        # Test with large content (but under 1MB limit and stream limit)
        large_text = "A" * 10000  # 10KB
        await self.send_request(
            writer,
            "tools/call",
            {"name": "set_clipboard", "arguments": {"text": large_text}},
            "large-set",
        )

        response = await self.read_response(reader)
        self.assertIn("result", response)

        # Verify we can get it back
        await self.send_request(
            writer,
            "tools/call",
            {"name": "get_clipboard", "arguments": {}},
            "large-get",
        )

        response = await self.read_response(reader)
        content = response["result"]["content"][0]["text"]
        self.assertEqual(len(content), 10000)
        self.assertEqual(content, large_text)

    async def test_rapid_requests(self):
        """Test server handling of rapid sequential requests."""
        reader, writer = await self.start_server()

        # Initialize
        await self.send_request(writer, "initialize", {}, "init-1")
        await self.read_response(reader)

        # Send multiple requests rapidly
        request_ids = []
        for i in range(10):
            request_id = f"rapid-{i}"
            request_ids.append(request_id)
            await self.send_request(
                writer,
                "tools/call",
                {"name": "set_clipboard", "arguments": {"text": f"test-{i}"}},
                request_id,
            )

        # Read all responses
        responses = {}
        for _ in range(10):
            response = await self.read_response(reader)
            responses[response["id"]] = response

        # Verify all requests were processed
        for request_id in request_ids:
            self.assertIn(request_id, responses)
            self.assertIn("result", responses[request_id])


def run_async_test(test_method):
    """Helper to run async test methods."""

    def wrapper(self):
        asyncio.run(test_method(self))

    return wrapper


# Convert async test methods to regular test methods
MCPIntegrationTest.test_full_handshake = run_async_test(
    MCPIntegrationTest.test_full_handshake
)
MCPIntegrationTest.test_clipboard_operations = run_async_test(
    MCPIntegrationTest.test_clipboard_operations
)
MCPIntegrationTest.test_unicode_content = run_async_test(
    MCPIntegrationTest.test_unicode_content
)
MCPIntegrationTest.test_error_scenarios = run_async_test(
    MCPIntegrationTest.test_error_scenarios
)
MCPIntegrationTest.test_malformed_json = run_async_test(
    MCPIntegrationTest.test_malformed_json
)
MCPIntegrationTest.test_ping_notification = run_async_test(
    MCPIntegrationTest.test_ping_notification
)
MCPIntegrationTest.test_large_content = run_async_test(
    MCPIntegrationTest.test_large_content
)
MCPIntegrationTest.test_rapid_requests = run_async_test(
    MCPIntegrationTest.test_rapid_requests
)


if __name__ == "__main__":
    unittest.main()
