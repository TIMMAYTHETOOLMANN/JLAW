"""
Conftest for integration tests.

This separate conftest is used for integration tests to avoid
dependencies on the agents module which may not be installed.
The integration tests can be run directly from the tests/integration directory.
"""

import pytest
import os
import sys

# Ensure the src directory is in the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Set default OpenAI API key if not present (for tests that may need it)
if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = "test_key"


# Override the fixtures from parent conftest that may cause import errors
@pytest.fixture(scope="session")
def integration_test_session():
    """Session-level fixture for integration tests."""
    yield


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for test files."""
    return tmp_path


# Skip OpenAI-related fixtures
@pytest.fixture(autouse=True)
def skip_openai_fixtures():
    """Skip OpenAI-related fixtures for integration tests."""
    pass
