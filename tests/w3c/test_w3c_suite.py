"""W3C XSD Test Suite conformance tests.

Automated test harness for W3C XSD 1.0 test suite.
Target: 60% coverage (must_pass tests) for MVP.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.w3c
@pytest.mark.skip(reason="Parser not yet implemented")
def test_must_pass_suite(w3c_suite_dir: Path, must_pass_tests: list[str]) -> None:
    """Test P0/P1 components (must pass for MVP).

    Target: 60% of total suite (~2100 tests).
    """
    # TODO: Implement when Schema.parse() is ready
    # for test_file in must_pass_tests:
    #     schema_path = w3c_suite_dir / test_file
    #     schema = Schema.parse(schema_path)
    #     assert schema is not None
    pass


@pytest.mark.w3c
@pytest.mark.skip(reason="Parser not yet implemented")
def test_should_pass_suite(w3c_suite_dir: Path, should_pass_tests: list[str]) -> None:
    """Test P2 components (should pass, nice to have).

    Target: Additional ~20% coverage.
    """
    # TODO: Implement when Schema.parse() is ready
    pass


@pytest.mark.w3c
@pytest.mark.skip(reason="Deferred to post-MVP")
def test_deferred_suite(w3c_suite_dir: Path, deferred_tests: list[str]) -> None:
    """Test P3 components (deferred to post-MVP).

    These tests validate identity constraints, notation, redefine.
    """
    pytest.skip("Deferred to post-MVP (identity constraints, notation, redefine)")


def test_suite_available(w3c_suite_dir: Path, test_categories: dict) -> None:
    """Verify W3C test suite is properly set up."""
    assert w3c_suite_dir.exists(), "W3C suite directory not found"

    total_tests = sum(len(cat["tests"]) for cat in test_categories.values())
    must_pass_count = len(test_categories["must_pass"]["tests"])

    print("\nW3C Test Suite Setup:")
    print(f"  Total tests: {total_tests}")
    print(f"  Must pass (MVP): {must_pass_count} ({must_pass_count / total_tests * 100:.1f}%)")
    print(f"  Should pass: {len(test_categories['should_pass']['tests'])}")
    print(f"  Deferred: {len(test_categories['deferred']['tests'])}")

    assert total_tests > 0, "No tests found in suite"
    assert must_pass_count > 0, "No must-pass tests categorized"
