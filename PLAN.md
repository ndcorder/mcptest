# mcptest — Implementation Plan

## Architecture Overview

The plugin wraps the MCP SDK's `Client` (in-memory) and `ClientSession` (stdio/HTTP)
behind a unified `MCPTestClient` that provides a synchronous-feeling API via pytest
fixtures, plus recording, replay, and snapshot capabilities.

```
src/mcptest/
  __init__.py          # Public API exports
  plugin.py            # Pytest plugin (hooks, CLI options, fixtures)
  client.py            # MCPTestClient — unified test client
  transports.py        # Transport enum + connection helpers
  conformance.py       # Conformance test suite runner
  recording.py         # Record/replay middleware (JSON fixtures)
  snapshot.py          # Snapshot comparison with configurable tolerance
```

## Critical Path (build order)

### Step 1: Core types and transport abstraction
- Define `Transport` enum (MEMORY, STDIO, HTTP)
- Helper functions to create read/write streams for each transport
- This is the foundation everything else builds on

### Step 2: MCPTestClient
- Wraps `mcp.Client` for in-memory testing (default)
- Wraps `ClientSession` + transport streams for stdio/HTTP
- Exposes: `call_tool()`, `list_tools()`, `list_resources()`, `read_resource()`,
  `list_prompts()`, `get_prompt()`, `initialize()`
- Async context manager

### Step 3: Pytest plugin and fixtures
- `pytest_addoption`: `--mcp-record`, `--mcp-replay`, `--mcp-transport`
- `pytest_configure`: register plugin
- Fixtures:
  - `mcp_client(server)` — returns MCPTestClient for a FastMCP app
  - `mcp_server()` — marker fixture for server under test
  - `tool_request` — factory fixture for building tool call args
  - `resource_request` — factory fixture for building resource read args

### Step 4: Recording middleware
- `Recorder` class that wraps client calls and saves request/response pairs
- Stores as JSON in a fixtures directory
- `Replayer` class that loads JSON and serves recorded responses
- Integration with `--mcp-record` and `--mcp-replay` CLI flags

### Step 5: Snapshot testing
- `SnapshotAssertion` that compares tool results to stored snapshots
- Configurable field ignoring (timestamps, IDs) via glob patterns
- `--snapshot-update` flag to overwrite snapshots
- `assert_matches_snapshot()` helper function

### Step 6: Conformance suite
- `ConformanceSuite` class with test methods:
  - `test_initialize` — server responds to initialize
  - `test_list_tools` — returns valid tool list
  - `test_call_tool` — tools are callable and return valid results
  - `test_list_resources` — returns valid resource list (if applicable)
  - `test_read_resource` — resources are readable (if applicable)
  - `test_list_prompts` — returns valid prompt list (if applicable)
  - `test_error_handling` — invalid tool call returns isError=True
  - `test_unknown_tool` — calling nonexistent tool errors properly
- `mcp_conformance_suite` fixture
- `run_all()` method that runs all applicable checks

## Design Decisions

1. **Default to in-memory transport**: Uses `mcp.Client` directly for zero-overhead
   unit testing. Stdio/HTTP available via `--mcp-transport` flag or fixture param.

2. **Async-first, sync wrapper**: All MCP operations are async. The client uses
   `anyio` internally. Tests use `pytest.mark.asyncio` or we provide sync wrappers.

3. **Recording format**: Simple JSON with `{method, params, result}` entries per
   interaction, one file per test function.

4. **Snapshot storage**: `__snapshots__/` directory next to test files, one JSON
   file per test function.

5. **Conformance is opt-in**: Users pass their server to the conformance fixture
   and call `run_all()` or individual checks.
