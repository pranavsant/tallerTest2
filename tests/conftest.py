"""
Pytest configuration and shared fixtures.
"""
import pytest


# Configure asyncio mode for all tests
def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (require DB)"
    )
