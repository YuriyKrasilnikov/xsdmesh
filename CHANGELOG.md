# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Type system core (`types/` module)
  - `Component` ABC with freeze/validate interface
  - `ComponentRegistry` with Bloom filter for O(1) negative lookups
  - `TypeReference` for lazy type resolution with caching
  - `ValidationContext` and `ValidationResult` for validation pipeline
  - `LexicalFacets` and `ValueFacets` for XSD facet validation (12 facets)
  - `QName` migrated from parser module
- Tests for type system (70 tests)

### Changed

- Moved `QName` from `parser/qname.py` to `types/qname.py`
- `FrozenError` moved to `exceptions.py`
- Renamed `ImportError` to `SchemaImportError` (avoid shadowing builtin)

### Fixed

- `ParseContext.is_at_schema_root()` now validates XSD namespace

## [0.1.0-dev] - 2025-11-23

### Added

- SAX streaming parser with O(depth) memory (`parser/` module)
  - `SAXParser` with lxml.iterparse and handler dispatch
  - `EventBuffer` with lookahead for simpleType disambiguation
  - `ParseContext` with namespace stack and path tracking
  - `ComponentHandler` protocol for XSD element handlers
- Exception hierarchy (8 exception types)
- Utility algorithms
  - `BloomFilter` for O(1) membership testing
  - `PatriciaTrie` for prefix-based lookups
  - `ARCCache` for adaptive caching
- CI/CD workflows (test, lint, benchmark)
- W3C test suite harness

### Changed

- Pre-commit config: added `--check` to ruff-format

### Fixed

- Constants typing for mypy strict compliance

[Unreleased]: https://github.com/username/xsdmesh/compare/v0.1.0-dev...HEAD
[0.1.0-dev]: https://github.com/username/xsdmesh/releases/tag/v0.1.0-dev
