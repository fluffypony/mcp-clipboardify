# Platform-Specific Installation and Configuration Guide

This guide provides detailed platform-specific instructions for installing and configuring the MCP Clipboard Server.

## 📋 Table of Contents

- [Windows](#windows)
- [macOS](#macos)
- [Linux](#linux)
- [WSL (Windows Subsystem for Linux)](#wsl-windows-subsystem-for-linux)
- [Docker/Containers](#dockercontainers)
- [CI/CD Environments](#cicd-environments)

## Windows

### Requirements
- Windows 10 (build 1903+) or Windows 11
- Python 3.8 or higher
- No additional dependencies required

### Installation

#### Option 1: Using pip (Recommended)
```cmd
pip install mcp-clipboardify
```

#### Option 2: Using Poetry
```cmd
git clone https://github.com/fluffypony/mcp-clipboardify
cd mcp-clipboardify
poetry install
poetry run mcp-clipboardify
```

### Configuration

#### Basic Usage
```cmd
# Start the server
mcp-clipboardify

# Or using Python module
python -m mcp_clipboard_server

# With debug logging
set MCP_LOG_LEVEL=DEBUG
mcp-clipboardify
```

#### Enterprise Environments

If running in a corporate environment with restricted permissions:

1. **Group Policy Settings**: Contact your IT administrator if clipboard access is blocked
2. **Antivirus Software**: Add exceptions for Python processes if clipboard access is blocked
3. **User Account Control**: Run with appropriate privileges

#### PowerShell Integration
```powershell
# Install using PowerShell
pip install mcp-clipboardify

# Start with environment variables
$env:MCP_LOG_LEVEL = "DEBUG"
mcp-clipboardify
```

### Troubleshooting

#### Common Issues

**Clipboard Access Denied**
```cmd
# Check for antivirus blocking
# Add Python.exe to antivirus exceptions

# Check for group policy restrictions
gpupdate /force
```

**Unicode Issues**
```cmd
# Ensure UTF-8 support
chcp 65001
set PYTHONIOENCODING=utf-8
```

**Service Installation**
```cmd
# For running as Windows service (advanced)
# Use tools like NSSM or create a proper Windows service wrapper
```

## macOS

### Requirements
- macOS 10.15 (Catalina) or later
- Python 3.8 or higher
- Xcode Command Line Tools (for some dependency compilation)

### Installation

#### Option 1: Using pip with Homebrew Python
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python

# Install MCP Clipboard Server
pip3 install mcp-clipboardify
```

#### Option 2: Using system Python
```bash
# Install using system Python (requires pip)
python3 -m pip install --user mcp-clipboardify
```

#### Option 3: Using Poetry
```bash
git clone https://github.com/fluffypony/mcp-clipboardify
cd mcp-clipboardify
poetry install
poetry run mcp-clipboardify
```

### Configuration

#### Security and Privacy Settings

macOS may require additional permissions:

1. **System Preferences → Security & Privacy → Privacy**
2. **Input Monitoring**: Add Terminal.app or your application
3. **Accessibility**: May be required for some clipboard operations

#### Terminal Configuration
```bash
# Add to ~/.zshrc or ~/.bash_profile
export MCP_LOG_LEVEL=DEBUG
alias mcp-clipboard="mcp-clipboardify"

# For better Unicode support
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
```

### Troubleshooting

#### Permission Denied Errors
```bash
# Reset permissions (macOS 12+)
tccutil reset All

# Manual permission grant
# Go to System Preferences → Security & Privacy → Privacy
# Add your terminal application to required categories
```

#### Sandboxed Applications
```bash
# Some sandboxed apps may have limited clipboard access
# This is expected behavior for security
# Use non-sandboxed terminals like iTerm2 or Terminal.app
```

#### M1/M2 Apple Silicon
```bash
# Ensure you're using the correct Python architecture
python3 -c "import platform; print(platform.machine())"

# Should show "arm64" for Apple Silicon
# Install universal or arm64 Python if needed
```

## Linux

### Requirements
- X11 display server (for GUI clipboard access)
- Python 3.8 or higher
- Clipboard utilities: `xclip` and/or `xsel`

### Distribution-Specific Installation

#### Ubuntu/Debian
```bash
# Update package list
sudo apt-get update

# Install dependencies
sudo apt-get install python3 python3-pip xclip xsel

# Install MCP Clipboard Server
pip3 install --user mcp-clipboardify

# Or system-wide (requires sudo)
sudo pip3 install mcp-clipboardify
```

#### RHEL/CentOS/Fedora
```bash
# RHEL/CentOS 7/8
sudo yum install python3 python3-pip xclip xsel

# Fedora/RHEL 9+
sudo dnf install python3 python3-pip xclip xsel

# Install MCP Clipboard Server
pip3 install --user mcp-clipboardify
```

#### Arch Linux
```bash
# Install dependencies
sudo pacman -S python python-pip xclip xsel

# Install from AUR (if available) or pip
pip install --user mcp-clipboardify
```

#### Alpine Linux
```bash
# Install dependencies
sudo apk add python3 py3-pip xclip xsel

# Install MCP Clipboard Server
pip3 install --user mcp-clipboardify
```

### Configuration

#### Environment Setup
```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"
export MCP_LOG_LEVEL=DEBUG

# Ensure DISPLAY is set for GUI applications
export DISPLAY=:0
```

#### Systemd Service (Optional)
```bash
# Create service file
sudo tee /etc/systemd/system/mcp-clipboard.service << EOF
[Unit]
Description=MCP Clipboard Server
After=graphical-session.target

[Service]
Type=simple
User=your-username
Environment=DISPLAY=:0
ExecStart=/home/your-username/.local/bin/mcp-clipboardify
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl enable mcp-clipboard.service
sudo systemctl start mcp-clipboard.service
```

### Troubleshooting

#### Missing Clipboard Utilities
```bash
# Error: "xclip not found"
sudo apt-get install xclip xsel  # Ubuntu/Debian
sudo yum install xclip xsel      # RHEL/CentOS
sudo pacman -S xclip xsel        # Arch

# Verify installation
which xclip xsel
```

#### No Display Server
```bash
# For headless systems (servers)
# Read operations will return empty string (graceful)
# Write operations will fail with descriptive error

# To test clipboard utilities
echo "test" | xclip -selection clipboard
xclip -selection clipboard -o
```

#### Wayland Compatibility
```bash
# For Wayland sessions, install wl-clipboard
sudo apt-get install wl-clipboard  # Ubuntu/Debian

# pyperclip should automatically detect and use wl-clipboard
```

## WSL (Windows Subsystem for Linux)

### Requirements
- WSL2 (recommended)
- Windows 10 build 19041+ or Windows 11
- Ubuntu 20.04+ or compatible distribution

### Installation

#### Step 1: Enable Clipboard Integration
```bash
# Install Windows integration tools
sudo apt-get update
sudo apt-get install wslu

# Verify clip.exe is available
which clip.exe
```

#### Step 2: Install MCP Clipboard Server
```bash
# Install dependencies
sudo apt-get install python3 python3-pip

# Install MCP Clipboard Server
pip3 install --user mcp-clipboardify
```

#### Step 3: Configure WSL
Add to `~/.wslconfig` (Windows user directory):
```ini
[wsl2]
guiApplications=true
systemdEnabled=true
```

### Configuration

#### Environment Setup
```bash
# Add to ~/.bashrc
export PATH="$HOME/.local/bin:$PATH"

# WSL clipboard integration
alias pbcopy='clip.exe'
alias pbpaste='powershell.exe -command "Get-Clipboard"'
```

#### Windows Terminal Integration
Ensure Windows Terminal has clipboard sharing enabled:
1. Open Windows Terminal
2. Settings → Interaction
3. Enable "Automatically copy selection to clipboard"

### Troubleshooting

#### Clipboard Not Working
```bash
# Test Windows clipboard integration
echo "test" | clip.exe
powershell.exe -command "Get-Clipboard"

# If that works but MCP server doesn't, check pyperclip detection
python3 -c "import pyperclip; print(pyperclip.paste())"
```

#### Permission Issues
```bash
# Ensure proper WSL2 permissions
# Restart WSL if clipboard stops working
wsl --shutdown
# Then restart your terminal
```

## Docker/Containers

### Considerations

Clipboard access in containers is limited by design. The MCP Clipboard Server handles this gracefully:

#### Behavior in Containers
- **Read operations**: Return empty string (graceful fallback)
- **Write operations**: Fail with descriptive error messages
- **Logging**: Indicates container environment detected

#### Testing in Containers
```dockerfile
# Example Dockerfile for testing
FROM python:3.11-slim

RUN pip install mcp-clipboardify

# For testing without clipboard access
ENTRYPOINT ["python", "-m", "mcp_clipboard_server"]
```

#### Host Clipboard Access (Linux)
```bash
# Mount X11 socket for clipboard access (not recommended for production)
docker run -v /tmp/.X11-unix:/tmp/.X11-unix \
           -e DISPLAY=$DISPLAY \
           your-image
```

## CI/CD Environments

### GitHub Actions
```yaml
- name: Setup clipboard dependencies (Linux)
  if: runner.os == 'Linux'
  run: |
    sudo apt-get update
    sudo apt-get install -y xclip xsel xvfb
    export DISPLAY=:99
    Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
    sleep 3

- name: Test MCP Clipboard Server
  run: |
    pip install mcp-clipboardify
    python -m mcp_clipboard_server --help
```

### GitLab CI
```yaml
test_clipboard:
  script:
    - apt-get update && apt-get install -y xclip xsel xvfb
    - export DISPLAY=:99
    - Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
    - sleep 3
    - pip install mcp-clipboardify
    - python -m mcp_clipboard_server --help
```

### Jenkins
```groovy
pipeline {
    agent any
    stages {
        stage('Setup') {
            steps {
                sh 'sudo apt-get update && sudo apt-get install -y xclip xsel xvfb'
                sh 'export DISPLAY=:99 && Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &'
            }
        }
        stage('Test') {
            steps {
                sh 'pip install mcp-clipboardify'
                sh 'python -m mcp_clipboard_server --help'
            }
        }
    }
}
```

### Handling CI Limitations
```python
# In your test code
import os
import sys

def is_ci_environment():
    """Detect if running in CI environment."""
    ci_indicators = ['CI', 'CONTINUOUS_INTEGRATION', 'GITHUB_ACTIONS', 'GITLAB_CI']
    return any(os.getenv(var) for var in ci_indicators)

def test_clipboard_operations():
    if is_ci_environment():
        # Use mock clipboard or skip clipboard-dependent tests
        pytest.skip("Skipping clipboard tests in CI environment")

    # Normal clipboard tests
    from mcp_clipboard_server.clipboard import get_clipboard, set_clipboard
    # ... test implementation
```

## Performance Considerations

### Memory Usage
- **Text Size Limit**: 1MB per operation
- **Memory Footprint**: ~10-20MB base usage
- **Concurrent Operations**: Single-threaded by design

### Platform Performance
- **Windows**: Native API access (fastest)
- **macOS**: Native pasteboard access (fast)
- **Linux**: External tool execution (slower but reliable)
- **WSL**: Cross-system calls (moderate performance)

### Optimization Tips
1. **Avoid Large Content**: Split into smaller chunks if possible
2. **Batch Operations**: Minimize frequent clipboard access
3. **Error Handling**: Implement retries for transient failures
4. **Monitoring**: Use debug logging to identify bottlenecks

## Security Considerations

### Data Privacy
- **No Persistence**: Clipboard content is not stored or logged
- **Memory Safety**: Content is not retained in memory after operations
- **Process Isolation**: Server runs in isolated process space

### Access Control
- **File Permissions**: Ensure proper permissions for Python executable
- **Network Isolation**: Server uses STDIO only (no network access)
- **Privilege Escalation**: Runs with user-level permissions only

### Enterprise Deployment
1. **Policy Compliance**: Verify clipboard policies allow automation
2. **Audit Logging**: Enable debug logging for audit trails
3. **Resource Limits**: Set appropriate memory and CPU limits
4. **Incident Response**: Monitor for unexpected errors or failures
