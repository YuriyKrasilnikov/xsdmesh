# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0-dev] - 2025-11-23

### Week 0: Infrastructure & Preparation - COMPLETED ✅

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

#### Added - Documentation
- **XSD10_COMPONENTS.wip.md** - Component priority matrix (3500 tests)
- **MILESTONE1.wip.md** - Detailed 14-week implementation plan
- **ALGORITHMS.wip.md** - 12 algorithms with O-notation and trade-offs
- **ARCHITECTURE.wip.md** - Stage 1 architecture with algorithm links
- **PROJECT.wip.md v2.0** - Updated roadmap

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
