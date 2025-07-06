"""
Pytest configuration and shared fixtures for the bookcast tests.
"""

import sys
from pathlib import Path

# Add src to path for imports
repo_root = Path(__file__).parent.parent
src_path = repo_root / "src"
sys.path.insert(0, str(src_path))

import pytest

from bookcast.services import initialize_service_manager


@pytest.fixture(scope="session")
def service_manager():
    """Create a service manager for testing."""
    return initialize_service_manager()


@pytest.fixture
def sample_filename():
    """Sample PDF filename for testing."""
    return "2506.05345.pdf"


@pytest.fixture
def sample_max_pages():
    """Sample max page number for testing."""
    return 23


@pytest.fixture
def clean_session(service_manager):
    """Provide a clean session state for testing."""
    # This fixture would be useful if we had session cleanup methods
    # For now, we just return the service manager
    return service_manager
