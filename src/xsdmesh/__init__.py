"""XSDMesh - Blazing fast XSD 1.1 parser with in-memory schema graph.

A Python library for parsing XSD 1.1 schemas into a structured graph representation
for validation, analysis, and transformations.
"""

from xsdmesh.exceptions import (
    CacheError,
    CircularReferenceError,
    FrozenError,
    NamespaceError,
    ParseError,
    ResolutionError,
    SchemaImportError,
    SchemaStructureError,
    ValidationError,
    XMLSyntaxError,
    XSDMeshError,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    # Exceptions
    "XSDMeshError",
    "FrozenError",
    "ParseError",
    "XMLSyntaxError",
    "SchemaStructureError",
    "NamespaceError",
    "ValidationError",
    "ResolutionError",
    "CircularReferenceError",
    "CacheError",
    "SchemaImportError",
]
