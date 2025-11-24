"""Core type system components: Component ABC, TypeReference, ValidationContext.

Provides immutable AST foundation with freeze() mechanism, apply() hook for extensibility,
and lazy type resolution via TypeReference.

Uses Python 3.10+ match/case for structural pattern matching instead of visitor pattern.
"""

from __future__ import annotations

import weakref
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal, Protocol, TypeVar

from xsdmesh.exceptions import FrozenError, ResolutionError, ValidationError
from xsdmesh.types.qname import QName

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Self


# Type variable for generic operations
T = TypeVar("T")


class ComponentLookup(Protocol):
    """Protocol for registry with component lookup capability.

    Any object implementing lookup(qname) -> Component | None satisfies this protocol
    via structural typing (duck typing). This enables type-safe dependency injection
    without circular imports.

    Examples of valid implementations:
        - ComponentRegistry (types/registry.py) - main registry
        - Mock objects for testing
        - Alternative registries (InMemoryRegistry, RemoteRegistry)

    Structural typing means no explicit inheritance required:
        class MyRegistry:  # No need to inherit ComponentLookup
            def lookup(self, qname: QName) -> Component | None:
                return ...  # Automatically satisfies protocol
    """

    def lookup(self, qname: QName) -> Component | None:
        """Look up component by qualified name.

        Args:
            qname: Qualified name (namespace + local name)

        Returns:
            Component if found in registry, None otherwise

        Invariants:
            - Deterministic: same qname always returns same result
            - Thread-safe: safe to call from multiple threads
            - No side effects: does not modify qname or registry state
        """
        ...


class Component(ABC):
    """Base class for all XSD schema components.

    Features:
    - Immutability via freeze() after construction
    - QName identity (namespace, name)
    - Validation interface
    - apply() hook for extensibility (use with match/case)
    - Weak references for annotations

    Lifecycle:
    1. Create mutable component during parsing
    2. Populate fields from XML attributes
    3. freeze() after complete initialization
    4. Immutable in Registry for thread-safety

    Extensibility via apply():
        def to_json(comp: Component) -> dict:
            match comp:
                case SimpleType(variety="atomic"):
                    return {"type": "simple"}
                case ComplexType(...):
                    return {"type": "complex"}

        result = component.apply(to_json)
    """

    def __init__(
        self,
        *,
        name: str | None = None,
        target_namespace: str | None = None,
        annotations: list[Any] | None = None,
    ) -> None:
        """Initialize component.

        Args:
            name: Local name (None for anonymous components)
            target_namespace: Namespace URI
            annotations: xs:annotation elements (stored as weak refs)
        """
        # Set _frozen first to allow initial attribute setting
        object.__setattr__(self, "_frozen", False)

        self.name = name
        self.target_namespace = target_namespace

        # Store annotations as weak references to prevent memory leaks
        self._annotation_refs: list[weakref.ref[Any]] = []
        if annotations:
            self._annotation_refs = [weakref.ref(a) for a in annotations]

    @property
    def qname(self) -> QName:
        """Qualified name: (namespace, local_name).

        Returns:
            QName tuple, empty namespace if None
        """
        return QName(self.target_namespace or "", self.name or "")

    @property
    def annotations(self) -> list[Any]:
        """Get annotations (dereferencing weak refs).

        Returns:
            List of alive annotation objects
        """
        return [ref() for ref in self._annotation_refs if ref() is not None]

    @property
    def is_frozen(self) -> bool:
        """Check if component is immutable."""
        return getattr(self, "_frozen", False)

    def freeze(self) -> None:
        """Make component immutable.

        Recursively freezes all child components.
        Call after complete initialization.
        """
        if self.is_frozen:
            return

        # Freeze self
        object.__setattr__(self, "_frozen", True)

        # Freeze children (override in subclasses)
        self._freeze_children()

    def _freeze_children(self) -> None:  # noqa: B027
        """Template Method hook for freezing nested components.

        Override in subclasses that contain child Components requiring freeze.
        Default no-op is correct for leaf components without children.

        This is a 'hook method' per Template Method pattern, NOT an abstract
        method. Subclasses MAY override if needed, but are not required to.

        Example override::

            def _freeze_children(self) -> None:
                if self.base_type_ref and self.base_type_ref._resolved:
                    self.base_type_ref._resolved.freeze()

        Note: B027 suppressed - empty hook method is intentional design.
        See: https://github.com/PyCQA/flake8-bugbear/issues/301
        """
        pass

    def __setattr__(self, name: str, value: Any) -> None:  # noqa: ANN401
        """Prevent attribute modification after freeze.

        Args:
            name: Attribute name
            value: Attribute value

        Raises:
            FrozenError: If component is frozen and attribute is not _frozen
        """
        if name == "_frozen" or not self.is_frozen:
            object.__setattr__(self, name, value)
        else:
            msg = f"Cannot modify frozen component: {self.qname}"
            raise FrozenError(msg)

    @abstractmethod
    def validate(self, value: Any, context: ValidationContext) -> ValidationResult:  # noqa: ANN401
        """Validate value against this component.

        Args:
            value: Value to validate
            context: Validation context with schema, namespaces, etc.

        Returns:
            ValidationResult with valid flag, errors, and normalized value
        """
        ...

    def apply(self, func: Callable[[Self], T]) -> T:
        """Apply custom function to component for extensibility.

        Enables user-defined operations without modifying Component hierarchy.
        Users can leverage Python 3.10+ match/case for type-safe processing.

        Args:
            func: Function to apply to this component

        Returns:
            Result of applying func to self

        Example:
            >>> def to_json(comp: Component) -> dict:
            ...     match comp:
            ...         case SimpleType(variety="atomic", name=n):
            ...             return {"type": "simple", "name": n}
            ...         case ComplexType(name=n):
            ...             return {"type": "complex", "name": n}
            >>> result = component.apply(to_json)
        """
        return func(self)

    def __repr__(self) -> str:
        """Debug representation."""
        frozen = " (frozen)" if self.is_frozen else ""
        return f"{self.__class__.__name__}({self.qname}){frozen}"


@dataclass
class TypeReference:
    """Lazy reference to a type component.

    Resolves QName to actual Component on first access.
    Caches resolved component for subsequent calls.

    Usage:
    - base_type references in Restriction
    - item_type in ListType
    - member_types in UnionType
    - element type="xs:string" references
    """

    ref_qname: QName
    _resolved: Component | None = field(default=None, init=False, repr=False)

    def resolve(self, registry: ComponentLookup) -> Component:
        """Resolve QName to component using registry.

        Args:
            registry: Object implementing ComponentLookup protocol (must have lookup method)

        Returns:
            Resolved component (cached after first resolution)

        Raises:
            ResolutionError: If QName cannot be resolved in registry
        """
        # Return cached if already resolved
        if self._resolved is not None:
            return self._resolved

        # Lookup in registry
        component: Component | None = registry.lookup(self.ref_qname)
        if component is None:
            msg = "Cannot resolve type reference"
            raise ResolutionError(
                msg,
                qname=str(self.ref_qname),
                reference_type="type",
            )

        # Cache and return
        self._resolved = component
        return component

    @property
    def is_resolved(self) -> bool:
        """Check if reference has been resolved.

        Returns:
            True if resolved
        """
        return self._resolved is not None

    def __repr__(self) -> str:
        """Debug representation."""
        status = "resolved" if self.is_resolved else "unresolved"
        return f"TypeReference({self.ref_qname}, {status})"


@dataclass
class ValidationContext:
    """Context for validating instance values against schema.

    Tracks:
    - Schema registry for type lookups
    - Active namespace mappings
    - ID/IDREF map for key constraints
    - Current path for error reporting
    - Error accumulation (strict vs permissive mode)
    """

    # Schema registry for type lookups (uses Protocol for type safety)
    registry: ComponentLookup | None = None

    # Active namespace prefixes
    namespaces: dict[str, str] = field(default_factory=dict)

    # ID -> element mapping for keyref validation
    id_map: dict[str, Any] = field(default_factory=dict)

    # XPath-like path for error reporting
    path: list[str] = field(default_factory=list)

    # Fail-fast (True) vs accumulate errors (False)
    strict: bool = True

    # Accumulated errors (used when strict=False)
    errors: list[ValidationError] = field(default_factory=list)

    def add_error(
        self,
        message: str,
        *,
        code: str | None = None,
        severity: Literal["error", "warning", "info"] = "error",
    ) -> None:
        """Add validation error to context.

        Args:
            message: Error description
            code: W3C error code
            severity: Error severity level
        """
        error = ValidationError(
            message,
            code=code,
            severity=severity,
            context="/".join(self.path) if self.path else None,
        )
        self.errors.append(error)

    def push_path(self, segment: str) -> None:
        """Push path segment for nested validation.

        Args:
            segment: Path segment (e.g., element name)
        """
        self.path.append(segment)

    def pop_path(self) -> str | None:
        """Pop path segment after validation.

        Returns:
            Popped segment or None if empty
        """
        return self.path.pop() if self.path else None

    def clone(self) -> ValidationContext:
        """Create independent copy for nested validation.

        Returns:
            New context with same registry and namespaces
        """
        return ValidationContext(
            registry=self.registry,
            namespaces=dict(self.namespaces),
            id_map=dict(self.id_map),
            path=list(self.path),
            strict=self.strict,
            errors=list(self.errors),
        )

    def __repr__(self) -> str:
        """Debug representation."""
        path_str = "/".join(self.path) if self.path else "/"
        return f"ValidationContext(path={path_str}, errors={len(self.errors)})"


@dataclass
class ValidationResult:
    """Result of component validation.

    Contains:
    - valid: Overall validation success
    - errors: List of validation errors
    - value: Normalized/coerced value (None if invalid)
    - warnings: Non-fatal issues
    """

    valid: bool
    errors: list[ValidationError] = field(default_factory=list)
    value: Any = None
    warnings: list[str] = field(default_factory=list)

    @staticmethod
    def success(value: Any, warnings: list[str] | None = None) -> ValidationResult:  # noqa: ANN401
        """Create successful validation result.

        Args:
            value: Validated and normalized value
            warnings: Optional warnings

        Returns:
            ValidationResult with valid=True
        """
        return ValidationResult(
            valid=True,
            value=value,
            warnings=warnings or [],
        )

    @staticmethod
    def failure(
        errors: list[ValidationError], warnings: list[str] | None = None
    ) -> ValidationResult:
        """Create failed validation result.

        Args:
            errors: Validation errors
            warnings: Optional warnings

        Returns:
            ValidationResult with valid=False
        """
        return ValidationResult(
            valid=False,
            errors=errors,
            warnings=warnings or [],
        )

    def __repr__(self) -> str:
        """Debug representation."""
        status = "valid" if self.valid else "invalid"
        err_count = len(self.errors)
        warn_count = len(self.warnings)
        return f"ValidationResult({status}, errors={err_count}, warnings={warn_count})"
