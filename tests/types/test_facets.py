"""Tests for types/facets.py: XSD Facet validators.

Tests cover:
- Whitespace normalization (preserve, replace, collapse)
- Lexical facets: pattern, enumeration, length
- Value facets: range (min/max), digits (total/fraction)
- Orchestrators: LexicalFacets, ValueFacets, FacetValidator
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from xsdmesh.types.facets import (
    DigitsFacet,
    EnumerationFacet,
    FacetResult,
    FacetValidator,
    LengthFacet,
    LexicalFacets,
    PatternFacet,
    RangeFacet,
    ValueFacets,
    WhitespaceFacet,
)

# =============================================================================
# FacetResult Tests
# =============================================================================


class TestFacetResult:
    """Tests for FacetResult dataclass."""

    def test_ok(self) -> None:
        """Test successful result."""
        result = FacetResult.ok()
        assert result.valid is True
        assert result.error is None

    def test_fail_with_message(self) -> None:
        """Test failed result with message."""
        result = FacetResult.fail("Value too short")
        assert result.valid is False
        assert result.error is not None
        assert "Value too short" in str(result.error)

    def test_fail_with_code(self) -> None:
        """Test failed result with error code."""
        result = FacetResult.fail("Invalid", code="cvc-test")
        assert result.valid is False
        assert result.error is not None
        assert result.error.code == "cvc-test"

    def test_frozen(self) -> None:
        """Test FacetResult is immutable."""
        result = FacetResult.ok()
        with pytest.raises(AttributeError):
            result.valid = False  # type: ignore[misc]


# =============================================================================
# WhitespaceFacet Tests
# =============================================================================


class TestWhitespaceFacet:
    """Tests for WhitespaceFacet normalization."""

    def test_preserve_keeps_all(self) -> None:
        """Test preserve mode keeps all whitespace."""
        value = "  hello\t\nworld  "
        result = WhitespaceFacet.normalize(value, "preserve")
        assert result == "  hello\t\nworld  "

    def test_replace_tabs_and_newlines(self) -> None:
        """Test replace mode converts tabs/newlines to spaces."""
        value = "hello\tworld\ntest\rfoo"
        result = WhitespaceFacet.normalize(value, "replace")
        assert result == "hello world test foo"

    def test_replace_keeps_multiple_spaces(self) -> None:
        """Test replace mode keeps multiple consecutive spaces."""
        value = "hello  world"
        result = WhitespaceFacet.normalize(value, "replace")
        assert result == "hello  world"

    def test_collapse_removes_consecutive_spaces(self) -> None:
        """Test collapse mode removes consecutive spaces."""
        value = "hello   world"
        result = WhitespaceFacet.normalize(value, "collapse")
        assert result == "hello world"

    def test_collapse_strips_leading_trailing(self) -> None:
        """Test collapse mode strips leading/trailing whitespace."""
        value = "  hello world  "
        result = WhitespaceFacet.normalize(value, "collapse")
        assert result == "hello world"

    def test_collapse_full_normalization(self) -> None:
        """Test collapse with mixed whitespace."""
        value = "  hello\t\n  world   test  "
        result = WhitespaceFacet.normalize(value, "collapse")
        assert result == "hello world test"

    def test_unknown_mode_preserves(self) -> None:
        """Test unknown mode defaults to preserve."""
        value = "hello\tworld"
        result = WhitespaceFacet.normalize(value, "unknown")
        assert result == "hello\tworld"

    def test_empty_string(self) -> None:
        """Test normalization of empty string."""
        assert WhitespaceFacet.normalize("", "preserve") == ""
        assert WhitespaceFacet.normalize("", "replace") == ""
        assert WhitespaceFacet.normalize("", "collapse") == ""

    def test_only_whitespace_collapse(self) -> None:
        """Test collapse on string with only whitespace."""
        value = "   \t\n   "
        result = WhitespaceFacet.normalize(value, "collapse")
        assert result == ""


# =============================================================================
# PatternFacet Tests
# =============================================================================


class TestPatternFacet:
    """Tests for PatternFacet regex validation."""

    def test_simple_pattern_match(self) -> None:
        """Test simple pattern matches."""
        result = PatternFacet.validate(r"\d+", "123")
        assert result.valid is True

    def test_simple_pattern_no_match(self) -> None:
        """Test simple pattern fails."""
        result = PatternFacet.validate(r"\d+", "abc")
        assert result.valid is False
        assert result.error is not None
        assert "cvc-pattern-valid" == result.error.code

    def test_fullmatch_required(self) -> None:
        """Test pattern must match entire string (fullmatch)."""
        result = PatternFacet.validate(r"\d+", "123abc")
        assert result.valid is False

    def test_multiple_patterns_or_logic(self) -> None:
        """Test multiple patterns use OR logic."""
        patterns = [r"\d+", r"[a-z]+"]
        assert PatternFacet.validate(patterns, "123").valid is True
        assert PatternFacet.validate(patterns, "abc").valid is True
        assert PatternFacet.validate(patterns, "ABC").valid is False

    def test_single_pattern_as_string(self) -> None:
        """Test single pattern can be passed as string."""
        result = PatternFacet.validate(r"[a-z]+", "hello")
        assert result.valid is True

    def test_empty_patterns_always_valid(self) -> None:
        """Test empty pattern list always passes."""
        result = PatternFacet.validate([], "anything")
        assert result.valid is True

    def test_invalid_regex_pattern(self) -> None:
        """Test invalid regex pattern returns error."""
        result = PatternFacet.validate(r"[invalid", "test")
        assert result.valid is False
        assert result.error is not None
        assert "pattern-invalid" == result.error.code

    def test_email_pattern(self) -> None:
        """Test realistic email pattern."""
        pattern = r"[^@]+@[^@]+\.[^@]+"
        assert PatternFacet.validate(pattern, "test@example.com").valid is True
        assert PatternFacet.validate(pattern, "invalid").valid is False

    def test_pattern_cache(self) -> None:
        """Test pattern compilation is cached."""
        PatternFacet.clear_cache()
        PatternFacet.validate(r"\d+", "123")
        PatternFacet.validate(r"\d+", "456")
        # Same pattern should be in cache
        assert r"\d+" in PatternFacet._cache

    def test_clear_cache(self) -> None:
        """Test cache clearing."""
        PatternFacet.validate(r"\d+", "123")
        PatternFacet.clear_cache()
        assert len(PatternFacet._cache) == 0


# =============================================================================
# EnumerationFacet Tests
# =============================================================================


class TestEnumerationFacet:
    """Tests for EnumerationFacet validation."""

    def test_value_in_enum(self) -> None:
        """Test value in enumeration passes."""
        result = EnumerationFacet.validate(["red", "green", "blue"], "green")
        assert result.valid is True

    def test_value_not_in_enum(self) -> None:
        """Test value not in enumeration fails."""
        result = EnumerationFacet.validate(["red", "green", "blue"], "yellow")
        assert result.valid is False
        assert result.error is not None
        assert "cvc-enumeration-valid" == result.error.code

    def test_empty_enum_always_valid(self) -> None:
        """Test empty enumeration always passes."""
        result = EnumerationFacet.validate([], "anything")
        assert result.valid is True

    def test_case_sensitive(self) -> None:
        """Test enumeration is case-sensitive."""
        result = EnumerationFacet.validate(["Red"], "red")
        assert result.valid is False

    def test_error_message_shows_values(self) -> None:
        """Test error message shows enumeration values (<=5)."""
        result = EnumerationFacet.validate(["a", "b", "c"], "x")
        assert result.error is not None
        assert "'a'" in str(result.error)
        assert "'b'" in str(result.error)

    def test_error_message_many_values(self) -> None:
        """Test error message for >5 values shows count."""
        result = EnumerationFacet.validate(["a", "b", "c", "d", "e", "f"], "x")
        assert result.error is not None
        assert "6 values" in str(result.error)

    def test_whitespace_values(self) -> None:
        """Test enumeration with whitespace values."""
        result = EnumerationFacet.validate(["hello world", "foo bar"], "hello world")
        assert result.valid is True


# =============================================================================
# LengthFacet Tests
# =============================================================================


class TestLengthFacet:
    """Tests for LengthFacet validation."""

    def test_exact_length_valid(self) -> None:
        """Test exact length matches."""
        result = LengthFacet.validate_length(5, "hello")
        assert result.valid is True

    def test_exact_length_invalid(self) -> None:
        """Test exact length mismatch."""
        result = LengthFacet.validate_length(5, "hi")
        assert result.valid is False
        assert "cvc-length-valid" == result.error.code  # type: ignore[union-attr]

    def test_min_length_valid(self) -> None:
        """Test minLength satisfied."""
        result = LengthFacet.validate_min_length(3, "hello")
        assert result.valid is True

    def test_min_length_exact(self) -> None:
        """Test minLength exact boundary."""
        result = LengthFacet.validate_min_length(5, "hello")
        assert result.valid is True

    def test_min_length_invalid(self) -> None:
        """Test minLength violated."""
        result = LengthFacet.validate_min_length(10, "hello")
        assert result.valid is False
        assert "cvc-minLength-valid" == result.error.code  # type: ignore[union-attr]

    def test_max_length_valid(self) -> None:
        """Test maxLength satisfied."""
        result = LengthFacet.validate_max_length(10, "hello")
        assert result.valid is True

    def test_max_length_exact(self) -> None:
        """Test maxLength exact boundary."""
        result = LengthFacet.validate_max_length(5, "hello")
        assert result.valid is True

    def test_max_length_invalid(self) -> None:
        """Test maxLength violated."""
        result = LengthFacet.validate_max_length(3, "hello")
        assert result.valid is False
        assert "cvc-maxLength-valid" == result.error.code  # type: ignore[union-attr]

    def test_empty_string(self) -> None:
        """Test length facets with empty string."""
        assert LengthFacet.validate_length(0, "").valid is True
        assert LengthFacet.validate_min_length(0, "").valid is True
        assert LengthFacet.validate_max_length(0, "").valid is True

    def test_unicode_characters(self) -> None:
        """Test length counts Unicode characters correctly."""
        # "привет" is 6 characters
        result = LengthFacet.validate_length(6, "привет")
        assert result.valid is True


# =============================================================================
# LexicalFacets Orchestrator Tests
# =============================================================================


class TestLexicalFacets:
    """Tests for LexicalFacets orchestrator."""

    def test_no_facets_valid(self) -> None:
        """Test empty facets always passes."""
        errors = LexicalFacets.check_all({}, "anything")
        assert errors == []

    def test_pattern_facet(self) -> None:
        """Test pattern facet through orchestrator."""
        facets: dict[str, str | list[str] | int] = {"pattern": r"\d+"}
        assert LexicalFacets.check_all(facets, "123") == []
        assert len(LexicalFacets.check_all(facets, "abc")) == 1

    def test_pattern_list(self) -> None:
        """Test multiple patterns through orchestrator."""
        facets: dict[str, str | list[str] | int] = {"pattern": [r"\d+", r"[a-z]+"]}
        assert LexicalFacets.check_all(facets, "123") == []
        assert LexicalFacets.check_all(facets, "abc") == []
        assert len(LexicalFacets.check_all(facets, "ABC")) == 1

    def test_enumeration_facet(self) -> None:
        """Test enumeration facet through orchestrator."""
        facets: dict[str, str | list[str] | int] = {"enumeration": ["red", "green", "blue"]}
        assert LexicalFacets.check_all(facets, "red") == []
        assert len(LexicalFacets.check_all(facets, "yellow")) == 1

    def test_length_facet(self) -> None:
        """Test length facet through orchestrator."""
        facets: dict[str, str | list[str] | int] = {"length": 5}
        assert LexicalFacets.check_all(facets, "hello") == []
        assert len(LexicalFacets.check_all(facets, "hi")) == 1

    def test_min_length_facet(self) -> None:
        """Test minLength facet through orchestrator."""
        facets: dict[str, str | list[str] | int] = {"minLength": 3}
        assert LexicalFacets.check_all(facets, "hello") == []
        assert len(LexicalFacets.check_all(facets, "hi")) == 1

    def test_max_length_facet(self) -> None:
        """Test maxLength facet through orchestrator."""
        facets: dict[str, str | list[str] | int] = {"maxLength": 3}
        assert LexicalFacets.check_all(facets, "hi") == []
        assert len(LexicalFacets.check_all(facets, "hello")) == 1

    def test_multiple_facets(self) -> None:
        """Test multiple facets combined."""
        facets: dict[str, str | list[str] | int] = {
            "pattern": r"[a-z]+",
            "minLength": 2,
            "maxLength": 5,
        }
        assert LexicalFacets.check_all(facets, "abc") == []
        # Too short
        assert len(LexicalFacets.check_all(facets, "a")) == 1
        # Too long
        assert len(LexicalFacets.check_all(facets, "abcdef")) == 1
        # Wrong pattern
        assert len(LexicalFacets.check_all(facets, "123")) == 1

    def test_multiple_failures(self) -> None:
        """Test multiple facets can fail together."""
        facets: dict[str, str | list[str] | int] = {
            "pattern": r"[a-z]+",
            "maxLength": 3,
        }
        # Both pattern and maxLength fail
        errors = LexicalFacets.check_all(facets, "12345")
        assert len(errors) == 2

    def test_length_as_string(self) -> None:
        """Test length facets accept string values."""
        facets: dict[str, str | list[str] | int] = {"length": "5"}
        assert LexicalFacets.check_all(facets, "hello") == []


# =============================================================================
# RangeFacet Tests
# =============================================================================


class TestRangeFacet:
    """Tests for RangeFacet validation."""

    def test_min_inclusive_valid(self) -> None:
        """Test minInclusive satisfied."""
        result = RangeFacet.validate_min_inclusive(Decimal("10"), Decimal("15"))
        assert result.valid is True

    def test_min_inclusive_boundary(self) -> None:
        """Test minInclusive at boundary."""
        result = RangeFacet.validate_min_inclusive(Decimal("10"), Decimal("10"))
        assert result.valid is True

    def test_min_inclusive_invalid(self) -> None:
        """Test minInclusive violated."""
        result = RangeFacet.validate_min_inclusive(Decimal("10"), Decimal("5"))
        assert result.valid is False
        assert "cvc-minInclusive-valid" == result.error.code  # type: ignore[union-attr]

    def test_max_inclusive_valid(self) -> None:
        """Test maxInclusive satisfied."""
        result = RangeFacet.validate_max_inclusive(Decimal("100"), Decimal("50"))
        assert result.valid is True

    def test_max_inclusive_boundary(self) -> None:
        """Test maxInclusive at boundary."""
        result = RangeFacet.validate_max_inclusive(Decimal("100"), Decimal("100"))
        assert result.valid is True

    def test_max_inclusive_invalid(self) -> None:
        """Test maxInclusive violated."""
        result = RangeFacet.validate_max_inclusive(Decimal("100"), Decimal("150"))
        assert result.valid is False
        assert "cvc-maxInclusive-valid" == result.error.code  # type: ignore[union-attr]

    def test_min_exclusive_valid(self) -> None:
        """Test minExclusive satisfied."""
        result = RangeFacet.validate_min_exclusive(Decimal("10"), Decimal("15"))
        assert result.valid is True

    def test_min_exclusive_boundary_invalid(self) -> None:
        """Test minExclusive at boundary (should fail)."""
        result = RangeFacet.validate_min_exclusive(Decimal("10"), Decimal("10"))
        assert result.valid is False
        assert "cvc-minExclusive-valid" == result.error.code  # type: ignore[union-attr]

    def test_max_exclusive_valid(self) -> None:
        """Test maxExclusive satisfied."""
        result = RangeFacet.validate_max_exclusive(Decimal("100"), Decimal("50"))
        assert result.valid is True

    def test_max_exclusive_boundary_invalid(self) -> None:
        """Test maxExclusive at boundary (should fail)."""
        result = RangeFacet.validate_max_exclusive(Decimal("100"), Decimal("100"))
        assert result.valid is False
        assert "cvc-maxExclusive-valid" == result.error.code  # type: ignore[union-attr]

    def test_negative_values(self) -> None:
        """Test range facets with negative values."""
        result = RangeFacet.validate_min_inclusive(Decimal("-100"), Decimal("-50"))
        assert result.valid is True

    def test_decimal_precision(self) -> None:
        """Test range facets with decimal precision."""
        result = RangeFacet.validate_max_inclusive(Decimal("10.5"), Decimal("10.50"))
        assert result.valid is True


# =============================================================================
# DigitsFacet Tests
# =============================================================================


class TestDigitsFacet:
    """Tests for DigitsFacet validation."""

    def test_total_digits_valid(self) -> None:
        """Test totalDigits satisfied."""
        result = DigitsFacet.validate_total_digits(5, Decimal("12345"))
        assert result.valid is True

    def test_total_digits_less_than_max(self) -> None:
        """Test totalDigits with fewer digits."""
        result = DigitsFacet.validate_total_digits(5, Decimal("123"))
        assert result.valid is True

    def test_total_digits_invalid(self) -> None:
        """Test totalDigits exceeded."""
        result = DigitsFacet.validate_total_digits(3, Decimal("12345"))
        assert result.valid is False
        assert "cvc-totalDigits-valid" == result.error.code  # type: ignore[union-attr]

    def test_total_digits_with_decimal(self) -> None:
        """Test totalDigits counts all digits including fraction."""
        # 123.45 has 5 digits total
        result = DigitsFacet.validate_total_digits(5, Decimal("123.45"))
        assert result.valid is True

    def test_fraction_digits_valid(self) -> None:
        """Test fractionDigits satisfied."""
        result = DigitsFacet.validate_fraction_digits(2, Decimal("123.45"))
        assert result.valid is True

    def test_fraction_digits_fewer(self) -> None:
        """Test fractionDigits with fewer fraction digits."""
        result = DigitsFacet.validate_fraction_digits(3, Decimal("123.4"))
        assert result.valid is True

    def test_fraction_digits_invalid(self) -> None:
        """Test fractionDigits exceeded."""
        result = DigitsFacet.validate_fraction_digits(2, Decimal("123.456"))
        assert result.valid is False
        assert "cvc-fractionDigits-valid" == result.error.code  # type: ignore[union-attr]

    def test_fraction_digits_integer(self) -> None:
        """Test fractionDigits with integer value."""
        result = DigitsFacet.validate_fraction_digits(0, Decimal("123"))
        assert result.valid is True

    def test_fraction_digits_zero_allowed(self) -> None:
        """Test fractionDigits=0 allows integers only."""
        assert DigitsFacet.validate_fraction_digits(0, Decimal("123")).valid is True
        assert DigitsFacet.validate_fraction_digits(0, Decimal("123.4")).valid is False


# =============================================================================
# ValueFacets Orchestrator Tests
# =============================================================================


class TestValueFacets:
    """Tests for ValueFacets orchestrator."""

    def test_no_facets_valid(self) -> None:
        """Test empty facets always passes."""
        errors = ValueFacets.check_all({}, Decimal("123"))
        assert errors == []

    def test_min_inclusive(self) -> None:
        """Test minInclusive through orchestrator."""
        facets: dict[str, str | int] = {"minInclusive": "10"}
        assert ValueFacets.check_all(facets, Decimal("15")) == []
        assert len(ValueFacets.check_all(facets, Decimal("5"))) == 1

    def test_max_inclusive(self) -> None:
        """Test maxInclusive through orchestrator."""
        facets: dict[str, str | int] = {"maxInclusive": "100"}
        assert ValueFacets.check_all(facets, Decimal("50")) == []
        assert len(ValueFacets.check_all(facets, Decimal("150"))) == 1

    def test_min_exclusive(self) -> None:
        """Test minExclusive through orchestrator."""
        facets: dict[str, str | int] = {"minExclusive": "10"}
        assert ValueFacets.check_all(facets, Decimal("15")) == []
        assert len(ValueFacets.check_all(facets, Decimal("10"))) == 1

    def test_max_exclusive(self) -> None:
        """Test maxExclusive through orchestrator."""
        facets: dict[str, str | int] = {"maxExclusive": "100"}
        assert ValueFacets.check_all(facets, Decimal("50")) == []
        assert len(ValueFacets.check_all(facets, Decimal("100"))) == 1

    def test_total_digits(self) -> None:
        """Test totalDigits through orchestrator."""
        facets: dict[str, str | int] = {"totalDigits": 3}
        assert ValueFacets.check_all(facets, Decimal("123")) == []
        assert len(ValueFacets.check_all(facets, Decimal("12345"))) == 1

    def test_fraction_digits(self) -> None:
        """Test fractionDigits through orchestrator."""
        facets: dict[str, str | int] = {"fractionDigits": 2}
        assert ValueFacets.check_all(facets, Decimal("1.23")) == []
        assert len(ValueFacets.check_all(facets, Decimal("1.234"))) == 1

    def test_multiple_facets(self) -> None:
        """Test multiple value facets combined."""
        facets: dict[str, str | int] = {
            "minInclusive": "0",
            "maxInclusive": "100",
            "totalDigits": 3,
        }
        assert ValueFacets.check_all(facets, Decimal("50")) == []
        assert len(ValueFacets.check_all(facets, Decimal("-10"))) == 1
        assert len(ValueFacets.check_all(facets, Decimal("1000"))) >= 1

    def test_multiple_failures(self) -> None:
        """Test multiple value facets can fail together."""
        facets: dict[str, str | int] = {
            "minInclusive": "100",
            "maxInclusive": "50",  # Impossible range
        }
        errors = ValueFacets.check_all(facets, Decimal("75"))
        # Both should fail
        assert len(errors) == 2

    def test_range_with_decimals(self) -> None:
        """Test range facets with decimal string values."""
        facets: dict[str, str | int] = {
            "minInclusive": "10.5",
            "maxInclusive": "20.5",
        }
        assert ValueFacets.check_all(facets, Decimal("15")) == []
        assert len(ValueFacets.check_all(facets, Decimal("10"))) == 1


# =============================================================================
# FacetValidator Unified Tests
# =============================================================================


class TestFacetValidator:
    """Tests for FacetValidator unified interface."""

    def test_check_lexical(self) -> None:
        """Test check_lexical delegates correctly."""
        facets: dict[str, str | list[str] | int] = {"pattern": r"\d+"}
        assert FacetValidator.check_lexical(facets, "123") == []
        assert len(FacetValidator.check_lexical(facets, "abc")) == 1

    def test_check_value(self) -> None:
        """Test check_value delegates correctly."""
        facets: dict[str, str | int] = {"minInclusive": "10"}
        assert FacetValidator.check_value(facets, Decimal("15")) == []
        assert len(FacetValidator.check_value(facets, Decimal("5"))) == 1

    def test_normalize_whitespace_preserve(self) -> None:
        """Test normalize_whitespace with preserve."""
        facets = {"whiteSpace": "preserve"}
        result = FacetValidator.normalize_whitespace("  hello  ", facets)
        assert result == "  hello  "

    def test_normalize_whitespace_collapse(self) -> None:
        """Test normalize_whitespace with collapse."""
        facets = {"whiteSpace": "collapse"}
        result = FacetValidator.normalize_whitespace("  hello  world  ", facets)
        assert result == "hello world"

    def test_normalize_whitespace_default(self) -> None:
        """Test normalize_whitespace defaults to preserve."""
        result = FacetValidator.normalize_whitespace("  hello  ", {})
        assert result == "  hello  "

    def test_get_supported_facets(self) -> None:
        """Test get_supported_facets returns all 12 facets."""
        facets = FacetValidator.get_supported_facets()
        assert len(facets) == 12
        assert "pattern" in facets
        assert "minInclusive" in facets
        assert "totalDigits" in facets

    def test_is_lexical_facet(self) -> None:
        """Test is_lexical_facet classification."""
        assert FacetValidator.is_lexical_facet("pattern") is True
        assert FacetValidator.is_lexical_facet("enumeration") is True
        assert FacetValidator.is_lexical_facet("length") is True
        assert FacetValidator.is_lexical_facet("minInclusive") is False

    def test_is_value_facet(self) -> None:
        """Test is_value_facet classification."""
        assert FacetValidator.is_value_facet("minInclusive") is True
        assert FacetValidator.is_value_facet("totalDigits") is True
        assert FacetValidator.is_value_facet("pattern") is False

    def test_lexical_facets_constant(self) -> None:
        """Test LEXICAL_FACETS contains correct facets."""
        expected = {"pattern", "enumeration", "length", "minLength", "maxLength", "whiteSpace"}
        assert FacetValidator.LEXICAL_FACETS == expected

    def test_value_facets_constant(self) -> None:
        """Test VALUE_FACETS contains correct facets."""
        expected = {
            "minInclusive",
            "maxInclusive",
            "minExclusive",
            "maxExclusive",
            "totalDigits",
            "fractionDigits",
        }
        assert FacetValidator.VALUE_FACETS == expected


# =============================================================================
# Integration Tests
# =============================================================================


class TestFacetsIntegration:
    """Integration tests for complete facet validation flow."""

    def test_xsd_string_pattern(self) -> None:
        """Test XSD string with pattern restriction."""
        # Simulate xs:string restricted to email pattern
        facets: dict[str, str | list[str] | int] = {
            "pattern": r"[^@]+@[^@]+\.[^@]+",
            "maxLength": 50,
        }
        errors = LexicalFacets.check_all(facets, "user@example.com")
        assert errors == []

        errors = LexicalFacets.check_all(facets, "invalid-email")
        assert len(errors) == 1

    def test_xsd_integer_range(self) -> None:
        """Test XSD integer with range restriction."""
        # Simulate xs:integer restricted to 0-100
        facets: dict[str, str | int] = {
            "minInclusive": "0",
            "maxInclusive": "100",
        }
        errors = ValueFacets.check_all(facets, Decimal("50"))
        assert errors == []

        errors = ValueFacets.check_all(facets, Decimal("-1"))
        assert len(errors) == 1

    def test_xsd_decimal_precision(self) -> None:
        """Test XSD decimal with precision restriction."""
        # Simulate xs:decimal with totalDigits=5, fractionDigits=2
        facets: dict[str, str | int] = {
            "totalDigits": 5,
            "fractionDigits": 2,
        }
        errors = ValueFacets.check_all(facets, Decimal("123.45"))
        assert errors == []

        errors = ValueFacets.check_all(facets, Decimal("1.234"))
        assert len(errors) == 1  # fractionDigits exceeded

    def test_full_validation_pipeline(self) -> None:
        """Test complete validation pipeline with whitespace."""
        # 1. Normalize whitespace
        raw_value = "  RED  "
        normalized = FacetValidator.normalize_whitespace(
            raw_value,
            {"whiteSpace": "collapse"},
        )
        assert normalized == "RED"

        # 2. Check lexical facets
        lexical_facets: dict[str, str | list[str] | int] = {
            "enumeration": ["RED", "GREEN", "BLUE"],
        }
        errors = FacetValidator.check_lexical(lexical_facets, normalized)
        assert errors == []

    def test_color_type_example(self) -> None:
        """Test realistic color type with enumeration."""
        facets: dict[str, str | list[str] | int] = {
            "enumeration": ["red", "green", "blue", "yellow", "black", "white"],
        }
        assert LexicalFacets.check_all(facets, "red") == []
        assert LexicalFacets.check_all(facets, "green") == []
        assert len(LexicalFacets.check_all(facets, "orange")) == 1

    def test_postal_code_pattern(self) -> None:
        """Test realistic postal code pattern."""
        facets: dict[str, str | list[str] | int] = {
            "pattern": r"\d{5}(-\d{4})?",  # US ZIP code
        }
        assert LexicalFacets.check_all(facets, "12345") == []
        assert LexicalFacets.check_all(facets, "12345-6789") == []
        assert len(LexicalFacets.check_all(facets, "1234")) == 1
        assert len(LexicalFacets.check_all(facets, "ABCDE")) == 1
