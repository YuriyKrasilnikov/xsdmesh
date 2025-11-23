"""Debug utilities for AST inspection and pretty-printing.

Provides utilities to format and display XSD component trees.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Any


def format_ast(obj: Any, *, indent: int = 0, max_depth: int = 10) -> str:
    """Format AST node as indented tree.

    Recursively formats dataclass instances with nested structure.

    Args:
        obj: Object to format (typically dataclass)
        indent: Current indentation level
        max_depth: Maximum recursion depth

    Returns:
        Formatted string representation
    """
    if max_depth <= 0:
        return "..."

    prefix = "  " * indent

    # Handle None
    if obj is None:
        return "None"

    # Handle primitives
    if isinstance(obj, (str, int, float, bool)):
        return repr(obj)

    # Handle lists
    if isinstance(obj, list):
        if not obj:
            return "[]"
        items = [
            f"{prefix}  - {format_ast(item, indent=indent + 1, max_depth=max_depth - 1)}"
            for item in obj
        ]
        return "[\n" + "\n".join(items) + f"\n{prefix}]"

    # Handle dicts
    if isinstance(obj, dict):
        if not obj:
            return "{}"
        items = [
            f"{prefix}  {k}: {format_ast(v, indent=indent + 1, max_depth=max_depth - 1)}"
            for k, v in obj.items()
        ]
        return "{\n" + "\n".join(items) + f"\n{prefix}" + "}"

    # Handle sets
    if isinstance(obj, (set, frozenset)):
        if not obj:
            return "{}"
        return "{" + ", ".join(repr(x) for x in sorted(obj, key=str)) + "}"

    # Handle dataclasses
    if is_dataclass(obj):
        class_name = obj.__class__.__name__
        field_strs = []
        for field in fields(obj):
            value = getattr(obj, field.name)
            # Skip None and empty collections for brevity
            if value is None:
                continue
            if isinstance(value, (list, dict, set, frozenset)) and not value:
                continue
            formatted = format_ast(value, indent=indent + 1, max_depth=max_depth - 1)
            field_strs.append(f"{prefix}  {field.name}={formatted}")

        if not field_strs:
            return f"{class_name}()"
        return f"{class_name}(\n" + ",\n".join(field_strs) + f"\n{prefix})"

    # Fallback to repr
    return repr(obj)


def pprint_component(component: Any, *, max_depth: int = 5) -> None:
    """Pretty-print XSD component to stdout.

    Args:
        component: Component to print
        max_depth: Maximum nesting depth
    """
    print(format_ast(component, max_depth=max_depth))


def format_qname(namespace: str | None, local_name: str) -> str:
    """Format QName for display.

    Args:
        namespace: Namespace URI or None
        local_name: Local name

    Returns:
        Formatted QName string
    """
    if namespace:
        return f"{{{namespace}}}{local_name}"
    return local_name


def truncate(text: str, max_len: int = 80) -> str:
    """Truncate text with ellipsis.

    Args:
        text: Text to truncate
        max_len: Maximum length

    Returns:
        Truncated text
    """
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."
