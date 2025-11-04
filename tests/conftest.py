"""
Shared pytest fixtures for FastAPI app testing.
Ensures all tests can reuse the same TestClient instance.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

from app import app  # Import FastAPI instance from app.py

@pytest.fixture(scope="session")
def client():
    """Provides a reusable FastAPI test client."""
    return TestClient(app)