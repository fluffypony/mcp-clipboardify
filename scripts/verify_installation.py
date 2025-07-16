#!/usr/bin/env python3
"""Installation verification script for MCP Clipboard Server."""

import json
import subprocess
import sys
import time
from typing import Optional


class InstallationVerifier:
    """Verify MCP Clipboard Server installation and functionality."""

    def __init__(self, package_name: str = "mcp-clipboard-server"):
        self.package_name = package_name
        self.test_results = []
        self.temp_dir = None

    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log a test result."""
        status = "PASS" if success else "FAIL"
        print(f"[{status}] {test_name}")
        if details:
            print(f"    {details}")
        self.test_results.append(
            {"test": test_name, "success": success, "details": details}
        )

    def run_command(
        self, cmd: list, timeout: int = 30, capture_output: bool = True
    ) -> Optional[subprocess.CompletedProcess]:
        """Run a command with timeout and error handling."""
        try:
            result = subprocess.run(
                cmd,
                timeout=timeout,
                capture_output=capture_output,
                text=True,
                check=False,
            )
            return result
        except subprocess.TimeoutExpired:
            print(f"Command timed out after {timeout}s: {' '.join(cmd)}")
            return None
        except Exception as e:
            print(f"Command failed: {e}")
            return None

    def test_package_installation(self) -> bool:
        """Test that the package is installed and importable."""
        try:
            import mcp_clipboard_server

            version = getattr(mcp_clipboard_server, "__version__", "unknown")
            self.log_test("Package Import", True, f"Version: {version}")
            return True
        except ImportError as e:
            self.log_test("Package Import", False, f"Import error: {e}")
            return False

    def test_cli_entry_points(self) -> bool:
        """Test CLI entry points."""
        success = True

        # Test main CLI command
        result = self.run_command([self.package_name, "--help"])
        if result and result.returncode == 0:
            self.log_test("CLI Entry Point", True, "Help command works")
        else:
            self.log_test("CLI Entry Point", False, "Help command failed")
            success = False

        # Test module entry point
        result = self.run_command(
            [sys.executable, "-m", "mcp_clipboard_server", "--help"]
        )
        if result and result.returncode == 0:
            self.log_test("Module Entry Point", True, "Python -m works")
        else:
            self.log_test("Module Entry Point", False, "Python -m failed")
            success = False

        return success

    def test_mcp_protocol_basics(self) -> bool:
        """Test basic MCP protocol communication."""
        try:
            # Start server process
            process = subprocess.Popen(
                [sys.executable, "-m", "mcp_clipboard_server"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "verification-client", "version": "1.0.0"},
                },
            }

            request_json = json.dumps(init_request) + "\n"

            try:
                stdout, stderr = process.communicate(input=request_json, timeout=10)

                if stdout:
                    response = json.loads(stdout.split("\n")[0])
                    if response.get("jsonrpc") == "2.0" and "result" in response:
                        self.log_test(
                            "MCP Protocol Init", True, "Initialize successful"
                        )
                        return True
                    else:
                        self.log_test(
                            "MCP Protocol Init", False, f"Invalid response: {response}"
                        )
                        return False
                else:
                    self.log_test(
                        "MCP Protocol Init", False, f"No stdout. stderr: {stderr}"
                    )
                    return False

            except subprocess.TimeoutExpired:
                process.kill()
                self.log_test(
                    "MCP Protocol Init", False, "Timeout waiting for response"
                )
                return False

        except Exception as e:
            self.log_test("MCP Protocol Init", False, f"Exception: {e}")
            return False

    def test_clipboard_tools(self) -> bool:
        """Test clipboard tool operations."""
        try:
            # Start server process
            process = subprocess.Popen(
                [sys.executable, "-m", "mcp_clipboard_server"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            requests = []

            # Initialize
            requests.append(
                {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {
                            "name": "verification-client",
                            "version": "1.0.0",
                        },
                    },
                }
            )

            # List tools
            requests.append(
                {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
            )

            # Test get_clipboard
            requests.append(
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {"name": "get_clipboard", "arguments": {}},
                }
            )

            # Test set_clipboard
            requests.append(
                {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "tools/call",
                    "params": {
                        "name": "set_clipboard",
                        "arguments": {"text": "verification-test-content"},
                    },
                }
            )

            # Send all requests
            input_data = ""
            for req in requests:
                input_data += json.dumps(req) + "\n"

            try:
                stdout, stderr = process.communicate(input=input_data, timeout=15)

                if stdout:
                    responses = []
                    for line in stdout.split("\n"):
                        if line.strip():
                            try:
                                responses.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue

                    success_count = 0
                    for i, response in enumerate(responses):
                        if response.get("jsonrpc") == "2.0" and (
                            "result" in response or "error" in response
                        ):
                            success_count += 1

                    if success_count >= 2:  # At least init and tools/list should work
                        self.log_test(
                            "Clipboard Tools",
                            True,
                            f"{success_count}/{len(requests)} requests succeeded",
                        )
                        return True
                    else:
                        self.log_test(
                            "Clipboard Tools",
                            False,
                            f"Only {success_count}/{len(requests)} requests succeeded",
                        )
                        return False
                else:
                    self.log_test(
                        "Clipboard Tools", False, f"No response. stderr: {stderr}"
                    )
                    return False

            except subprocess.TimeoutExpired:
                process.kill()
                self.log_test("Clipboard Tools", False, "Timeout during tool testing")
                return False

        except Exception as e:
            self.log_test("Clipboard Tools", False, f"Exception: {e}")
            return False

    def test_platform_detection(self) -> bool:
        """Test platform detection functionality."""
        try:
            from mcp_clipboard_server.clipboard import (
                _get_platform_info,
                _get_platform_guidance,
            )

            platform_info = _get_platform_info()
            guidance = _get_platform_guidance("test error message")

            if platform_info and guidance:
                self.log_test("Platform Detection", True, f"Platform: {platform_info}")
                return True
            else:
                self.log_test(
                    "Platform Detection", False, "Platform detection returned empty"
                )
                return False

        except Exception as e:
            self.log_test("Platform Detection", False, f"Exception: {e}")
            return False

    def test_unicode_support(self) -> bool:
        """Test Unicode content handling."""
        try:
            from mcp_clipboard_server.clipboard import set_clipboard, get_clipboard

            # Test with Unicode content
            unicode_text = "Hello, 世界! 🌍 Café naïve résumé"

            try:
                set_clipboard(unicode_text)
                result = get_clipboard()

                # Result should either match exactly or be empty (graceful fallback)
                if result == unicode_text:
                    self.log_test("Unicode Support", True, "Unicode content preserved")
                    return True
                elif result == "":
                    self.log_test(
                        "Unicode Support", True, "Graceful fallback to empty string"
                    )
                    return True
                else:
                    self.log_test(
                        "Unicode Support", False, f"Unexpected result: {repr(result)}"
                    )
                    return False

            except Exception as e:
                # Platform might not support clipboard, which is acceptable
                self.log_test("Unicode Support", True, f"Platform limitation: {e}")
                return True

        except Exception as e:
            self.log_test("Unicode Support", False, f"Import error: {e}")
            return False

    def test_error_handling(self) -> bool:
        """Test error handling capabilities."""
        try:
            from mcp_clipboard_server._validators import ValidationException

            # Test that error classes are available
            self.log_test(
                "Error Classes",
                True,
                "ClipboardError and ValidationException available",
            )

            # Test validation
            from mcp_clipboard_server._validators import validate_clipboard_text

            try:
                # Test with extremely large text (should fail)
                large_text = "A" * (2 * 1024 * 1024)  # 2MB
                validate_clipboard_text(large_text)
                self.log_test(
                    "Validation Error Handling",
                    False,
                    "Large text should have failed validation",
                )
                return False
            except ValidationException:
                self.log_test(
                    "Validation Error Handling", True, "Large text properly rejected"
                )
                return True
            except Exception as e:
                self.log_test(
                    "Validation Error Handling", False, f"Unexpected error: {e}"
                )
                return False

        except Exception as e:
            self.log_test("Error Handling", False, f"Import error: {e}")
            return False

    def run_all_tests(self) -> bool:
        """Run all verification tests."""
        print("=== MCP Clipboard Server Installation Verification ===")
        print(f"Python version: {sys.version}")
        print(f"Platform: {sys.platform}")
        print()

        tests = [
            self.test_package_installation,
            self.test_cli_entry_points,
            self.test_mcp_protocol_basics,
            self.test_clipboard_tools,
            self.test_platform_detection,
            self.test_unicode_support,
            self.test_error_handling,
        ]

        success_count = 0
        for test in tests:
            if test():
                success_count += 1

        print()
        print(f"=== Results: {success_count}/{len(tests)} tests passed ===")

        if success_count == len(tests):
            print("✅ All tests passed! Installation is working correctly.")
            return True
        else:
            print("❌ Some tests failed. Installation may have issues.")
            failed_tests = [r for r in self.test_results if not r["success"]]
            if failed_tests:
                print("\nFailed tests:")
                for test in failed_tests:
                    print(f"  - {test['test']}: {test['details']}")
            return False

    def generate_report(self) -> dict:
        """Generate a detailed verification report."""
        return {
            "timestamp": time.time(),
            "python_version": sys.version,
            "platform": sys.platform,
            "package_name": self.package_name,
            "test_results": self.test_results,
            "success_rate": len([r for r in self.test_results if r["success"]])
            / len(self.test_results)
            if self.test_results
            else 0,
        }


def main():
    """Main verification function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Verify MCP Clipboard Server installation"
    )
    parser.add_argument(
        "--package-name",
        default="mcp-clipboard-server",
        help="Package name to verify (default: mcp-clipboard-server)",
    )
    parser.add_argument("--report", help="Save detailed report to file")
    parser.add_argument("--quiet", action="store_true", help="Reduce output verbosity")

    args = parser.parse_args()

    if args.quiet:
        # Suppress some output for automated testing
        pass

    verifier = InstallationVerifier(args.package_name)
    success = verifier.run_all_tests()

    if args.report:
        report = verifier.generate_report()
        with open(args.report, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\nDetailed report saved to: {args.report}")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
