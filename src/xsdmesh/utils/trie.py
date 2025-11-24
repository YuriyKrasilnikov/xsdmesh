"""Patricia Trie (Radix Tree) for namespace URIs.

Optimizes common URI prefixes: "http://www.w3.org/2001/XMLSchema"
Memory saving: 30-50% vs separate strings.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TrieNode[V]:
    """Node in Patricia Trie.

    Unlike regular trie, edges can have multi-character labels.
    """

    # Edge label prefix (empty for root)
    prefix: str = ""

    # Value at this node (None if not a complete key)
    value: V | None = None

    # Child nodes: first char → node
    children: dict[str, TrieNode[V]] = field(default_factory=dict)

    def is_leaf(self) -> bool:
        """Check if node is leaf."""
        return len(self.children) == 0


class PatriciaTrie[V]:
    """Patricia Trie (Radix Tree) for efficient prefix storage.

    Optimized for namespace URIs with common prefixes.

    Example:
        trie = PatriciaTrie()
        trie["http://www.w3.org/2001/XMLSchema"] = "xsd"
        trie["http://www.w3.org/1999/xhtml"] = "html"

        # Shared prefix stored once: "http://www.w3.org/"
    """

    def __init__(self) -> None:
        """Initialize empty trie."""
        self.root: TrieNode[V] = TrieNode()
        self.size = 0

    def _common_prefix_length(self, s1: str, s2: str) -> int:
        """Find length of common prefix.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Length of common prefix
        """
        min_len = min(len(s1), len(s2))
        for i in range(min_len):
            if s1[i] != s2[i]:
                return i
        return min_len

    def __setitem__(self, key: str, value: V) -> None:
        """Insert or update key-value pair.

        Args:
            key: Key string
            value: Associated value
        """
        if not key:
            raise ValueError("Key cannot be empty")

        node = self.root
        remaining = key

        while remaining:
            # Find child with matching first character
            first_char = remaining[0]

            if first_char not in node.children:
                # No matching child, create new node
                node.children[first_char] = TrieNode(prefix=remaining, value=value)
                self.size += 1
                return

            child = node.children[first_char]
            prefix_len = self._common_prefix_length(remaining, child.prefix)

            if prefix_len == len(child.prefix):
                # Full prefix match, continue to child
                remaining = remaining[prefix_len:]
                node = child
            elif prefix_len < len(child.prefix):
                # Partial match, split the edge
                # Example: insert "test" when "testing" exists
                # Split "testing" into "test" → "ing"

                # Create intermediate node with common prefix
                split_node: TrieNode[V] = TrieNode(prefix=remaining[:prefix_len])

                # Old child becomes child of split node
                old_suffix = child.prefix[prefix_len:]
                child.prefix = old_suffix
                split_node.children[old_suffix[0]] = child

                # Replace child with split node
                node.children[first_char] = split_node

                remaining = remaining[prefix_len:]
                node = split_node

                if not remaining:
                    # Inserted key is prefix of existing key
                    node.value = value
                    self.size += 1
                    return
            else:
                # This shouldn't happen (prefix_len > len(child.prefix))
                raise RuntimeError("Unexpected prefix length")

        # No remaining characters, set value at current node
        if node.value is None:
            self.size += 1
        node.value = value

    def __getitem__(self, key: str) -> V:
        """Get value for key.

        Args:
            key: Key string

        Returns:
            Associated value

        Raises:
            KeyError: If key not found
        """
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value

    def get(self, key: str, default: V | None = None) -> V | None:
        """Get value for key with default.

        Args:
            key: Key string
            default: Default if not found

        Returns:
            Value or default
        """
        node = self.root
        remaining = key

        while remaining:
            first_char = remaining[0]

            if first_char not in node.children:
                return default

            child = node.children[first_char]
            prefix_len = self._common_prefix_length(remaining, child.prefix)

            if prefix_len < len(child.prefix):
                # Partial match, key not in trie
                return default

            remaining = remaining[prefix_len:]
            node = child

        return node.value if node.value is not None else default

    def __contains__(self, key: str) -> bool:
        """Check if key exists.

        Args:
            key: Key string

        Returns:
            True if key exists
        """
        return self.get(key) is not None

    def keys_with_prefix(self, prefix: str) -> list[str]:
        """Find all keys with given prefix.

        Args:
            prefix: Prefix to search

        Returns:
            List of matching keys
        """
        # Navigate to prefix node
        node = self.root
        remaining = prefix
        path = ""

        while remaining:
            first_char = remaining[0]

            if first_char not in node.children:
                return []

            child = node.children[first_char]
            prefix_len = self._common_prefix_length(remaining, child.prefix)

            if prefix_len < len(remaining):
                # Partial match
                if prefix_len == len(child.prefix):
                    # Continue to child
                    path += child.prefix
                    remaining = remaining[prefix_len:]
                    node = child
                else:
                    # Prefix not in trie
                    return []
            else:
                # Full match of remaining - use full edge label since all
                # keys in subtree have this edge as prefix
                path += child.prefix
                node = child
                break

        # Collect all keys in subtree
        results: list[str] = []
        self._collect_keys(node, path, results)
        return results

    def _collect_keys(self, node: TrieNode[V], path: str, results: list[str]) -> None:
        """Recursively collect all keys in subtree.

        Args:
            node: Current node
            path: Path to current node
            results: Result accumulator
        """
        if node.value is not None:
            results.append(path)

        for child in node.children.values():
            self._collect_keys(child, path + child.prefix, results)

    def __len__(self) -> int:
        """Number of keys."""
        return self.size

    def __repr__(self) -> str:
        """String representation."""
        return f"PatriciaTrie(size={self.size})"
