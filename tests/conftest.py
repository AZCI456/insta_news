"""
Shared pytest configuration.

Teaching note:
- `main.py` reads `insta_news_db_path` at import time and exits if it is missing.
  Tests must set that environment variable *before* importing `src.web.main`.
- We use a temporary SQLite file (not `:memory:`) so PRAGMA journal_mode=WAL behaves
  like a normal file-backed DB.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

_fd, _TEST_DB_PATH = tempfile.mkstemp(suffix=".sqlite")
os.close(_fd)
os.environ["insta_news_db_path"] = _TEST_DB_PATH

from fastapi.testclient import TestClient  # noqa: E402  (import after env)

from src.web.main import app  # noqa: E402


def pytest_sessionfinish(session, exitstatus):
    try:
        Path(_TEST_DB_PATH).unlink(missing_ok=True)
    except OSError:
        pass


@pytest.fixture
def client() -> TestClient:
    """In-process HTTP client; no real network."""
    return TestClient(app)
