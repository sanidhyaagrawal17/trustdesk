"""Pytest configuration and fixtures for TrustDesk test suite.
Technical demonstration on synthetic data - not a regulated banking system.
"""

import os
import sys
from pathlib import Path
import pytest

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Load telemetry shim early
import backend.core.telemetry_shim  # noqa: F401


@pytest.fixture
def anyio_backend():
    return "asyncio"
