---
name: Bug report
about: Create a report to help us improve
title: '[BUG] '
labels: bug
assignees: ''

---

## 🐛 Bug Description

A clear and concise description of what the bug is.

## 🔄 Steps to Reproduce

1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

## ✅ Expected Behavior

A clear and concise description of what you expected to happen.

## ❌ Actual Behavior

A clear and concise description of what actually happened.

## 💻 Environment Information

**Platform Details:**
- OS: [e.g. Ubuntu 22.04, Windows 11, macOS 13.0]
- Python Version: [output of `python3 --version`]
- Package Version: [output of `pip show mcp-clipboardify`]
- Terminal/Shell: [e.g. bash, PowerShell, zsh, iTerm2]

**Clipboard Environment:**
- Desktop Environment: [e.g. GNOME, KDE, Windows Desktop, macOS]
- Display Server: [e.g. X11, Wayland, Native] (Linux only)
- Clipboard Utilities: [output of `which xclip xsel`] (Linux only)

## 📝 Debug Output

Please run with debug logging and include the output:

```bash
export MCP_LOG_LEVEL=DEBUG
mcp-clipboardify 2> debug.log

# Reproduce the issue here

cat debug.log
```

```
[Paste debug output here]
```

## 🔍 Additional Context

Add any other context about the problem here:

- Does this happen consistently or intermittently?
- Any recent system changes or updates?
- Other applications that might interfere with clipboard?
- Any security software that might block clipboard access?

## 📱 Screenshots/Recordings

If applicable, add screenshots or screen recordings to help explain your problem.

## ✅ Health Check

Please run the health check script and include results:

```bash
# Option 1: Direct download
curl -sSL https://raw.githubusercontent.com/fluffypony/mcp-clipboardify/main/scripts/verify_installation.sh | bash

# Option 2: Local script (if you have the repository)
./scripts/verify_installation.sh
```

```
[Paste health check output here]
```

## 🚀 Workarounds

Have you found any workarounds for this issue? Please describe them here.

## 🔗 Related Issues

Link to any related issues, discussions, or pull requests.

---

**Note**: Please ensure you've checked the [troubleshooting guide](../../docs/troubleshooting.md) and [platform guide](../../docs/platform_guide.md) before submitting this bug report.
