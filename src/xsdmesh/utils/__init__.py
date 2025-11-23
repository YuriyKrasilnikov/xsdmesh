"""Utility modules for XSDMesh.

Provides logging, profiling, debugging, and data structure utilities.
"""

from xsdmesh.utils.bloom import BloomFilter
from xsdmesh.utils.cache import ARCCache
from xsdmesh.utils.debug import format_ast, format_qname, pprint_component, truncate
from xsdmesh.utils.logger import (
    LogContext,
    get_logger,
    log_parse_event,
    log_performance,
    setup_logging,
)
from xsdmesh.utils.profiler import (
    MemoryTracker,
    Timer,
    profile_memory,
    profile_time,
)
from xsdmesh.utils.trie import PatriciaTrie

__all__ = [
    # Logging
    "get_logger",
    "setup_logging",
    "LogContext",
    "log_parse_event",
    "log_performance",
    # Profiling
    "profile_time",
    "profile_memory",
    "Timer",
    "MemoryTracker",
    # Debug
    "format_ast",
    "pprint_component",
    "format_qname",
    "truncate",
    # Data Structures
    "BloomFilter",
    "PatriciaTrie",
    "ARCCache",
]
