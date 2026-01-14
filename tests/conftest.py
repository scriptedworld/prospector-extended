"""Pytest configuration and fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the fixtures directory."""
    return Path(__file__).parent / "fixtures_exempt"


@pytest.fixture
def clean_file(fixtures_dir: Path) -> Path:
    """Return path to clean.py fixture."""
    return fixtures_dir / "clean.py"


@pytest.fixture
def type_errors_file(fixtures_dir: Path) -> Path:
    """Return path to type_errors.py fixture."""
    return fixtures_dir / "type_errors.py"


@pytest.fixture
def high_complexity_file(fixtures_dir: Path) -> Path:
    """Return path to high_complexity.py fixture."""
    return fixtures_dir / "high_complexity.py"


@pytest.fixture
def missing_docstrings_file(fixtures_dir: Path) -> Path:
    """Return path to missing_docstrings.py fixture."""
    return fixtures_dir / "missing_docstrings.py"
