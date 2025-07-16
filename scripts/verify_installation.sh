#!/bin/bash

# Installation verification script for non-Python environments
# This script can be run in environments where Python might not be easily available

set -e

PACKAGE_NAME="${1:-mcp-clipboard-server}"
PYTHON_CMD="${PYTHON_CMD:-python3}"

echo "=== MCP Clipboard Server Installation Verification ==="
echo "Package: $PACKAGE_NAME"
echo "Python: $PYTHON_CMD"
echo "Platform: $(uname -s)"
echo

# Function to run a test and report results
run_test() {
    local test_name="$1"
    local test_command="$2"

    echo -n "[$test_name] "
    if eval "$test_command" >/dev/null 2>&1; then
        echo "PASS"
        return 0
    else
        echo "FAIL"
        return 1
    fi
}

# Function to run a test with output capture
run_test_with_output() {
    local test_name="$1"
    local test_command="$2"

    echo -n "[$test_name] "
    local output
    if output=$(eval "$test_command" 2>&1); then
        echo "PASS"
        if [ -n "$output" ]; then
            echo "    Output: $(echo "$output" | head -1)"
        fi
        return 0
    else
        echo "FAIL"
        if [ -n "$output" ]; then
            echo "    Error: $(echo "$output" | head -1)"
        fi
        return 1
    fi
}

# Test counter
tests_run=0
tests_passed=0

# Test 1: Python availability
echo "Testing Python environment..."
if run_test "Python Available" "$PYTHON_CMD --version"; then
    ((tests_passed++))
fi
((tests_run++))

# Test 2: Package importability
if run_test "Package Import" "$PYTHON_CMD -c 'import mcp_clipboard_server; print(mcp_clipboard_server.__version__)'"; then
    ((tests_passed++))
fi
((tests_run++))

# Test 3: CLI entry point
if run_test "CLI Entry Point" "$PACKAGE_NAME --help"; then
    ((tests_passed++))
fi
((tests_run++))

# Test 4: Module entry point
if run_test "Module Entry Point" "$PYTHON_CMD -m mcp_clipboard_server --help"; then
    ((tests_passed++))
fi
((tests_run++))

# Test 5: Basic MCP communication
echo "Testing MCP protocol..."
cat > /tmp/mcp_test.json << 'EOF'
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0.0"}}}
EOF

if timeout 10 $PYTHON_CMD -m mcp_clipboard_server < /tmp/mcp_test.json > /tmp/mcp_response.json 2>/dev/null; then
    if grep -q '"jsonrpc":"2.0"' /tmp/mcp_response.json; then
        echo "[MCP Protocol] PASS"
        ((tests_passed++))
    else
        echo "[MCP Protocol] FAIL - Invalid response format"
    fi
else
    echo "[MCP Protocol] FAIL - No response or timeout"
fi
((tests_run++))

# Clean up temporary files
rm -f /tmp/mcp_test.json /tmp/mcp_response.json

# Test 6: Platform detection (if Python script is available)
if [ -f "scripts/verify_installation.py" ]; then
    if run_test "Platform Detection" "$PYTHON_CMD scripts/verify_installation.py --quiet"; then
        ((tests_passed++))
    fi
    ((tests_run++))
else
    echo "[Platform Detection] SKIP - verification script not found"
fi

# Summary
echo
echo "=== Results: $tests_passed/$tests_run tests passed ==="

if [ "$tests_passed" -eq "$tests_run" ]; then
    echo "✅ All tests passed! Installation is working correctly."
    exit 0
else
    echo "❌ Some tests failed. Installation may have issues."
    exit 1
fi
