"""Tests for types/storage.py: StorageStrategy implementations."""

from __future__ import annotations

from typing import Any

import pytest

from xsdmesh.types import (
    Component,
    DictStorage,
    StorageStrategy,
    TrieStorage,
    ValidationContext,
    ValidationResult,
    create_storage,
)
from xsdmesh.types.qname import QName

# =============================================================================
# Test fixture: Concrete Component for testing
# =============================================================================


class MockComponent(Component):
    """Concrete Component for storage testing."""

    def validate(self, value: Any, context: ValidationContext) -> ValidationResult:
        return ValidationResult.success(value)


def make_component(name: str, namespace: str = "http://example.com") -> MockComponent:
    """Factory for creating test components."""
    return MockComponent(name=name, target_namespace=namespace)


# =============================================================================
# StorageStrategy Protocol Compliance
# =============================================================================


class TestStorageProtocol:
    """Tests that implementations satisfy StorageStrategy Protocol."""

    def test_dict_storage_is_protocol(self) -> None:
        """Test DictStorage satisfies Protocol."""
        storage = DictStorage[MockComponent]()
        assert isinstance(storage, StorageStrategy)

    def test_trie_storage_is_protocol(self) -> None:
        """Test TrieStorage satisfies Protocol."""
        storage = TrieStorage[MockComponent]()
        assert isinstance(storage, StorageStrategy)


# =============================================================================
# DictStorage Tests
# =============================================================================


class TestDictStorageBasic:
    """Tests for DictStorage basic operations."""

    def test_init_empty(self) -> None:
        """Test DictStorage initializes empty."""
        storage = DictStorage[MockComponent]()
        assert len(storage) == 0
        assert storage.namespaces() == []

    def test_store_and_lookup(self) -> None:
        """Test store and lookup component."""
        storage = DictStorage[MockComponent]()
        comp = make_component("MyType")

        storage.store(comp.qname, comp)

        assert len(storage) == 1
        assert storage.lookup(comp.qname) is comp

    def test_store_duplicate_raises(self) -> None:
        """Test store raises on duplicate QName."""
        storage = DictStorage[MockComponent]()
        comp1 = make_component("MyType")
        comp2 = make_component("MyType")

        storage.store(comp1.qname, comp1)

        with pytest.raises(ValueError, match="already registered"):
            storage.store(comp2.qname, comp2)

    def test_lookup_not_found(self) -> None:
        """Test lookup returns None when not found."""
        storage = DictStorage[MockComponent]()
        qname = QName("http://x.com", "X")

        assert storage.lookup(qname) is None

    def test_contains(self) -> None:
        """Test __contains__ operator."""
        storage = DictStorage[MockComponent]()
        comp = make_component("MyType")

        assert comp.qname not in storage
        storage.store(comp.qname, comp)
        assert comp.qname in storage

    def test_remove(self) -> None:
        """Test remove component."""
        storage = DictStorage[MockComponent]()
        comp = make_component("MyType")
        storage.store(comp.qname, comp)

        assert storage.remove(comp.qname) is True
        assert len(storage) == 0
        assert comp.qname not in storage

    def test_remove_not_found(self) -> None:
        """Test remove returns False when not found."""
        storage = DictStorage[MockComponent]()
        qname = QName("http://x.com", "X")

        assert storage.remove(qname) is False


class TestDictStorageNamespace:
    """Tests for DictStorage namespace operations."""

    def test_by_namespace(self) -> None:
        """Test by_namespace returns components in namespace."""
        storage = DictStorage[MockComponent]()
        comp1 = make_component("Type1", "http://ns1.com")
        comp2 = make_component("Type2", "http://ns1.com")
        comp3 = make_component("Type3", "http://ns2.com")

        storage.store(comp1.qname, comp1)
        storage.store(comp2.qname, comp2)
        storage.store(comp3.qname, comp3)

        ns1 = storage.by_namespace("http://ns1.com")
        assert len(ns1) == 2
        assert comp1 in ns1
        assert comp2 in ns1

    def test_by_namespace_empty(self) -> None:
        """Test by_namespace returns empty for unknown namespace."""
        storage = DictStorage[MockComponent]()

        assert storage.by_namespace("http://unknown.com") == []

    def test_by_namespace_prefix(self) -> None:
        """Test by_namespace_prefix with O(n) scan."""
        storage = DictStorage[MockComponent]()
        comp1 = make_component("Type1", "http://example.com/v1")
        comp2 = make_component("Type2", "http://example.com/v2")
        comp3 = make_component("Type3", "http://other.com/v1")

        storage.store(comp1.qname, comp1)
        storage.store(comp2.qname, comp2)
        storage.store(comp3.qname, comp3)

        prefix_comps = storage.by_namespace_prefix("http://example.com/")
        assert len(prefix_comps) == 2
        assert comp1 in prefix_comps
        assert comp2 in prefix_comps

    def test_namespaces(self) -> None:
        """Test namespaces returns all unique namespaces."""
        storage = DictStorage[MockComponent]()
        storage.store(
            make_component("T1", "http://ns1.com").qname, make_component("T1", "http://ns1.com")
        )
        storage.store(
            make_component("T2", "http://ns2.com").qname, make_component("T2", "http://ns2.com")
        )
        storage.store(
            make_component("T3", "http://ns1.com").qname, make_component("T3", "http://ns1.com")
        )

        namespaces = storage.namespaces()
        assert len(namespaces) == 2
        assert "http://ns1.com" in namespaces
        assert "http://ns2.com" in namespaces


class TestDictStorageIteration:
    """Tests for DictStorage iteration."""

    def test_iter(self) -> None:
        """Test iteration over QNames."""
        storage = DictStorage[MockComponent]()
        comp1 = make_component("Type1")
        comp2 = make_component("Type2")

        storage.store(comp1.qname, comp1)
        storage.store(comp2.qname, comp2)

        qnames = list(storage)
        assert len(qnames) == 2
        assert comp1.qname in qnames
        assert comp2.qname in qnames

    def test_all_items(self) -> None:
        """Test all_items returns all components."""
        storage = DictStorage[MockComponent]()
        comp1 = make_component("Type1")
        comp2 = make_component("Type2")

        storage.store(comp1.qname, comp1)
        storage.store(comp2.qname, comp2)

        items = storage.all_items()
        assert len(items) == 2
        assert comp1 in items
        assert comp2 in items


class TestDictStorageClear:
    """Tests for DictStorage clear operation."""

    def test_clear(self) -> None:
        """Test clear removes all components."""
        storage = DictStorage[MockComponent]()
        storage.store(make_component("T1").qname, make_component("T1"))
        storage.store(make_component("T2").qname, make_component("T2"))

        storage.clear()

        assert len(storage) == 0
        assert storage.namespaces() == []


class TestDictStorageStats:
    """Tests for DictStorage statistics."""

    def test_stats(self) -> None:
        """Test stats returns correct metrics."""
        storage = DictStorage[MockComponent]()
        storage.store(
            make_component("T1", "http://ns1.com").qname, make_component("T1", "http://ns1.com")
        )
        storage.store(
            make_component("T2", "http://ns2.com").qname, make_component("T2", "http://ns2.com")
        )

        stats = storage.stats()
        assert stats.total_items == 2
        assert stats.namespaces == 2
        assert stats.memory_estimate_bytes > 0


# =============================================================================
# TrieStorage Tests
# =============================================================================


class TestTrieStorageBasic:
    """Tests for TrieStorage basic operations."""

    def test_init_empty(self) -> None:
        """Test TrieStorage initializes empty."""
        storage = TrieStorage[MockComponent]()
        assert len(storage) == 0
        assert storage.namespaces() == []

    def test_init_custom_params(self) -> None:
        """Test TrieStorage with custom Bloom parameters."""
        storage = TrieStorage[MockComponent](
            expected_items=5000,
            bloom_fp_rate=0.01,
        )
        assert len(storage) == 0

    def test_store_and_lookup(self) -> None:
        """Test store and lookup component."""
        storage = TrieStorage[MockComponent]()
        comp = make_component("MyType")

        storage.store(comp.qname, comp)

        assert len(storage) == 1
        assert storage.lookup(comp.qname) is comp

    def test_store_duplicate_raises(self) -> None:
        """Test store raises on duplicate QName."""
        storage = TrieStorage[MockComponent]()
        comp1 = make_component("MyType")
        comp2 = make_component("MyType")

        storage.store(comp1.qname, comp1)

        with pytest.raises(ValueError, match="already registered"):
            storage.store(comp2.qname, comp2)

    def test_lookup_not_found_bloom_negative(self) -> None:
        """Test Bloom filter provides fast negative lookup."""
        storage = TrieStorage[MockComponent]()
        qname = QName("http://x.com", "X")

        # Bloom filter should return None quickly
        assert storage.lookup(qname) is None

    def test_contains_with_bloom(self) -> None:
        """Test __contains__ uses Bloom filter."""
        storage = TrieStorage[MockComponent]()
        comp = make_component("MyType")

        assert comp.qname not in storage
        storage.store(comp.qname, comp)
        assert comp.qname in storage

    def test_remove(self) -> None:
        """Test remove component (Bloom not updated)."""
        storage = TrieStorage[MockComponent]()
        comp = make_component("MyType")
        storage.store(comp.qname, comp)

        assert storage.remove(comp.qname) is True
        assert len(storage) == 0
        # Note: Bloom filter may still return True (acceptable false positive)

    def test_remove_not_found(self) -> None:
        """Test remove returns False when not found."""
        storage = TrieStorage[MockComponent]()
        qname = QName("http://x.com", "X")

        assert storage.remove(qname) is False


class TestTrieStorageNamespacePrefix:
    """Tests for TrieStorage namespace prefix search - key feature!"""

    def test_by_namespace(self) -> None:
        """Test by_namespace returns components in exact namespace."""
        storage = TrieStorage[MockComponent]()
        comp1 = make_component("Type1", "http://ns1.com")
        comp2 = make_component("Type2", "http://ns1.com")
        comp3 = make_component("Type3", "http://ns2.com")

        storage.store(comp1.qname, comp1)
        storage.store(comp2.qname, comp2)
        storage.store(comp3.qname, comp3)

        ns1 = storage.by_namespace("http://ns1.com")
        assert len(ns1) == 2
        assert comp1 in ns1
        assert comp2 in ns1

    def test_by_namespace_prefix_trie_search(self) -> None:
        """Test by_namespace_prefix uses Trie for O(k+m) search."""
        storage = TrieStorage[MockComponent]()

        # Create components in versioned namespaces
        comp_v1 = make_component("Type1", "http://example.com/api/v1")
        comp_v2 = make_component("Type2", "http://example.com/api/v2")
        comp_v3 = make_component("Type3", "http://example.com/api/v3")
        comp_other = make_component("Other", "http://other.com/api/v1")

        storage.store(comp_v1.qname, comp_v1)
        storage.store(comp_v2.qname, comp_v2)
        storage.store(comp_v3.qname, comp_v3)
        storage.store(comp_other.qname, comp_other)

        # Find all components under http://example.com/api/
        prefix_comps = storage.by_namespace_prefix("http://example.com/api/")
        assert len(prefix_comps) == 3
        assert comp_v1 in prefix_comps
        assert comp_v2 in prefix_comps
        assert comp_v3 in prefix_comps
        assert comp_other not in prefix_comps

    def test_by_namespace_prefix_no_match(self) -> None:
        """Test by_namespace_prefix returns empty when no match."""
        storage = TrieStorage[MockComponent]()
        comp = make_component("Type", "http://example.com")
        storage.store(comp.qname, comp)

        assert storage.by_namespace_prefix("http://other.com/") == []

    def test_by_namespace_prefix_shared_prefix(self) -> None:
        """Test Trie correctly handles shared URI prefixes."""
        storage = TrieStorage[MockComponent]()

        # W3C-style namespaces with shared prefix
        xsd_type = make_component("string", "http://www.w3.org/2001/XMLSchema")
        xslt_type = make_component("transform", "http://www.w3.org/1999/XSL/Transform")
        xlink_type = make_component("href", "http://www.w3.org/1999/xlink")

        storage.store(xsd_type.qname, xsd_type)
        storage.store(xslt_type.qname, xslt_type)
        storage.store(xlink_type.qname, xlink_type)

        # All W3C namespaces
        w3c_all = storage.by_namespace_prefix("http://www.w3.org/")
        assert len(w3c_all) == 3

        # Only 1999 namespaces
        w3c_1999 = storage.by_namespace_prefix("http://www.w3.org/1999/")
        assert len(w3c_1999) == 2
        assert xslt_type in w3c_1999
        assert xlink_type in w3c_1999

    def test_namespaces_from_trie(self) -> None:
        """Test namespaces returns all from Trie."""
        storage = TrieStorage[MockComponent]()
        storage.store(
            make_component("T1", "http://ns1.com").qname, make_component("T1", "http://ns1.com")
        )
        storage.store(
            make_component("T2", "http://ns2.com").qname, make_component("T2", "http://ns2.com")
        )

        namespaces = storage.namespaces()
        assert len(namespaces) == 2
        assert "http://ns1.com" in namespaces
        assert "http://ns2.com" in namespaces


class TestTrieStorageBloom:
    """Tests for TrieStorage Bloom filter integration."""

    def test_bloom_negative_lookup_fast(self) -> None:
        """Test Bloom filter provides fast negative lookups."""
        storage = TrieStorage[MockComponent]()

        for i in range(100):
            comp = make_component(f"Type{i}")
            storage.store(comp.qname, comp)

        # Non-existent should hit Bloom fast path
        result = storage.lookup(QName("http://example.com", "NonExistent"))
        assert result is None

    def test_bloom_false_positive_rate(self) -> None:
        """Test Bloom filter FP rate property."""
        storage = TrieStorage[MockComponent](
            expected_items=1000,
            bloom_fp_rate=0.001,
        )

        for i in range(100):
            comp = make_component(f"Type{i}")
            storage.store(comp.qname, comp)

        # FP rate should be low
        assert storage.bloom_false_positive_rate < 0.01

    def test_bloom_memory_bytes(self) -> None:
        """Test Bloom filter memory reporting."""
        storage = TrieStorage[MockComponent]()
        assert storage.bloom_memory_bytes > 0


class TestTrieStorageIteration:
    """Tests for TrieStorage iteration."""

    def test_iter_qnames(self) -> None:
        """Test iteration over QNames."""
        storage = TrieStorage[MockComponent]()
        comp1 = make_component("Type1", "http://ns1.com")
        comp2 = make_component("Type2", "http://ns2.com")

        storage.store(comp1.qname, comp1)
        storage.store(comp2.qname, comp2)

        qnames = list(storage)
        assert len(qnames) == 2
        assert comp1.qname in qnames
        assert comp2.qname in qnames

    def test_all_items(self) -> None:
        """Test all_items returns all components."""
        storage = TrieStorage[MockComponent]()
        comp1 = make_component("Type1")
        comp2 = make_component("Type2")

        storage.store(comp1.qname, comp1)
        storage.store(comp2.qname, comp2)

        items = storage.all_items()
        assert len(items) == 2
        assert comp1 in items
        assert comp2 in items


class TestTrieStorageClear:
    """Tests for TrieStorage clear operation."""

    def test_clear(self) -> None:
        """Test clear removes all and resets Trie/Bloom."""
        storage = TrieStorage[MockComponent]()
        storage.store(make_component("T1").qname, make_component("T1"))
        storage.store(make_component("T2").qname, make_component("T2"))

        storage.clear()

        assert len(storage) == 0
        assert storage.namespaces() == []


class TestTrieStorageStats:
    """Tests for TrieStorage statistics."""

    def test_stats(self) -> None:
        """Test stats returns correct metrics."""
        storage = TrieStorage[MockComponent]()
        storage.store(
            make_component("T1", "http://ns1.com").qname, make_component("T1", "http://ns1.com")
        )
        storage.store(
            make_component("T2", "http://ns2.com").qname, make_component("T2", "http://ns2.com")
        )

        stats = storage.stats()
        assert stats.total_items == 2
        assert stats.namespaces == 2
        assert stats.memory_estimate_bytes > 0


# =============================================================================
# Factory Tests
# =============================================================================


class TestCreateStorage:
    """Tests for create_storage factory function."""

    def test_create_trie_default(self) -> None:
        """Test create_storage defaults to trie."""
        storage: TrieStorage[MockComponent] = create_storage()
        assert isinstance(storage, TrieStorage)

    def test_create_trie_explicit(self) -> None:
        """Test create_storage with trie strategy."""
        storage: TrieStorage[MockComponent] = create_storage("trie")
        assert isinstance(storage, TrieStorage)

    def test_create_dict(self) -> None:
        """Test create_storage with dict strategy."""
        storage: DictStorage[MockComponent] = create_storage("dict")
        assert isinstance(storage, DictStorage)

    def test_create_trie_custom_params(self) -> None:
        """Test create_storage passes params to TrieStorage."""
        storage: TrieStorage[MockComponent] = create_storage(
            "trie",
            expected_items=5000,
            bloom_fp_rate=0.01,
        )
        assert isinstance(storage, TrieStorage)

    def test_create_unknown_raises(self) -> None:
        """Test create_storage raises for unknown strategy."""
        with pytest.raises(ValueError, match="Unknown storage strategy"):
            create_storage("unknown")


# =============================================================================
# ComponentRegistry with Storage Strategy
# =============================================================================


class TestRegistryWithDictStorage:
    """Tests for ComponentRegistry with DictStorage."""

    def test_registry_with_dict_storage(self) -> None:
        """Test registry works with DictStorage."""
        from xsdmesh.types import ComponentRegistry

        storage = DictStorage[MockComponent]()
        registry: ComponentRegistry[MockComponent] = ComponentRegistry(storage=storage)

        comp = make_component("MyType")
        registry.register(comp)

        assert registry.lookup(comp.qname) is comp
        assert registry.storage is storage

    def test_registry_dict_no_bloom_stats(self) -> None:
        """Test DictStorage registry has zero Bloom stats."""
        from xsdmesh.types import ComponentRegistry

        storage = DictStorage[MockComponent]()
        registry: ComponentRegistry[MockComponent] = ComponentRegistry(storage=storage)

        stats = registry.stats()
        assert stats.bloom_size_bytes == 0
        assert stats.bloom_false_positive_rate == 0.0


class TestRegistryWithTrieStorage:
    """Tests for ComponentRegistry with TrieStorage."""

    def test_registry_default_is_trie(self) -> None:
        """Test registry defaults to TrieStorage."""
        from xsdmesh.types import ComponentRegistry

        registry: ComponentRegistry[MockComponent] = ComponentRegistry()
        assert isinstance(registry.storage, TrieStorage)

    def test_registry_trie_prefix_search(self) -> None:
        """Test registry exposes Trie prefix search."""
        from xsdmesh.types import ComponentRegistry

        registry: ComponentRegistry[MockComponent] = ComponentRegistry()

        comp1 = make_component("Type1", "http://example.com/v1")
        comp2 = make_component("Type2", "http://example.com/v2")
        comp3 = make_component("Type3", "http://other.com/v1")

        registry.register(comp1)
        registry.register(comp2)
        registry.register(comp3)

        # Use by_namespace_prefix
        prefix_comps = registry.by_namespace_prefix("http://example.com/")
        assert len(prefix_comps) == 2
        assert comp1 in prefix_comps
        assert comp2 in prefix_comps


class TestRegistryRepr:
    """Tests for registry repr with storage type."""

    def test_repr_shows_storage_type(self) -> None:
        """Test __repr__ shows storage type."""
        from xsdmesh.types import ComponentRegistry

        # Default Trie
        registry_trie: ComponentRegistry[MockComponent] = ComponentRegistry()
        assert "TrieStorage" in repr(registry_trie)

        # Dict storage
        registry_dict: ComponentRegistry[MockComponent] = ComponentRegistry(storage=DictStorage())
        assert "DictStorage" in repr(registry_dict)
