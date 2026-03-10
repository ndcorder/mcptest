# mcptest — Project Conventions

## Code Style
- Python 3.10+ (use `X | Y` union syntax, not `Optional`)
- Ruff for linting and formatting (line-length 100)
- Type hints on all public functions
- Docstrings on public classes and functions (Google style)
- Import order: stdlib, third-party, local (enforced by ruff)

## Commit Format
- `feat:` new feature
- `fix:` bug fix
- `test:` adding/updating tests
- `docs:` documentation
- `refactor:` code restructuring
- `chore:` project setup, CI, dependencies

## Project Structure
```
src/mcptest/         # Main package
  plugin.py          # Pytest plugin hooks and fixtures
  client.py          # Mock MCP client
  transports/        # Transport implementations (stdio, HTTP, SSE)
  conformance/       # Conformance test suite
  recording.py       # Request recording/replay
  snapshot.py        # Snapshot testing utilities
tests/               # Test suite
```

## Test Patterns
- Test files mirror source: `tests/test_client.py` for `src/mcptest/client.py`
- Use pytest fixtures, not setUp/tearDown
- Async tests use `pytest.mark.asyncio`
- Run: `uv run pytest`
- Lint: `uv run ruff check .`
