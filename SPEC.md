# mcptest — Project Specification

**4. mcptest**

*A pytest plugin for testing MCP servers without spinning up an LLM.*

  --------------------- -------------------------------------------------
  **Language**          Python 3.10+

  **Distribution**      PyPI (pip install pytest-mcptest)

  **Build Time**        7--10 days

  **License**           MIT

  **Category**          AI Tooling / Testing
  --------------------- -------------------------------------------------

**Problem**

The Model Context Protocol (MCP) is becoming the standard interface
between AI assistants and tools/data sources. But testing MCP servers
today means manual curl commands, ad-hoc scripts, or wiring up a real
LLM client. There's no testing framework that lets developers write unit
and integration tests for MCP tool handlers, validate protocol
conformance, or record/replay interactions.

**Solution**

A pytest plugin that provides mock MCP clients, protocol conformance
validators, request/response recording, and snapshot testing for MCP
server implementations. Developers can test their tool handlers in
isolation without needing a running LLM.

**Core Features**

- **Mock MCP client:** A configurable test client that sends MCP
  requests and captures responses. Supports both stdio and HTTP
  transports.

- **Conformance suite:** Built-in test cases that validate a server's
  compliance with the MCP specification: capability negotiation, tool
  listing, error responses, and resource handling.

- **Request recording:** Record real MCP interactions and replay them as
  regression tests. Stored as JSON fixtures.

- **Snapshot testing:** Assert tool responses match expected snapshots
  with configurable diff tolerance for timestamps and IDs.

- **Fixtures and factories:** Pytest fixtures for common patterns:
  mcp_client, mcp_server, tool_request, resource_request.

- **Transport abstraction:** Test the same handlers over stdio, SSE, and
  streamable HTTP without changing test code.

**Technical Architecture**

Built as a pytest plugin using pytest's fixture and hook system. The
mock client directly invokes server handler functions (for unit tests)
or connects via subprocess/HTTP (for integration tests). Protocol
conformance tests are parameterized from a YAML spec file tracking MCP
versions. Recording uses a middleware layer that serializes interactions
to JSON.

**CLI / API Surface**

> # In test files
>
> def test_my_tool(mcp_client):
>
> result = mcp_client.call_tool('search', {'query': 'test'})
>
> assert result.content[0].text == 'expected'
>
> def test_conformance(mcp_conformance_suite):
>
> mcp_conformance_suite.run_all() # runs full protocol checks
>
> # CLI
>
> pytest --mcp-record=fixtures/ # record mode
>
> pytest --mcp-replay=fixtures/ # replay mode

**Key Dependencies**

- pytest >= 7.0

- httpx (for HTTP transport testing)

- pydantic (protocol models)

- mcp SDK (for protocol types)

**Scope Boundaries**

**In scope:** Unit testing tool handlers, integration testing full
servers, protocol conformance, recording/replay, stdio and HTTP
transports.

**Out of scope:** Load testing, MCP client library (this tests servers
only), LLM response simulation, MCP proxy functionality.

**Success Criteria**

- Successfully tests 3+ real open-source MCP servers (filesystem,
  memory, git)

- Conformance suite catches known protocol violations

- Published on PyPI with pytest plugin entry point