"""Tests for QName parsing utilities."""

from __future__ import annotations

import pytest

from xsdmesh.exceptions import ParseError
from xsdmesh.types.qname import QName, is_ncname, parse_qname, split_qname


class TestQName:
    """Test QName NamedTuple."""

    def test_qname_creation(self) -> None:
        """Test QName creation."""
        qname = QName("http://www.w3.org/2001/XMLSchema", "string")
        assert qname.namespace == "http://www.w3.org/2001/XMLSchema"
        assert qname.local_name == "string"

    def test_qname_expanded_with_namespace(self) -> None:
        """Test QName.expanded with namespace."""
        qname = QName("http://www.w3.org/2001/XMLSchema", "string")
        assert qname.expanded == "{http://www.w3.org/2001/XMLSchema}string"

    def test_qname_expanded_without_namespace(self) -> None:
        """Test QName.expanded without namespace."""
        qname = QName("", "localName")
        assert qname.expanded == "localName"

    def test_qname_str(self) -> None:
        """Test QName.__str__."""
        qname = QName("http://example.com", "foo")
        assert str(qname) == "{http://example.com}foo"

    def test_qname_repr(self) -> None:
        """Test QName.__repr__."""
        qname = QName("http://example.com", "foo")
        assert repr(qname) == "QName('http://example.com', 'foo')"

    def test_qname_repr_no_namespace(self) -> None:
        """Test QName.__repr__ without namespace."""
        qname = QName("", "foo")
        assert repr(qname) == "QName('foo')"


class TestParseQName:
    """Test parse_qname function."""

    def test_clark_notation(self) -> None:
        """Test Clark notation parsing."""
        qname = parse_qname("{http://www.w3.org/2001/XMLSchema}string")
        assert qname.namespace == "http://www.w3.org/2001/XMLSchema"
        assert qname.local_name == "string"

    def test_clark_notation_empty_namespace(self) -> None:
        """Test Clark notation with empty namespace."""
        qname = parse_qname("{}local")
        assert qname.namespace == ""
        assert qname.local_name == "local"

    def test_prefix_notation_with_resolver(self) -> None:
        """Test prefix notation with resolver."""
        resolver = {"xs": "http://www.w3.org/2001/XMLSchema"}
        qname = parse_qname("xs:string", resolver=resolver)
        assert qname.namespace == "http://www.w3.org/2001/XMLSchema"
        assert qname.local_name == "string"

    def test_prefix_notation_without_resolver(self) -> None:
        """Test prefix notation without resolver raises error."""
        with pytest.raises(ParseError, match="No namespace resolver provided"):
            parse_qname("xs:string")

    def test_prefix_notation_undefined_prefix(self) -> None:
        """Test prefix notation with undefined prefix."""
        resolver = {"xs": "http://www.w3.org/2001/XMLSchema"}
        with pytest.raises(ParseError, match="Undefined namespace prefix: 'foo'"):
            parse_qname("foo:bar", resolver=resolver)

    def test_local_name_with_default_namespace(self) -> None:
        """Test local name with default namespace."""
        qname = parse_qname("localName", default_namespace="http://example.com")
        assert qname.namespace == "http://example.com"
        assert qname.local_name == "localName"

    def test_local_name_without_default_namespace(self) -> None:
        """Test local name without default namespace."""
        qname = parse_qname("localName")
        assert qname.namespace == ""
        assert qname.local_name == "localName"

    def test_empty_prefix_error(self) -> None:
        """Test empty prefix raises error."""
        with pytest.raises(ParseError, match="Empty prefix"):
            parse_qname(":localName")

    def test_empty_local_name_error(self) -> None:
        """Test empty local name raises error."""
        resolver = {"xs": "http://www.w3.org/2001/XMLSchema"}
        with pytest.raises(ParseError, match="Empty local name"):
            parse_qname("xs:", resolver=resolver)

    def test_empty_text_error(self) -> None:
        """Test empty text raises error."""
        with pytest.raises(ParseError, match="QName text cannot be empty"):
            parse_qname("")

    def test_whitespace_stripped(self) -> None:
        """Test whitespace is stripped."""
        qname = parse_qname("  localName  ")
        assert qname.local_name == "localName"


class TestSplitQName:
    """Test split_qname function."""

    def test_split_with_prefix(self) -> None:
        """Test splitting QName with prefix."""
        prefix, local = split_qname("xs:string")
        assert prefix == "xs"
        assert local == "string"

    def test_split_without_prefix(self) -> None:
        """Test splitting QName without prefix."""
        prefix, local = split_qname("localName")
        assert prefix is None
        assert local == "localName"

    def test_split_multiple_colons(self) -> None:
        """Test splitting with multiple colons (only first is separator)."""
        prefix, local = split_qname("xs:foo:bar")
        assert prefix == "xs"
        assert local == "foo:bar"


class TestIsNCName:
    """Test is_ncname function."""

    def test_valid_ncname(self) -> None:
        """Test valid NCName."""
        assert is_ncname("validName")
        assert is_ncname("_validName")
        assert is_ncname("valid-name")
        assert is_ncname("valid.name")
        assert is_ncname("valid123")

    def test_invalid_ncname_starts_with_digit(self) -> None:
        """Test NCName starting with digit is invalid."""
        assert not is_ncname("123invalid")

    def test_invalid_ncname_starts_with_dash(self) -> None:
        """Test NCName starting with dash is invalid."""
        assert not is_ncname("-invalid")

    def test_invalid_ncname_starts_with_dot(self) -> None:
        """Test NCName starting with dot is invalid."""
        assert not is_ncname(".invalid")

    def test_invalid_ncname_with_colon(self) -> None:
        """Test NCName with colon is invalid."""
        assert not is_ncname("invalid:name")

    def test_invalid_ncname_empty(self) -> None:
        """Test empty string is invalid NCName."""
        assert not is_ncname("")

    def test_invalid_ncname_special_chars(self) -> None:
        """Test NCName with special characters is invalid."""
        assert not is_ncname("invalid@name")
        assert not is_ncname("invalid name")
        assert not is_ncname("invalid#name")
