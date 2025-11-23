"""Tests for ParseContext."""

from __future__ import annotations

import pytest

from xsdmesh.constants import XSD_NAMESPACE
from xsdmesh.exceptions import ParseError
from xsdmesh.parser.context import ParseContext
from xsdmesh.parser.qname import QName


class TestParseContextInit:
    """Test ParseContext initialization."""

    def test_default_initialization(self) -> None:
        """Test default ParseContext initialization."""
        ctx = ParseContext()
        assert ctx.schema_location is None
        assert ctx.target_namespace is None
        assert ctx.depth == 0
        assert len(ctx.errors) == 0
        assert len(ctx.current_path) == 0

    def test_initialization_with_location(self) -> None:
        """Test ParseContext with schema location."""
        ctx = ParseContext(schema_location="test.xsd")
        assert ctx.schema_location == "test.xsd"

    def test_initialization_with_target_namespace(self) -> None:
        """Test ParseContext with target namespace."""
        ctx = ParseContext(target_namespace="http://example.com")
        assert ctx.target_namespace == "http://example.com"

    def test_builtin_namespaces_initialized(self) -> None:
        """Test builtin namespaces are initialized."""
        ctx = ParseContext()
        assert ctx.resolve_prefix("xs") == XSD_NAMESPACE
        assert ctx.resolve_prefix("xsd") == XSD_NAMESPACE
        assert ctx.resolve_prefix("xml") == "http://www.w3.org/XML/1998/namespace"


class TestNamespaceStack:
    """Test namespace stack operations."""

    def test_push_namespace(self) -> None:
        """Test pushing namespace."""
        ctx = ParseContext()
        ctx.push_namespace("tns", "http://example.com")
        assert ctx.resolve_prefix("tns") == "http://example.com"

    def test_push_namespace_scope(self) -> None:
        """Test pushing namespace scope."""
        ctx = ParseContext()
        ctx.push_namespace_scope({"tns": "http://example.com"})
        assert ctx.resolve_prefix("tns") == "http://example.com"

    def test_push_namespace_scope_empty(self) -> None:
        """Test pushing empty namespace scope."""
        ctx = ParseContext()
        initial_depth = len(ctx.namespace_stack)
        ctx.push_namespace_scope()
        assert len(ctx.namespace_stack) == initial_depth + 1

    def test_pop_namespace_scope(self) -> None:
        """Test popping namespace scope."""
        ctx = ParseContext()
        ctx.push_namespace_scope({"tns": "http://example.com"})
        ctx.pop_namespace_scope()
        assert ctx.resolve_prefix("tns") is None

    def test_pop_namespace_scope_error_on_root(self) -> None:
        """Test popping root namespace scope raises error."""
        ctx = ParseContext()
        with pytest.raises(ParseError, match="Cannot pop root namespace scope"):
            ctx.pop_namespace_scope()

    def test_resolve_prefix_not_found(self) -> None:
        """Test resolving undefined prefix returns None."""
        ctx = ParseContext()
        assert ctx.resolve_prefix("undefined") is None

    def test_namespace_scope_inheritance(self) -> None:
        """Test namespace scope inherits from parent."""
        ctx = ParseContext()
        ctx.push_namespace_scope({"a": "http://a.com"})
        ctx.push_namespace_scope({"b": "http://b.com"})

        # Both prefixes should be visible
        assert ctx.resolve_prefix("a") == "http://a.com"
        assert ctx.resolve_prefix("b") == "http://b.com"

        # Pop scope, only 'a' should remain
        ctx.pop_namespace_scope()
        assert ctx.resolve_prefix("a") == "http://a.com"
        assert ctx.resolve_prefix("b") is None


class TestElementPath:
    """Test element path tracking."""

    def test_push_element(self) -> None:
        """Test pushing element to path."""
        ctx = ParseContext()
        ctx.push_element("http://example.com", "root")
        assert ctx.depth == 1
        assert len(ctx.current_path) == 1
        assert ctx.current_path[0] == ("http://example.com", "root")

    def test_pop_element(self) -> None:
        """Test popping element from path."""
        ctx = ParseContext()
        ctx.push_element("http://example.com", "root")
        result = ctx.pop_element()
        assert result == ("http://example.com", "root")
        assert ctx.depth == 0

    def test_pop_element_empty_stack(self) -> None:
        """Test popping from empty path returns None."""
        ctx = ParseContext()
        assert ctx.pop_element() is None

    def test_current_qname(self) -> None:
        """Test current_qname property."""
        ctx = ParseContext()
        ctx.push_element("http://example.com", "root")
        qname = ctx.current_qname
        assert qname is not None
        assert qname.namespace == "http://example.com"
        assert qname.local_name == "root"

    def test_current_qname_empty_path(self) -> None:
        """Test current_qname when path is empty."""
        ctx = ParseContext()
        assert ctx.current_qname is None

    def test_get_path_str(self) -> None:
        """Test get_path_str."""
        ctx = ParseContext()
        ctx.push_element("http://example.com", "root")
        ctx.push_element("http://example.com", "child")
        path = ctx.get_path_str()
        assert path == "/{http://example.com}root/{http://example.com}child"

    def test_get_path_str_empty(self) -> None:
        """Test get_path_str with empty path."""
        ctx = ParseContext()
        assert ctx.get_path_str() == "/"

    def test_get_path_str_no_namespace(self) -> None:
        """Test get_path_str with no namespace."""
        ctx = ParseContext()
        ctx.push_element("", "root")
        assert ctx.get_path_str() == "/root"


class TestQNameResolution:
    """Test QName resolution."""

    def test_resolve_qname_clark_notation(self) -> None:
        """Test resolving Clark notation QName."""
        ctx = ParseContext()
        qname = ctx.resolve_qname("{http://example.com}local")
        assert qname.namespace == "http://example.com"
        assert qname.local_name == "local"

    def test_resolve_qname_prefix_notation(self) -> None:
        """Test resolving prefix notation QName."""
        ctx = ParseContext()
        ctx.push_namespace_scope({"tns": "http://example.com"})
        qname = ctx.resolve_qname("tns:local")
        assert qname.namespace == "http://example.com"
        assert qname.local_name == "local"

    def test_resolve_qname_local_with_target_namespace(self) -> None:
        """Test resolving local name uses target namespace."""
        ctx = ParseContext(target_namespace="http://example.com")
        qname = ctx.resolve_qname("local")
        assert qname.namespace == "http://example.com"
        assert qname.local_name == "local"

    def test_resolve_qname_local_with_default_namespace(self) -> None:
        """Test resolving local name with default namespace override."""
        ctx = ParseContext(target_namespace="http://example.com")
        qname = ctx.resolve_qname("local", default_namespace="http://other.com")
        assert qname.namespace == "http://other.com"
        assert qname.local_name == "local"

    def test_resolve_qname_undefined_prefix_error(self) -> None:
        """Test resolving undefined prefix raises error with context."""
        ctx = ParseContext(schema_location="test.xsd")
        ctx.push_element("http://example.com", "root")

        with pytest.raises(ParseError) as exc_info:
            ctx.resolve_qname("undefined:local")

        assert exc_info.value.file_path == "test.xsd"
        assert exc_info.value.element == "{http://example.com}root"


class TestErrorHandling:
    """Test error accumulation."""

    def test_add_error(self) -> None:
        """Test adding error."""
        ctx = ParseContext(schema_location="test.xsd")
        ctx.add_error("Test error", line=10, column=5)

        assert len(ctx.errors) == 1
        error = ctx.errors[0]
        assert "Test error" in str(error)
        assert error.file_path == "test.xsd"
        assert error.line == 10
        assert error.column == 5

    def test_add_error_with_context(self) -> None:
        """Test adding error with element context."""
        ctx = ParseContext()
        ctx.push_element("http://example.com", "root")
        ctx.add_error("Test error")

        error = ctx.errors[0]
        assert error.element == "{http://example.com}root"

    def test_multiple_errors(self) -> None:
        """Test accumulating multiple errors."""
        ctx = ParseContext()
        ctx.add_error("Error 1")
        ctx.add_error("Error 2")
        ctx.add_error("Error 3")

        assert len(ctx.errors) == 3


class TestContextClone:
    """Test context cloning."""

    def test_clone_basic(self) -> None:
        """Test basic cloning."""
        ctx = ParseContext(schema_location="test.xsd", target_namespace="http://example.com")
        clone = ctx.clone()

        assert clone.schema_location == ctx.schema_location
        assert clone.target_namespace == ctx.target_namespace

    def test_clone_with_namespace_stack(self) -> None:
        """Test cloning preserves namespace stack."""
        ctx = ParseContext()
        ctx.push_namespace_scope({"tns": "http://example.com"})

        clone = ctx.clone()
        assert clone.resolve_prefix("tns") == "http://example.com"

    def test_clone_with_path(self) -> None:
        """Test cloning preserves element path."""
        ctx = ParseContext()
        ctx.push_element("http://example.com", "root")

        clone = ctx.clone()
        assert clone.depth == 1
        assert clone.current_qname == QName("http://example.com", "root")

    def test_clone_independence(self) -> None:
        """Test cloned context is independent."""
        ctx = ParseContext()
        ctx.push_namespace_scope({"tns": "http://example.com"})

        clone = ctx.clone()
        clone.push_namespace_scope({"other": "http://other.com"})

        # Original should not have "other" prefix
        assert ctx.resolve_prefix("other") is None
        assert clone.resolve_prefix("other") == "http://other.com"

    def test_clone_errors_not_copied(self) -> None:
        """Test errors are not copied to clone."""
        ctx = ParseContext()
        ctx.add_error("Original error")

        clone = ctx.clone()
        assert len(clone.errors) == 0

    def test_clone_copies_all_form_defaults(self) -> None:
        """Test clone copies form defaults and derivation settings."""

        ctx = ParseContext()
        ctx.element_form_default = "qualified"
        ctx.attribute_form_default = "qualified"
        ctx.block_default = {"extension", "restriction"}
        ctx.final_default = {"restriction"}
        ctx.in_redefine = True

        clone = ctx.clone()

        assert clone.element_form_default == "qualified"
        assert clone.attribute_form_default == "qualified"
        assert clone.block_default == {"extension", "restriction"}
        assert clone.final_default == {"restriction"}
        assert clone.in_redefine is True

        # Verify deep copy of sets
        clone.block_default.add("substitution")
        assert "substitution" not in ctx.block_default


class TestSchemaRootDetection:
    """Test schema root detection."""

    def test_is_at_schema_root_true(self) -> None:
        """Test is_at_schema_root returns True for direct schema children."""
        ctx = ParseContext()
        ctx.push_element(XSD_NAMESPACE, "schema")
        ctx.push_element(XSD_NAMESPACE, "element")

        assert ctx.is_at_schema_root()

    def test_is_at_schema_root_false_too_deep(self) -> None:
        """Test is_at_schema_root returns False when too deep."""
        ctx = ParseContext()
        ctx.push_element(XSD_NAMESPACE, "schema")
        ctx.push_element(XSD_NAMESPACE, "complexType")
        ctx.push_element(XSD_NAMESPACE, "sequence")

        assert not ctx.is_at_schema_root()

    def test_is_at_schema_root_false_not_schema_parent(self) -> None:
        """Test is_at_schema_root returns False when parent is not schema."""
        ctx = ParseContext()
        ctx.push_element(XSD_NAMESPACE, "other")
        ctx.push_element(XSD_NAMESPACE, "element")

        assert not ctx.is_at_schema_root()

    def test_is_at_schema_root_false_empty_path(self) -> None:
        """Test is_at_schema_root returns False for empty path."""
        ctx = ParseContext()
        assert not ctx.is_at_schema_root()

    def test_is_at_schema_root_wrong_namespace(self) -> None:
        """Test is_at_schema_root with wrong namespace for schema element.

        NOTE: Current implementation does NOT check namespace,
        this test documents the behavior.
        """
        ctx = ParseContext()
        # Push schema element with WRONG namespace
        ctx.push_element("http://evil.com", "schema")
        ctx.push_element(XSD_NAMESPACE, "element")

        # Current implementation returns True (only checks local_name)
        # This is a limitation that should be fixed in the implementation
        assert ctx.is_at_schema_root()  # FIXME: Should be False!
