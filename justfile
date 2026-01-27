set dotenv-load

# Show available commands
default:
    @just --list

# Install dependencies
[group('dev')]
install:
    uv sync

# Install pre-commit hooks
[group('dev')]
hooks:
    uv run prek install

# Update dependencies
[group('dev')]
update:
    uv lock --upgrade
    uv sync

# Run the MCP server
[group('dev')]
serve:
    uv run wahoo-systm-mcp

# Run unit tests
[group('test')]
test:
    uv run pytest

# Run unit tests with coverage
[group('test')]
test-cov:
    uv run pytest --cov=src/wahoo_systm_mcp --cov-report=term-missing

# Run integration tests
[group('test')]
test-integration:
    uv run pytest -m integration

# Run all tests (unit + integration)
[group('test')]
test-all:
    uv run pytest -m "" --cov=src/wahoo_systm_mcp --cov-report=term-missing

# Lint code with ruff
[group('lint')]
lint:
    uv run ruff check

# Type check with ty
[group('lint')]
typecheck:
    uv run ty check src/

# Format code with ruff
[group('lint')]
format:
    uv run ruff format

# Format and fix lint issues
[group('lint')]
fix:
    uv run ruff check --fix
    uv run ruff format

# Run all lint checks
[group('lint')]
check: lint typecheck

# Security audit dependencies
audit:
    uv run python -m pip_audit

# Clean build artifacts
[confirm("Delete all build artifacts?")]
clean:
    rm -rf .pytest_cache .ruff_cache .coverage htmlcov dist build *.egg-info
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
