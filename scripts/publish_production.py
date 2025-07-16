#!/usr/bin/env python3
"""Production PyPI publishing script with comprehensive validation."""

import os
import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd, check=True, capture_output=False, timeout=300):
    """Run a shell command with error handling and timeout."""
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, check=check, capture_output=capture_output, text=True, timeout=timeout
        )
        if capture_output:
            return result.stdout.strip()
        return result
    except subprocess.TimeoutExpired:
        print(f"Command timed out after {timeout}s")
        if check:
            sys.exit(1)
        return None
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


def validate_version_consistency():
    """Validate version consistency across all files."""
    print("Validating version consistency...")

    version = get_package_version()
    if not version:
        print("Error: Could not determine package version")
        return False

    print(f"Package version: {version}")

    # Check pyproject.toml
    pyproject_file = Path("pyproject.toml")
    if pyproject_file.exists():
        content = pyproject_file.read_text()
        if f'version = "{version}"' not in content:
            print("Error: Version mismatch in pyproject.toml")
            return False
        print("✓ pyproject.toml version matches")

    # Check __init__.py fallback version
    init_file = Path("src/mcp_clipboard_server/__init__.py")
    if init_file.exists():
        content = init_file.read_text()
        expected_fallback = f'__version__ = "{version}-dev"'
        if expected_fallback not in content:
            print("Warning: Fallback version in __init__.py may be outdated")
            print(f"Expected: {expected_fallback}")
        else:
            print("✓ __init__.py fallback version consistent")

    return True


def validate_changelog():
    """Validate that CHANGELOG.md exists and has entry for current version."""
    print("Validating changelog...")

    version = get_package_version()
    changelog_file = Path("CHANGELOG.md")

    if not changelog_file.exists():
        print("Warning: CHANGELOG.md not found")
        return True  # Not critical for publishing

    content = changelog_file.read_text()
    version_patterns = [
        f"## [{version}]",
        f"## [v{version}]",
        f"## {version}",
        f"## v{version}",
    ]

    found_version = any(pattern in content for pattern in version_patterns)
    if found_version:
        print(f"✓ Changelog contains entry for version {version}")
        return True
    else:
        print(f"Warning: No changelog entry found for version {version}")
        return True  # Warning only


def run_comprehensive_tests():
    """Run comprehensive test suite before publishing."""
    print("Running comprehensive test suite...")

    # Run pytest with coverage
    test_cmd = ["poetry", "run", "pytest", "tests/", "-v", "--tb=short"]
    result = run_command(test_cmd, check=False)

    if result.returncode != 0:
        print("Error: Test suite failed")
        return False

    print("✓ All tests passed")
    return True


def validate_package_metadata():
    """Validate package metadata completeness."""
    print("Validating package metadata...")

    # Check that Poetry configuration is valid
    result = run_command(["poetry", "check"], check=False, capture_output=True)
    if result.returncode != 0:
        print(f"Error: Poetry configuration invalid: {result.stdout}")
        return False

    print("✓ Poetry configuration is valid")

    # Check required files exist
    required_files = [
        "README.md",
        "pyproject.toml",
        "src/mcp_clipboard_server/__init__.py",
    ]

    for file_path in required_files:
        if not Path(file_path).exists():
            print(f"Error: Required file missing: {file_path}")
            return False

    print("✓ All required files present")
    return True


def build_and_validate_package():
    """Build package and validate contents."""
    print("Building and validating package...")

    # Clean previous builds
    dist_dir = Path("dist")
    if dist_dir.exists():
        print("Cleaning previous builds...")
        for file in dist_dir.glob("*"):
            file.unlink()

    # Build package
    result = run_command(["poetry", "build"], check=False)
    if result.returncode != 0:
        print("Error: Package build failed")
        return False

    # Verify build outputs
    wheel_files = list(dist_dir.glob("*.whl"))
    tar_files = list(dist_dir.glob("*.tar.gz"))

    if not wheel_files:
        print("Error: No wheel file generated")
        return False

    if not tar_files:
        print("Error: No source distribution generated")
        return False

    print(f"✓ Built wheel: {wheel_files[0]}")
    print(f"✓ Built source dist: {tar_files[0]}")

    # Validate package contents
    version = get_package_version()
    expected_wheel = f"mcp_clipboard_server-{version}-py3-none-any.whl"
    expected_tar = f"mcp_clipboard_server-{version}.tar.gz"

    if wheel_files[0].name != expected_wheel:
        print(f"Warning: Unexpected wheel name: {wheel_files[0].name}")

    if tar_files[0].name != expected_tar:
        print(f"Warning: Unexpected tar name: {tar_files[0].name}")

    return True


def check_pypi_token():
    """Check if PyPI token is configured."""
    print("Checking PyPI token configuration...")

    try:
        # Try to check poetry config
        result = run_command(
            ["poetry", "config", "pypi-token.pypi"], check=False, capture_output=True
        )
        if result and result.returncode == 0 and result.stdout.strip():
            print("✓ PyPI token is configured")
            return True
    except Exception:
        pass

    # Check environment variable
    if os.getenv("POETRY_PYPI_TOKEN_PYPI"):
        print("✓ PyPI token found in environment")
        return True

    print("Error: No PyPI token configured")
    print("Set token with: poetry config pypi-token.pypi <your-token>")
    print("Or set environment variable: POETRY_PYPI_TOKEN_PYPI")
    return False


def check_package_availability():
    """Check if package name and version are available on PyPI."""
    print("Checking package availability on PyPI...")

    version = get_package_version()

    # Try to get package info from PyPI
    try:
        import requests

        response = requests.get(
            f"https://pypi.org/pypi/mcp-clipboardify/{version}/json", timeout=10
        )
        if response.status_code == 200:
            print(f"Error: Version {version} already exists on PyPI")
            return False
        elif response.status_code == 404:
            print(f"✓ Version {version} is available for publishing")
            return True
        else:
            print(
                f"Warning: Could not check PyPI availability (status: {response.status_code})"
            )
            return True  # Proceed anyway
    except ImportError:
        print("Warning: requests not available, skipping PyPI availability check")
        return True
    except Exception as e:
        print(f"Warning: Could not check PyPI availability: {e}")
        return True


def publish_to_pypi():
    """Publish package to production PyPI."""
    print("Publishing to production PyPI...")

    try:
        # Publish with retries
        max_retries = 3
        for attempt in range(max_retries):
            print(f"Publishing attempt {attempt + 1}/{max_retries}")

            result = run_command(
                ["poetry", "publish", "--no-interaction"], check=False, timeout=300
            )

            if result.returncode == 0:
                print("✓ Successfully published to PyPI!")
                return True
            elif "already exists" in str(result.stderr):
                print("Error: Version already exists on PyPI")
                return False
            else:
                print(f"Publish attempt {attempt + 1} failed")
                if attempt < max_retries - 1:
                    print("Retrying in 30 seconds...")
                    time.sleep(30)

        print("Error: Failed to publish after all retries")
        return False

    except Exception as e:
        print(f"Error during publishing: {e}")
        return False


def verify_pypi_installation():
    """Verify package can be installed from PyPI."""
    print("Verifying PyPI installation...")

    version = get_package_version()

    print("Waiting for PyPI propagation...")
    time.sleep(60)  # Wait for PyPI to propagate

    # Test installation in clean environment
    try:
        import tempfile
        import venv

        with tempfile.TemporaryDirectory() as temp_dir:
            venv_dir = Path(temp_dir) / "test_venv"

            # Create virtual environment
            print("Creating test virtual environment...")
            venv.create(venv_dir, with_pip=True)

            # Determine paths
            if sys.platform == "win32":
                pip_path = venv_dir / "Scripts" / "pip.exe"
                python_path = venv_dir / "Scripts" / "python.exe"
            else:
                pip_path = venv_dir / "bin" / "pip"
                python_path = venv_dir / "bin" / "python"

            # Install from PyPI
            print(f"Installing mcp-clipboardify=={version} from PyPI...")
            install_cmd = [
                str(pip_path),
                "install",
                f"mcp-clipboardify=={version}",
                "--no-cache-dir",
            ]

            result = run_command(install_cmd, check=False, timeout=300)
            if result.returncode != 0:
                print("Error: Installation from PyPI failed")
                return False

            # Test CLI
            print("Testing CLI entry point...")
            test_cmd = [str(python_path), "-m", "mcp_clipboard_server", "--help"]
            test_result = run_command(
                test_cmd, check=False, capture_output=True, timeout=30
            )

            if test_result.returncode != 0:
                print("Error: CLI test failed")
                return False

            print("✓ Installation and CLI test successful!")
            return True

    except Exception as e:
        print(f"Error during installation verification: {e}")
        return False


def main():
    """Main publishing function."""
    print("=== MCP Clipboard Server - Production PyPI Publishing ===")

    # Change to project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)

    print(f"Working directory: {os.getcwd()}")

    # Check Poetry installation
    try:
        run_command(["poetry", "--version"], capture_output=True)
        print("✓ Poetry is available")
    except subprocess.CalledProcessError:
        print("Error: Poetry not found. Please install Poetry first.")
        sys.exit(1)

    # Pre-flight checks
    checks = [
        ("Version Consistency", validate_version_consistency),
        ("Package Metadata", validate_package_metadata),
        ("Changelog", validate_changelog),
        ("Comprehensive Tests", run_comprehensive_tests),
        ("Package Build", build_and_validate_package),
        ("PyPI Token", check_pypi_token),
        ("Package Availability", check_package_availability),
    ]

    print("\n=== Pre-flight Checks ===")
    for check_name, check_func in checks:
        print(f"\n{check_name}...")
        if not check_func():
            print(f"❌ {check_name} failed")
            sys.exit(1)
        print(f"✅ {check_name} passed")

    # Final confirmation
    version = get_package_version()
    print("\n=== Ready to Publish ===")
    print("Package: mcp-clipboardify")
    print(f"Version: {version}")
    print("Target: https://pypi.org/")

    response = input("\nProceed with production publishing? [y/N]: ")
    if response.lower() not in ["y", "yes"]:
        print("Publishing cancelled by user")
        sys.exit(0)

    # Publish to PyPI
    print("\n=== Publishing to PyPI ===")
    if not publish_to_pypi():
        print("❌ Publishing failed")
        sys.exit(1)

    # Verify installation
    print("\n=== Verifying Installation ===")
    if not verify_pypi_installation():
        print("❌ Installation verification failed")
        print("Package was published but may have issues")
        sys.exit(1)

    print("\n=== Publishing Complete ===")
    print(f"✅ Successfully published mcp-clipboardify {version} to PyPI!")
    print(f"📦 Install with: pip install mcp-clipboardify=={version}")
    print(f"🔗 Package URL: https://pypi.org/project/mcp-clipboardify/{version}/")

    # Cleanup
    response = input("\nClean up build artifacts? [Y/n]: ")
    if response.lower() not in ["n", "no"]:
        dist_dir = Path("dist")
        if dist_dir.exists():
            for file in dist_dir.glob("*"):
                file.unlink()
            print("✓ Build artifacts cleaned up")


if __name__ == "__main__":
    main()
