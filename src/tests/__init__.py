# src/tests/__init__.py
"""
Test Package

This package contains all tests for the my_bot_project application.
Tests are organized into three categories:
- unit/: Unit tests for individual components
- integration/: Integration tests for component interactions
- e2e/: End-to-end tests for complete user flows

Usage:
    pytest tests/
    pytest tests/unit/
    pytest tests/integration/
    pytest tests/e2e/
"""

# Common test utilities can be imported here if needed
# from .conftest import pytest_configure, pytest_collection_modifyitems

__version__ = "1.0.0"

# Define what's exported when using "from tests import *"
__all__ = [
    # Add common test utilities here as needed
]