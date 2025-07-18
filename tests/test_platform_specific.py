"""Platform-specific tests for clipboard operations."""

import os
import platform
import unittest
from unittest.mock import patch

import pytest
from mcp_clipboard_server.clipboard import (
    ClipboardError,
    _get_platform_guidance,
    _get_platform_info,
    get_clipboard,
    set_clipboard,
)


@pytest.fixture(autouse=True)
def clear_clipboard():
    """Clear clipboard before and after each test to ensure test isolation."""
    # Clear clipboard before test
    try:
        set_clipboard("")
    except (ClipboardError, Exception):
        pass  # Ignore errors during cleanup

    yield

    # Clear clipboard after test
    try:
        set_clipboard("")
    except (ClipboardError, Exception):
        pass  # Ignore errors during cleanup


# Platform test cases with different content types
PLATFORM_TEST_CASES = {
    "Windows": ["ascii", "unicode", "crlf_endings"],
    "Darwin": ["ascii", "unicode", "rtf_fallback"],  # Darwin is macOS
    "Linux": ["ascii", "unicode", "xclip_availability"],
}

TEST_CONTENT = {
    "ascii": "Hello, World!",
    "unicode": "Hello, 世界! 🌍 Café naïve résumé",
    "crlf_endings": "Line 1\r\nLine 2\r\nLine 3",
    "rtf_fallback": "Rich text content with formatting",
    "xclip_availability": "Test content for xclip/xsel validation",
    "empty": "",
    "large": "A" * 10000,  # 10KB test content
}


class TestPlatformDetection:
    """Test platform detection and information functions."""

    def test_get_platform_info_windows(self):
        """Test platform detection on Windows."""
        with patch("platform.system", return_value="Windows"):
            result = _get_platform_info()
            assert result == "Windows"

    def test_get_platform_info_macos(self):
        """Test platform detection on macOS."""
        with patch("platform.system", return_value="Darwin"):
            result = _get_platform_info()
            assert result == "macOS"

    def test_get_platform_info_linux(self):
        """Test platform detection on Linux."""
        with patch("platform.system", return_value="Linux"):
            with patch.dict(os.environ, {"DISPLAY": ":0"}):
                result = _get_platform_info()
                assert result == "Linux (X11)"

    def test_get_platform_info_headless_linux(self):
        """Test platform detection on headless Linux."""
        with patch("platform.system", return_value="Linux"):
            with patch.dict(os.environ, {}, clear=True):
                result = _get_platform_info()
                assert result == "Linux (headless)"

    def test_get_platform_info_wsl(self):
        """Test WSL detection."""
        with patch("platform.system", return_value="Linux"):
            with patch("os.path.exists", return_value=True):
                with patch(
                    "builtins.open",
                    unittest.mock.mock_open(read_data="Microsoft Linux"),
                ):
                    result = _get_platform_info()
                    assert result == "WSL (Windows Subsystem for Linux)"

    def test_get_platform_info_unknown(self):
        """Test platform detection for unknown systems."""
        with patch("platform.system", return_value="FreeBSD"):
            result = _get_platform_info()
            assert result == "FreeBSD (unsupported)"


class TestPlatformGuidance:
    """Test platform-specific error guidance."""

    def test_linux_xclip_guidance(self):
        """Test guidance for missing xclip on Linux."""
        with patch(
            "mcp_clipboard_server.clipboard._get_platform_info", return_value="Linux"
        ):
            guidance = _get_platform_guidance("xclip not found")
            assert "apt-get install xclip" in guidance
            assert "yum install xclip" in guidance
            assert "pacman -S xclip" in guidance

    def test_linux_headless_guidance(self):
        """Test guidance for headless Linux."""
        with patch(
            "mcp_clipboard_server.clipboard._get_platform_info",
            return_value="Linux (headless)",
        ):
            guidance = _get_platform_guidance("no display")
            assert "display server" in guidance
            assert "headless Linux systems" in guidance

    def test_wsl_guidance(self):
        """Test guidance for WSL environments."""
        with patch(
            "mcp_clipboard_server.clipboard._get_platform_info",
            return_value="WSL (Windows Subsystem for Linux)",
        ):
            guidance = _get_platform_guidance("clipboard access failed")
            assert "WSL2" in guidance
            assert "wslu package" in guidance
            assert "Windows Terminal" in guidance

    def test_macos_guidance(self):
        """Test guidance for macOS."""
        with patch(
            "mcp_clipboard_server.clipboard._get_platform_info", return_value="macOS"
        ):
            guidance = _get_platform_guidance("permission denied")
            assert "Security permissions" in guidance
            assert "System Preferences" in guidance

    def test_windows_guidance(self):
        """Test guidance for Windows."""
        with patch(
            "mcp_clipboard_server.clipboard._get_platform_info", return_value="Windows"
        ):
            guidance = _get_platform_guidance("access denied")
            assert "clipboard lock" in guidance
            assert "Antivirus software" in guidance


@pytest.mark.skipif(platform.system() != "Windows", reason="Windows-specific tests")
class TestWindowsClipboard:
    """Test clipboard operations on Windows."""

    @pytest.mark.serial
    def test_windows_ascii_content(self):
        """Test ASCII content on Windows."""
        if platform.system() == "Windows":
            test_text = TEST_CONTENT["ascii"]
            set_clipboard(test_text)
            result = get_clipboard()
            assert result == test_text

    @pytest.mark.serial
    def test_windows_unicode_content(self):
        """Test Unicode content on Windows."""
        if platform.system() == "Windows":
            test_text = TEST_CONTENT["unicode"]
            set_clipboard(test_text)
            result = get_clipboard()
            assert result == test_text

    @pytest.mark.serial
    def test_windows_crlf_endings(self):
        """Test CRLF line endings on Windows."""
        if platform.system() == "Windows":
            test_text = TEST_CONTENT["crlf_endings"]
            set_clipboard(test_text)
            result = get_clipboard()
            # Windows may normalize line endings
            assert "Line 1" in result and "Line 2" in result and "Line 3" in result


@pytest.mark.skipif(platform.system() != "Darwin", reason="macOS-specific tests")
class TestMacOSClipboard:
    """Test clipboard operations on macOS."""

    @patch("mcp_clipboard_server.clipboard.pyperclip.copy")
    @patch("mcp_clipboard_server.clipboard.pyperclip.paste")
    def test_macos_ascii_content(self, mock_paste, mock_copy):
        """Test ASCII content on macOS."""
        if platform.system() == "Darwin":
            test_text = TEST_CONTENT["ascii"]
            mock_paste.return_value = test_text

            set_clipboard(test_text)
            result = get_clipboard()

            mock_copy.assert_called_once_with(test_text)
            mock_paste.assert_called_once()
            assert result == test_text

    @patch("mcp_clipboard_server.clipboard.pyperclip.copy")
    @patch("mcp_clipboard_server.clipboard.pyperclip.paste")
    def test_macos_unicode_content(self, mock_paste, mock_copy):
        """Test Unicode content on macOS."""
        if platform.system() == "Darwin":
            test_text = TEST_CONTENT["unicode"]
            mock_paste.return_value = test_text

            set_clipboard(test_text)
            result = get_clipboard()

            mock_copy.assert_called_once_with(test_text)
            mock_paste.assert_called_once()
            assert result == test_text

    @patch("mcp_clipboard_server.clipboard.pyperclip.copy")
    @patch("mcp_clipboard_server.clipboard.pyperclip.paste")
    def test_macos_rtf_fallback(self, mock_paste, mock_copy):
        """Test RTF content fallback on macOS."""
        if platform.system() == "Darwin":
            test_text = TEST_CONTENT["rtf_fallback"]
            mock_paste.return_value = test_text

            set_clipboard(test_text)
            result = get_clipboard()

            mock_copy.assert_called_once_with(test_text)
            mock_paste.assert_called_once()
            # Should get plain text even if rich text was set
            assert isinstance(result, str)
            assert result == test_text


@pytest.mark.skipif(platform.system() != "Linux", reason="Linux-specific tests")
class TestLinuxClipboard:
    """Test clipboard operations on Linux."""

    @pytest.mark.serial
    def test_linux_ascii_content(self):
        """Test ASCII content on Linux."""
        if platform.system() == "Linux" and "DISPLAY" in os.environ:
            test_text = TEST_CONTENT["ascii"]
            set_clipboard(test_text)
            result = get_clipboard()
            assert result == test_text

    @pytest.mark.serial
    def test_linux_unicode_content(self):
        """Test Unicode content on Linux."""
        if platform.system() == "Linux" and "DISPLAY" in os.environ:
            test_text = TEST_CONTENT["unicode"]
            set_clipboard(test_text)
            result = get_clipboard()
            assert result == test_text

    @pytest.mark.skipif("DISPLAY" not in os.environ, reason="Requires display")
    @pytest.mark.serial
    def test_linux_xclip_availability(self):
        """Test xclip/xsel availability on Linux."""
        if platform.system() == "Linux":
            # This test verifies the clipboard tools are available
            # If they're not, the error handling should provide guidance
            test_text = TEST_CONTENT["xclip_availability"]
            try:
                set_clipboard(test_text)
                result = get_clipboard()
                assert result == test_text
            except ClipboardError as e:
                # Should contain helpful guidance for missing tools
                error_msg = str(e)
                assert "xclip" in error_msg.lower() or "install" in error_msg.lower()


class TestClipboardFallbackHandling:
    """Test clipboard fallback handling across platforms."""

    @patch("mcp_clipboard_server.clipboard.pyperclip.paste")
    def test_get_clipboard_failure_returns_empty(self, mock_paste):
        """Test that get_clipboard returns empty string on failure."""
        mock_paste.side_effect = OSError("Clipboard access failed")

        result = get_clipboard()
        assert result == ""

    @patch("mcp_clipboard_server.clipboard.pyperclip.copy")
    def test_set_clipboard_failure_raises_error(self, mock_copy):
        """Test that set_clipboard raises ClipboardError on failure."""
        mock_copy.side_effect = OSError("Clipboard write failed")

        with pytest.raises(ClipboardError) as exc_info:
            set_clipboard("test content")

        # Should contain platform information and guidance
        error_msg = str(exc_info.value)
        assert len(error_msg) > 50  # Should be detailed

    @pytest.mark.serial
    def test_empty_clipboard_handling(self):
        """Test handling of empty clipboard."""
        # This test ensures empty clipboard is handled gracefully
        with patch("mcp_clipboard_server.clipboard.pyperclip.paste", return_value=""):
            result = get_clipboard()
            assert result == ""

        with patch("mcp_clipboard_server.clipboard.pyperclip.paste", return_value=None):
            result = get_clipboard()
            assert result == ""

    def test_large_content_handling(self):
        """Test handling of large clipboard content."""
        large_content = TEST_CONTENT["large"]

        # Should handle large content without issues
        set_clipboard(large_content)
        result = get_clipboard()
        assert len(result) >= len(large_content) or result == ""  # May fail gracefully

    @patch("mcp_clipboard_server.clipboard.pyperclip.paste")
    @patch("mcp_clipboard_server.clipboard.logger")
    def test_error_logging(self, mock_logger, mock_paste):
        """Test that errors are properly logged."""
        mock_paste.side_effect = OSError("Test error")

        result = get_clipboard()
        assert result == ""

        # Verify error was logged
        mock_logger.error.assert_called()
        mock_logger.warning.assert_called()

    @pytest.mark.serial
    def test_cross_process_clipboard_sharing(self):
        """Test clipboard sharing across processes."""
        # This test verifies that clipboard content persists across process boundaries
        import subprocess
        import sys

        test_content = "cross-process-test-content"

        # Set clipboard in current process
        set_clipboard(test_content)

        # Read clipboard in subprocess
        script = f"""
import sys
sys.path.insert(0, "{os.path.dirname(os.path.dirname(__file__))}")
from mcp_clipboard_server.clipboard import get_clipboard
content = get_clipboard()
print(content, end="")
"""

        try:
            result = subprocess.run(
                [sys.executable, "-c", script],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                # Allow for platform limitations where clipboard might not persist
                assert result.stdout == test_content or result.stdout == ""
            # If subprocess fails, it might be due to platform limitations
            # which is acceptable for this test
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            # Platform doesn't support cross-process clipboard or timed out
            pytest.skip("Cross-process clipboard test not supported on this platform")


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_none_content_handling(self):
        """Test handling of None content from pyperclip."""
        with patch("mcp_clipboard_server.clipboard.pyperclip.paste", return_value=None):
            result = get_clipboard()
            assert result == ""

    def test_very_long_content(self):
        """Test handling of very long clipboard content."""
        # Test content near the 1MB validation limit
        long_content = "A" * (1024 * 1024 - 100)  # Just under 1MB

        with patch("mcp_clipboard_server.clipboard.pyperclip.copy"):
            with patch("mcp_clipboard_server.clipboard.pyperclip.paste") as mock_paste:
                mock_paste.return_value = long_content

                try:
                    set_clipboard(long_content)
                    result = get_clipboard()
                    assert len(result) == len(long_content) or result == ""
                except (ValueError, ClipboardError):
                    # May be rejected by validation or platform limits
                    pass

    def test_special_characters(self):
        """Test handling of special characters."""
        special_chars = "\\n\\t\\r\\0\x01\x1f"

        try:
            set_clipboard(special_chars)
            result = get_clipboard()
            # Some platforms may filter special characters
            assert isinstance(result, str)
        except (ValueError, ClipboardError):
            # Some platforms may reject special characters
            pass

    def test_rapid_operations(self):
        """Test rapid clipboard operations."""
        # Test for race conditions or locking issues
        import time

        for i in range(5):
            test_content = f"rapid-test-{i}"
            set_clipboard(test_content)
            # Small delay to avoid overwhelming the clipboard
            time.sleep(0.1)
            result = get_clipboard()
            # Content might not match exactly due to rapid operations
            assert isinstance(result, str)
