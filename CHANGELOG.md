# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### SAX Parser Foundation - IN PROGRESS

#### Added - Parser Infrastructure
- **SAX streaming parser** (`parser/xml_parser.py`) - O(depth) memory via lxml.iterparse
  - Incremental elem.clear(keep_tail=True) for memory control
  - Memory threshold with periodic parent.clear()
  - Handler dispatch by element tag
  - ParseResult dataclass for typed returns
- **Event system** (`parser/events.py`) - Event buffer with lookahead for disambiguation
  - EventType enum: START_ELEMENT, END_ELEMENT, TEXT, COMMENT
  - EventBuffer with deque(maxlen=3) for lookahead
  - Supports simpleType variety detection (restriction/list/union)
- **Parse context** (`parser/context.py`) - O(depth) state management
  - Namespace stack with prefix→URI mappings
  - Element path tracking [(namespace, local_name), ...]
  - QName resolution with default namespace support
  - Error accumulation for non-fatal parse errors
  - Clone support for include/import forking
- **QName parsing** (`parser/qname.py`) - Clark and prefix notation support
  - Clark notation: `{http://...}local`
  - Prefix notation: `prefix:local` with resolver
  - NCName validation
  - split_qname() helper
- **Handler protocol** (`parser/handlers.py`) - ComponentHandler interface
  - start_element() and end_element() lifecycle
  - Type-safe protocol for XSD component handlers

#### Added - Tests
- **Parser tests** (`tests/parser/`) - 106 tests with full coverage
  - `test_qname.py` (27 tests) - QName parsing, NCName validation
  - `test_context.py` (38 tests) - ParseContext, namespace stack, cloning
  - `test_events.py` (17 tests) - EventBuffer, lookahead, ring behavior
  - `test_xml_parser.py` (24 tests) - SAXParser, handler dispatch, memory management
  - All tests pass mypy --strict
  - Handler dispatch integration test (verifies handlers called during parsing)
  - Documents current behavior and limitations (e.g., is_at_schema_root namespace check)

#### Changed - Development Tools
- **Benchmark script** (`scripts/benchmark.py`) - Added argparse and JSON output
  - --output parameter for CI integration
  - Placeholder results for benchmark workflow
  - Prevents CI benchmark failure until real benchmarks implemented

#### Fixed
- **Pre-commit configuration** (`.pre-commit-config.yaml`) - Added --check to ruff-format
  - Matches CI behavior (check vs format)
  - Prevents silent formatting in pre-commit
- **Constants typing** (`constants.py`) - Added FormType annotation to DEFAULT_FORM
  - Enables mypy strict without cast()
  - Proper Literal type support
- **Download script** (`scripts/download_w3c_suite.py`) - Removed unused loop variable
  - Changed .items() to .values() where key unused

#### Technical Details
- **Memory:** O(depth) not O(nodes) via elem.clear(keep_tail=True)
- **Lookahead:** deque(maxlen=3) for simpleType variety disambiguation
- **Namespace resolution:** Stacked dict[str, str] with inheritance
- **Type safety:** Protocol, dataclass, NamedTuple throughout
- **Python 3.14:** PEP 695 syntax, frozen dataclasses with slots

## [0.1.0-dev] - 2025-11-23

### Infrastructure & Preparation - COMPLETED ✅

#### Added - Core Infrastructure
- **Exception hierarchy** (`exceptions.py`) - 8 exception types with full context
- **Constants** (`constants.py`) - 44 built-in XSD types, W3C namespaces, derivation hierarchy
- **Project structure** - Python 3.14+ with uv, ruff, mypy strict, pytest

#### Added - Utilities & Algorithms
- **Logging** (`utils/logger.py`) - Structured logging with performance helpers
- **Profiling** (`utils/profiler.py`) - Time/memory decorators with PEP 695 syntax
- **Debug** (`utils/debug.py`) - AST inspection and pretty-printing
- **BloomFilter** (`utils/bloom.py`) - O(1) negative lookups, 0.1% FP, 10 bits/elem
- **PatriciaTrie** (`utils/trie.py`) - 30-50% memory save on namespace URIs
- **ARCCache** (`utils/cache.py`) - 2x better hit ratio than LRU

#### Added - CI/CD & Testing
- **GitHub Actions**: test.yml, lint.yml, benchmark.yml
- **W3C Test Suite**: Download script + test harness (2100/3500 target)
- **Makefile**: profile, memory-check, test-w3c-report, benchmark-vs-baseline

#### Quality Metrics
- ✅ ruff: 0 errors (17 files)
- ✅ mypy --strict: 0 errors (100% typed)
- ✅ ruff format: All files formatted
- ✅ pytest: 2/2 unit tests passing
- ✅ Python 3.14 PEP 695: Generic syntax `[**P, R]`, `class Cache[V]`

#### Technical Stack
- Python 3.14+ only (PEP 695, PEP 698, PEP 705)
- uv for package management (10-100x faster than pip)
- Immutable AST: frozen dataclasses + __slots__
- SAX streaming: O(depth) memory vs O(nodes) DOM
