"""Tests for JSON-RPC protocol handling."""

import json
import pytest
from mcp_clipboard_server.protocol import (
    JsonRpcRequest, JsonRpcError, JsonRpcResponse, ErrorCodes,
    parse_json_rpc_message, create_success_response, create_error_response
)


class TestJsonRpcRequest:
    """Test JsonRpcRequest class."""

    def test_from_dict_minimal(self):
        """Test creating request from minimal dict."""
        data = {"jsonrpc": "2.0", "method": "test", "id": 1}
        request = JsonRpcRequest.from_dict(data)
        assert request.jsonrpc == "2.0"
        assert request.method == "test"
        assert request.id == 1
        assert request.params is None

    def test_from_dict_with_params(self):
        """Test creating request with parameters."""
        data = {
            "jsonrpc": "2.0",
            "method": "test",
            "id": "test-id",
            "params": {"arg1": "value1"}
        }
        request = JsonRpcRequest.from_dict(data)
        assert request.params == {"arg1": "value1"}


class TestJsonRpcError:
    """Test JsonRpcError class."""

    def test_to_dict_minimal(self):
        """Test converting error to dict without data."""
        error = JsonRpcError(code=-32600, message="Invalid Request")
        result = error.to_dict()
        assert result == {"code": -32600, "message": "Invalid Request"}

    def test_to_dict_with_data(self):
        """Test converting error to dict with data."""
        error = JsonRpcError(code=-32600, message="Invalid Request", data={"detail": "missing field"})
        result = error.to_dict()
        expected = {
            "code": -32600,
            "message": "Invalid Request",
            "data": {"detail": "missing field"}
        }
        assert result == expected


class TestJsonRpcResponse:
    """Test JsonRpcResponse class."""

    def test_to_dict_success(self):
        """Test converting success response to dict."""
        response = JsonRpcResponse(jsonrpc="2.0", id=1, result="success")
        result = response.to_dict()
        expected = {"jsonrpc": "2.0", "id": 1, "result": "success"}
        assert result == expected

    def test_to_dict_error(self):
        """Test converting error response to dict."""
        error = JsonRpcError(code=-32600, message="Invalid Request")
        response = JsonRpcResponse(jsonrpc="2.0", id=1, error=error)
        result = response.to_dict()
        expected = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -32600, "message": "Invalid Request"}
        }
        assert result == expected


class TestParseJsonRpcMessage:
    """Test JSON-RPC message parsing."""

    def test_parse_valid_message(self):
        """Test parsing valid JSON-RPC message."""
        data = '{"jsonrpc": "2.0", "method": "test", "id": 1}'
        request = parse_json_rpc_message(data)
        assert request.jsonrpc == "2.0"
        assert request.method == "test"
        assert request.id == 1

    def test_parse_invalid_json(self):
        """Test parsing malformed JSON."""
        data = '{"jsonrpc": "2.0", "method":'
        with pytest.raises(ValueError, match="Parse error"):
            parse_json_rpc_message(data)

    def test_parse_non_object(self):
        """Test parsing JSON array instead of object."""
        data = '["not", "an", "object"]'
        with pytest.raises(ValueError, match="Invalid request: must be JSON object"):
            parse_json_rpc_message(data)

    def test_parse_missing_jsonrpc(self):
        """Test parsing message without jsonrpc field."""
        data = '{"method": "test", "id": 1}'
        with pytest.raises(ValueError, match="Invalid request: jsonrpc must be '2.0'"):
            parse_json_rpc_message(data)

    def test_parse_wrong_jsonrpc_version(self):
        """Test parsing message with wrong jsonrpc version."""
        data = '{"jsonrpc": "1.0", "method": "test", "id": 1}'
        with pytest.raises(ValueError, match="Invalid request: jsonrpc must be '2.0'"):
            parse_json_rpc_message(data)

    def test_parse_missing_method(self):
        """Test parsing message without method field."""
        data = '{"jsonrpc": "2.0", "id": 1}'
        with pytest.raises(ValueError, match="Invalid request: missing method"):
            parse_json_rpc_message(data)

    def test_parse_notification(self):
        """Test parsing notification (no id field)."""
        data = '{"jsonrpc": "2.0", "method": "test"}'
        request = parse_json_rpc_message(data)
        assert request.id is None


class TestResponseCreation:
    """Test response creation functions."""

    def test_create_success_response(self):
        """Test creating success response."""
        response_json = create_success_response(1, {"data": "test"})
        response = json.loads(response_json)
        expected = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"data": "test"}
        }
        assert response == expected

    def test_create_error_response_minimal(self):
        """Test creating error response without data."""
        response_json = create_error_response(1, -32600, "Invalid Request")
        response = json.loads(response_json)
        expected = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": -32600,
                "message": "Invalid Request"
            }
        }
        assert response == expected

    def test_create_error_response_with_data(self):
        """Test creating error response with additional data."""
        response_json = create_error_response(
            1, -32602, "Invalid params", {"field": "missing"}
        )
        response = json.loads(response_json)
        expected = {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": -32602,
                "message": "Invalid params",
                "data": {"field": "missing"}
            }
        }
        assert response == expected

    def test_response_with_string_id(self):
        """Test responses with string IDs."""
        response_json = create_success_response("test-id", "result")
        response = json.loads(response_json)
        assert response["id"] == "test-id"

    def test_response_with_null_id(self):
        """Test responses with null ID."""
        response_json = create_error_response(None, -32700, "Parse error")
        response = json.loads(response_json)
        assert response["id"] is None


class TestErrorCodes:
    """Test error code constants."""

    def test_error_codes_defined(self):
        """Test that all required error codes are defined."""
        assert ErrorCodes.PARSE_ERROR == -32700
        assert ErrorCodes.INVALID_REQUEST == -32600
        assert ErrorCodes.METHOD_NOT_FOUND == -32601
        assert ErrorCodes.INVALID_PARAMS == -32602
        assert ErrorCodes.INTERNAL_ERROR == -32603
        assert ErrorCodes.SERVER_ERROR == -32000
