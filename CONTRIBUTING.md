# Contributing to XSDMesh

Thank you for your interest in contributing to XSDMesh! This project is in early development and welcomes contributions.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YourUsername/xsdmesh.git
   cd xsdmesh
   ```

3. **Set up development environment**:
   ```bash
   make dev-setup
   ```

4. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Running Tests

```bash
# All tests
make test

# Unit tests only
make test-unit

# Watch mode during development
uv run pytest tests/unit/ --watch
```

### Code Quality

Before committing, ensure your code passes all checks:

```bash
# Format code
make format

# Run linters
make lint

# Type checking
make type-check
```

Or let pre-commit handle it automatically:
```bash
git commit -m "Your message"  # pre-commit runs automatically
```

### Code Style

- **Python 3.14+ only** - use modern Python features
- **Type hints required** - strict mypy mode
- **Line length**: 100 characters
- **Follow PEP 8** - enforced by ruff
- **Docstrings**: Use Google style for public APIs

Example:
```python
def parse_element(node: Element, *, strict: bool = True) -> ElementModel:
    """Parse an XSD element node into ElementModel.

    Args:
        node: lxml Element node to parse
        strict: Raise errors on invalid schema (default: True)

    Returns:
        Parsed element model

    Raises:
        SchemaError: If element is invalid and strict=True
    """
    ...
```

## Testing Guidelines

- **Write tests first** (TDD encouraged)
- **Unit tests**: Test individual functions/classes in isolation
- **Integration tests**: Test module interactions
- **Coverage**: Aim for 90%+ coverage
- **Use fixtures**: Share test data via pytest fixtures

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add support for xs:assert parsing
fix: handle namespace prefix in QName resolution
docs: update README with installation instructions
test: add tests for complex type inheritance
refactor: simplify XPath context setup
perf: optimize schema graph traversal
```

## Pull Request Process

1. **Update tests** - ensure all tests pass
2. **Update documentation** - if adding features
3. **Run all checks** - `make lint` must pass
4. **Write clear PR description**:
   - What does this PR do?
   - Why is it needed?
   - Any breaking changes?
5. **Link related issues** - e.g., "Closes #123"

## Project Structure

```
src/xsdmesh/
├── parser/       # XSD parsing logic
├── loader/       # Import/include/override
├── types/        # Object model
├── xsd11/        # XSD 1.1 features
├── xpath/        # XPath 2.0 engine
├── graph/        # Dependency graph
└── utils/        # Utilities
```

## Questions?

- Open an [issue](https://github.com/YuriyKrasilnikov/xsdmesh/issues)
- Start a [discussion](https://github.com/YuriyKrasilnikov/xsdmesh/discussions)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
