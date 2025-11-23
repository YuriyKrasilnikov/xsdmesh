.PHONY: help install test test-unit test-integration test-w3c lint format type-check clean build publish benchmark dev-setup

help:
	@echo "XSDMesh development commands:"
	@echo ""
	@echo "Setup:"
	@echo "  make install       - Setup development environment with uv"
	@echo "  make dev-setup     - Full development setup (install + pre-commit)"
	@echo ""
	@echo "Testing:"
	@echo "  make test          - Run all tests with coverage"
	@echo "  make test-unit     - Run unit tests only"
	@echo "  make test-integration - Run integration tests"
	@echo "  make test-w3c      - Run W3C conformance tests"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint          - Run linters (ruff check + mypy)"
	@echo "  make format        - Format code with ruff"
	@echo "  make type-check    - Run mypy type checking"
	@echo ""
	@echo "Build & Publish:"
	@echo "  make clean         - Remove build artifacts"
	@echo "  make build         - Build wheel and sdist"
	@echo "  make publish       - Publish to PyPI"
	@echo ""
	@echo "Performance:"
	@echo "  make benchmark     - Run performance benchmarks"

install:
	@echo "Installing xsdmesh in development mode..."
	uv venv --python 3.14
	uv pip install -e ".[dev]"
	@echo "✅ Development environment ready!"
	@echo "Activate with: source .venv/bin/activate"

dev-setup: install
	@echo "Setting up pre-commit hooks..."
	uv pip install pre-commit
	pre-commit install
	@echo "✅ Full development setup complete!"

test:
	@echo "Running all tests with coverage..."
	uv run pytest \
		--cov=xsdmesh \
		--cov-report=html \
		--cov-report=term \
		--cov-report=xml \
		-n auto \
		-v

test-unit:
	@echo "Running unit tests..."
	uv run pytest tests/unit/ -n auto -v

test-integration:
	@echo "Running integration tests..."
	uv run pytest tests/integration/ -v

test-w3c:
	@echo "Running W3C XSD 1.1 conformance tests..."
	uv run pytest tests/w3c/ -v

lint:
	@echo "Running ruff check..."
	uv run ruff check .
	@echo "Running mypy..."
	uv run mypy src/xsdmesh

format:
	@echo "Formatting code with ruff..."
	uv run ruff format .
	@echo "Fixing auto-fixable issues..."
	uv run ruff check . --fix

type-check:
	@echo "Running mypy type checker..."
	uv run mypy src/xsdmesh

clean:
	@echo "Cleaning build artifacts..."
	rm -rf build/ dist/ *.egg-info htmlcov/ .coverage .pytest_cache/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleanup complete!"

build: clean
	@echo "Building package..."
	uv pip install build
	python -m build
	@echo "✅ Build complete! Check dist/ directory"

publish: build
	@echo "Publishing to PyPI..."
	uv pip install twine
	twine check dist/*
	twine upload dist/*
	@echo "✅ Published to PyPI!"

benchmark:
	@echo "Running performance benchmarks..."
	uv run python scripts/benchmark.py
