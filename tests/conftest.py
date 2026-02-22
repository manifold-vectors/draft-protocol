"""Pytest configuration for draft-protocol tests."""

import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: requires live services")
    config.addinivalue_line("markers", "slow: long-running tests")
