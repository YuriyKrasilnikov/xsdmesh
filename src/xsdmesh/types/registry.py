"""Component registry with pluggable storage strategies.

Registry separates business logic (deferred resolution, callbacks)
from storage concerns (lookup, indexing) via Strategy Pattern.

Default storage: TrieStorage (O(k) lookup, prefix search, Bloom filter).
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass

from xsdmesh.types.base import Component
from xsdmesh.types.qname import QName
from xsdmesh.types.storage import (
    DictStorage,
    StorageStrategy,
    TrieStorage,
)


@dataclass(frozen=True)
class RegistryStats:
    """Statistics about registry contents and performance."""

    total_components: int
    namespaces: int
    bloom_size_bytes: int
    bloom_false_positive_rate: float
    pending_callbacks: int


class ComponentRegistry[T: Component]:
    """Registry for schema components with pluggable storage.

    Features:
    - Pluggable storage backend (TrieStorage, DictStorage)
    - Deferred resolution callbacks for forward references
    - Namespace-based queries
    - Statistics and introspection

    Default storage is TrieStorage with Bloom filter:
    - O(k) lookup where k = key length
    - O(1) negative lookup via Bloom (99.9% accurate)
    - Namespace prefix search

    Implements ComponentLookup protocol for use with TypeReference.

    Thread-safety:
    - register() is NOT thread-safe (call before validation)
    - lookup() is thread-safe after registration complete

    Usage:
        # Default Trie storage
        registry = ComponentRegistry()
        registry.register(my_type)
        component = registry.lookup(QName("http://example.com", "MyType"))

        # Custom dict storage
        registry = ComponentRegistry(storage=DictStorage())

        # Deferred resolution for forward references
        registry.defer_resolution(qname, lambda c: print(f"Resolved: {c}"))
    """

    def __init__(
        self,
        storage: StorageStrategy[T] | None = None,
        *,
        expected_components: int = 1000,
        bloom_fp_rate: float = 0.001,
    ) -> None:
        """Initialize registry with storage strategy.

        Args:
            storage: Storage backend. If None, creates TrieStorage.
            expected_components: Expected number of components (for default TrieStorage)
            bloom_fp_rate: Target Bloom false positive rate (for default TrieStorage)
        """
        # Use provided storage or create default TrieStorage
        self._storage: StorageStrategy[T]
        if storage is not None:
            self._storage = storage
        else:
            self._storage = TrieStorage[T](
                expected_items=expected_components,
                bloom_fp_rate=bloom_fp_rate,
            )

        # Deferred resolution callbacks: QName -> list of callbacks
        self._callbacks: dict[QName, list[Callable[[T], None]]] = {}

    def register(self, component: T) -> None:
        """Register component in registry.

        Delegates storage to backend, triggers pending callbacks.

        Args:
            component: Component to register (must have qname)

        Raises:
            ValueError: If component with same QName already registered
        """
        qname = component.qname
        self._storage.store(qname, component)
        self._process_callbacks(qname, component)

    def lookup(self, qname: QName) -> T | None:
        """Look up component by QName.

        Delegates to storage backend.

        Args:
            qname: Qualified name to look up

        Returns:
            Component if found, None otherwise
        """
        return self._storage.lookup(qname)

    def get(self, qname: QName, default: T | None = None) -> T | None:
        """Get component with default value.

        Args:
            qname: Qualified name to look up
            default: Value to return if not found

        Returns:
            Component if found, default otherwise
        """
        result = self._storage.lookup(qname)
        return result if result is not None else default

    def __contains__(self, qname: QName) -> bool:
        """Check if QName is registered."""
        return qname in self._storage

    def __getitem__(self, qname: QName) -> T:
        """Get component by QName, raising KeyError if not found.

        Args:
            qname: Qualified name

        Returns:
            Component

        Raises:
            KeyError: If not found
        """
        result = self._storage.lookup(qname)
        if result is None:
            raise KeyError(qname)
        return result

    def __len__(self) -> int:
        """Number of registered components."""
        return len(self._storage)

    def __iter__(self) -> Iterator[QName]:
        """Iterate over registered QNames."""
        return iter(self._storage)

    def by_namespace(self, namespace: str) -> list[T]:
        """Get all components in namespace.

        Args:
            namespace: Namespace URI

        Returns:
            List of components (empty if namespace not found)
        """
        return self._storage.by_namespace(namespace)

    def by_namespace_prefix(self, prefix: str) -> list[T]:
        """Get all components in namespaces matching prefix.

        Only available with TrieStorage.

        Args:
            prefix: Namespace URI prefix (e.g., "http://example.com/")

        Returns:
            List of components from all matching namespaces
        """
        return self._storage.by_namespace_prefix(prefix)

    def namespaces(self) -> list[str]:
        """Get all registered namespaces.

        Returns:
            List of namespace URIs
        """
        return self._storage.namespaces()

    def all_components(self) -> list[T]:
        """Get all registered components.

        Returns:
            List of all components
        """
        return self._storage.all_items()

    def defer_resolution(self, qname: QName, callback: Callable[[T], None]) -> bool:
        """Register callback for deferred resolution.

        If QName already registered, callback is invoked immediately.
        Otherwise, callback is stored and invoked when QName is registered.

        Args:
            qname: QName to wait for
            callback: Function to call with resolved component

        Returns:
            True if resolved immediately, False if deferred
        """
        # Check if already registered
        component = self._storage.lookup(qname)
        if component is not None:
            callback(component)
            return True

        # Defer callback
        if qname not in self._callbacks:
            self._callbacks[qname] = []
        self._callbacks[qname].append(callback)
        return False

    def _process_callbacks(self, qname: QName, component: T) -> None:
        """Process pending callbacks for newly registered component.

        Args:
            qname: QName that was just registered
            component: Component that was registered
        """
        callbacks = self._callbacks.pop(qname, [])
        for callback in callbacks:
            callback(component)

    def pending_qnames(self) -> list[QName]:
        """Get QNames with pending callbacks.

        Returns:
            List of QNames waiting for resolution
        """
        return list(self._callbacks.keys())

    def stats(self) -> RegistryStats:
        """Get registry statistics.

        Returns:
            RegistryStats dataclass with metrics
        """
        storage_stats = self._storage.stats()
        pending = sum(len(cbs) for cbs in self._callbacks.values())

        # Get Bloom stats if available (TrieStorage)
        bloom_bytes = 0
        bloom_fp = 0.0
        if isinstance(self._storage, TrieStorage):
            bloom_bytes = self._storage.bloom_memory_bytes
            bloom_fp = self._storage.bloom_false_positive_rate

        return RegistryStats(
            total_components=storage_stats.total_items,
            namespaces=storage_stats.namespaces,
            bloom_size_bytes=bloom_bytes,
            bloom_false_positive_rate=bloom_fp,
            pending_callbacks=pending,
        )

    def clear(self) -> None:
        """Clear all registered components.

        Warning: Does not invoke pending callbacks.
        """
        self._storage.clear()
        self._callbacks.clear()

    @property
    def storage(self) -> StorageStrategy[T]:
        """Access underlying storage backend.

        Returns:
            Storage strategy instance
        """
        return self._storage

    def __repr__(self) -> str:
        """Debug representation."""
        stats = self.stats()
        storage_type = type(self._storage).__name__
        return (
            f"ComponentRegistry("
            f"storage={storage_type}, "
            f"components={stats.total_components}, "
            f"namespaces={stats.namespaces}, "
            f"pending={stats.pending_callbacks})"
        )


# Type alias for common registry type
SchemaRegistry = ComponentRegistry[Component]
