"""SAX-based streaming XML parser with O(depth) memory complexity.

Implements Algorithm #1 from ALGORITHMS.wip.md:
- Modified SAX using lxml.iterparse
- Selective tree building
- Incremental elem.clear(keep_tail=True) for memory control
- Event buffer with lookahead for disambiguation

Memory: O(depth) not O(nodes) - critical for large schemas.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import IO

from lxml import etree

from xsdmesh.exceptions import ParseError
from xsdmesh.parser.context import ParseContext
from xsdmesh.parser.events import Event, EventBuffer, EventType
from xsdmesh.parser.handlers import ComponentHandler
from xsdmesh.parser.qname import QName
from xsdmesh.utils.logger import get_logger
from xsdmesh.utils.profiler import profile_time

logger = get_logger(__name__)


@dataclass
class ParseResult:
    """Result of SAX parsing.

    Attributes:
        context: Parse context with accumulated state
        errors: List of non-fatal parse errors
        elements_processed: Number of elements parsed
    """

    context: ParseContext
    errors: list[ParseError]
    elements_processed: int


class SAXParser:
    """Streaming SAX parser for XSD schemas with O(depth) memory.

    Features:
    - Incremental parsing via lxml.iterparse
    - Event buffer for lookahead (disambiguation)
    - Automatic elem.clear() for memory control
    - Namespace-aware QName resolution
    - Handler dispatch by element tag

    Example:
        parser = SAXParser()
        result = parser.parse("schema.xsd")
    """

    def __init__(
        self,
        *,
        memory_threshold: int = 1000,
        strict: bool = False,
    ) -> None:
        """Initialize SAX parser.

        Args:
            memory_threshold: Number of elements before aggressive clear
            strict: If True, fail fast on first error; if False, accumulate errors
        """
        self._memory_threshold = memory_threshold
        self._strict = strict

        # State
        self._context: ParseContext | None = None
        self._event_buffer: EventBuffer | None = None
        self._elements_since_clear = 0

        # Handler registry (populated later)
        self._handlers: dict[str, ComponentHandler] = {}

    def _extract_namespaces(self, elem: etree._Element) -> dict[str, str]:
        """Extract namespace declarations from element.

        Args:
            elem: Element to inspect

        Returns:
            Dict of prefix→URI mappings from xmlns attributes
        """
        namespaces: dict[str, str] = {}

        # lxml stores nsmap on element
        if hasattr(elem, "nsmap") and elem.nsmap:
            for prefix, uri in elem.nsmap.items():
                # None prefix means default namespace
                prefix_key = prefix if prefix is not None else ""
                namespaces[prefix_key] = uri

        return namespaces

    def _get_qname(self, elem: etree._Element) -> QName:
        """Extract QName from element.

        Args:
            elem: Element node

        Returns:
            QName (namespace, local_name)
        """
        # lxml stores tag as "{namespace}local" or just "local"
        tag = elem.tag

        if isinstance(tag, str):
            if tag.startswith("{"):
                # Clark notation: "{http://...}local"
                ns_end = tag.find("}")
                namespace = tag[1:ns_end]
                local = tag[ns_end + 1 :]
                return QName(namespace, local)
            # No namespace
            return QName("", tag)

        # Should not happen with well-formed XML
        msg = f"Unexpected tag type: {type(tag)}"
        raise ParseError(msg)

    def _handle_start_element(
        self,
        elem: etree._Element,
        context: ParseContext,
        buffer: EventBuffer,
    ) -> None:
        """Process START_ELEMENT event.

        Args:
            elem: Element node
            context: Parse context
            buffer: Event buffer
        """
        qname = self._get_qname(elem)

        # Push new namespace scope with declarations from this element
        ns_declarations = self._extract_namespaces(elem)
        if ns_declarations:
            context.push_namespace_scope(ns_declarations)
        else:
            context.push_namespace_scope()

        # Push element onto path stack
        context.push_element(qname.namespace, qname.local_name)

        # Dispatch to handler if registered
        handler = self._handlers.get(qname.local_name)
        if handler:
            try:
                handler.start_element(elem, context, buffer)
            except Exception as e:
                if self._strict:
                    raise
                logger.warning(
                    f"Handler error in {qname.local_name}.start_element: {e}"
                )
                context.add_error(
                    f"Handler error: {e}",
                    line=elem.sourceline if hasattr(elem, "sourceline") else None,
                )

    def _handle_end_element(
        self,
        elem: etree._Element,
        context: ParseContext,
        buffer: EventBuffer,
    ) -> None:
        """Process END_ELEMENT event.

        CRITICAL: Must call elem.clear(keep_tail=True) for O(depth) memory!

        Args:
            elem: Element node
            context: Parse context
            buffer: Event buffer
        """
        qname = self._get_qname(elem)

        # Dispatch to handler if registered
        handler = self._handlers.get(qname.local_name)
        if handler:
            try:
                handler.end_element(elem, context, buffer)
            except Exception as e:
                if self._strict:
                    raise
                logger.warning(
                    f"Handler error in {qname.local_name}.end_element: {e}"
                )
                context.add_error(
                    f"Handler error: {e}",
                    line=elem.sourceline if hasattr(elem, "sourceline") else None,
                )

        # Pop element from path stack
        context.pop_element()

        # Pop namespace scope
        try:
            context.pop_namespace_scope()
        except ParseError:
            # Root namespace scope - don't pop
            pass

        # ========================================================================
        # CRITICAL: Clear element to maintain O(depth) memory
        # ========================================================================
        elem.clear(keep_tail=True)
        self._elements_since_clear += 1

        # Periodic aggressive cleanup
        if self._elements_since_clear >= self._memory_threshold:
            parent = elem.getparent()
            if parent is not None:
                parent.clear()
            self._elements_since_clear = 0
            logger.debug(f"Memory threshold reached: cleared parent at depth {context.depth}")

    @profile_time
    def parse(
        self,
        source: str | Path | IO[bytes],
        *,
        target_namespace: str | None = None,
    ) -> ParseResult:
        """Parse XSD schema from source.

        Args:
            source: File path, URL, or file-like object
            target_namespace: Override target namespace

        Returns:
            ParseResult with context, errors, and element count

        Raises:
            ParseError: On parse errors (if strict=True)
        """
        # Initialize context and buffer
        schema_location = str(source) if not isinstance(source, (IO, BytesIO)) else None
        self._context = ParseContext(
            schema_location=schema_location,
            target_namespace=target_namespace,
        )
        self._event_buffer = EventBuffer()
        self._elements_since_clear = 0
        elements_count = 0

        # Prepare source for lxml
        if isinstance(source, (str, Path)):
            source_path = Path(source)
            if not source_path.exists():
                msg = f"Schema file not found: {source}"
                raise ParseError(msg, file_path=str(source))
            source_input: str | IO[bytes] = str(source_path)
        else:
            source_input = source

        try:
            # ===================================================================
            # lxml.iterparse: streaming SAX parser
            # ===================================================================
            parser_context = etree.iterparse(
                source_input,
                events=("start", "end"),
                huge_tree=True,  # Allow large schemas
            )

            for raw_event, elem in parser_context:
                # Convert to our Event type
                event_type = (
                    EventType.START_ELEMENT
                    if raw_event == "start"
                    else EventType.END_ELEMENT
                )

                line = (
                    elem.sourceline
                    if hasattr(elem, "sourceline") and elem.sourceline is not None
                    else 0
                )
                event = Event(
                    type=event_type,
                    element=elem,
                    text=None,
                    line=line,
                    column=0,  # lxml doesn't provide column
                )

                # Push to event buffer for lookahead
                self._event_buffer.push(event)

                # Process event
                if event_type == EventType.START_ELEMENT:
                    self._handle_start_element(elem, self._context, self._event_buffer)
                    elements_count += 1
                elif event_type == EventType.END_ELEMENT:
                    self._handle_end_element(elem, self._context, self._event_buffer)

            # Parsing complete
            logger.info(
                f"Parsed {schema_location or 'schema'}: "
                f"elements={elements_count}, "
                f"depth={self._context.depth}, "
                f"errors={len(self._context.errors)}"
            )

            # Return structured result
            return ParseResult(
                context=self._context,
                errors=self._context.errors,
                elements_processed=elements_count,
            )

        except etree.XMLSyntaxError as e:
            msg = f"XML syntax error: {e}"
            raise ParseError(
                msg,
                file_path=schema_location,
                line=e.lineno if hasattr(e, "lineno") else None,
            ) from e

        except Exception as e:
            if isinstance(e, ParseError):
                raise
            msg = f"Parse error: {e}"
            raise ParseError(msg, file_path=schema_location) from e

    def register_handler(self, tag: str, handler: ComponentHandler) -> None:
        """Register handler for element tag.

        Args:
            tag: Element local name (e.g., "simpleType")
            handler: Handler instance with start_element/end_element methods
        """
        self._handlers[tag] = handler

    def __repr__(self) -> str:
        """Debug representation."""
        return (
            f"SAXParser("
            f"handlers={len(self._handlers)}, "
            f"threshold={self._memory_threshold}, "
            f"strict={self._strict})"
        )


def parse_schema(
    source: str | Path | IO[bytes],
    *,
    strict: bool = False,
) -> ParseResult:
    """Convenience function to parse XSD schema.

    Args:
        source: File path, URL, or file-like object
        strict: Fail fast on errors

    Returns:
        ParseResult with context, errors, and element count

    Example:
        result = parse_schema("schema.xsd")
        errors = result.errors
        count = result.elements_processed
    """
    parser = SAXParser(strict=strict)
    return parser.parse(source)
