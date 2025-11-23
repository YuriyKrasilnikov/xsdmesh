"""Exception hierarchy for XSDMesh.

All exceptions inherit from XSDMeshError for easy catching.
Provides detailed context for parsing, validation, and resolution errors.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from pathlib import Path


class XSDMeshError(Exception):
    """Base exception for all XSDMesh errors.

    All library exceptions inherit from this for unified error handling.
    """


class ParseError(XSDMeshError):
    """XML/XSD parsing error with location context.

    Raised when XML is malformed or XSD structure is invalid.
    """

    def __init__(
        self,
        message: str,
        *,
        file_path: Path | str | None = None,
        line: int | None = None,
        column: int | None = None,
        context: str | None = None,
        element: str | None = None,
    ) -> None:
        """Initialize parse error with location context.

        Args:
            message: Error description
            file_path: Schema file path
            line: Line number (1-indexed)
            column: Column number (1-indexed)
            context: XPath-like path to error location
            element: Current element name
        """
        self.file_path = file_path
        self.line = line
        self.column = column
        self.context = context
        self.element = element

        # Build detailed message
        parts = [message]
        if file_path:
            parts.append(f"in {file_path}")
        if line is not None:
            if column is not None:
                parts.append(f"at line {line}, column {column}")
            else:
                parts.append(f"at line {line}")
        if context:
            parts.append(f"(context: {context})")
        if element:
            parts.append(f"(element: {element})")

        super().__init__(" ".join(parts))


class XMLSyntaxError(ParseError):
    """Malformed XML syntax.

    XML is not well-formed according to XML 1.0 spec.
    """


class SchemaStructureError(ParseError):
    """Invalid XSD schema structure.

    Schema violates XSD meta-schema constraints.
    """


class NamespaceError(ParseError):
    """Namespace resolution error.

    Unresolved prefix, conflicting namespaces, or invalid URI.
    """


class ValidationError(XSDMeshError):
    """Schema validation error with severity levels.

    Supports W3C error codes and optional error recovery.
    """

    def __init__(
        self,
        message: str,
        *,
        severity: Literal["error", "warning", "info"] = "error",
        code: str | None = None,
        context: str | None = None,
        recovery: Callable[[], Any] | None = None,
    ) -> None:
        """Initialize validation error.

        Args:
            message: Error description
            severity: Error severity level
            code: W3C error code (e.g., "src-element.2.1")
            context: Schema component path
            recovery: Optional recovery function
        """
        self.severity = severity
        self.code = code
        self.context = context
        self.recovery = recovery

        # Build message with code
        parts = [f"[{severity.upper()}]"]
        if code:
            parts.append(f"[{code}]")
        parts.append(message)
        if context:
            parts.append(f"(at {context})")

        super().__init__(" ".join(parts))


class ResolutionError(XSDMeshError):
    """Reference resolution error.

    Failed to resolve QName reference to schema component.
    """

    def __init__(
        self,
        message: str,
        *,
        qname: str | None = None,
        reference_type: Literal["type", "element", "attribute", "group", "attributeGroup"]
        | None = None,
        location: str | None = None,
    ) -> None:
        """Initialize resolution error.

        Args:
            message: Error description
            qname: Unresolved QName
            reference_type: Type of reference
            location: Where reference was found
        """
        self.qname = qname
        self.reference_type = reference_type
        self.location = location

        # Build detailed message
        parts = [message]
        if qname:
            parts.append(f"'{qname}'")
        if reference_type:
            parts.append(f"(type: {reference_type})")
        if location:
            parts.append(f"at {location}")

        super().__init__(" ".join(parts))


class CircularReferenceError(ResolutionError):
    """Circular dependency detected.

    Schema contains circular type derivation, element substitution,
    or import/include cycle.
    """

    def __init__(
        self,
        message: str,
        *,
        cycle: list[str] | None = None,
        qname: str | None = None,
        reference_type: Literal["type", "element", "attribute", "group", "attributeGroup"]
        | None = None,
        location: str | None = None,
    ) -> None:
        """Initialize circular reference error.

        Args:
            message: Error description
            cycle: List of QNames forming cycle
            qname: Unresolved QName
            reference_type: Type of reference
            location: Where reference was found
        """
        self.cycle = cycle or []
        super().__init__(message, qname=qname, reference_type=reference_type, location=location)

        if self.cycle:
            cycle_str = " -> ".join(self.cycle + [self.cycle[0]])
            self.args = (f"{self.args[0]} (cycle: {cycle_str})",)


class CacheError(XSDMeshError):
    """Cache operation error.

    Failed to load, save, or invalidate cached schema.
    """


class ImportError(XSDMeshError):
    """Schema import/include error.

    Failed to locate, download, or parse imported schema.
    """

    def __init__(
        self,
        message: str,
        *,
        namespace: str | None = None,
        location: str | None = None,
        cause: Exception | None = None,
    ) -> None:
        """Initialize import error.

        Args:
            message: Error description
            namespace: Target namespace
            location: Schema location
            cause: Original exception
        """
        self.namespace = namespace
        self.location = location
        self.cause = cause

        # Build message
        parts = [message]
        if namespace:
            parts.append(f"(namespace: {namespace})")
        if location:
            parts.append(f"(location: {location})")
        if cause:
            parts.append(f"- caused by: {cause}")

        super().__init__(" ".join(parts))
