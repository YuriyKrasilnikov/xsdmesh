"""XSD Facet validators for SimpleType restrictions.

Architecture follows XSD specification with two validation spaces:
- Lexical Space: operates on string representation (pattern, length, enumeration)
- Value Space: operates on typed values (range, digits)

Pipeline:
    XML string → Whitespace Normalization → Lexical Validation
              → Lexical-to-Value Mapping → Value Validation → Typed result

Implements all 12 XSD 1.0 facets:
- Lexical: length, minLength, maxLength, pattern, enumeration, whiteSpace
- Value: minInclusive, maxInclusive, minExclusive, maxExclusive, totalDigits, fractionDigits
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from xsdmesh.exceptions import ValidationError


@dataclass(frozen=True)
class FacetResult:
    """Result of facet validation."""

    valid: bool
    error: ValidationError | None = None

    @staticmethod
    def ok() -> FacetResult:
        """Create successful result."""
        return FacetResult(valid=True)

    @staticmethod
    def fail(message: str, code: str | None = None) -> FacetResult:
        """Create failed result with error."""
        return FacetResult(
            valid=False,
            error=ValidationError(message, code=code, severity="error"),
        )


# =============================================================================
# Whitespace Normalization (preprocessing step)
# =============================================================================


class WhitespaceFacet:
    """Whitespace facet: preserve, replace, collapse.

    Applied during normalization before validation.
    """

    @staticmethod
    def normalize(value: str, mode: str) -> str:
        """Normalize whitespace according to mode.

        Args:
            value: String to normalize
            mode: "preserve", "replace", or "collapse"

        Returns:
            Normalized string
        """
        if mode == "preserve":
            return value

        if mode == "replace":
            # Replace tab, newline, carriage return with space
            return value.replace("\t", " ").replace("\n", " ").replace("\r", " ")

        if mode == "collapse":
            # Replace + collapse consecutive spaces + strip
            normalized = value.replace("\t", " ").replace("\n", " ").replace("\r", " ")
            while "  " in normalized:
                normalized = normalized.replace("  ", " ")
            return normalized.strip()

        # Unknown mode - preserve
        return value


# =============================================================================
# Lexical Space Facets (operate on string representation)
# =============================================================================


class PatternFacet:
    """Pattern facet validator using regex.

    Operates in LEXICAL space - validates string representation.
    Supports multiple patterns (OR logic - value must match at least one).
    """

    _cache: dict[str, re.Pattern[str]] = {}

    @classmethod
    def validate(cls, patterns: list[str] | str, value: str) -> FacetResult:
        """Validate string value against pattern(s).

        Args:
            patterns: Single pattern or list of patterns (OR logic)
            value: String value to validate

        Returns:
            FacetResult indicating success or failure
        """
        if isinstance(patterns, str):
            patterns = [patterns]

        if not patterns:
            return FacetResult.ok()

        for pattern_str in patterns:
            try:
                pattern = cls._get_compiled(pattern_str)
                if pattern.fullmatch(value):
                    return FacetResult.ok()
            except re.error as e:
                return FacetResult.fail(
                    f"Invalid pattern '{pattern_str}': {e}",
                    code="pattern-invalid",
                )

        return FacetResult.fail(
            f"Value '{value}' does not match pattern(s)",
            code="cvc-pattern-valid",
        )

    @classmethod
    def _get_compiled(cls, pattern: str) -> re.Pattern[str]:
        """Get compiled pattern from cache."""
        if pattern not in cls._cache:
            cls._cache[pattern] = re.compile(pattern)
        return cls._cache[pattern]

    @classmethod
    def clear_cache(cls) -> None:
        """Clear pattern cache."""
        cls._cache.clear()


class EnumerationFacet:
    """Enumeration facet validator.

    Operates in LEXICAL space - compares string representations.
    """

    @staticmethod
    def validate(enum_values: list[str], value: str) -> FacetResult:
        """Validate string value is in enumeration.

        Args:
            enum_values: List of allowed string values
            value: String value to validate

        Returns:
            FacetResult indicating success or failure
        """
        if not enum_values:
            return FacetResult.ok()

        if value in enum_values:
            return FacetResult.ok()

        if len(enum_values) <= 5:
            allowed = ", ".join(f"'{v}'" for v in enum_values)
            msg = f"Value '{value}' not in enumeration: [{allowed}]"
        else:
            msg = f"Value '{value}' not in enumeration ({len(enum_values)} values)"

        return FacetResult.fail(msg, code="cvc-enumeration-valid")


class LengthFacet:
    """Length facets validator: length, minLength, maxLength.

    Operates in LEXICAL space - counts characters in string.
    """

    @staticmethod
    def validate_length(expected: int, value: str) -> FacetResult:
        """Validate exact string length."""
        actual = len(value)
        if actual == expected:
            return FacetResult.ok()
        return FacetResult.fail(
            f"Length {actual} != required {expected}",
            code="cvc-length-valid",
        )

    @staticmethod
    def validate_min_length(min_len: int, value: str) -> FacetResult:
        """Validate minimum string length."""
        actual = len(value)
        if actual >= min_len:
            return FacetResult.ok()
        return FacetResult.fail(
            f"Length {actual} < minLength {min_len}",
            code="cvc-minLength-valid",
        )

    @staticmethod
    def validate_max_length(max_len: int, value: str) -> FacetResult:
        """Validate maximum string length."""
        actual = len(value)
        if actual <= max_len:
            return FacetResult.ok()
        return FacetResult.fail(
            f"Length {actual} > maxLength {max_len}",
            code="cvc-maxLength-valid",
        )


class LexicalFacets:
    """Orchestrator for lexical space facet validation.

    All facets here operate on string (lexical) representation.
    """

    @staticmethod
    def check_all(facets: dict[str, str | list[str] | int], value: str) -> list[ValidationError]:
        """Check string value against all lexical facets.

        Args:
            facets: Dict of facet_name -> facet_value
            value: String value to validate

        Returns:
            List of ValidationError (empty if all pass)
        """
        errors: list[ValidationError] = []

        # Pattern
        if "pattern" in facets:
            raw_patterns = facets["pattern"]
            if isinstance(raw_patterns, str):
                patterns_list = [raw_patterns]
            elif isinstance(raw_patterns, list):
                patterns_list = [str(p) for p in raw_patterns]
            else:
                patterns_list = [str(raw_patterns)]
            result = PatternFacet.validate(patterns_list, value)
            if not result.valid and result.error:
                errors.append(result.error)

        # Enumeration
        if "enumeration" in facets:
            enum_vals = facets["enumeration"]
            if isinstance(enum_vals, list):
                # Ensure all enum values are strings
                str_enum = [str(v) for v in enum_vals]
                result = EnumerationFacet.validate(str_enum, value)
                if not result.valid and result.error:
                    errors.append(result.error)

        # Length facets
        if "length" in facets:
            length_val = facets["length"]
            if isinstance(length_val, int):
                result = LengthFacet.validate_length(length_val, value)
            else:
                result = LengthFacet.validate_length(int(str(length_val)), value)
            if not result.valid and result.error:
                errors.append(result.error)

        if "minLength" in facets:
            min_len_val = facets["minLength"]
            if isinstance(min_len_val, int):
                result = LengthFacet.validate_min_length(min_len_val, value)
            else:
                result = LengthFacet.validate_min_length(int(str(min_len_val)), value)
            if not result.valid and result.error:
                errors.append(result.error)

        if "maxLength" in facets:
            max_len_val = facets["maxLength"]
            if isinstance(max_len_val, int):
                result = LengthFacet.validate_max_length(max_len_val, value)
            else:
                result = LengthFacet.validate_max_length(int(str(max_len_val)), value)
            if not result.valid and result.error:
                errors.append(result.error)

        return errors


# =============================================================================
# Value Space Facets (operate on typed values)
# =============================================================================


class RangeFacet:
    """Range facets validator: min/max Inclusive/Exclusive.

    Operates in VALUE space - compares Decimal values.
    """

    @staticmethod
    def validate_min_inclusive(min_val: Decimal, value: Decimal) -> FacetResult:
        """Validate value >= minInclusive."""
        if value >= min_val:
            return FacetResult.ok()
        return FacetResult.fail(
            f"Value {value} < minInclusive {min_val}",
            code="cvc-minInclusive-valid",
        )

    @staticmethod
    def validate_max_inclusive(max_val: Decimal, value: Decimal) -> FacetResult:
        """Validate value <= maxInclusive."""
        if value <= max_val:
            return FacetResult.ok()
        return FacetResult.fail(
            f"Value {value} > maxInclusive {max_val}",
            code="cvc-maxInclusive-valid",
        )

    @staticmethod
    def validate_min_exclusive(min_val: Decimal, value: Decimal) -> FacetResult:
        """Validate value > minExclusive."""
        if value > min_val:
            return FacetResult.ok()
        return FacetResult.fail(
            f"Value {value} <= minExclusive {min_val}",
            code="cvc-minExclusive-valid",
        )

    @staticmethod
    def validate_max_exclusive(max_val: Decimal, value: Decimal) -> FacetResult:
        """Validate value < maxExclusive."""
        if value < max_val:
            return FacetResult.ok()
        return FacetResult.fail(
            f"Value {value} >= maxExclusive {max_val}",
            code="cvc-maxExclusive-valid",
        )


class DigitsFacet:
    """Digits facets validator: totalDigits, fractionDigits.

    Operates in VALUE space - analyzes Decimal structure.
    """

    @staticmethod
    def validate_total_digits(max_digits: int, value: Decimal) -> FacetResult:
        """Validate total number of digits."""
        sign, digits, exp = value.as_tuple()
        total = len(digits)

        if total <= max_digits:
            return FacetResult.ok()

        return FacetResult.fail(
            f"Value has {total} digits, exceeds totalDigits {max_digits}",
            code="cvc-totalDigits-valid",
        )

    @staticmethod
    def validate_fraction_digits(max_fraction: int, value: Decimal) -> FacetResult:
        """Validate number of fraction digits."""
        sign, digits, exp = value.as_tuple()
        fraction_digits = -exp if isinstance(exp, int) and exp < 0 else 0

        if fraction_digits <= max_fraction:
            return FacetResult.ok()

        return FacetResult.fail(
            f"Value has {fraction_digits} fraction digits, exceeds {max_fraction}",
            code="cvc-fractionDigits-valid",
        )


class ValueFacets:
    """Orchestrator for value space facet validation.

    All facets here operate on typed (Decimal) values.
    """

    @staticmethod
    def check_all(facets: dict[str, str | int], value: Decimal) -> list[ValidationError]:
        """Check typed value against all value facets.

        Args:
            facets: Dict of facet_name -> facet_value (as strings from XML)
            value: Decimal value to validate

        Returns:
            List of ValidationError (empty if all pass)
        """
        errors: list[ValidationError] = []

        try:
            # Range facets
            if "minInclusive" in facets:
                min_val = Decimal(str(facets["minInclusive"]))
                result = RangeFacet.validate_min_inclusive(min_val, value)
                if not result.valid and result.error:
                    errors.append(result.error)

            if "maxInclusive" in facets:
                max_val = Decimal(str(facets["maxInclusive"]))
                result = RangeFacet.validate_max_inclusive(max_val, value)
                if not result.valid and result.error:
                    errors.append(result.error)

            if "minExclusive" in facets:
                min_val = Decimal(str(facets["minExclusive"]))
                result = RangeFacet.validate_min_exclusive(min_val, value)
                if not result.valid and result.error:
                    errors.append(result.error)

            if "maxExclusive" in facets:
                max_val = Decimal(str(facets["maxExclusive"]))
                result = RangeFacet.validate_max_exclusive(max_val, value)
                if not result.valid and result.error:
                    errors.append(result.error)

            # Digits facets
            if "totalDigits" in facets:
                result = DigitsFacet.validate_total_digits(int(facets["totalDigits"]), value)
                if not result.valid and result.error:
                    errors.append(result.error)

            if "fractionDigits" in facets:
                result = DigitsFacet.validate_fraction_digits(int(facets["fractionDigits"]), value)
                if not result.valid and result.error:
                    errors.append(result.error)

        except InvalidOperation as e:
            errors.append(ValidationError(f"Invalid decimal value: {e}", code="cvc-datatype-valid"))

        return errors


# =============================================================================
# Unified Validator (convenience wrapper)
# =============================================================================


class FacetValidator:
    """Unified facet validation for both lexical and value spaces.

    Provides convenience methods that internally dispatch to appropriate space.
    """

    # All supported facet names
    LEXICAL_FACETS: frozenset[str] = frozenset(
        {
            "pattern",
            "enumeration",
            "length",
            "minLength",
            "maxLength",
            "whiteSpace",
        }
    )

    VALUE_FACETS: frozenset[str] = frozenset(
        {
            "minInclusive",
            "maxInclusive",
            "minExclusive",
            "maxExclusive",
            "totalDigits",
            "fractionDigits",
        }
    )

    @classmethod
    def check_lexical(
        cls,
        facets: dict[str, str | list[str] | int],
        value: str,
    ) -> list[ValidationError]:
        """Check lexical (string) facets only.

        Args:
            facets: Facets dictionary
            value: String value

        Returns:
            List of errors
        """
        return LexicalFacets.check_all(facets, value)

    @classmethod
    def check_value(
        cls,
        facets: dict[str, str | int],
        value: Decimal,
    ) -> list[ValidationError]:
        """Check value (Decimal) facets only.

        Args:
            facets: Facets dictionary
            value: Decimal value

        Returns:
            List of errors
        """
        return ValueFacets.check_all(facets, value)

    @classmethod
    def normalize_whitespace(cls, value: str, facets: dict[str, str]) -> str:
        """Apply whitespace normalization.

        Args:
            value: String to normalize
            facets: Facets dict (looks for "whiteSpace")

        Returns:
            Normalized string
        """
        mode = str(facets.get("whiteSpace", "preserve"))
        return WhitespaceFacet.normalize(value, mode)

    @classmethod
    def get_supported_facets(cls) -> list[str]:
        """Get all supported facet names."""
        return sorted(cls.LEXICAL_FACETS | cls.VALUE_FACETS)

    @classmethod
    def is_lexical_facet(cls, name: str) -> bool:
        """Check if facet operates in lexical space."""
        return name in cls.LEXICAL_FACETS

    @classmethod
    def is_value_facet(cls, name: str) -> bool:
        """Check if facet operates in value space."""
        return name in cls.VALUE_FACETS
