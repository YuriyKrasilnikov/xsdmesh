"""Component handlers for SAX parsing.

Base handler protocol and concrete handlers for XSD elements.
"""

from __future__ import annotations

from typing import Protocol

from lxml import etree

from xsdmesh.parser.context import ParseContext
from xsdmesh.parser.events import EventBuffer


class ComponentHandler(Protocol):
    """Protocol for XSD element handlers.

    Handlers process XML elements during SAX parsing via start/end events.
    Each handler corresponds to an XSD component type (simpleType, element, etc.).

    Contract:
    - start_element: Extract attributes, prepare builder state
    - end_element: Assemble component from state and children, return result
    """

    def start_element(
        self,
        elem: etree._Element,
        context: ParseContext,
        buffer: EventBuffer,
    ) -> None:
        """Process element start event.

        Args:
            elem: XML element node
            context: Parse context with namespace stack
            buffer: Event buffer for lookahead
        """
        ...

    def end_element(
        self,
        elem: etree._Element,
        context: ParseContext,
        buffer: EventBuffer,
    ) -> None:
        """Process element end event.

        Args:
            elem: XML element node
            context: Parse context
            buffer: Event buffer

        Note:
            Result should be added to SchemaBuilder (passed via context or global)
        """
        ...
