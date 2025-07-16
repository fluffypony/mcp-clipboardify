"""Tests for clipboard module."""

import pytest
from unittest.mock import patch
from mcp_clipboard_server.clipboard import get_clipboard, set_clipboard, ClipboardError


class TestClipboard:
    """Test cases for clipboard operations."""

    @patch("mcp_clipboard_server.clipboard.pyperclip.paste")
    def test_get_clipboard_success(self, mock_paste):
        """Test successful clipboard read."""
        mock_paste.return_value = "test content"
        result = get_clipboard()
        assert result == "test content"
        mock_paste.assert_called_once()

    @patch("mcp_clipboard_server.clipboard.pyperclip.paste")
    def test_get_clipboard_empty(self, mock_paste):
        """Test reading empty clipboard."""
        mock_paste.return_value = None
        result = get_clipboard()
        assert result == ""

    @patch("mcp_clipboard_server.clipboard.pyperclip.paste")
    def test_get_clipboard_failure(self, mock_paste):
        """Test clipboard read failure returns empty string gracefully."""
        mock_paste.side_effect = RuntimeError("Clipboard access denied")
        # Should return empty string instead of raising exception
        result = get_clipboard()
        assert result == ""

    @patch("mcp_clipboard_server.clipboard.pyperclip.copy")
    def test_set_clipboard_success(self, mock_copy):
        """Test successful clipboard write."""
        set_clipboard("test content")
        mock_copy.assert_called_once_with("test content")

    @patch("mcp_clipboard_server.clipboard.pyperclip.copy")
    def test_set_clipboard_failure(self, mock_copy):
        """Test clipboard write failure."""
        mock_copy.side_effect = RuntimeError("Clipboard access denied")
        with pytest.raises(ClipboardError, match="Failed to write to clipboard"):
            set_clipboard("test content")

    def test_set_clipboard_invalid_type(self):
        """Test setting clipboard with non-string type."""
        with pytest.raises(ValueError, match="Text must be a string"):
            set_clipboard(123)

    def test_set_clipboard_size_limit(self):
        """Test clipboard size limit enforcement."""
        # Create text larger than 1MB
        large_text = "a" * (1024 * 1024 + 1)
        with pytest.raises(ValueError, match="Text exceeds 1MB limit"):
            set_clipboard(large_text)

    @patch("mcp_clipboard_server.clipboard.pyperclip.copy")
    def test_set_clipboard_unicode(self, mock_copy):
        """Test setting clipboard with Unicode content."""
        unicode_text = "Hello 🌍 こんにちは"
        set_clipboard(unicode_text)
        mock_copy.assert_called_once_with(unicode_text)
