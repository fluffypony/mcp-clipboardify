"""Tests for MCP tool implementations."""

import pytest
from unittest.mock import patch

from mcp_clipboard_server.tools import (
    list_tools,
    validate_tool_params,
    execute_tool,
    get_tool_error_code,
)
from mcp_clipboard_server._tool_schemas import get_all_tool_definitions
from mcp_clipboard_server.clipboard import ClipboardError
from mcp_clipboard_server.protocol import ErrorCodes


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

    def test_set_clipboard_schema(self):
        """Test set_clipboard tool schema."""
        tool_definitions = get_all_tool_definitions()
        tool = tool_definitions["set_clipboard"]
        assert tool["name"] == "set_clipboard"
        assert "description" in tool
        assert "text" in tool["inputSchema"]["properties"]
        assert tool["inputSchema"]["required"] == ["text"]


class TestListTools:
    """Test tools listing functionality."""

    def test_list_tools_format(self):
        """Test that list_tools returns correct format."""
        result = list_tools()
        assert "tools" in result
        assert isinstance(result["tools"], list)
        assert len(result["tools"]) == 2

    def test_list_tools_contains_all(self):
        """Test that all tools are included in the list."""
        result = list_tools()
        tool_names = [tool["name"] for tool in result["tools"]]
        assert "get_clipboard" in tool_names
        assert "set_clipboard" in tool_names


class TestValidateToolParams:
    """Test parameter validation."""

    def test_validate_unknown_tool(self):
        """Test validation with unknown tool name."""
        with pytest.raises(ValueError, match="Unknown tool"):
            validate_tool_params("unknown_tool", {})

    def test_validate_get_clipboard_no_params(self):
        """Test get_clipboard with no parameters (valid)."""
        validate_tool_params("get_clipboard", {})
        validate_tool_params("get_clipboard", None)

    def test_validate_get_clipboard_with_params(self):
        """Test get_clipboard with parameters (invalid)."""
        with pytest.raises(ValueError, match="does not accept parameters"):
            validate_tool_params("get_clipboard", {"extra": "param"})

    def test_validate_set_clipboard_valid(self):
        """Test set_clipboard with valid parameters."""
        validate_tool_params("set_clipboard", {"text": "hello"})

    def test_validate_set_clipboard_missing_text(self):
        """Test set_clipboard without text parameter."""
        with pytest.raises(ValueError, match="requires 'text' parameter"):
            validate_tool_params("set_clipboard", {})

        with pytest.raises(ValueError, match="requires 'text' parameter"):
            validate_tool_params("set_clipboard", {"other": "param"})

    def test_validate_set_clipboard_wrong_type(self):
        """Test set_clipboard with non-string text."""
        with pytest.raises(ValueError, match="must be a string"):
            validate_tool_params("set_clipboard", {"text": 123})

    def test_validate_set_clipboard_extra_params(self):
        """Test set_clipboard with extra parameters."""
        with pytest.raises(ValueError, match="Unexpected parameters"):
            validate_tool_params("set_clipboard", {"text": "hello", "extra": "param"})


class TestExecuteTool:
    """Test tool execution."""

    @patch("mcp_clipboard_server.tools.get_clipboard")
    def test_execute_get_clipboard_success(self, mock_get):
        """Test successful get_clipboard execution."""
        mock_get.return_value = "test content"

        result = execute_tool("get_clipboard", {})

        assert result["content"][0]["type"] == "text"
        assert result["content"][0]["text"] == "test content"
        mock_get.assert_called_once()

    @patch("mcp_clipboard_server.tools.get_clipboard")
    def test_execute_get_clipboard_failure(self, mock_get):
        """Test get_clipboard with clipboard error."""
        mock_get.side_effect = ClipboardError("Access denied")

        with pytest.raises(RuntimeError, match="Clipboard operation failed"):
            execute_tool("get_clipboard", {})

    @patch("mcp_clipboard_server.tools.set_clipboard")
    def test_execute_set_clipboard_success(self, mock_set):
        """Test successful set_clipboard execution."""
        result = execute_tool("set_clipboard", {"text": "hello world"})

        assert result["content"][0]["type"] == "text"
        assert "Successfully copied 11 characters" in result["content"][0]["text"]
        mock_set.assert_called_once_with("hello world")

    @patch("mcp_clipboard_server.tools.set_clipboard")
    def test_execute_set_clipboard_failure(self, mock_set):
        """Test set_clipboard with clipboard error."""
        mock_set.side_effect = ClipboardError("Access denied")

        with pytest.raises(RuntimeError, match="Clipboard operation failed"):
            execute_tool("set_clipboard", {"text": "hello"})

    def test_execute_invalid_tool(self):
        """Test execution with invalid tool name."""
        with pytest.raises(ValueError, match="Unknown tool"):
            execute_tool("invalid_tool", {})

    def test_execute_invalid_params(self):
        """Test execution with invalid parameters."""
        with pytest.raises(ValueError, match="does not accept parameters"):
            execute_tool("get_clipboard", {"extra": "param"})

    @patch("mcp_clipboard_server.tools.get_clipboard")
    def test_execute_unexpected_error(self, mock_get):
        """Test handling of unexpected errors."""
        mock_get.side_effect = Exception("Unexpected error")

        with pytest.raises(RuntimeError, match="Tool execution failed"):
            execute_tool("get_clipboard", {})


class TestGetToolErrorCode:
    """Test error code mapping."""

    def test_value_error_mapping(self):
        """Test that ValueError maps to INVALID_PARAMS."""
        error = ValueError("Invalid parameter")
        code = get_tool_error_code(error)
        assert code == ErrorCodes.INVALID_PARAMS

    def test_runtime_error_mapping(self):
        """Test that RuntimeError maps to SERVER_ERROR."""
        error = RuntimeError("Server error")
        code = get_tool_error_code(error)
        assert code == ErrorCodes.SERVER_ERROR

    def test_generic_error_mapping(self):
        """Test that generic exceptions map to SERVER_ERROR."""
        error = Exception("Generic error")
        code = get_tool_error_code(error)
        assert code == ErrorCodes.SERVER_ERROR


class TestPlatformSpecificIntegration:
    """Test platform-specific integration with tools."""

    @patch("mcp_clipboard_server.tools.get_clipboard")
    def test_execute_get_clipboard_platform_failure(self, mock_get):
        """Test get_clipboard execution with platform-specific failure."""
        # Simulate platform failure that returns empty string
        mock_get.return_value = ""

        result = execute_tool("get_clipboard", {})

        assert result["content"][0]["type"] == "text"
        assert result["content"][0]["text"] == ""
        mock_get.assert_called_once()

    @patch("mcp_clipboard_server.tools.set_clipboard")
    def test_execute_set_clipboard_platform_error(self, mock_set):
        """Test set_clipboard with enhanced platform error message."""
        enhanced_error = ClipboardError(
            "Failed to write to clipboard on Linux: xclip not found. "
            "Solution: Missing clipboard utilities. Install with: sudo apt-get install xclip xsel"
        )
        mock_set.side_effect = enhanced_error

        with pytest.raises(RuntimeError) as exc_info:
            execute_tool("set_clipboard", {"text": "hello"})

        error_msg = str(exc_info.value)
        assert "Clipboard operation failed" in error_msg
        assert "Linux" in error_msg
        assert "Solution:" in error_msg

    @patch("mcp_clipboard_server.clipboard._get_platform_info")
    @patch("mcp_clipboard_server.tools.set_clipboard")
    def test_execute_with_wsl_error(self, mock_set, mock_platform):
        """Test tool execution with WSL-specific error."""
        mock_platform.return_value = "WSL (Windows Subsystem for Linux)"
        mock_set.side_effect = ClipboardError("WSL clipboard access limited")

        with pytest.raises(RuntimeError) as exc_info:
            execute_tool("set_clipboard", {"text": "test"})

        error_msg = str(exc_info.value)
        assert "WSL" in error_msg or "clipboard" in error_msg

    def test_unicode_content_handling(self):
        """Test handling of Unicode content through tools."""
        unicode_text = "Hello, 世界! 🌍 Café naïve résumé"

        with patch("mcp_clipboard_server.tools.set_clipboard") as mock_set:
            with patch(
                "mcp_clipboard_server.tools.get_clipboard", return_value=unicode_text
            ) as mock_get:
                # Test setting Unicode content
                result = execute_tool("set_clipboard", {"text": unicode_text})
                mock_set.assert_called_once_with(unicode_text)

                # Test getting Unicode content
                result = execute_tool("get_clipboard", {})
                assert result["content"][0]["text"] == unicode_text
