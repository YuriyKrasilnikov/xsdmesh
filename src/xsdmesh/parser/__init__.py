"""SAX-based streaming parser for XML Schema.

Provides O(depth) memory parsing via incremental SAX with selective tree building.
"""

from xsdmesh.parser.context import ParseContext
from xsdmesh.parser.events import Event, EventBuffer, EventType
from xsdmesh.parser.handlers import ComponentHandler
from xsdmesh.parser.xml_parser import ParseResult, SAXParser, parse_schema
from xsdmesh.types.qname import QName, is_ncname, parse_qname, split_qname

__all__ = [
    # Core parser
    "SAXParser",
    "parse_schema",
    "ParseResult",
    # Context
    "ParseContext",
    # Events
    "Event",
    "EventBuffer",
    "EventType",
    # Handlers
    "ComponentHandler",
    # QName utilities
    "QName",
    "parse_qname",
    "split_qname",
    "is_ncname",
]
