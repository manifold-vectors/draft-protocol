"""Pytest configuration for draft-protocol tests."""


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: requires live services")
    config.addinivalue_line("markers", "slow: long-running tests")
