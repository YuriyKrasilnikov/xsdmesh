"""W3C XSD constants and built-in type definitions.

Defines namespace URIs, built-in types, derivation hierarchy,
and enumeration values per XSD 1.0 specification.
"""

from __future__ import annotations

from typing import Literal

# ============================================================================
# W3C Namespace URIs
# ============================================================================

XSD_NAMESPACE = "http://www.w3.org/2001/XMLSchema"
"""XML Schema namespace URI (xs/xsd prefix)."""

XML_NAMESPACE = "http://www.w3.org/XML/1998/namespace"
"""XML namespace URI (xml prefix) for xml:lang, xml:space, etc."""

XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"
"""XML Schema Instance namespace URI (xsi prefix) for xsi:type, xsi:nil, etc."""

XMLNS_NAMESPACE = "http://www.w3.org/2000/xmlns/"
"""XML Namespace declarations (xmlns prefix)."""

# ============================================================================
# Built-in Primitive Types (19 types)
# ============================================================================

PRIMITIVE_TYPES = frozenset(
    [
        "string",
        "boolean",
        "decimal",
        "float",
        "double",
        "duration",
        "dateTime",
        "time",
        "date",
        "gYearMonth",
        "gYear",
        "gMonthDay",
        "gDay",
        "gMonth",
        "hexBinary",
        "base64Binary",
        "anyURI",
        "QName",
        "NOTATION",
    ]
)
"""XSD 1.0 primitive types - atomic, not derived from other types."""

# ============================================================================
# Built-in Derived Types (25 types)
# ============================================================================

DERIVED_TYPES = frozenset(
    [
        # String-derived
        "normalizedString",
        "token",
        "language",
        "NMTOKEN",
        "NMTOKENS",
        "Name",
        "NCName",
        "ID",
        "IDREF",
        "IDREFS",
        "ENTITY",
        "ENTITIES",
        # Decimal-derived integers
        "integer",
        "nonPositiveInteger",
        "negativeInteger",
        "long",
        "int",
        "short",
        "byte",
        "nonNegativeInteger",
        "unsignedLong",
        "unsignedInt",
        "unsignedShort",
        "unsignedByte",
        "positiveInteger",
    ]
)
"""XSD 1.0 derived types - defined via restriction/list."""

# ============================================================================
# Special Base Types
# ============================================================================

SPECIAL_TYPES = frozenset(["anyType", "anySimpleType", "anyAtomicType"])
"""Special types: anyType (complex base), anySimpleType (simple base), anyAtomicType (XSD 1.1)."""

ALL_BUILTIN_TYPES = PRIMITIVE_TYPES | DERIVED_TYPES | SPECIAL_TYPES
"""All built-in types (primitive + derived + special)."""

# ============================================================================
# Type Derivation Hierarchy
# ============================================================================

TYPE_DERIVATION: dict[str, str | None] = {
    # Primitives derive from anySimpleType
    **dict.fromkeys(PRIMITIVE_TYPES, "anySimpleType"),
    # String derivatives
    "normalizedString": "string",
    "token": "normalizedString",
    "language": "token",
    "NMTOKEN": "token",
    "NMTOKENS": "NMTOKEN",  # list type
    "Name": "token",
    "NCName": "Name",
    "ID": "NCName",
    "IDREF": "NCName",
    "IDREFS": "IDREF",  # list type
    "ENTITY": "NCName",
    "ENTITIES": "ENTITY",  # list type
    # Decimal derivatives
    "integer": "decimal",
    "nonPositiveInteger": "integer",
    "negativeInteger": "nonPositiveInteger",
    "long": "integer",
    "int": "long",
    "short": "int",
    "byte": "short",
    "nonNegativeInteger": "integer",
    "unsignedLong": "nonNegativeInteger",
    "unsignedInt": "unsignedLong",
    "unsignedShort": "unsignedInt",
    "unsignedByte": "unsignedShort",
    "positiveInteger": "nonNegativeInteger",
    # Special types
    "anySimpleType": "anyType",
    "anyAtomicType": "anySimpleType",  # XSD 1.1
    "anyType": None,  # root of hierarchy
}
"""Derivation base for each built-in type."""

# ============================================================================
# List Types (derived via xs:list)
# ============================================================================

LIST_TYPES = frozenset(["NMTOKENS", "IDREFS", "ENTITIES"])
"""Built-in list types (space-separated values)."""

# ============================================================================
# XSD Element Names
# ============================================================================

# Top-level components
ELEMENT_SCHEMA = "schema"
ELEMENT_ELEMENT = "element"
ELEMENT_ATTRIBUTE = "attribute"
ELEMENT_SIMPLE_TYPE = "simpleType"
ELEMENT_COMPLEX_TYPE = "complexType"
ELEMENT_GROUP = "group"
ELEMENT_ATTRIBUTE_GROUP = "attributeGroup"

# Directives
ELEMENT_IMPORT = "import"
ELEMENT_INCLUDE = "include"
ELEMENT_REDEFINE = "redefine"
ELEMENT_OVERRIDE = "override"  # XSD 1.1

# Simple type derivation
ELEMENT_RESTRICTION = "restriction"
ELEMENT_EXTENSION = "extension"
ELEMENT_LIST = "list"
ELEMENT_UNION = "union"

# Complex type content
ELEMENT_SIMPLE_CONTENT = "simpleContent"
ELEMENT_COMPLEX_CONTENT = "complexContent"
ELEMENT_SEQUENCE = "sequence"
ELEMENT_CHOICE = "choice"
ELEMENT_ALL = "all"

# Facets
ELEMENT_MIN_EXCLUSIVE = "minExclusive"
ELEMENT_MIN_INCLUSIVE = "minInclusive"
ELEMENT_MAX_EXCLUSIVE = "maxExclusive"
ELEMENT_MAX_INCLUSIVE = "maxInclusive"
ELEMENT_TOTAL_DIGITS = "totalDigits"
ELEMENT_FRACTION_DIGITS = "fractionDigits"
ELEMENT_LENGTH = "length"
ELEMENT_MIN_LENGTH = "minLength"
ELEMENT_MAX_LENGTH = "maxLength"
ELEMENT_ENUMERATION = "enumeration"
ELEMENT_WHITE_SPACE = "whiteSpace"
ELEMENT_PATTERN = "pattern"

# Wildcards
ELEMENT_ANY = "any"
ELEMENT_ANY_ATTRIBUTE = "anyAttribute"

# Identity constraints
ELEMENT_UNIQUE = "unique"
ELEMENT_KEY = "key"
ELEMENT_KEYREF = "keyref"
ELEMENT_SELECTOR = "selector"
ELEMENT_FIELD = "field"

# Annotation
ELEMENT_ANNOTATION = "annotation"
ELEMENT_DOCUMENTATION = "documentation"
ELEMENT_APPINFO = "appinfo"

# ============================================================================
# XSD Attribute Names
# ============================================================================

ATTR_NAME = "name"
ATTR_TYPE = "type"
ATTR_REF = "ref"
ATTR_BASE = "base"
ATTR_ITEM_TYPE = "itemType"
ATTR_MEMBER_TYPES = "memberTypes"

# Schema attributes
ATTR_TARGET_NAMESPACE = "targetNamespace"
ATTR_ELEMENT_FORM_DEFAULT = "elementFormDefault"
ATTR_ATTRIBUTE_FORM_DEFAULT = "attributeFormDefault"
ATTR_BLOCK_DEFAULT = "blockDefault"
ATTR_FINAL_DEFAULT = "finalDefault"
ATTR_VERSION = "version"

# Occurrence constraints
ATTR_MIN_OCCURS = "minOccurs"
ATTR_MAX_OCCURS = "maxOccurs"

# Attribute constraints
ATTR_USE = "use"
ATTR_DEFAULT = "default"
ATTR_FIXED = "fixed"

# Derivation control
ATTR_ABSTRACT = "abstract"
ATTR_BLOCK = "block"
ATTR_FINAL = "final"

# Element-specific
ATTR_NILLABLE = "nillable"
ATTR_SUBSTITUTION_GROUP = "substitutionGroup"

# Wildcard
ATTR_NAMESPACE = "namespace"
ATTR_PROCESS_CONTENTS = "processContents"

# Import/Include
ATTR_SCHEMA_LOCATION = "schemaLocation"

# Mixed content
ATTR_MIXED = "mixed"

# Facet value
ATTR_VALUE = "value"

# XPath (XSD 1.1)
ATTR_XPATH = "xpath"
ATTR_TEST = "test"

# ============================================================================
# Enumeration Types
# ============================================================================

DerivationMethod = Literal["restriction", "extension", "substitution", "list", "union"]
"""Type derivation methods."""

FormType = Literal["qualified", "unqualified"]
"""Namespace qualification form."""

UseType = Literal["required", "optional", "prohibited"]
"""Attribute use type."""

ProcessContents = Literal["strict", "lax", "skip"]
"""Wildcard processing mode."""

WhiteSpaceAction = Literal["preserve", "replace", "collapse"]
"""Whitespace normalization action."""

BlockSet = Literal["#all", "extension", "restriction", "substitution"]
"""Block derivation/substitution set."""

FinalSet = Literal["#all", "extension", "restriction", "list", "union"]
"""Final derivation set."""

# ============================================================================
# Default Values
# ============================================================================

DEFAULT_FORM: FormType = "unqualified"
"""Default form for elements/attributes (per XSD 1.0 spec)."""

DEFAULT_MIN_OCCURS = 1
"""Default minOccurs value."""

DEFAULT_MAX_OCCURS = 1
"""Default maxOccurs value."""

UNBOUNDED = "unbounded"
"""Unbounded maxOccurs value."""

# ============================================================================
# Facet Names Set
# ============================================================================

FACET_NAMES = frozenset(
    [
        "minExclusive",
        "minInclusive",
        "maxExclusive",
        "maxInclusive",
        "totalDigits",
        "fractionDigits",
        "length",
        "minLength",
        "maxLength",
        "enumeration",
        "whiteSpace",
        "pattern",
        "assertion",  # XSD 1.1
        "explicitTimezone",  # XSD 1.1
    ]
)
"""All facet element names."""

NUMERIC_FACETS = frozenset(
    [
        "minExclusive",
        "minInclusive",
        "maxExclusive",
        "maxInclusive",
        "totalDigits",
        "fractionDigits",
    ]
)
"""Numeric range and precision facets."""

LENGTH_FACETS = frozenset(["length", "minLength", "maxLength"])
"""String/list length facets."""

# ============================================================================
# W3C Error Code Prefixes
# ============================================================================

ERROR_CODE_SCHEMA = "src-"
"""Schema component constraint error code prefix."""

ERROR_CODE_ELEMENT = "e-props-correct"
"""Element properties constraint."""

ERROR_CODE_ATTRIBUTE = "a-props-correct"
"""Attribute properties constraint."""

ERROR_CODE_TYPE = "st-props-correct"
"""Simple type properties constraint."""

ERROR_CODE_COMPLEX = "ct-props-correct"
"""Complex type properties constraint."""
