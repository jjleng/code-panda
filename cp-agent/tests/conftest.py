"""Test configuration."""

import os

import pytest


@pytest.fixture(autouse=True)
def set_test_environment() -> None:
    """Ensure all tests use the development environment."""
    os.environ["ENV"] = "development"
