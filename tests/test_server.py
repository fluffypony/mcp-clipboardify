"""Tests for MCP server implementation."""

import json
import pytest
from unittest.mock import patch, MagicMock

from mcp_clipboard_server.server import MCPServer
from mcp_clipboard_server.protocol import JsonRpcRequest, ErrorCodes


class TestMCPServer:
    """Test MCP server functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.server = MCPServer()

    def test_initialization(self):
        """Test server initialization state."""
        assert not self.server.initialized
        assert self.server.server_info["name"] == "mcp-clipboard-server"
        assert "tools" in self.server.capabilities

    def test_handle_initialize(self):
        """Test initialize request handling."""
        request = JsonRpcRequest(
            jsonrpc="2.0",
            method="initialize",
            id=1,
            params={"clientInfo": {"name": "test-client"}}
        )
        
        response_json = self.server.handle_initialize(request)
        response = json.loads(response_json)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        assert "serverInfo" in response["result"]
        assert "capabilities" in response["result"]
        assert self.server.initialized

    def test_handle_initialize_without_params(self):
        """Test initialize without client info."""
        request = JsonRpcRequest(
            jsonrpc="2.0",
            method="initialize",
            id=1
        )
        
        response_json = self.server.handle_initialize(request)
        response = json.loads(response_json)
        
        assert "error" not in response
        assert self.server.initialized

    def test_handle_tools_list_not_initialized(self):
        """Test tools/list before initialization."""
        request = JsonRpcRequest(
            jsonrpc="2.0",
            method="tools/list",
            id=2
        )
        
        response_json = self.server.handle_tools_list(request)
        response = json.loads(response_json)
        
        assert "error" in response
        assert response["error"]["code"] == ErrorCodes.SERVER_ERROR

    def test_handle_tools_list_initialized(self):
        """Test tools/list after initialization."""
        self.server.initialized = True
        
        request = JsonRpcRequest(
            jsonrpc="2.0",
            method="tools/list",
            id=2
        )
        
        response_json = self.server.handle_tools_list(request)
        response = json.loads(response_json)
        
        assert "error" not in response
        assert "result" in response
        assert "tools" in response["result"]
        assert len(response["result"]["tools"]) == 2

    def test_handle_tools_call_not_initialized(self):
        """Test tools/call before initialization."""
        request = JsonRpcRequest(
            jsonrpc="2.0",
            method="tools/call",
            id=3,
            params={"name": "get_clipboard", "arguments": {}}
        )
        
        response_json = self.server.handle_tools_call(request)
        response = json.loads(response_json)
        
        assert "error" in response
        assert response["error"]["code"] == ErrorCodes.SERVER_ERROR

    def test_handle_tools_call_missing_params(self):
        """Test tools/call without parameters."""
        self.server.initialized = True
        
        request = JsonRpcRequest(
            jsonrpc="2.0",
            method="tools/call",
            id=3
        )
        
        response_json = self.server.handle_tools_call(request)
        response = json.loads(response_json)
        
        assert "error" in response
        assert response["error"]["code"] == ErrorCodes.INVALID_PARAMS

    def test_handle_tools_call_missing_name(self):
        """Test tools/call without tool name."""
        self.server.initialized = True
        
        request = JsonRpcRequest(
            jsonrpc="2.0",
            method="tools/call",
            id=3,
            params={"arguments": {}}
        )
        
        response_json = self.server.handle_tools_call(request)
        response = json.loads(response_json)
        
        assert "error" in response
        assert response["error"]["code"] == ErrorCodes.INVALID_PARAMS

    @patch('mcp_clipboard_server._mcp_handler.get_clipboard')
    def test_handle_tools_call_success(self, mock_get_clipboard):
        """Test successful tools/call."""
        self.server.initialized = True
        mock_get_clipboard.return_value = "test content"
        
        request = JsonRpcRequest(
            jsonrpc="2.0",
            method="tools/call",
            id=3,
            params={"name": "get_clipboard", "arguments": {}}
        )
        
        response_json = self.server.handle_tools_call(request)
        response = json.loads(response_json)
        
        assert "error" not in response
        assert "result" in response
        mock_get_clipboard.assert_called_once()

    @patch('mcp_clipboard_server._mcp_handler.get_clipboard')
    def test_handle_tools_call_tool_error(self, mock_get_clipboard):
        """Test tools/call with tool execution error."""
        self.server.initialized = True
        from mcp_clipboard_server.clipboard import ClipboardError
        mock_get_clipboard.side_effect = ClipboardError("Clipboard error")
        
        request = JsonRpcRequest(
            jsonrpc="2.0",
            method="tools/call",
            id=3,
            params={"name": "get_clipboard", "arguments": {}}
        )
        
        response_json = self.server.handle_tools_call(request)
        response = json.loads(response_json)
        
        assert "error" in response
        assert response["error"]["code"] == -32001  # CLIPBOARD_ERROR

    def test_handle_ping(self):
        """Test ping notification handling."""
        request = JsonRpcRequest(
            jsonrpc="2.0",
            method="$/ping",
            id=None
        )
        
        response = self.server.handle_ping(request)
        assert response is None

    def test_handle_unknown_method_with_id(self):
        """Test unknown method with ID (should return error)."""
        request = JsonRpcRequest(
            jsonrpc="2.0",
            method="unknown/method",
            id=999
        )
        
        response_json = self.server.handle_request(request)
        response = json.loads(response_json)
        
        assert "error" in response
        assert response["error"]["code"] == ErrorCodes.METHOD_NOT_FOUND

    def test_handle_unknown_notification(self):
        """Test unknown notification (should be ignored)."""
        request = JsonRpcRequest(
            jsonrpc="2.0",
            method="unknown/notification",
            id=None
        )
        
        response = self.server.handle_request(request)
        assert response is None

    def test_full_mcp_handshake(self):
        """Test complete MCP handshake sequence."""
        # 1. Initialize
        init_request = JsonRpcRequest(
            jsonrpc="2.0",
            method="initialize",
            id=1,
            params={"protocolVersion": "0.8.0"}
        )
        
        init_response = self.server.handle_request(init_request)
        assert json.loads(init_response)["result"]["serverInfo"]["name"] == "mcp-clipboard-server"
        
        # 2. List tools
        list_request = JsonRpcRequest(
            jsonrpc="2.0",
            method="tools/list",
            id=2
        )
        
        list_response = self.server.handle_request(list_request)
        tools = json.loads(list_response)["result"]["tools"]
        assert len(tools) == 2
        
        # 3. Call tool (mocked)
        with patch('mcp_clipboard_server._mcp_handler.get_clipboard') as mock_get_clipboard:
            mock_get_clipboard.return_value = "clipboard content"
            
            call_request = JsonRpcRequest(
                jsonrpc="2.0",
                method="tools/call",
                id=3,
                params={"name": "get_clipboard", "arguments": {}}
            )
            
            call_response = self.server.handle_request(call_request)
            result = json.loads(call_response)["result"]
            assert result["content"][0]["text"] == "clipboard content"
