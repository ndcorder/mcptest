"""Tests for the pytest plugin fixtures and CLI options."""

from __future__ import annotations

import pytest

from mcptest.transports import Transport


def test_tool_request_fixture(tool_request):
    """Test the tool_request factory fixture."""
    req = tool_request("search", query="test", limit=10)
    assert req == {"name": "search", "arguments": {"query": "test", "limit": 10}}


def test_resource_request_fixture(resource_request):
    """Test the resource_request factory fixture."""
    req = resource_request("file:///tmp/test.txt")
    assert req == {"uri": "file:///tmp/test.txt"}


def test_mcp_transport_fixture(mcp_transport):
    """Test the mcp_transport fixture returns a Transport."""
    assert isinstance(mcp_transport, Transport)
    assert mcp_transport == Transport.MEMORY


@pytest.mark.asyncio
async def test_mcp_client_fixture(mcp_client, sample_server):
    """Test the mcp_client factory fixture."""
    client = mcp_client(sample_server)
    async with client.connect():
        tools = await client.list_tools()
        assert len(tools) == 3


@pytest.mark.asyncio
async def test_mcp_conformance_fixture(mcp_conformance_suite, sample_server):
    """Test the mcp_conformance_suite factory fixture."""
    suite = mcp_conformance_suite(sample_server)
    result = await suite.run_all()
    assert result.passed
