# pytest-mcptest

A pytest plugin for testing MCP (Model Context Protocol) servers without spinning up an LLM.

## Why?

Testing MCP servers today means manual curl commands, ad-hoc scripts, or wiring up a real LLM client. **pytest-mcptest** gives you:

- A **mock MCP client** that calls your tool handlers directly — no subprocess, no network
- A **conformance suite** that validates your server against the MCP specification
- **Request recording/replay** for regression testing with JSON fixtures
- **Snapshot testing** for tool responses with configurable diff tolerance
- **Pytest fixtures** for common patterns: `mcp_client`, `tool_request`, `resource_request`

## Installation

```bash
pip install pytest-mcptest
```

## Quick Start

```python
import pytest
from mcp.server.fastmcp import FastMCP

# Your server under test
server = FastMCP("my-server")


@server.tool()
def search(query: str) -> str:
    """Search for something."""
    return f"Results for: {query}"


# Test it
@pytest.fixture
def my_server():
    return server


@pytest.mark.asyncio
async def test_search_tool(mcp_client, my_server):
    client = mcp_client(my_server)
    async with client.connect():
        result = await client.call_tool("search", {"query": "test"})
        assert client.get_text_content(result) == "Results for: test"
```

## Fixtures

### `mcp_client`

Factory fixture that creates an `MCPTestClient` for a given server.

```python
@pytest.mark.asyncio
async def test_my_tool(mcp_client, my_server):
    client = mcp_client(my_server)
    async with client.connect():
        # List tools
        tools = await client.list_tools()

        # Call a tool
        result = await client.call_tool("add", {"a": 1, "b": 2})

        # List and read resources
        resources = await client.list_resources()
        content = await client.read_resource("config://app")

        # List and get prompts
        prompts = await client.list_prompts()
        prompt = await client.get_prompt("review", {"code": "x = 1"})
```

### `mcp_conformance_suite`

Factory fixture that runs the full MCP protocol conformance suite against your server.

```python
@pytest.mark.asyncio
async def test_conformance(mcp_conformance_suite, my_server):
    suite = mcp_conformance_suite(my_server)
    result = await suite.run_all()
    assert result.passed, result.summary()
```

The suite checks:
- `list_tools` — server lists tools correctly
- `call_tool` — tools are callable and return valid results
- `list_resources` — server lists resources correctly
- `list_prompts` — server lists prompts correctly
- `unknown_tool` — calling a nonexistent tool errors properly
- `tool_schema_valid` — all tool input schemas are valid JSON Schema

### `tool_request` / `resource_request`

Factory fixtures for building request arguments.

```python
def test_request_building(tool_request, resource_request):
    req = tool_request("search", query="test", limit=10)
    # {"name": "search", "arguments": {"query": "test", "limit": 10}}

    res = resource_request("file:///tmp/data.json")
    # {"uri": "file:///tmp/data.json"}
```

## Recording & Replay

Record real MCP interactions and replay them as regression tests.

```bash
# Record mode — saves interactions to JSON fixtures
pytest --mcp-record=fixtures/

# Replay mode — serves pre-recorded responses
pytest --mcp-replay=fixtures/
```

```python
from mcptest import Recorder, Replayer

# Manual recording
recorder = Recorder("fixtures/")
recorder.record("call_tool", {"name": "search", "arguments": {"query": "test"}}, result)
recorder.save("test_search")

# Manual replay
replayer = Replayer("fixtures/")
replayer.load("test_search")
result = replayer.replay_call_tool("search", {"query": "test"})
```

## Snapshot Testing

Assert tool responses match stored snapshots with configurable field ignoring.

```python
from mcptest import assert_matches_snapshot


@pytest.mark.asyncio
async def test_tool_snapshot(mcp_client, my_server):
    client = mcp_client(my_server)
    async with client.connect():
        result = await client.call_tool("search", {"query": "test"})
        assert_matches_snapshot(
            result,
            "tests/__snapshots__/test_search.json",
            ignore_fields=["*timestamp*", "id"],  # glob patterns
        )
```

```bash
# Update snapshots
pytest --snapshot-update
```

## CLI Options

| Option | Description |
|-|-|
| `--mcp-record=DIR` | Record MCP interactions to JSON fixtures in DIR |
| `--mcp-replay=DIR` | Replay MCP interactions from JSON fixtures in DIR |
| `--mcp-transport=MODE` | Transport mode: `memory` (default), `stdio`, `http` |
| `--snapshot-update` | Update snapshot files instead of comparing |

## API Reference

### `MCPTestClient`

| Method | Description |
|-|-|
| `connect()` | Async context manager — connects to the server |
| `call_tool(name, arguments)` | Call a tool, returns `CallToolResult` |
| `list_tools()` | List available tools |
| `list_resources()` | List available resources |
| `read_resource(uri)` | Read a resource by URI |
| `list_prompts()` | List available prompts |
| `get_prompt(name, arguments)` | Get a prompt by name |
| `get_text_content(result)` | Extract text from a `CallToolResult` |

### `ConformanceSuite`

| Method | Description |
|-|-|
| `run_all()` | Run all conformance checks, returns `ConformanceSuiteResult` |
| `test_list_tools()` | Check tool listing |
| `test_call_tool()` | Check tool calling |
| `test_list_resources()` | Check resource listing |
| `test_list_prompts()` | Check prompt listing |
| `test_unknown_tool()` | Check error on unknown tool |
| `test_tool_schema_valid()` | Check tool schema validity |

### `Recorder` / `Replayer`

| Method | Description |
|-|-|
| `Recorder.record(method, params, result)` | Record an interaction |
| `Recorder.save(test_name)` | Save to JSON file |
| `Recorder.clear()` | Clear recorded interactions |
| `Replayer.load(test_name)` | Load from JSON file |
| `Replayer.next_response(method, params)` | Get next recorded response |
| `Replayer.replay_call_tool(name, arguments)` | Replay as `CallToolResult` |

## Contributing

1. Clone the repo
2. Install dependencies: `uv sync`
3. Run tests: `uv run pytest`
4. Run linter: `uv run ruff check .`
5. Format code: `uv run ruff format .`

## License

MIT
