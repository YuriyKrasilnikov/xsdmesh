"""QName parsing utilities for XML Schema.

Supports two notations:
1. Clark notation: "{http://www.w3.org/2001/XMLSchema}string"
2. Prefix notation: "xs:string" (requires namespace resolver)
3. Local name: "string" (uses default namespace or no namespace)
"""

from __future__ import annotations

import re
from typing import NamedTuple

from xsdmesh.exceptions import ParseError


class QName(NamedTuple):
    """Qualified Name: namespace + local name.

    Attributes:
        namespace: Namespace URI (empty string for no namespace)
        local_name: Local part of the name
    """

    namespace: str
    local_name: str

    @property
    def expanded(self) -> str:
        """Clark notation: {namespace}local."""
        if self.namespace:
            return f"{{{self.namespace}}}{self.local_name}"
        return self.local_name

    def __str__(self) -> str:
        """String representation (Clark notation)."""
        return self.expanded

    def __repr__(self) -> str:
        """Debug representation."""
        if self.namespace:
            return f"QName('{self.namespace}', '{self.local_name}')"
        return f"QName('{self.local_name}')"


# Clark notation pattern: {namespace}localName
_CLARK_PATTERN = re.compile(r"^\{([^}]*)\}(.+)$")


def parse_qname(
    text: str,
    *,
    resolver: dict[str, str] | None = None,
    default_namespace: str = "",
) -> QName:
    """Parse QName from text in Clark or prefix notation.

    Args:
        text: QName text ("{ns}local", "prefix:local", or "local")
        resolver: Prefix to namespace URI mapping (for prefix notation)
        default_namespace: Default namespace for unprefixed names

    Returns:
        QName tuple (namespace, local_name)

    Raises:
        ParseError: If prefix is undefined or format is invalid

    Examples:
        >>> parse_qname("{http://www.w3.org/2001/XMLSchema}string")
        QName('http://www.w3.org/2001/XMLSchema', 'string')

        >>> parse_qname("xs:string", resolver={"xs": "http://www.w3.org/2001/XMLSchema"})
        QName('http://www.w3.org/2001/XMLSchema', 'string')

        >>> parse_qname("localName", default_namespace="http://example.com")
        QName('http://example.com', 'localName')
    """
    if not text or not text.strip():
        msg = "QName text cannot be empty"
        raise ParseError(msg)

    text = text.strip()

    # Clark notation: {namespace}localName
    if match := _CLARK_PATTERN.match(text):
        namespace, local_name = match.groups()
        return QName(namespace, local_name)

    # Prefix notation: prefix:localName
    if ":" in text:
        prefix, local_name = text.split(":", 1)

        if not prefix:
            msg = f"Empty prefix in QName: '{text}'"
            raise ParseError(msg)

        if not local_name:
            msg = f"Empty local name in QName: '{text}'"
            raise ParseError(msg)

        if resolver is None:
            msg = f"No namespace resolver provided for prefixed QName: '{text}'"
            raise ParseError(msg)

        if prefix not in resolver:
            msg = f"Undefined namespace prefix: '{prefix}' in QName: '{text}'"
            raise ParseError(msg)

        namespace = resolver[prefix]
        return QName(namespace, local_name)

    # No prefix: use default namespace
    return QName(default_namespace, text)


def split_qname(text: str) -> tuple[str | None, str]:
    """Split QName into prefix and local name.

    Args:
        text: QName text ("prefix:local" or "local")

    Returns:
        Tuple of (prefix or None, local_name)

    Examples:
        >>> split_qname("xs:string")
        ('xs', 'string')

        >>> split_qname("localName")
        (None, 'localName')
    """
    if ":" in text:
        prefix, local = text.split(":", 1)
        return (prefix, local)
    return (None, text)


def is_ncname(name: str) -> bool:
    """Check if name is a valid NCName (no colon name).

    NCName: Names without colons, as defined in XML Namespaces.

    Args:
        name: Name to validate

    Returns:
        True if valid NCName

    Note:
        Simplified validation - full XML NCName has complex Unicode rules.
    """
    if not name:
        return False

    # Simplified: alphanumeric + underscore, dash, dot
    # First char: letter or underscore
    # Following: letter, digit, underscore, dash, dot
    return (
        name[0].isalpha() or name[0] == "_"
    ) and all(
        c.isalnum() or c in "_-." for c in name
    )
