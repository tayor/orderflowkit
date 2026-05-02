# Contributing

Thanks for helping improve OrderFlowKit.

## Development Setup

```bash
uv venv
uv sync --extra dev --extra stream --extra viz --extra bars
```

## Local Checks

Run these before opening a pull request:

```bash
uv run pytest
uv run ruff check .
uv run mypy
uv run python -m build
uv run twine check dist/*
```

Tests must not depend on live exchange connectivity. Use fixtures, mocks, and tiny deterministic datasets.

## Scope

OrderFlowKit focuses on free-data market microstructure research. Please avoid adding private order execution, paid-data wrappers, portfolio backtesting, or manipulation-detection claims without a separate design discussion.

## Style

- Keep APIs pandas-first and deterministic.
- Prefer small composable functions over framework-heavy abstractions.
- Preserve raw market-data payloads where practical.
- Make invalid data explicit through flags and reports.
