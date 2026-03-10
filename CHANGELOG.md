# Changelog

All notable changes to pytest-mcptest will be documented in this file.

## [0.1.0] — 2026-03-10

First release of pytest-mcptest — a pytest plugin for testing MCP servers without spinning up an LLM.

### New Features

- **Mock MCP Client**: Test your MCP server tool handlers directly in-memory with zero subprocess or network overhead. Call tools, list resources, read prompts — all through a simple async API.

- **Transport Abstraction**: Write tests once, run them over in-memory, stdio, SSE, or streamable HTTP transports. Switch transports with `--mcp-transport` without changing test code.

- **Conformance Suite**: Validate your server against the MCP protocol with built-in checks for tool listing, tool calling, resource listing, prompt listing, unknown tool error handling, and input schema validation. Run the full suite or individual checks.

- **Request Recording & Replay**: Record real MCP interactions to JSON fixture files with `--mcp-record`, then replay them as regression tests with `--mcp-replay`. Never worry about regressions in tool responses again.

- **Snapshot Testing**: Assert tool responses match stored snapshots with `assert_matches_snapshot()`. Supports configurable field ignoring via glob patterns (e.g., `["*timestamp*", "id"]`) so dynamic fields don't break your tests. Update snapshots in bulk with `--snapshot-update`.

- **Pytest Fixtures**: Ready-to-use fixtures for common testing patterns:
  - `mcp_client` — factory that creates a connected test client for any FastMCP server
  - `mcp_server` — overridable fixture to provide your server under test
  - `mcp_conformance_suite` — factory that creates a conformance runner for your server
  - `tool_request` / `resource_request` — helpers to build request argument dicts
  - `mcp_recorder` / `mcp_replayer` — access recording and replay when CLI flags are active
  - `mcp_snapshot_update` — check if `--snapshot-update` was passed

### CLI Options

| Option | Description |
|-|-|
| `--mcp-record=DIR` | Record MCP interactions to JSON fixtures |
| `--mcp-replay=DIR` | Replay MCP interactions from JSON fixtures |
| `--mcp-transport=MODE` | Transport mode: `memory`, `stdio`, `sse`, `http` |
| `--snapshot-update` | Update snapshot files instead of comparing |

### Infrastructure

- Pytest plugin auto-loads via `pytest11` entry point — just `pip install pytest-mcptest` and it works
- GitHub Actions CI for Python 3.10–3.13
- MIT licensed
