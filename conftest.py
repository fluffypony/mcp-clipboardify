"""Global pytest configuration for clipboard tests."""


def pytest_configure(config):
    """Configure pytest to handle serial markers correctly."""
    # Register the serial marker
    config.addinivalue_line(
        "markers", "serial: mark test to run serially (not in parallel)"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test items to ensure serial tests run without conflicts."""
    # When running with pytest-xdist, warn about clipboard test conflicts
    # The serial marker helps identify tests that may conflict in parallel
    pass  # Serial marker is now mainly for documentation/identification
