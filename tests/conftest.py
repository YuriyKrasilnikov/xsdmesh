"""Pytest configuration and shared fixtures."""

from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def simple_fixtures(fixtures_dir: Path) -> Path:
    """Return path to simple XSD fixtures."""
    return fixtures_dir / "simple"


@pytest.fixture
def complex_fixtures(fixtures_dir: Path) -> Path:
    """Return path to complex XSD fixtures."""
    return fixtures_dir / "complex"


@pytest.fixture
def xsd11_fixtures(fixtures_dir: Path) -> Path:
    """Return path to XSD 1.1 specific fixtures."""
    return fixtures_dir / "xsd11"
