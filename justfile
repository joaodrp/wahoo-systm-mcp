# Wahoo SYSTM MCP - Development Commands

# Default recipe: show available commands
default:
    @just --list

# Run unit tests
test:
    uv run pytest

# Run unit tests with coverage
test-cov:
    uv run pytest --cov=src/wahoo_systm_mcp --cov-report=term-missing

# Run integration tests (requires .env with credentials)
test-integration:
    uv run --env-file .env pytest -m integration

# Run all tests (unit + integration)
test-all:
    uv run --env-file .env pytest -m "" --cov=src/wahoo_systm_mcp --cov-report=term-missing

# Lint code with ruff
lint:
    uv run ruff check

# Type check with ty
typecheck:
    uv run ty check src/

# Run all checks (lint + typecheck)
check: lint typecheck

# Format code with ruff
format:
    uv run ruff format

# Format and fix lint issues
fix:
    uv run ruff check --fix
    uv run ruff format

# Install dependencies
install:
    uv sync

# Install pre-commit hooks
hooks:
    uv run prek install

# Update dependencies
update:
    uv lock --upgrade
    uv sync

# Clean build artifacts
clean:
    rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage htmlcov dist build *.egg-info
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

# Run the MCP server (requires .env with credentials)
serve:
    uv run --env-file .env wahoo-systm-mcp
