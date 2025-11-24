"""Tests for types/registry.py: ComponentRegistry with Bloom filter."""

from __future__ import annotations

from typing import Any

import pytest

from xsdmesh.types import (
    Component,
    ComponentRegistry,
    TypeReference,
    ValidationContext,
    ValidationResult,
)
from xsdmesh.types.qname import QName

# =============================================================================
# Test fixture: Concrete Component for testing
# =============================================================================


class MockComponent(Component):
    """Concrete Component for registry testing."""

    def validate(self, value: Any, context: ValidationContext) -> ValidationResult:
        return ValidationResult.success(value)


def make_component(name: str, namespace: str = "http://example.com") -> MockComponent:
    """Factory for creating test components."""
    return MockComponent(name=name, target_namespace=namespace)


# =============================================================================
# MockComponentRegistry - Basic Operations
# =============================================================================


class TestRegistryBasicOperations:
    """Tests for basic registry operations."""

    def test_init_default(self) -> None:
        """Test default initialization."""
        registry: ComponentRegistry[MockComponent] = ComponentRegistry()
        assert len(registry) == 0
        stats = registry.stats()
        assert stats.total_components == 0
        assert stats.namespaces == 0

    def test_init_custom_params(self) -> None:
        """Test initialization with custom parameters."""
        registry: ComponentRegistry[MockComponent] = ComponentRegistry(
            expected_components=5000,
            bloom_fp_rate=0.01,
        )
        assert len(registry) == 0

    def test_register_single(self) -> None:
        """Test registering single component."""
        registry: ComponentRegistry[MockComponent] = ComponentRegistry()
        comp = make_component("MyType")

        registry.register(comp)

        assert len(registry) == 1
        assert comp.qname in registry

    def test_register_duplicate_raises(self) -> None:
        """Test that duplicate registration raises ValueError."""
        registry: ComponentRegistry[MockComponent] = ComponentRegistry()
        comp1 = make_component("MyType")
        comp2 = make_component("MyType")  # Same QName

        registry.register(comp1)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(comp2)

    def test_register_multiple(self) -> None:
        """Test registering multiple components."""
        registry: ComponentRegistry[MockComponent] = ComponentRegistry()

        for i in range(10):
            registry.register(make_component(f"Type{i}"))

        assert len(registry) == 10


class TestRegistryLookup:
    """Tests for registry lookup operations."""

    def test_lookup_found(self) -> None:
        """Test lookup returns component when found."""
        registry: ComponentRegistry[MockComponent] = ComponentRegistry()
        comp = make_component("MyType")
        registry.register(comp)

        result = registry.lookup(comp.qname)
        assert result is comp

    def test_lookup_not_found(self) -> None:
        """Test lookup returns None when not found."""
        registry: ComponentRegistry[MockComponent] = ComponentRegistry()
        qname = QName("http://example.com", "NonExistent")

        result = registry.lookup(qname)
        assert result is None

    def test_lookup_wrong_namespace(self) -> None:
        """Test lookup fails with wrong namespace."""
        registry: ComponentRegistry[MockComponent] = ComponentRegistry()
        comp = make_component("MyType", namespace="http://ns1.com")
        registry.register(comp)

        result = registry.lookup(QName("http://ns2.com", "MyType"))
        assert result is None

    def test_get_with_default(self) -> None:
        """Test get() returns default when not found."""
        registry: ComponentRegistry[MockComponent] = ComponentRegistry()
        default = make_component("Default")

        result = registry.get(QName("http://x.com", "X"), default)
        assert result is default

    def test_getitem_found(self) -> None:
        """Test __getitem__ returns component."""
        registry: ComponentRegistry[MockComponent] = ComponentRegistry()
        comp = make_component("MyType")
        registry.register(comp)

        result = registry[comp.qname]
        assert result is comp

    def test_getitem_not_found_raises(self) -> None:
        """Test __getitem__ raises KeyError when not found."""
        registry: ComponentRegistry[MockComponent] = ComponentRegistry()

        with pytest.raises(KeyError):
            _ = registry[QName("http://x.com", "X")]


class TestRegistryBloomFilter:
    """Tests for Bloom filter negative lookup optimization."""

    def test_bloom_negative_fast_path(self) -> None:
        """Test that Bloom filter provides fast negative lookup."""
        registry: ComponentRegistry[MockComponent] = ComponentRegistry()

        # Register some components
        for i in range(100):
            registry.register(make_component(f"Type{i}"))

        # Lookup non-existent - should hit Bloom fast path
        result = registry.lookup(QName("http://example.com", "NonExistent"))
        assert result is None

    def test_bloom_false_positive_handled(self) -> None:
        """Test that Bloom false positives are handled correctly."""
        registry: ComponentRegistry[MockComponent] = ComponentRegistry(
            expected_components=10,
            bloom_fp_rate=0.5,  # High FP rate for testing
        )

        registry.register(make_component("Exists"))

        # Even with high FP rate, lookup should return None for non-existent
        result = registry.lookup(QName("http://example.com", "NotExists"))
        assert result is None

    def test_bloom_stats(self) -> None:
        """Test Bloom filter statistics."""
        registry: ComponentRegistry[MockComponent] = ComponentRegistry(
            expected_components=1000,
        )

        for i in range(100):
            registry.register(make_component(f"Type{i}"))

        stats = registry.stats()
        assert stats.bloom_size_bytes > 0
        # FP rate should be low with 100 elements when sized for 1000
        assert stats.bloom_false_positive_rate < 0.01


class TestRegistryNamespaceIndex:
    """Tests for namespace-based indexing."""

    def test_by_namespace_single(self) -> None:
        """Test by_namespace returns components in namespace."""
        registry: ComponentRegistry[MockComponent] = ComponentRegistry()

        comp1 = make_component("Type1", "http://ns1.com")
        comp2 = make_component("Type2", "http://ns1.com")
        comp3 = make_component("Type3", "http://ns2.com")

        registry.register(comp1)
        registry.register(comp2)
        registry.register(comp3)

        ns1_components = registry.by_namespace("http://ns1.com")
        assert len(ns1_components) == 2
        assert comp1 in ns1_components
        assert comp2 in ns1_components

    def test_by_namespace_empty(self) -> None:
        """Test by_namespace returns empty list for unknown namespace."""
        registry: ComponentRegistry[MockComponent] = ComponentRegistry()
        registry.register(make_component("Type1"))

        result = registry.by_namespace("http://unknown.com")
        assert result == []

    def test_namespaces_list(self) -> None:
        """Test namespaces() returns all registered namespaces."""
        registry: ComponentRegistry[MockComponent] = ComponentRegistry()

        registry.register(make_component("T1", "http://ns1.com"))
        registry.register(make_component("T2", "http://ns2.com"))
        registry.register(make_component("T3", "http://ns1.com"))

        namespaces = registry.namespaces()
        assert len(namespaces) == 2
        assert "http://ns1.com" in namespaces
        assert "http://ns2.com" in namespaces


class TestRegistryDeferredResolution:
    """Tests for deferred resolution callbacks."""

    def test_defer_already_registered(self) -> None:
        """Test defer_resolution invokes callback immediately if registered."""
        registry: ComponentRegistry[MockComponent] = ComponentRegistry()
        comp = make_component("MyType")
        registry.register(comp)

        resolved: list[MockComponent] = []
        immediate = registry.defer_resolution(comp.qname, resolved.append)

        assert immediate is True
        assert len(resolved) == 1
        assert resolved[0] is comp

    def test_defer_not_registered(self) -> None:
        """Test defer_resolution stores callback for later."""
        registry: ComponentRegistry[MockComponent] = ComponentRegistry()
        qname = QName("http://example.com", "Future")

        resolved: list[MockComponent] = []
        immediate = registry.defer_resolution(qname, resolved.append)

        assert immediate is False
        assert len(resolved) == 0
        assert qname in registry.pending_qnames()

    def test_defer_callback_on_register(self) -> None:
        """Test deferred callback is invoked when component registered."""
        registry: ComponentRegistry[MockComponent] = ComponentRegistry()
        qname = QName("http://example.com", "Future")

        resolved: list[MockComponent] = []
        registry.defer_resolution(qname, resolved.append)

        # Now register the component
        comp = MockComponent(name="Future", target_namespace="http://example.com")
        registry.register(comp)

        assert len(resolved) == 1
        assert resolved[0] is comp
        assert qname not in registry.pending_qnames()

    def test_defer_multiple_callbacks(self) -> None:
        """Test multiple callbacks for same QName."""
        registry: ComponentRegistry[MockComponent] = ComponentRegistry()
        qname = QName("http://example.com", "Shared")

        results1: list[MockComponent] = []
        results2: list[MockComponent] = []

        registry.defer_resolution(qname, results1.append)
        registry.defer_resolution(qname, results2.append)

        comp = MockComponent(name="Shared", target_namespace="http://example.com")
        registry.register(comp)

        assert len(results1) == 1
        assert len(results2) == 1


class TestRegistryIteration:
    """Tests for registry iteration."""

    def test_iter_qnames(self) -> None:
        """Test iterating over QNames."""
        registry: ComponentRegistry[MockComponent] = ComponentRegistry()

        comps = [make_component(f"Type{i}") for i in range(5)]
        for comp in comps:
            registry.register(comp)

        qnames = list(registry)
        assert len(qnames) == 5
        for comp in comps:
            assert comp.qname in qnames

    def test_all_components(self) -> None:
        """Test all_components returns all registered components."""
        registry: ComponentRegistry[MockComponent] = ComponentRegistry()

        comps = [make_component(f"Type{i}") for i in range(5)]
        for comp in comps:
            registry.register(comp)

        all_comps = registry.all_components()
        assert len(all_comps) == 5
        for comp in comps:
            assert comp in all_comps


class TestRegistryWithTypeReference:
    """Tests for registry integration with TypeReference."""

    def test_type_reference_resolve(self) -> None:
        """Test TypeReference resolves using registry."""
        registry: ComponentRegistry[MockComponent] = ComponentRegistry()
        target = make_component("TargetType")
        registry.register(target)

        ref = TypeReference(target.qname)
        resolved = ref.resolve(registry)

        assert resolved is target

    def test_type_reference_not_found(self) -> None:
        """Test TypeReference raises when not in registry."""
        from xsdmesh.exceptions import ResolutionError

        registry: ComponentRegistry[MockComponent] = ComponentRegistry()
        ref = TypeReference(QName("http://x.com", "Missing"))

        with pytest.raises(ResolutionError):
            ref.resolve(registry)


class TestRegistryStats:
    """Tests for RegistryStats dataclass."""

    def test_stats_empty(self) -> None:
        """Test stats for empty registry."""
        registry: ComponentRegistry[MockComponent] = ComponentRegistry()
        stats = registry.stats()

        assert stats.total_components == 0
        assert stats.namespaces == 0
        assert stats.pending_callbacks == 0
        assert stats.bloom_size_bytes > 0

    def test_stats_populated(self) -> None:
        """Test stats for populated registry."""
        registry: ComponentRegistry[MockComponent] = ComponentRegistry()

        for i in range(50):
            ns = f"http://ns{i % 5}.com"
            registry.register(make_component(f"Type{i}", ns))

        # Add pending callback
        registry.defer_resolution(QName("http://x.com", "Future"), lambda x: None)

        stats = registry.stats()
        assert stats.total_components == 50
        assert stats.namespaces == 5
        assert stats.pending_callbacks == 1


class TestRegistryClear:
    """Tests for registry clear operation."""

    def test_clear(self) -> None:
        """Test clear removes all components."""
        registry: ComponentRegistry[MockComponent] = ComponentRegistry()

        for i in range(10):
            registry.register(make_component(f"Type{i}"))
        registry.defer_resolution(QName("http://x.com", "X"), lambda x: None)

        registry.clear()

        assert len(registry) == 0
        assert registry.namespaces() == []
        assert registry.pending_qnames() == []


class TestRegistryRepr:
    """Tests for registry string representation."""

    def test_repr(self) -> None:
        """Test __repr__ output."""
        registry: ComponentRegistry[MockComponent] = ComponentRegistry()
        registry.register(make_component("Type1"))

        repr_str = repr(registry)
        assert "ComponentRegistry" in repr_str
        assert "components=1" in repr_str
