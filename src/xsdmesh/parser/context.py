"""Parse context for SAX streaming with namespace stack and path tracking.

Implements O(depth) state management
Namespace resolution using stacked prefix mappings.
"""

from __future__ import annotations

from pathlib import Path

from xsdmesh.constants import (
    DEFAULT_FORM,
    XML_NAMESPACE,
    XMLNS_NAMESPACE,
    XSD_NAMESPACE,
    FormType,
)
from xsdmesh.exceptions import ParseError
from xsdmesh.types.qname import QName, parse_qname


class ParseContext:
    """Mutable parsing state during SAX streaming.

    Tracks namespace prefix mappings, element path, and schema-level settings.
    Stack-based: grows with XML depth, supports push/pop operations.

    Memory: O(depth) where depth = XML nesting level.

    Attributes:
        namespace_stack: List of prefix→URI mappings, one dict per nesting level
        current_path: List of (namespace, local_name) tuples from root to current
        schema_location: Source file/URL being parsed
        target_namespace: targetNamespace attribute from <schema>
        element_form_default: qualified/unqualified for elements
        attribute_form_default: qualified/unqualified for attributes
        block_default: Default blocking derivations
        final_default: Default final derivations
        in_redefine: True if inside <redefine> element (XSD 1.0)
        depth: Current nesting depth (= len(current_path))
        errors: Accumulated non-fatal parse errors
    """

    def __init__(
        self,
        *,
        schema_location: str | Path | None = None,
        target_namespace: str | None = None,
    ) -> None:
        """Initialize parse context.

        Args:
            schema_location: Source file/URL for error reporting
            target_namespace: Target namespace from <schema> element
        """
        # Namespace stack: each level has prefix→URI mapping
        self.namespace_stack: list[dict[str, str]] = []

        # Current element path: [(namespace, local_name), ...]
        self.current_path: list[tuple[str, str]] = []

        # Schema-level attributes
        self.schema_location = str(schema_location) if schema_location else None
        self.target_namespace = target_namespace

        # Form defaults per XSD spec
        self.element_form_default: FormType = DEFAULT_FORM
        self.attribute_form_default: FormType = DEFAULT_FORM

        # Derivation control defaults
        self.block_default: set[str] = set()
        self.final_default: set[str] = set()

        # State flags
        self.in_redefine = False

        # Error accumulation
        self.errors: list[ParseError] = []

        # Initialize with XML built-in namespaces
        self._init_builtin_namespaces()

    def _init_builtin_namespaces(self) -> None:
        """Initialize with XML built-in namespace prefixes."""
        builtin_ns: dict[str, str] = {
            "xml": XML_NAMESPACE,
            "xmlns": XMLNS_NAMESPACE,
            "xs": XSD_NAMESPACE,
            "xsd": XSD_NAMESPACE,
        }
        self.namespace_stack.append(builtin_ns)

    @property
    def depth(self) -> int:
        """Current nesting depth (number of elements from root)."""
        return len(self.current_path)

    @property
    def current_qname(self) -> QName | None:
        """QName of current element (top of path stack)."""
        if not self.current_path:
            return None
        namespace, local = self.current_path[-1]
        return QName(namespace, local)

    def push_namespace(self, prefix: str, uri: str) -> None:
        """Add namespace prefix mapping to current scope.

        Args:
            prefix: Namespace prefix (e.g., "xs", "tns")
            uri: Namespace URI
        """
        if not self.namespace_stack:
            self.namespace_stack.append({})

        # Add to current scope (top of stack)
        self.namespace_stack[-1][prefix] = uri

    def push_namespace_scope(self, mappings: dict[str, str] | None = None) -> None:
        """Push new namespace scope level.

        Creates a new namespace context for nested element.
        Inherits all parent mappings implicitly via lookup chain.

        Args:
            mappings: Initial prefix→URI mappings for this scope
        """
        new_scope: dict[str, str] = dict(mappings) if mappings else {}
        self.namespace_stack.append(new_scope)

    def pop_namespace_scope(self) -> None:
        """Pop namespace scope level when exiting element.

        Raises:
            ParseError: If stack is empty (mismatched push/pop)
        """
        if len(self.namespace_stack) <= 1:
            msg = "Cannot pop root namespace scope"
            raise ParseError(msg, file_path=self.schema_location)

        self.namespace_stack.pop()

    def resolve_prefix(self, prefix: str) -> str | None:
        """Resolve namespace prefix to URI using stack lookup.

        Searches from current scope upward through parent scopes.

        Args:
            prefix: Namespace prefix to resolve

        Returns:
            Namespace URI or None if prefix undefined
        """
        # Search from current scope up to root
        for scope in reversed(self.namespace_stack):
            if prefix in scope:
                return scope[prefix]
        return None

    def resolve_qname(
        self,
        text: str,
        *,
        default_namespace: str | None = None,
    ) -> QName:
        """Resolve QName text to (namespace, local_name) tuple.

        Supports:
        - Clark notation: "{http://...}local"
        - Prefix notation: "prefix:local" (uses namespace stack)
        - Local name: "local" (uses default_namespace or target_namespace)

        Args:
            text: QName text to resolve
            default_namespace: Override default namespace (uses target_namespace if None)

        Returns:
            Resolved QName

        Raises:
            ParseError: If prefix is undefined
        """
        if default_namespace is None:
            default_namespace = self.target_namespace or ""

        # Build resolver dict from namespace stack
        resolver: dict[str, str] = {}
        for scope in self.namespace_stack:
            resolver.update(scope)

        try:
            return parse_qname(
                text,
                resolver=resolver,
                default_namespace=default_namespace,
            )
        except ParseError as e:
            # Add context to error
            e.file_path = self.schema_location
            e.element = self.current_qname.expanded if self.current_qname else None
            raise

    def push_element(self, namespace: str, local_name: str) -> None:
        """Push element onto path stack when entering element.

        Args:
            namespace: Element namespace URI
            local_name: Element local name
        """
        self.current_path.append((namespace, local_name))

    def pop_element(self) -> tuple[str, str] | None:
        """Pop element from path stack when exiting element.

        Returns:
            Popped (namespace, local_name) tuple or None if stack empty
        """
        if not self.current_path:
            return None
        return self.current_path.pop()

    def get_path_str(self) -> str:
        """Get current path as slash-separated string.

        Returns:
            Path like "/{ns}schema/{ns}complexType/{ns}sequence"
        """
        parts = [f"{{{ns}}}{local}" if ns else local for ns, local in self.current_path]
        return "/" + "/".join(parts) if parts else "/"

    def is_at_schema_root(self) -> bool:
        """Check if current element is direct child of <schema>.

        Returns:
            True if depth=1 and parent is schema element
        """
        return (
            self.depth == 2 and len(self.current_path) >= 2 and self.current_path[0][1] == "schema"
        )

    def add_error(
        self,
        message: str,
        *,
        line: int | None = None,
        column: int | None = None,
        context: str | None = None,
    ) -> None:
        """Add non-fatal parse error to accumulator.

        Args:
            message: Error description
            line: Line number in source
            column: Column number in source
            context: Additional error context
        """
        error = ParseError(
            message,
            file_path=self.schema_location,
            line=line,
            column=column,
            element=self.current_qname.expanded if self.current_qname else None,
            context=context,
        )
        self.errors.append(error)

    def clone(self) -> ParseContext:
        """Create deep copy of context for forking (include/import).

        Returns:
            Independent copy with same state
        """
        ctx = ParseContext(
            schema_location=self.schema_location,
            target_namespace=self.target_namespace,
        )

        # Deep copy stacks
        ctx.namespace_stack = [dict(scope) for scope in self.namespace_stack]
        ctx.current_path = list(self.current_path)

        # Copy settings
        ctx.element_form_default = self.element_form_default
        ctx.attribute_form_default = self.attribute_form_default
        ctx.block_default = set(self.block_default)
        ctx.final_default = set(self.final_default)
        ctx.in_redefine = self.in_redefine

        # Errors are NOT copied (each context tracks its own)

        return ctx

    def __repr__(self) -> str:
        """Debug representation."""
        return (
            f"ParseContext("
            f"depth={self.depth}, "
            f"path={self.get_path_str()}, "
            f"ns_scopes={len(self.namespace_stack)}, "
            f"errors={len(self.errors)})"
        )
