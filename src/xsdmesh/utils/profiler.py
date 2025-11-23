"""Performance profiling decorators for XSDMesh.

Provides time and memory profiling decorators for performance monitoring.
Uses tracemalloc for memory tracking and perf_counter for timing.
"""

from __future__ import annotations

import functools
import time
import tracemalloc
from collections.abc import Callable
from typing import Any

from xsdmesh.utils.logger import get_logger

logger = get_logger(__name__)


def profile_time[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    """Decorator to measure function execution time.

    Logs duration in milliseconds. Warns if >1s.

    Args:
        func: Function to profile

    Returns:
        Wrapped function with timing
    """

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration_ms = (time.perf_counter() - start) * 1000
            func_name = f"{func.__module__}.{func.__qualname__}"

            if duration_ms > 1000:
                logger.warning(f"{func_name} took {duration_ms:.1f}ms")
            else:
                logger.debug(f"{func_name}: {duration_ms:.1f}ms")

    return wrapper


def profile_memory[**P, R](func: Callable[P, R]) -> Callable[P, R]:
    """Decorator to measure memory usage.

    Tracks memory allocated during function execution.
    Logs peak memory and final delta.

    Args:
        func: Function to profile

    Returns:
        Wrapped function with memory tracking
    """

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        tracemalloc.start()
        try:
            result = func(*args, **kwargs)
            current, peak = tracemalloc.get_traced_memory()
            func_name = f"{func.__module__}.{func.__qualname__}"

            current_mb = current / 1024 / 1024
            peak_mb = peak / 1024 / 1024

            logger.debug(f"{func_name} memory: current={current_mb:.2f}MB, peak={peak_mb:.2f}MB")

            if peak_mb > 100:
                logger.warning(f"{func_name} used {peak_mb:.2f}MB peak memory")

            return result
        finally:
            tracemalloc.stop()

    return wrapper


class Timer:
    """Context manager for timing code blocks.

    Usage:
        with Timer("parse schema") as t:
            schema = parse(...)
        print(t.elapsed_ms)
    """

    def __init__(self, name: str, *, log: bool = True) -> None:
        """Initialize timer.

        Args:
            name: Operation name
            log: Whether to log duration
        """
        self.name = name
        self.log = log
        self.start_time: float = 0.0
        self.elapsed_ms: float = 0.0

    def __enter__(self) -> Timer:
        """Start timer."""
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args: Any) -> None:
        """Stop timer and log."""
        self.elapsed_ms = (time.perf_counter() - self.start_time) * 1000
        if self.log:
            if self.elapsed_ms > 1000:
                logger.warning(f"{self.name} took {self.elapsed_ms:.1f}ms")
            else:
                logger.debug(f"{self.name}: {self.elapsed_ms:.1f}ms")


class MemoryTracker:
    """Context manager for tracking memory usage.

    Usage:
        with MemoryTracker("schema parse") as m:
            schema = parse(...)
        print(f"Used {m.peak_mb:.2f}MB")
    """

    def __init__(self, name: str, *, log: bool = True) -> None:
        """Initialize memory tracker.

        Args:
            name: Operation name
            log: Whether to log memory usage
        """
        self.name = name
        self.log = log
        self.current_mb: float = 0.0
        self.peak_mb: float = 0.0

    def __enter__(self) -> MemoryTracker:
        """Start memory tracking."""
        tracemalloc.start()
        return self

    def __exit__(self, *args: Any) -> None:
        """Stop tracking and log."""
        current, peak = tracemalloc.get_traced_memory()
        self.current_mb = current / 1024 / 1024
        self.peak_mb = peak / 1024 / 1024
        tracemalloc.stop()

        if self.log:
            logger.debug(
                f"{self.name} memory: current={self.current_mb:.2f}MB, peak={self.peak_mb:.2f}MB"
            )
            if self.peak_mb > 100:
                logger.warning(f"{self.name} used {self.peak_mb:.2f}MB peak memory")
