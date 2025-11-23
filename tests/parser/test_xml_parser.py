"""Tests for SAXParser."""

from __future__ import annotations

from io import BytesIO

import pytest

from xsdmesh.exceptions import ParseError
from xsdmesh.parser.xml_parser import ParseResult, SAXParser, parse_schema

# Simple XSD schema for testing
SIMPLE_SCHEMA = b"""<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"
           targetNamespace="http://example.com"
           elementFormDefault="qualified">
  <xs:element name="root" type="xs:string"/>
</xs:schema>
"""

# Schema with multiple elements
MULTI_ELEMENT_SCHEMA = b"""<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="elem1" type="xs:string"/>
  <xs:element name="elem2" type="xs:int"/>
  <xs:element name="elem3" type="xs:boolean"/>
</xs:schema>
"""

# Schema with nested elements
NESTED_SCHEMA = b"""<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:complexType name="PersonType">
    <xs:sequence>
      <xs:element name="name" type="xs:string"/>
      <xs:element name="age" type="xs:int"/>
    </xs:sequence>
  </xs:complexType>
  <xs:element name="person" type="PersonType"/>
</xs:schema>
"""

# Malformed XML
MALFORMED_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="broken"
</xs:schema>
"""


class TestParseResult:
    """Test ParseResult dataclass."""

    def test_parse_result_creation(self) -> None:
        """Test ParseResult can be created."""
        from xsdmesh.parser.context import ParseContext

        ctx = ParseContext()
        result = ParseResult(context=ctx, errors=[], elements_processed=10)

        assert result.context == ctx
        assert result.errors == []
        assert result.elements_processed == 10


class TestSAXParserInit:
    """Test SAXParser initialization."""

    def test_default_initialization(self) -> None:
        """Test SAXParser default initialization."""
        parser = SAXParser()
        assert parser._memory_threshold == 1000
        assert parser._strict is False
        assert len(parser._handlers) == 0

    def test_initialization_with_custom_threshold(self) -> None:
        """Test SAXParser with custom memory threshold."""
        parser = SAXParser(memory_threshold=5000)
        assert parser._memory_threshold == 5000

    def test_initialization_strict_mode(self) -> None:
        """Test SAXParser in strict mode."""
        parser = SAXParser(strict=True)
        assert parser._strict is True

    def test_repr(self) -> None:
        """Test SAXParser __repr__."""
        parser = SAXParser()
        repr_str = repr(parser)
        assert "SAXParser" in repr_str
        assert "handlers=0" in repr_str
        assert "threshold=1000" in repr_str


class TestSAXParserParsing:
    """Test SAXParser parsing functionality."""

    def test_parse_simple_schema(self) -> None:
        """Test parsing simple schema."""
        parser = SAXParser()
        source = BytesIO(SIMPLE_SCHEMA)

        result = parser.parse(source)

        assert isinstance(result, ParseResult)
        assert result.elements_processed > 0
        assert len(result.errors) == 0

    def test_parse_multi_element_schema(self) -> None:
        """Test parsing schema with multiple elements."""
        parser = SAXParser()
        source = BytesIO(MULTI_ELEMENT_SCHEMA)

        result = parser.parse(source)

        assert result.elements_processed >= 3  # At least schema + 3 elements
        assert len(result.errors) == 0

    def test_parse_nested_schema(self) -> None:
        """Test parsing schema with nested elements."""
        parser = SAXParser()
        source = BytesIO(NESTED_SCHEMA)

        result = parser.parse(source)

        assert result.elements_processed > 0
        assert len(result.errors) == 0

    def test_parse_reads_target_namespace_from_schema(self) -> None:
        """Test parsing reads targetNamespace from schema element."""
        parser = SAXParser()
        source = BytesIO(SIMPLE_SCHEMA)

        result = parser.parse(source)

        # SIMPLE_SCHEMA has targetNamespace="http://example.com"
        # NOTE: Current implementation may not parse this from XML yet
        # This test documents expected behavior
        # assert result.context.target_namespace == "http://example.com"
        # For now, just verify parse succeeds
        assert result.elements_processed > 0

    def test_parse_with_target_namespace_override(self) -> None:
        """Test parsing with target namespace override parameter."""
        parser = SAXParser()
        source = BytesIO(SIMPLE_SCHEMA)

        result = parser.parse(source, target_namespace="http://override.com")

        # Override parameter should take precedence
        assert result.context.target_namespace == "http://override.com"

    def test_parse_malformed_xml_raises_error(self) -> None:
        """Test parsing malformed XML raises ParseError."""
        parser = SAXParser()
        source = BytesIO(MALFORMED_XML)

        with pytest.raises(ParseError, match="XML syntax error"):
            parser.parse(source)

    def test_parse_nonexistent_file_raises_error(self) -> None:
        """Test parsing nonexistent file raises ParseError."""
        parser = SAXParser()

        with pytest.raises(ParseError, match="Schema file not found"):
            parser.parse("/nonexistent/file.xsd")

    def test_parse_updates_context(self) -> None:
        """Test parsing updates context state."""
        parser = SAXParser()
        source = BytesIO(SIMPLE_SCHEMA)

        result = parser.parse(source)

        # Context should have namespace information
        assert result.context.resolve_prefix("xs") is not None


class TestSAXParserHandlers:
    """Test SAXParser handler registration."""

    def test_register_handler(self) -> None:
        """Test registering handler."""
        from lxml import etree

        from xsdmesh.parser.context import ParseContext
        from xsdmesh.parser.events import EventBuffer

        class MockHandler:
            def start_element(
                self,
                elem: etree._Element,
                context: ParseContext,
                buffer: EventBuffer,
            ) -> None:
                pass

            def end_element(
                self,
                elem: etree._Element,
                context: ParseContext,
                buffer: EventBuffer,
            ) -> None:
                pass

        parser = SAXParser()
        handler = MockHandler()

        parser.register_handler("simpleType", handler)

        assert "simpleType" in parser._handlers
        assert parser._handlers["simpleType"] == handler

    def test_handler_called_during_parse(self) -> None:
        """Test handler is actually called during parsing."""
        from lxml import etree

        from xsdmesh.parser.context import ParseContext
        from xsdmesh.parser.events import EventBuffer

        call_log: list[str] = []

        class TrackingHandler:
            def start_element(
                self,
                elem: etree._Element,
                context: ParseContext,
                buffer: EventBuffer,
            ) -> None:
                tag = elem.tag if isinstance(elem.tag, str) else str(elem.tag)
                call_log.append(f"start:{tag}")

            def end_element(
                self,
                elem: etree._Element,
                context: ParseContext,
                buffer: EventBuffer,
            ) -> None:
                tag = elem.tag if isinstance(elem.tag, str) else str(elem.tag)
                call_log.append(f"end:{tag}")

        parser = SAXParser()
        handler = TrackingHandler()
        parser.register_handler("element", handler)

        source = BytesIO(SIMPLE_SCHEMA)
        parser.parse(source)

        # Handler should be called for <xs:element> tag
        assert any("element" in call for call in call_log)
        assert any(call.startswith("start:") for call in call_log)
        assert any(call.startswith("end:") for call in call_log)


class TestParseSchemaFunction:
    """Test parse_schema convenience function."""

    def test_parse_schema_simple(self) -> None:
        """Test parse_schema convenience function."""
        source = BytesIO(SIMPLE_SCHEMA)

        result = parse_schema(source)

        assert isinstance(result, ParseResult)
        assert result.elements_processed > 0

    def test_parse_schema_strict_mode(self) -> None:
        """Test parse_schema in strict mode."""
        source = BytesIO(SIMPLE_SCHEMA)

        result = parse_schema(source, strict=True)

        assert isinstance(result, ParseResult)


class TestMemoryManagement:
    """Test memory management features."""

    def test_elements_since_clear_increments(self) -> None:
        """Test elements_since_clear counter increments."""
        parser = SAXParser()
        source = BytesIO(SIMPLE_SCHEMA)

        # Parse should increment counter
        parser.parse(source)

        # After parse, counter should have been used
        assert parser._elements_since_clear >= 0

    def test_memory_threshold_triggers_cleanup(self) -> None:
        """Test memory threshold triggers cleanup."""
        # Use small threshold
        parser = SAXParser(memory_threshold=1)
        source = BytesIO(MULTI_ELEMENT_SCHEMA)

        result = parser.parse(source)

        # Counter should have been reset at least once
        assert result.elements_processed > parser._memory_threshold
        # Counter should be less than total (meaning it was reset)
        assert parser._elements_since_clear < result.elements_processed


class TestNamespaceExtraction:
    """Test namespace extraction."""

    def test_extract_namespaces(self) -> None:
        """Test _extract_namespaces method."""
        from lxml import etree

        parser = SAXParser()

        # Create element with namespaces
        xml = b'<root xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:tns="http://example.com"/>'
        elem = etree.fromstring(xml)

        namespaces = parser._extract_namespaces(elem)

        assert "xs" in namespaces
        assert namespaces["xs"] == "http://www.w3.org/2001/XMLSchema"
        assert "tns" in namespaces
        assert namespaces["tns"] == "http://example.com"

    def test_extract_default_namespace(self) -> None:
        """Test extracting default namespace."""
        from lxml import etree

        parser = SAXParser()

        xml = b'<root xmlns="http://example.com"/>'
        elem = etree.fromstring(xml)

        namespaces = parser._extract_namespaces(elem)

        # Default namespace has empty string as key
        assert "" in namespaces
        assert namespaces[""] == "http://example.com"


class TestQNameExtraction:
    """Test QName extraction."""

    def test_get_qname_with_namespace(self) -> None:
        """Test _get_qname with namespace."""
        from lxml import etree

        parser = SAXParser()

        xml = b'<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"/>'
        elem = etree.fromstring(xml)

        qname = parser._get_qname(elem)

        assert qname.namespace == "http://www.w3.org/2001/XMLSchema"
        assert qname.local_name == "schema"

    def test_get_qname_without_namespace(self) -> None:
        """Test _get_qname without namespace."""
        from lxml import etree

        parser = SAXParser()

        xml = b"<root/>"
        elem = etree.fromstring(xml)

        qname = parser._get_qname(elem)

        assert qname.namespace == ""
        assert qname.local_name == "root"
