"""XSD type system models.

Object model for XSD types, elements, attributes, and groups.
"""

from xsdmesh.exceptions import FrozenError
from xsdmesh.types.base import (
    Component,
    ComponentLookup,
    TypeReference,
    ValidationContext,
    ValidationResult,
)
from xsdmesh.types.facets import (
    FacetResult,
    FacetValidator,
    LexicalFacets,
    ValueFacets,
    WhitespaceFacet,
)
from xsdmesh.types.qname import QName, is_ncname, parse_qname, split_qname
from xsdmesh.types.registry import ComponentRegistry, RegistryStats
from xsdmesh.types.storage import (
    DictStorage,
    StorageStats,
    StorageStrategy,
    TrieStorage,
    create_storage,
)

__all__ = [
    # Base classes
    "Component",
    "ComponentLookup",
    "FrozenError",
    "TypeReference",
    "ValidationContext",
    "ValidationResult",
    # Registry
    "ComponentRegistry",
    "RegistryStats",
    # Storage strategies
    "StorageStrategy",
    "StorageStats",
    "DictStorage",
    "TrieStorage",
    "create_storage",
    # Facets
    "FacetResult",
    "FacetValidator",
    "LexicalFacets",
    "ValueFacets",
    "WhitespaceFacet",
    # QName utilities
    "QName",
    "parse_qname",
    "split_qname",
    "is_ncname",
]
