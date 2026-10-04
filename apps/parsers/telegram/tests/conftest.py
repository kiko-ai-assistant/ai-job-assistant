"""Pytest fixtures for telegram parser test suite."""

import json
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to tests/fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_posts(fixtures_dir: Path) -> list[dict[str, Any]]:
    """Load sample posts fixture."""
    posts_path = fixtures_dir / "sample_posts.json"
    with open(posts_path, encoding="utf-8") as f:
        data: list[dict[str, Any]] = json.load(f)
        return data
