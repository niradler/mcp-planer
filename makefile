# Makefile for Planer MCP Server

.PHONY: help install install-dev test lint format type-check clean run setup build publish

# Default target
help:
	@echo "Available commands:"
	@echo "  install      - Install package dependencies"
	@echo "  install-dev  - Install package with development dependencies"
	@echo "  test         - Run tests"
	@echo "  lint         - Run linting checks"
	@echo "  format       - Format code with black"
	@echo "  type-check   - Run type checking with mypy"
	@echo "  clean        - Clean up temporary files"
	@echo "  run          - Run the MCP server"
	@echo "  setup        - Complete setup including tests"
	@echo "  build        - Build package for distribution"
	@echo "  publish      - Build and publish to PyPI"

# Install package
install:
	uv pip install -e .

# Install with development dependencies
install-dev:
	uv pip install -e ".[dev]"

# Run tests
test:
	uv run pytest tests/ -v --cov=src/planer_mcp

# Lint code
lint:
	uv run ruff check src/ tests/
	uv run black --check src/ tests/

# Format code
format:
	uv run black src/ tests/
	uv run ruff check --fix src/ tests/

# Type checking
type-check:
	uv run mypy src/planer_mcp/

# Clean temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +

# Run the server
run:
	uv run python main.py

# Complete setup
setup: install-dev test
	@echo "✅ Setup complete! Server is ready to use."

# Development workflow
dev-check: format type-check test
	@echo "✅ All development checks passed!"

# Build package
build: clean
	uv build

# Publish to PyPI
publish: build
	uv publish