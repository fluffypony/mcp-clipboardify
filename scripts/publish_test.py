#!/usr/bin/env python3
"""Script to publish package to TestPyPI for validation."""

import os
import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd, check=True, capture_output=False):
    """Run a shell command with error handling."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, check=check, capture_output=capture_output, text=True
        )
        if capture_output:
            return result.stdout.strip()
        return result
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        if capture_output and e.stdout:
            print(f"stdout: {e.stdout}")
        if capture_output and e.stderr:
            print(f"stderr: {e.stderr}")
        if check:
            sys.exit(1)
        return None


def get_package_version():
    """Get the current package version from pyproject.toml."""
    try:
        result = run_command(["poetry", "version", "-s"], capture_output=True)
        return result
    except Exception as e:
        print(f"Failed to get version: {e}")
        return None


def validate_package_metadata():
    """Validate package metadata before publishing."""
    print("Validating package metadata...")

    # Check that required files exist
    required_files = [
        "README.md",
        "pyproject.toml",
        "src/mcp_clipboard_server/__init__.py",
    ]
    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"Error: Required file missing: {file_path}")
            return False

    # Check version consistency
    version = get_package_version()
    if not version:
        print("Error: Could not determine package version")
        return False

    print(f"Package version: {version}")

    # Check __init__.py version
    init_file = Path("src/mcp_clipboard_server/__init__.py")
    init_content = init_file.read_text()
    if f'__version__ = "{version}"' not in init_content:
        print("Warning: Version mismatch in __init__.py")
        print(f'Expected: __version__ = "{version}"')

    return True


def build_package():
    """Build the package using Poetry."""
    print("Building package...")

    # Clean previous builds
    dist_dir = Path("dist")
    if dist_dir.exists():
        print("Cleaning previous builds...")
        for file in dist_dir.glob("*"):
            file.unlink()

    # Build package
    run_command(["poetry", "build"])

    # Verify build outputs
    wheel_files = list(dist_dir.glob("*.whl"))
    tar_files = list(dist_dir.glob("*.tar.gz"))

    if not wheel_files:
        print("Error: No wheel file generated")
        return False

    if not tar_files:
        print("Error: No source distribution generated")
        return False

    print(f"Built wheel: {wheel_files[0]}")
    print(f"Built source dist: {tar_files[0]}")

    return True


def check_testpypi_token():
    """Check if TestPyPI token is configured."""
    try:
        # Try to check poetry config
        result = run_command(
            ["poetry", "config", "pypi-token.testpypi"],
            check=False,
            capture_output=True,
        )
        if result and result.returncode == 0:
            print("TestPyPI token is configured")
            return True
    except Exception:
        pass

    # Check environment variable
    if os.getenv("POETRY_PYPI_TOKEN_TESTPYPI"):
        print("TestPyPI token found in environment")
        return True

    print("Warning: No TestPyPI token configured")
    print("Set token with: poetry config pypi-token.testpypi <your-token>")
    print("Or set environment variable: POETRY_PYPI_TOKEN_TESTPYPI")
    return False


def publish_to_testpypi():
    """Publish package to TestPyPI."""
    print("Publishing to TestPyPI...")

    # Configure TestPyPI repository if not already configured
    run_command(
        ["poetry", "config", "repositories.testpypi", "https://test.pypi.org/legacy/"],
        check=False,
    )

    # Publish to TestPyPI
    try:
        run_command(
            ["poetry", "publish", "--repository", "testpypi", "--skip-existing"]
        )
        print("Successfully published to TestPyPI!")
        return True
    except Exception as e:
        print(f"Failed to publish to TestPyPI: {e}")
        return False


def verify_testpypi_installation():
    """Verify that package can be installed from TestPyPI."""
    print("Verifying TestPyPI installation...")

    version = get_package_version()
    if not version:
        print("Cannot verify installation without version")
        return False

    print("Waiting for TestPyPI propagation...")
    time.sleep(30)

    # Try to install from TestPyPI
    print(f"Attempting to install mcp-clipboard-server=={version} from TestPyPI...")

    try:
        # Create a temporary virtual environment for testing
        import tempfile
        import venv

        with tempfile.TemporaryDirectory() as temp_dir:
            venv_dir = Path(temp_dir) / "test_venv"

            # Create virtual environment
            venv.create(venv_dir, with_pip=True)

            # Determine pip path
            if sys.platform == "win32":
                pip_path = venv_dir / "Scripts" / "pip.exe"
                python_path = venv_dir / "Scripts" / "python.exe"
            else:
                pip_path = venv_dir / "bin" / "pip"
                python_path = venv_dir / "bin" / "python"

            # Install from TestPyPI
            install_cmd = [
                str(pip_path),
                "install",
                "--index-url",
                "https://test.pypi.org/simple/",
                "--extra-index-url",
                "https://pypi.org/simple/",
                f"mcp-clipboard-server=={version}",
            ]

            result = run_command(install_cmd, check=False)
            if result and result.returncode == 0:
                print("Successfully installed from TestPyPI!")

                # Test CLI
                test_cmd = [str(python_path), "-m", "mcp_clipboard_server", "--help"]
                test_result = run_command(test_cmd, check=False, capture_output=True)
                if test_result and test_result.returncode == 0:
                    print("CLI test passed!")
                    return True
                else:
                    print("CLI test failed")
                    return False
            else:
                print("Installation from TestPyPI failed")
                return False

    except Exception as e:
        print(f"Verification failed: {e}")
        return False


def main():
    """Main function."""
    print("=== MCP Clipboard Server - TestPyPI Publishing Script ===")

    # Change to project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)

    print(f"Working directory: {os.getcwd()}")

    # Check Poetry installation
    try:
        run_command(["poetry", "--version"], capture_output=True)
    except subprocess.CalledProcessError:
        print("Error: Poetry not found. Please install Poetry first.")
        sys.exit(1)

    # Validation phase
    if not validate_package_metadata():
        print("Metadata validation failed")
        sys.exit(1)

    # Build phase
    if not build_package():
        print("Package build failed")
        sys.exit(1)

    # Token check
    if not check_testpypi_token():
        print("Proceeding without token check (may fail during publish)")

    # Publish phase
    if not publish_to_testpypi():
        print("TestPyPI publishing failed")
        sys.exit(1)

    # Verification phase
    if not verify_testpypi_installation():
        print("TestPyPI installation verification failed")
        sys.exit(1)

    print("=== TestPyPI Publishing Complete ===")
    print("Package successfully published and verified on TestPyPI!")
    print("Install with:")
    print(
        f"pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ mcp-clipboard-server=={get_package_version()}"
    )


if __name__ == "__main__":
    main()
