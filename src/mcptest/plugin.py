"""Pytest plugin for mcptest — hooks, CLI options, and fixtures."""

from __future__ import annotations

from typing import Any

import pytest

from mcptest.client import MCPTestClient
from mcptest.conformance import ConformanceSuite
from mcptest.recording import Recorder, Replayer
from mcptest.transports import Transport


def pytest_addoption(parser: pytest.Parser) -> None:
    """Register mcptest CLI options."""
    group = parser.getgroup("mcptest", "MCP server testing")
    group.addoption(
        "--mcp-record",
        metavar="DIR",
        default=None,
        help="Record MCP interactions to JSON fixtures in DIR.",
    )
    group.addoption(
        "--mcp-replay",
        metavar="DIR",
        default=None,
        help="Replay MCP interactions from JSON fixtures in DIR.",
    )
    group.addoption(
        "--mcp-transport",
        metavar="TRANSPORT",
        default="memory",
        choices=["memory", "stdio", "http"],
        help="MCP transport to use for testing (default: memory).",
    )
    group.addoption(
        "--snapshot-update",
        action="store_true",
        default=False,
        help="Update MCP snapshot files instead of comparing.",
    )


class MCPTestPlugin:
    """Plugin state holder for mcptest."""

    def __init__(self, config: pytest.Config) -> None:
        self.record_dir = config.getoption("--mcp-record")
        self.replay_dir = config.getoption("--mcp-replay")
        self.transport_name = config.getoption("--mcp-transport")
        self.snapshot_update = config.getoption("--snapshot-update")
        self.transport = Transport(self.transport_name)

        self.recorder: Recorder | None = None
        self.replayer: Replayer | None = None

        if self.record_dir:
            self.recorder = Recorder(self.record_dir)
        if self.replay_dir:
            self.replayer = Replayer(self.replay_dir)


def pytest_configure(config: pytest.Config) -> None:
    """Register the mcptest plugin."""
    plugin = MCPTestPlugin(config)
    config._mcptest_plugin = plugin  # type: ignore[attr-defined]
    config.addinivalue_line("markers", "mcp_server: mark test with an MCP server fixture")


@pytest.fixture
def mcp_transport(request: pytest.FixtureRequest) -> Transport:
    """The MCP transport mode for the current test session."""
    plugin: MCPTestPlugin = request.config._mcptest_plugin  # type: ignore[attr-defined]
    return plugin.transport


@pytest.fixture
def mcp_client(mcp_transport: Transport):
    """Factory fixture: creates an MCPTestClient for a given server.

    Usage:
        def test_my_tool(mcp_client):
            server = FastMCP("test")
            client = mcp_client(server)
            # client is an MCPTestClient ready for use in async with client.connect()
    """

    def _factory(server, transport: Transport | None = None, **kwargs):
        t = transport or mcp_transport
        return MCPTestClient(server, transport=t, **kwargs)

    return _factory


@pytest.fixture
def mcp_recorder(request: pytest.FixtureRequest) -> Recorder | None:
    """Provides the recorder if --mcp-record is active."""
    plugin: MCPTestPlugin = request.config._mcptest_plugin  # type: ignore[attr-defined]
    if plugin.recorder:
        plugin.recorder.clear()
    return plugin.recorder


@pytest.fixture
def mcp_replayer(request: pytest.FixtureRequest) -> Replayer | None:
    """Provides the replayer if --mcp-replay is active."""
    plugin: MCPTestPlugin = request.config._mcptest_plugin  # type: ignore[attr-defined]
    return plugin.replayer


@pytest.fixture
def mcp_snapshot_update(request: pytest.FixtureRequest) -> bool:
    """Whether --snapshot-update was passed."""
    plugin: MCPTestPlugin = request.config._mcptest_plugin  # type: ignore[attr-defined]
    return plugin.snapshot_update


@pytest.fixture
def mcp_conformance_suite(mcp_transport: Transport):
    """Factory fixture: creates a ConformanceSuite for a given server.

    Usage:
        async def test_conformance(mcp_conformance_suite):
            suite = mcp_conformance_suite(my_server)
            result = await suite.run_all()
            assert result.passed
    """

    def _factory(server, transport: Transport | None = None):
        t = transport or mcp_transport
        return ConformanceSuite(server, transport=t)

    return _factory


@pytest.fixture
def tool_request():
    """Factory fixture for building tool call arguments.

    Usage:
        def test_tool(tool_request):
            req = tool_request("search", query="test")
            # req == {"name": "search", "arguments": {"query": "test"}}
    """

    def _factory(name: str, **kwargs: Any) -> dict[str, Any]:
        return {"name": name, "arguments": kwargs}

    return _factory


@pytest.fixture
def resource_request():
    """Factory fixture for building resource read arguments.

    Usage:
        def test_resource(resource_request):
            req = resource_request("file:///tmp/test.txt")
            # req == {"uri": "file:///tmp/test.txt"}
    """

    def _factory(uri: str) -> dict[str, str]:
        return {"uri": uri}

    return _factory
