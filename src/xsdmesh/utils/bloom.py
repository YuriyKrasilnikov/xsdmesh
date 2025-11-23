"""Bloom Filter for fast negative lookup.

Used in Registry for O(1) "not found" checks before Trie search.
Target: 0.1% false positive rate, 10 bits per element.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Hashable


class BloomFilter:
    """Space-efficient probabilistic set for membership testing.

    Properties:
    - False negatives: impossible
    - False positives: ~0.1% with 10 bits/element
    - Memory: 10 bits per element vs dict's ~288 bits
    - Lookup: O(1) with k hash functions
    """

    def __init__(self, expected_elements: int = 1000, false_positive_rate: float = 0.001) -> None:
        """Initialize Bloom filter.

        Args:
            expected_elements: Expected number of elements
            false_positive_rate: Target false positive rate (default: 0.1%)
        """
        self.expected_elements = expected_elements
        self.false_positive_rate = false_positive_rate

        # Optimal size: m = -n*ln(p) / (ln(2)^2)
        self.size = self._optimal_size(expected_elements, false_positive_rate)

        # Optimal hash functions: k = (m/n) * ln(2)
        self.num_hashes = self._optimal_num_hashes(self.size, expected_elements)

        # Bit array
        self.bits = bytearray((self.size + 7) // 8)  # Round up to bytes

        self.count = 0

    @staticmethod
    def _optimal_size(n: int, p: float) -> int:
        """Calculate optimal bit array size.

        Args:
            n: Expected elements
            p: False positive rate

        Returns:
            Optimal size in bits
        """
        return int(-n * math.log(p) / (math.log(2) ** 2))

    @staticmethod
    def _optimal_num_hashes(m: int, n: int) -> int:
        """Calculate optimal number of hash functions.

        Args:
            m: Bit array size
            n: Expected elements

        Returns:
            Optimal number of hashes
        """
        if n == 0:
            return 1
        return max(1, int((m / n) * math.log(2)))

    def _hashes(self, item: Hashable) -> list[int]:
        """Generate k hash values for item.

        Uses double hashing: h(i) = (h1 + i*h2) % m

        Args:
            item: Item to hash

        Returns:
            List of k hash values
        """
        # Serialize item
        data = str(item).encode("utf-8")

        # Two base hashes
        h1 = int(hashlib.md5(data, usedforsecurity=False).hexdigest(), 16)
        h2 = int(hashlib.sha1(data, usedforsecurity=False).hexdigest(), 16)

        # Generate k hashes using double hashing
        return [(h1 + i * h2) % self.size for i in range(self.num_hashes)]

    def add(self, item: Hashable) -> None:
        """Add item to filter.

        Args:
            item: Item to add
        """
        for hash_val in self._hashes(item):
            byte_idx = hash_val // 8
            bit_idx = hash_val % 8
            self.bits[byte_idx] |= 1 << bit_idx

        self.count += 1

    def __contains__(self, item: Hashable) -> bool:
        """Check if item might be in filter.

        Returns:
            True: item MIGHT be present (with FP rate)
            False: item DEFINITELY not present
        """
        for hash_val in self._hashes(item):
            byte_idx = hash_val // 8
            bit_idx = hash_val % 8
            if not (self.bits[byte_idx] & (1 << bit_idx)):
                return False
        return True

    def clear(self) -> None:
        """Clear all bits."""
        self.bits = bytearray((self.size + 7) // 8)
        self.count = 0

    @property
    def memory_bytes(self) -> int:
        """Memory usage in bytes."""
        return len(self.bits)

    def current_false_positive_rate(self) -> float:
        """Estimate current false positive rate.

        Returns:
            Estimated FP rate based on current fill
        """
        if self.count == 0:
            return 0.0
        # FPR = (1 - e^(-kn/m))^k
        return (1 - math.exp(-self.num_hashes * self.count / self.size)) ** self.num_hashes

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"BloomFilter(size={self.size}, "
            f"hashes={self.num_hashes}, "
            f"count={self.count}, "
            f"fp_rate={self.current_false_positive_rate():.4f})"
        )
