# XSDMesh

**Blazing fast XSD 1.1 parser with in-memory schema graph**

[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](http://mypy-lang.org/)

A Python library for parsing XSD 1.1 schemas into a structured graph representation for validation, analysis, and transformations.

## ⚠️ Development Status

**Alpha - Under Active Development**

This project is in early development. The API is not stable and may change significantly.

## Features (Planned)

- ✅ Full XSD 1.1 specification support
- ✅ In-memory schema graph representation
- ✅ XPath 2.0 expression evaluation
- ✅ Assertions and conditional type assignment
- ✅ Schema validation and analysis
- ✅ 100% W3C XSD 1.1 test suite coverage (goal)

## Requirements

- **Python 3.14+** (uses latest Python features)
- lxml 6.0+
- elementpath 5.0+

## Installation

**Note:** XSDMesh requires Python 3.14+, which is currently in development.

```bash
# Install xsdmesh (when published)
pip install xsdmesh

# Or with uv
uv pip install xsdmesh
```

## Quick Start

```python
from xsdmesh import Schema

# Parse XSD schema
schema = Schema.from_file("path/to/schema.xsd")

# Access schema components
for element in schema.elements:
    print(f"Element: {element.name}")

# Traverse dependency graph
for dependency in schema.graph.dependencies():
    print(f"{dependency.source} -> {dependency.target}")
```

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/YuriyKrasilnikov/xsdmesh.git
cd xsdmesh

# Setup development environment (requires uv)
make dev-setup
```

### Running Tests

```bash
# All tests with coverage
make test

# Unit tests only
make test-unit

# W3C conformance tests
make test-w3c
```

### Code Quality

```bash
# Run linters
make lint

# Format code
make format

# Type checking
make type-check
```

## Project Goals

1. **100% W3C XSD 1.1 Test Suite Coverage** - Full compliance with W3C standards
2. **Performance** - Parse medium schemas (1000 elements) in < 1 second
3. **Memory Efficiency** - Use < 100MB for typical schemas
4. **Type Safety** - Strict mypy type checking throughout
5. **Clean API** - Intuitive and Pythonic interface

## Architecture

```
xsdmesh/
├── parser/       # XSD parsing logic
├── loader/       # Import/include/override handling
├── types/        # Object model for XSD types
├── xsd11/        # XSD 1.1 specific features
├── xpath/        # XPath 2.0 engine
├── graph/        # Dependency graph builder
├── validators/   # Validation logic
└── utils/        # Common utilities
```

## Roadmap

### Current Status: Milestone 1 - MVP Development

**Latest:** SAX Parser Foundation complete - streaming parser with O(depth) memory, namespace resolution, 106 tests passing

### Milestone 1: MVP - Basic XSD 1.0 Parser (3-4 months)
- [x] **SAX Parser Foundation** - O(depth) streaming parser with event buffer
- [x] **Namespace handling** - Stacked prefix→URI resolution
- [x] **Parse context** - Element path tracking, error accumulation
- [ ] Simple and complex types parsing
- [ ] Element and attribute declarations
- [ ] Import/include support
- [ ] Basic schema graph

### Milestone 2: XSD 1.1 Support (3-4 months)
- [ ] Assertions (xs:assert, xs:assertion)
- [ ] Conditional type assignment (xs:alternative)
- [ ] Open content
- [ ] XPath 2.0 integration

### Milestone 3: Production Ready (2-3 months)
- [ ] 100% W3C test suite coverage
- [ ] Performance optimization
- [ ] Complete documentation
- [ ] PyPI release

## Contributing

Contributions are welcome! This project is in early stages, so please open an issue first to discuss major changes.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Links

- **Repository:** https://github.com/YuriyKrasilnikov/xsdmesh
- **Issues:** https://github.com/YuriyKrasilnikov/xsdmesh/issues
- **Documentation:** Coming soon
- **W3C XSD 1.1 Spec:** https://www.w3.org/TR/xmlschema11-1/

## Acknowledgments

- Built with [uv](https://github.com/astral-sh/uv) for blazing fast dependency management
- XPath evaluation powered by [elementpath](https://github.com/sissaschool/elementpath)
- XML parsing via [lxml](https://lxml.de/)

---

**Status:** Pre-alpha | **Python:** 3.14+ | **License:** MIT
