# JLAW Forensic Analysis System - Makefile
# This Makefile provides targets for CI/CD workflows using uv for dependency management

.PHONY: sync format-check format lint mypy coverage build-docs test old_version_tests clean help

# Default target
help:
	@echo "JLAW Forensic Analysis System - Makefile Targets"
	@echo ""
	@echo "  sync              - Install/sync dependencies using uv"
	@echo "  format-check      - Check code formatting with ruff"
	@echo "  format            - Format code with ruff"
	@echo "  lint              - Run linting with ruff"
	@echo "  mypy              - Run type checking with mypy"
	@echo "  test              - Run tests"
	@echo "  coverage          - Run tests with coverage"
	@echo "  build-docs        - Build documentation"
	@echo "  old_version_tests - Run tests on older Python versions"
	@echo "  clean             - Clean build artifacts and cache"

# Sync dependencies using uv
sync:
	uv sync --frozen --all-extras

# Check code formatting
format-check:
	uv run ruff format --check .

# Format code
format:
	uv run ruff format .

# Run linting
lint:
	uv run ruff check .

# Run type checking
mypy:
	uv run mypy src/agents

# Run tests
test:
	uv run pytest tests/

# Run tests with coverage
coverage:
	uv run pytest --cov=src/agents --cov=tests --cov-report=term-missing tests/

# Build documentation
build-docs:
	@echo "Building documentation..."
	@echo "Note: Documentation build requires additional setup"
	@echo "For now, documentation is in markdown format in docs/"

# Run tests on old Python versions
old_version_tests:
	uv run pytest tests/

# Clean build artifacts
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .coverage htmlcov/ 2>/dev/null || true
	@echo "Cleaned build artifacts and cache"
