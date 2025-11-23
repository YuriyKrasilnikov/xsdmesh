"""Pytest configuration for W3C test suite."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator


@pytest.fixture(scope="session")
def w3c_suite_dir() -> Path:
    """Return path to W3C test suite."""
    suite_dir = Path(__file__).parent / "suite" / "xsd10"
    if not suite_dir.exists():
        pytest.skip(
            "W3C test suite not found. Run: python scripts/download_w3c_suite.py"
        )
    return suite_dir


@pytest.fixture(scope="session")
def test_categories(w3c_suite_dir: Path) -> dict[str, dict]:
    """Load test categorization."""
    categories_file = w3c_suite_dir.parent / "xsd10_categories.json"
    if not categories_file.exists():
        pytest.skip("Test categories not found. Run download script with categorization.")

    with categories_file.open() as f:
        return json.load(f)


@pytest.fixture
def must_pass_tests(test_categories: dict[str, dict]) -> list[str]:
    """P0/P1 tests that must pass for MVP."""
    return test_categories["must_pass"]["tests"]


@pytest.fixture
def should_pass_tests(test_categories: dict[str, dict]) -> list[str]:
    """P2 tests that should pass."""
    return test_categories["should_pass"]["tests"]


@pytest.fixture
def deferred_tests(test_categories: dict[str, dict]) -> list[str]:
    """P3 tests deferred to post-MVP."""
    return test_categories["deferred"]["tests"]
