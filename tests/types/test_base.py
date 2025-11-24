"""Tests for types/base.py: Component, TypeReference, ValidationContext, ValidationResult."""

from __future__ import annotations

from typing import Any

import pytest

from xsdmesh.exceptions import FrozenError, ResolutionError, ValidationError
from xsdmesh.types import (
    Component,
    TypeReference,
    ValidationContext,
    ValidationResult,
)
from xsdmesh.types.qname import QName

# =============================================================================
# Test Component - concrete implementation for testing ABC
# =============================================================================


class ConcreteComponent(Component):
    """Concrete Component for testing ABC functionality."""

    def __init__(
        self,
        *,
        name: str | None = None,
        target_namespace: str | None = None,
        annotations: list[Any] | None = None,
        child: Component | None = None,
    ) -> None:
        super().__init__(name=name, target_namespace=target_namespace, annotations=annotations)
        self.child = child

    def validate(self, value: Any, context: ValidationContext) -> ValidationResult:
        """Simple validation: accept strings, reject others."""
        if isinstance(value, str):
            return ValidationResult.success(value)
        return ValidationResult.failure([ValidationError("Expected string")])

    def _freeze_children(self) -> None:
        """Freeze child component if present."""
        if self.child is not None:
            self.child.freeze()


class MockRegistry:
    """Mock registry implementing ComponentLookup protocol."""

    def __init__(self, components: dict[QName, Component] | None = None) -> None:
        self._components: dict[QName, Component] = components or {}

    def register(self, component: Component) -> None:
        self._components[component.qname] = component

    def lookup(self, qname: QName) -> Component | None:
        return self._components.get(qname)


# =============================================================================
# TestComponent - Component ABC tests
# =============================================================================


class TestComponentInit:
    """Tests for Component initialization."""

    def test_init_with_name_and_namespace(self) -> None:
        """Test initialization with name and namespace."""
        comp = ConcreteComponent(name="myType", target_namespace="http://example.com")
        assert comp.name == "myType"
        assert comp.target_namespace == "http://example.com"
        assert not comp.is_frozen

    def test_init_anonymous(self) -> None:
        """Test anonymous component (no name)."""
        comp = ConcreteComponent()
        assert comp.name is None
        assert comp.target_namespace is None

    def test_init_with_annotations(self) -> None:
        """Test initialization with annotations stored as weak refs."""

        # Use objects that support weakref (classes do, dicts don't)
        class Annotation:
            def __init__(self, doc: str) -> None:
                self.doc = doc

        ann1 = Annotation("First annotation")
        ann2 = Annotation("Second annotation")
        comp = ConcreteComponent(annotations=[ann1, ann2])

        # Annotations accessible while objects exist
        assert len(comp.annotations) == 2
        assert comp.annotations[0] is ann1
        assert comp.annotations[1] is ann2

    def test_annotations_weak_reference(self) -> None:
        """Test that annotations are stored as weak references."""
        import weakref

        class Annotation:
            def __init__(self, doc: str) -> None:
                self.doc = doc

        comp = ConcreteComponent()

        # Create annotation and manually add weak ref
        ann = Annotation("test")
        comp._annotation_refs.append(weakref.ref(ann))
        assert len(comp.annotations) == 1

        # Delete strong reference - weak ref should become dead
        del ann
        # Annotations list filters out dead refs
        assert len(comp.annotations) == 0


class TestComponentQName:
    """Tests for Component.qname property."""

    def test_qname_with_namespace(self) -> None:
        """Test qname with namespace."""
        comp = ConcreteComponent(name="myType", target_namespace="http://example.com")
        assert comp.qname == QName("http://example.com", "myType")

    def test_qname_without_namespace(self) -> None:
        """Test qname without namespace uses empty string."""
        comp = ConcreteComponent(name="myType")
        assert comp.qname == QName("", "myType")

    def test_qname_anonymous(self) -> None:
        """Test qname for anonymous component."""
        comp = ConcreteComponent()
        assert comp.qname == QName("", "")


class TestComponentFreeze:
    """Tests for Component.freeze() and immutability."""

    def test_freeze_sets_frozen_flag(self) -> None:
        """Test that freeze() sets is_frozen to True."""
        comp = ConcreteComponent(name="test")
        assert not comp.is_frozen
        comp.freeze()
        assert comp.is_frozen

    def test_freeze_idempotent(self) -> None:
        """Test that freeze() can be called multiple times."""
        comp = ConcreteComponent(name="test")
        comp.freeze()
        comp.freeze()  # Should not raise
        assert comp.is_frozen

    def test_freeze_children_called(self) -> None:
        """Test that _freeze_children() is called during freeze()."""
        child = ConcreteComponent(name="child")
        parent = ConcreteComponent(name="parent", child=child)

        assert not child.is_frozen
        parent.freeze()

        # Parent's _freeze_children() should have frozen child
        assert child.is_frozen

    def test_frozen_component_rejects_modification(self) -> None:
        """Test that frozen component raises FrozenError on modification."""
        comp = ConcreteComponent(name="test")
        comp.freeze()

        with pytest.raises(FrozenError) as exc_info:
            comp.name = "new_name"

        assert "frozen" in str(exc_info.value).lower()

    def test_unfrozen_component_allows_modification(self) -> None:
        """Test that unfrozen component allows modification."""
        comp = ConcreteComponent(name="test")
        comp.name = "new_name"
        assert comp.name == "new_name"


class TestComponentApply:
    """Tests for Component.apply() extensibility hook."""

    def test_apply_returns_function_result(self) -> None:
        """Test that apply() returns the result of the applied function."""
        comp = ConcreteComponent(name="test", target_namespace="http://example.com")

        def get_name(c: Component) -> str:
            return c.name or ""

        result = comp.apply(get_name)
        assert result == "test"

    def test_apply_with_match_case(self) -> None:
        """Test apply() with match/case pattern matching."""
        comp = ConcreteComponent(name="test")

        def to_dict(c: Component) -> dict[str, Any]:
            match c:
                case ConcreteComponent(name=n):
                    return {"type": "concrete", "name": n}
                case _:
                    return {"type": "unknown"}

        result = comp.apply(to_dict)
        assert result == {"type": "concrete", "name": "test"}

    def test_apply_with_frozen_component(self) -> None:
        """Test that apply() works on frozen components (read-only)."""
        comp = ConcreteComponent(name="test")
        comp.freeze()

        def get_qname(c: Component) -> QName:
            return c.qname

        result = comp.apply(get_qname)
        assert result == QName("", "test")


class TestComponentRepr:
    """Tests for Component.__repr__()."""

    def test_repr_unfrozen(self) -> None:
        """Test repr for unfrozen component."""
        comp = ConcreteComponent(name="test", target_namespace="http://example.com")
        repr_str = repr(comp)
        assert "ConcreteComponent" in repr_str
        assert "test" in repr_str
        assert "frozen" not in repr_str.lower()

    def test_repr_frozen(self) -> None:
        """Test repr for frozen component."""
        comp = ConcreteComponent(name="test")
        comp.freeze()
        repr_str = repr(comp)
        assert "frozen" in repr_str.lower()


class TestComponentValidate:
    """Tests for Component.validate() abstract method."""

    def test_validate_success(self) -> None:
        """Test successful validation."""
        comp = ConcreteComponent(name="test")
        result = comp.validate("hello", ValidationContext())
        assert result.valid
        assert result.value == "hello"

    def test_validate_failure(self) -> None:
        """Test failed validation."""
        comp = ConcreteComponent(name="test")
        result = comp.validate(123, ValidationContext())
        assert not result.valid
        assert len(result.errors) == 1


# =============================================================================
# TestTypeReference
# =============================================================================


class TestTypeReference:
    """Tests for TypeReference lazy resolution."""

    def test_resolve_success(self) -> None:
        """Test successful type resolution."""
        target = ConcreteComponent(name="TargetType", target_namespace="http://example.com")
        registry = MockRegistry()
        registry.register(target)

        ref = TypeReference(QName("http://example.com", "TargetType"))
        assert not ref.is_resolved

        resolved = ref.resolve(registry)
        assert resolved is target
        assert ref.is_resolved

    def test_resolve_caching(self) -> None:
        """Test that resolve() caches result."""
        target = ConcreteComponent(name="TargetType", target_namespace="http://example.com")
        registry = MockRegistry()
        registry.register(target)

        ref = TypeReference(QName("http://example.com", "TargetType"))

        # First resolution
        resolved1 = ref.resolve(registry)

        # Remove from registry
        registry._components.clear()

        # Second resolution should return cached value
        resolved2 = ref.resolve(registry)
        assert resolved1 is resolved2

    def test_resolve_not_found(self) -> None:
        """Test ResolutionError when type not in registry."""
        registry = MockRegistry()
        ref = TypeReference(QName("http://example.com", "NonExistent"))

        with pytest.raises(ResolutionError) as exc_info:
            ref.resolve(registry)

        assert "resolve" in str(exc_info.value).lower()

    def test_is_resolved_property(self) -> None:
        """Test is_resolved property tracks resolution state."""
        ref = TypeReference(QName("http://example.com", "Type"))
        assert not ref.is_resolved

        target = ConcreteComponent(name="Type", target_namespace="http://example.com")
        registry = MockRegistry()
        registry.register(target)

        ref.resolve(registry)
        assert ref.is_resolved

    def test_repr_unresolved(self) -> None:
        """Test repr for unresolved reference."""
        ref = TypeReference(QName("http://example.com", "Type"))
        repr_str = repr(ref)
        assert "TypeReference" in repr_str
        assert "unresolved" in repr_str

    def test_repr_resolved(self) -> None:
        """Test repr for resolved reference."""
        target = ConcreteComponent(name="Type", target_namespace="http://example.com")
        registry = MockRegistry()
        registry.register(target)

        ref = TypeReference(QName("http://example.com", "Type"))
        ref.resolve(registry)

        repr_str = repr(ref)
        assert "resolved" in repr_str


# =============================================================================
# TestValidationContext
# =============================================================================


class TestValidationContext:
    """Tests for ValidationContext."""

    def test_init_defaults(self) -> None:
        """Test default initialization."""
        ctx = ValidationContext()
        assert ctx.registry is None
        assert ctx.namespaces == {}
        assert ctx.id_map == {}
        assert ctx.path == []
        assert ctx.strict is True
        assert ctx.errors == []

    def test_init_with_registry(self) -> None:
        """Test initialization with registry."""
        registry = MockRegistry()
        ctx = ValidationContext(registry=registry)
        assert ctx.registry is registry

    def test_add_error(self) -> None:
        """Test add_error() accumulates errors."""
        ctx = ValidationContext()
        ctx.add_error("First error", code="E001")
        ctx.add_error("Second error", severity="warning")

        assert len(ctx.errors) == 2
        assert "First error" in str(ctx.errors[0])
        assert ctx.errors[0].code == "E001"
        assert ctx.errors[1].severity == "warning"

    def test_add_error_with_path_context(self) -> None:
        """Test that add_error() includes current path in error context."""
        ctx = ValidationContext()
        ctx.push_path("root")
        ctx.push_path("child")
        ctx.add_error("Error at child")

        assert ctx.errors[0].context == "root/child"

    def test_push_pop_path(self) -> None:
        """Test push_path() and pop_path()."""
        ctx = ValidationContext()

        ctx.push_path("root")
        assert ctx.path == ["root"]

        ctx.push_path("child")
        assert ctx.path == ["root", "child"]

        popped = ctx.pop_path()
        assert popped == "child"
        assert ctx.path == ["root"]

    def test_pop_path_empty(self) -> None:
        """Test pop_path() on empty path returns None."""
        ctx = ValidationContext()
        assert ctx.pop_path() is None

    def test_clone(self) -> None:
        """Test clone() creates independent copy."""
        registry = MockRegistry()
        ctx = ValidationContext(
            registry=registry,
            namespaces={"xs": "http://www.w3.org/2001/XMLSchema"},
            strict=False,
        )
        ctx.push_path("root")
        ctx.add_error("Original error")

        cloned = ctx.clone()

        # Same registry reference
        assert cloned.registry is ctx.registry

        # Independent copies of mutable data
        cloned.namespaces["tns"] = "http://example.com"
        assert "tns" not in ctx.namespaces

        cloned.push_path("child")
        assert ctx.path == ["root"]
        assert cloned.path == ["root", "child"]

        cloned.add_error("Cloned error")
        assert len(ctx.errors) == 1
        assert len(cloned.errors) == 2

    def test_repr(self) -> None:
        """Test __repr__() output."""
        ctx = ValidationContext()
        ctx.push_path("root")
        ctx.push_path("child")
        ctx.add_error("Error")

        repr_str = repr(ctx)
        assert "ValidationContext" in repr_str
        assert "root/child" in repr_str
        assert "errors=1" in repr_str


# =============================================================================
# TestValidationResult
# =============================================================================


class TestValidationResult:
    """Tests for ValidationResult."""

    def test_success_factory(self) -> None:
        """Test ValidationResult.success() factory."""
        result = ValidationResult.success("normalized_value")
        assert result.valid is True
        assert result.value == "normalized_value"
        assert result.errors == []
        assert result.warnings == []

    def test_success_with_warnings(self) -> None:
        """Test ValidationResult.success() with warnings."""
        result = ValidationResult.success("value", warnings=["Deprecated format"])
        assert result.valid is True
        assert result.warnings == ["Deprecated format"]

    def test_failure_factory(self) -> None:
        """Test ValidationResult.failure() factory."""
        errors = [ValidationError("Invalid type"), ValidationError("Out of range")]
        result = ValidationResult.failure(errors)
        assert result.valid is False
        assert len(result.errors) == 2
        assert result.value is None

    def test_failure_with_warnings(self) -> None:
        """Test ValidationResult.failure() with warnings."""
        errors = [ValidationError("Error")]
        result = ValidationResult.failure(errors, warnings=["Warning"])
        assert not result.valid
        assert result.warnings == ["Warning"]

    def test_repr_valid(self) -> None:
        """Test __repr__() for valid result."""
        result = ValidationResult.success("value")
        repr_str = repr(result)
        assert "valid" in repr_str
        assert "errors=0" in repr_str

    def test_repr_invalid(self) -> None:
        """Test __repr__() for invalid result."""
        result = ValidationResult.failure([ValidationError("E1"), ValidationError("E2")])
        repr_str = repr(result)
        assert "invalid" in repr_str
        assert "errors=2" in repr_str


# =============================================================================
# TestComponentLookup Protocol
# =============================================================================


class TestComponentLookupProtocol:
    """Tests for ComponentLookup protocol structural typing."""

    def test_mock_registry_satisfies_protocol(self) -> None:
        """Test that MockRegistry satisfies ComponentLookup protocol."""
        registry = MockRegistry()

        # TypeReference.resolve() accepts ComponentLookup
        target = ConcreteComponent(name="Type", target_namespace="http://example.com")
        registry.register(target)

        ref = TypeReference(QName("http://example.com", "Type"))
        # This should work without any explicit Protocol inheritance
        resolved = ref.resolve(registry)
        assert resolved is target

    def test_any_class_with_lookup_satisfies_protocol(self) -> None:
        """Test that any class with lookup() method works."""

        class CustomLookup:
            """Custom lookup without inheriting Protocol."""

            def lookup(self, qname: QName) -> Component | None:
                if qname.local_name == "Found":
                    return ConcreteComponent(name="Found")
                return None

        ref = TypeReference(QName("", "Found"))
        resolved = ref.resolve(CustomLookup())
        assert resolved.name == "Found"
