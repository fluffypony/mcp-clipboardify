# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with the MCP Clipboard Server.

## 📋 Table of Contents

- [Quick Diagnosis](#quick-diagnosis)
- [Platform-Specific Issues](#platform-specific-issues)
- [Error Messages](#error-messages)
- [Performance Issues](#performance-issues)
- [Debug Procedures](#debug-procedures)
- [Known Limitations](#known-limitations)
- [Getting Help](#getting-help)

## Quick Diagnosis

### 🔍 Health Check Script

Run this quick health check to identify issues:

```bash
# Download and run verification script
curl -sSL https://raw.githubusercontent.com/fluffypony/mcp-clipboardify/main/scripts/verify_installation.sh | bash

# Or if you have the repository
./scripts/verify_installation.sh
```

### 🩺 Manual Health Check

```bash
# 1. Check Python version
python3 --version  # Should be 3.8+

# 2. Check package installation
python3 -c "import mcp_clipboard_server; print(mcp_clipboard_server.__version__)"

# 3. Check CLI entry point
mcp-clipboardify --help

# 4. Check basic MCP protocol
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}' | timeout 5 mcp-clipboardify
```

## Platform-Specific Issues

### 🪟 Windows Issues

### # Error: "Access is denied" or "Clipboard unavailable"

**Symptoms:**
- Clipboard operations fail with permission errors
- Error messages mention access denied

**Diagnosis:**
```cmd
# Check antivirus logs
# Look for Python process blocking in security software

# Test basic clipboard access
python -c "import pyperclip; print(pyperclip.paste())"
```

**Solutions:**
1. **Antivirus Exception**: Add Python.exe to antivirus whitelist
2. **Group Policy**: Contact IT admin if in corporate environment
3. **UAC Settings**: Try running with elevated privileges (not recommended)
4. **Windows Updates**: Ensure latest Windows updates installed

### # Error: "Unicode decode error" or strange characters

**Symptoms:**
- International text displays incorrectly
- Emoji or special characters cause errors

**Solutions:**
```cmd
# Set UTF-8 encoding
set PYTHONIOENCODING=utf-8
chcp 65001

# Run with encoding fix
python -X utf8 -m mcp_clipboard_server
```

### 🍎 macOS Issues

### # Error: "Operation not permitted" or "Accessibility access required"

**Symptoms:**
- Clipboard access denied
- macOS security prompts appear

**Solutions:**
1. **System Preferences → Security & Privacy → Privacy**
2. **Input Monitoring**: Add Terminal.app
3. **Accessibility**: Add Terminal.app if required
4. **Full Disk Access**: May be needed in some cases

```bash
# Reset permissions (macOS 12+)
tccutil reset All

# Check current permissions
tccutil list
```

### # Error: "No module named '_tkinter'" with some clipboard operations

**Solutions:**
```bash
# Install Python with tkinter support
brew install python-tk

# Or use conda
conda install tk
```

### 🐧 Linux Issues

### # Error: "xclip: command not found" or "xsel: command not found"

**Symptoms:**
- Clipboard operations fail on Linux
- Error mentions missing xclip or xsel

**Solutions:**
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install xclip xsel

# RHEL/CentOS/Fedora
sudo yum install xclip xsel    # RHEL/CentOS 7-8
sudo dnf install xclip xsel    # Fedora/RHEL 9+

# Arch Linux
sudo pacman -S xclip xsel

# Alpine Linux
sudo apk add xclip xsel

# Verify installation
which xclip xsel
xclip -version
```

### # Error: "Cannot open display" or "No protocol specified"

**Symptoms:**
- X11 display errors
- DISPLAY variable issues

**Solutions:**
```bash
# Check DISPLAY variable
echo $DISPLAY

# Set DISPLAY (usually :0 for local display)
export DISPLAY=:0

# For SSH with X forwarding
ssh -X username@hostname

# For headless systems - expected behavior
# Read operations will return empty string gracefully
```

### # Error: Wayland clipboard issues

**Solutions:**
```bash
# Install Wayland clipboard utilities
sudo apt-get install wl-clipboard  # Ubuntu/Debian

# Test Wayland clipboard
wl-copy "test"
wl-paste

# pyperclip should auto-detect wl-clipboard
```

### 🔧 WSL Issues

### # Error: "clip.exe not found" or clipboard not working

**Symptoms:**
- WSL clipboard integration fails
- Windows clipboard not accessible from WSL

**Solutions:**
```bash
# Install Windows integration tools
sudo apt-get update
sudo apt-get install wslu

# Verify clip.exe is in PATH
which clip.exe
/mnt/c/Windows/System32/clip.exe

# Test Windows clipboard integration
echo "test" | clip.exe
powershell.exe -command "Get-Clipboard"

# Add to PATH if missing
echo 'export PATH="$PATH:/mnt/c/Windows/System32"' >> ~/.bashrc
source ~/.bashrc
```

### # Error: WSL clipboard stops working after sleep/hibernate

**Solutions:**
```bash
# Restart WSL completely
wsl --shutdown
# Then restart your terminal

# Or restart specific distribution
wsl --terminate Ubuntu-20.04
```

## Error Messages

### Common JSON-RPC Errors

### # Parse Error (-32700)
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32700,
    "message": "Parse error"
  },
  "id": null
}
```

**Cause:** Invalid JSON sent to server
**Solution:** Check JSON formatting, ensure proper escaping

### # Invalid Request (-32600)
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32600,
    "message": "Invalid Request"
  },
  "id": null
}
}
```

**Cause:** Malformed JSON-RPC request
**Solution:** Ensure jsonrpc, method, and id fields are present

### # Method Not Found (-32601)
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32601,
    "message": "Method not found"
  },
  "id": 1
}
```

**Cause:** Called undefined method
**Solution:** Use only supported methods: initialize, tools/list, tools/call

### # Invalid Params (-32602)
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Invalid params"
  },
  "id": 1
}
```

**Cause:** Wrong parameters for method
**Solution:** Check parameter format for tools/call

### Clipboard-Specific Errors

### # "Clipboard operation failed: Failed to read clipboard"
**Cause:** Platform-specific clipboard access issue
**Diagnosis:**
```bash
# Enable debug logging
export MCP_LOG_LEVEL=DEBUG
mcp-clipboardify

# Check platform-specific requirements
python3 -c "from mcp_clipboard_server.clipboard import _get_platform_info; print(_get_platform_info())"
```

### # "Validation error: Text exceeds maximum size"
**Cause:** Text larger than 1MB limit
**Solution:** Split large text into smaller chunks

### # "Failed to write to clipboard: Permission denied"
**Cause:** Insufficient permissions or platform restrictions
**Solution:** Check platform-specific permission requirements

## Performance Issues

### Slow Clipboard Operations

**Symptoms:**
- Operations take longer than expected
- Timeouts in client applications

**Diagnosis:**
```bash
# Time clipboard operations
time echo "test" | xclip -selection clipboard  # Linux
time echo "test" | pbcopy                      # macOS

# Profile MCP server
export MCP_LOG_LEVEL=DEBUG
mcp-clipboardify  # Watch for timing information
```

**Solutions:**
1. **Reduce Text Size**: Keep clipboard content under 100KB for best performance
2. **Check System Load**: High CPU/memory usage affects clipboard performance
3. **Platform Optimization**: Use native tools when possible

### Memory Usage Issues

**Symptoms:**
- High memory consumption
- Out of memory errors

**Diagnosis:**
```bash
# Monitor memory usage
ps aux | grep mcp-clipboardify
top -p $(pgrep -f mcp-clipboardify)

# Check for memory leaks
valgrind python3 -m mcp_clipboard_server  # Linux only
```

**Solutions:**
1. **Text Size Limits**: Enforce 1MB limit strictly
2. **Restart Periodically**: For long-running processes
3. **Monitor Usage**: Set up memory monitoring

## Debug Procedures

### Enable Debug Logging

```bash
# Set environment variables
export MCP_LOG_LEVEL=DEBUG
export MCP_LOG_JSON=true

# Run with debug output
mcp-clipboardify 2> debug.log

# Analyze logs
tail -f debug.log
```

### Capture Network Traffic (for debugging JSON-RPC)

```bash
# Using strace (Linux)
strace -e trace=read,write -o strace.log mcp-clipboardify

# Using dtruss (macOS)
sudo dtruss -t read,write mcp-clipboardify

# Manual JSON-RPC testing
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0.0"}}}' | mcp-clipboardify
```

### Python Debugging

```python
# Add to test script
import logging
import sys

# Enable all logging
logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)

# Test individual components
from mcp_clipboard_server.clipboard import get_clipboard, set_clipboard
from mcp_clipboard_server.protocol import handle_request

# Test clipboard directly
try:
    content = get_clipboard()
    print(f"Clipboard content: {repr(content)}")

    set_clipboard("test content")
    print("Set clipboard successful")
except Exception as e:
    print(f"Clipboard error: {e}")
    import traceback
    traceback.print_exc()
```

### Minimal Test Case

```python
#!/usr/bin/env python3
"""Minimal test case for issue reproduction."""

import json
import subprocess
import sys

def test_mcp_server():
    """Test basic MCP server functionality."""

    # Start server
    process = subprocess.Popen(
        [sys.executable, "-m", "mcp_clipboard_server"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # Send initialize request
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0.0"}
        }
    }

    try:
        stdout, stderr = process.communicate(
            input=json.dumps(request) + "\n",
            timeout=10
        )

        print(f"stdout: {stdout}")
        print(f"stderr: {stderr}")
        print(f"returncode: {process.returncode}")

        if stdout:
            response = json.loads(stdout.split('\n')[0])
            print(f"response: {response}")

    except Exception as e:
        print(f"Error: {e}")
        process.kill()

if __name__ == "__main__":
    test_mcp_server()
```

## Known Limitations

### Platform Limitations

### # Linux
- **Headless Systems**: No clipboard access (graceful degradation)
- **Wayland**: Requires wl-clipboard utilities
- **Performance**: Slower than native platforms due to external tools

### # macOS
- **Sandboxed Apps**: Limited clipboard access in sandboxed environments
- **Security**: Requires explicit permission grants
- **RTF Content**: Complex formatted content may be simplified

### # Windows
- **Enterprise Policies**: May restrict clipboard access
- **Antivirus**: May interfere with clipboard operations
- **Unicode**: Encoding issues in some terminal environments

### # WSL
- **Sleep/Resume**: Clipboard may stop working after system sleep
- **Performance**: Cross-system calls add latency
- **Integration**: Requires Windows integration tools

### Technical Limitations

### # Text Size
- **Maximum**: 1MB per operation
- **Performance**: Degrades with large content
- **Memory**: Held in memory during operations

### # Concurrency
- **Single-threaded**: One operation at a time
- **No Queuing**: Operations may fail if clipboard is busy
- **State**: No persistence between operations

### # Protocol
- **STDIO Only**: No network or file-based transport
- **Synchronous**: No async operations
- **Session**: No multi-session support

## Getting Help

### Before Asking for Help

1. **Run Diagnostics**: Use the verification scripts
2. **Check Logs**: Enable debug logging and review output
3. **Reproduce Issue**: Create minimal test case
4. **Platform Info**: Note your OS, Python version, and environment

### Where to Get Help

### # GitHub Issues
- **Bug Reports**: [Create an issue](https://github.com/fluffypony/mcp-clipboardify/issues/new?template=bug_report.md)
- **Feature Requests**: [Request a feature](https://github.com/fluffypony/mcp-clipboardify/issues/new?template=feature_request.md)
- **Search**: Check existing issues first

### # Discussions
- **Questions**: [GitHub Discussions](https://github.com/fluffypony/mcp-clipboardify/discussions)
- **Community**: Get help from other users
- **Best Practices**: Share and learn implementation tips

### # Documentation
- **Platform Guide**: [Platform-specific instructions](platform_guide.md)
- **API Reference**: [MCP Protocol Documentation](https://spec.modelcontextprotocol.io/)
- **Examples**: Check the examples directory

### What to Include in Bug Reports

```markdown
## Environment
- OS: [e.g., Ubuntu 22.04, Windows 11, macOS 13.0]
- Python Version: [output of python3 --version]
- Package Version: [output of pip show mcp-clipboardify]
- Terminal: [e.g., bash, PowerShell, iTerm2]

## Issue Description
[Clear description of the problem]

## Steps to Reproduce
1. [First step]
2. [Second step]
3. [etc.]

## Expected Behavior
[What you expected to happen]

## Actual Behavior
[What actually happened]

## Debug Output
```bash
# Include output from:
export MCP_LOG_LEVEL=DEBUG
mcp-clipboardify 2> debug.log
# ... reproduce issue ...
cat debug.log
```

## Additional Context
[Any other relevant information]
```

### Common Support Questions

### # "How do I integrate with my application?"
See the [integration examples](../examples/) and MCP protocol documentation.

### # "Can I use this in production?"
Yes, the server is production-ready with comprehensive error handling and logging.

### # "Does this work with my CI/CD system?"
Yes, with proper setup. See the [platform guide](platform_guide.md) for CI/CD configurations.

### # "How do I handle large clipboard content?"
Split content into chunks under 1MB each, or use alternative transfer methods for large data.

### # "Can I run multiple instances?"
Each instance manages its own clipboard state. Multiple instances may interfere with each other.

### # "Is clipboard content secure?"
Content is not logged or persisted. Use appropriate security measures for sensitive data.
