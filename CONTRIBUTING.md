# Contributing to Corrigo SDK for Python

Thanks for your interest in contributing! This guide covers everything you need to get started.

## Development Setup

**Prerequisites:** Python 3.9+ and [uv](https://docs.astral.sh/uv/)

```bash
# Clone the repository
git clone https://github.com/wksusa/corrigo-python.git
cd corrigo-python

# Install all dependencies (SDK + CLI + dev + docs)
uv sync --all-extras

# Verify everything works
uv run pytest
```

## Running Tests

```bash
# Run the full test suite with coverage
uv run pytest

# Run a specific test file
uv run pytest tests/test_query.py

# Run a specific test
uv run pytest tests/test_query.py::test_where_equal
```

All PRs must pass the test suite. New features should include tests.

## Linting and Type Checking

```bash
# Lint with ruff
uv run ruff check src/ tests/

# Auto-fix lint issues
uv run ruff check --fix src/ tests/

# Type check with mypy (strict mode)
uv run mypy src/
```

Both `ruff` and `mypy` must pass cleanly before merging.

## Code Style

- **Line length:** 100 characters
- **Type hints:** Required on all public functions (strict mypy is enforced)
- **Docstrings:** Required on all public classes and methods
- **Imports:** Sorted by `isort` rules (handled by ruff)

## Submitting Changes

1. Fork the repository and create a branch from `main`
2. Make your changes
3. Add or update tests as needed
4. Ensure `uv run pytest`, `uv run ruff check src/ tests/`, and `uv run mypy src/` all pass
5. Submit a pull request

### PR Guidelines

- Keep PRs focused — one feature or fix per PR
- Write a clear description of what changed and why
- Reference any related issues

## Building Documentation

```bash
# Serve docs locally
uv run mkdocs serve

# Build static site
uv run mkdocs build
```

## Project Structure

```
src/corrigo/
  __init__.py        # Public API exports
  client.py          # Main CorrigoClient class
  auth.py            # OAuth 2.0 authentication
  http.py            # HTTP client and region config
  cli.py             # CLI implementation
  config.py          # Configuration management
  exceptions.py      # Exception hierarchy
  models/            # Pydantic models and enums
  api/               # API resources and query builder
tests/               # Test suite
docs/                # MkDocs documentation
```

## Questions?

Open an issue on [GitHub](https://github.com/wksusa/corrigo-python/issues) for bugs, feature requests, or questions.
