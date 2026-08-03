"""Tests for MCPTestClient."""

from __future__ import annotations

import pytest
from mcp.server import MCPServer
from mcp.types import TextContent

from mcptest.client import MCPTestClient
from mcptest.transports import Transport


@pytest.mark.asyncio
async def test_call_tool_add(sample_server: MCPServer):
    """Test calling a tool that adds two numbers."""
    client = MCPTestClient(sample_server)
    async with client.connect():
        result = await client.call_tool("add", {"a": 2, "b": 3})
        text = client.get_text_content(result)
        assert text == "5"


@pytest.mark.asyncio
async def test_call_tool_greet(sample_server: MCPServer):
    """Test calling a tool that greets by name."""
    client = MCPTestClient(sample_server)
    async with client.connect():
        result = await client.call_tool("greet", {"name": "World"})
        text = client.get_text_content(result)
        assert text == "Hello, World!"


@pytest.mark.asyncio
async def test_list_tools(sample_server: MCPServer):
    """Test listing all available tools."""
    client = MCPTestClient(sample_server)
    async with client.connect():
        tools = await client.list_tools()
        names = {t["name"] for t in tools}
        assert "add" in names
        assert "greet" in names
        assert "divide" in names
        assert len(tools) == 3


@pytest.mark.asyncio
async def test_list_resources(sample_server: MCPServer):
    """Test listing all available resources."""
    client = MCPTestClient(sample_server)
    async with client.connect():
        resources = await client.list_resources()
        assert len(resources) == 1
        assert resources[0]["name"] == "get_config"


@pytest.mark.asyncio
async def test_read_resource(sample_server: MCPServer):
    """Test reading a resource."""
    client = MCPTestClient(sample_server)
    async with client.connect():
        result = await client.read_resource("config://app")
        assert len(result.contents) > 0


@pytest.mark.asyncio
async def test_list_prompts(sample_server: MCPServer):
    """Test listing all available prompts."""
    client = MCPTestClient(sample_server)
    async with client.connect():
        prompts = await client.list_prompts()
        assert len(prompts) == 1
        assert prompts[0]["name"] == "review_code"


@pytest.mark.asyncio
async def test_get_prompt(sample_server: MCPServer):
    """Test getting a prompt."""
    client = MCPTestClient(sample_server)
    async with client.connect():
        result = await client.get_prompt("review_code", {"code": "print('hi')"})
        assert result.messages is not None
        assert len(result.messages) > 0


@pytest.mark.asyncio
async def test_tool_error_handling(sample_server: MCPServer):
    """Test that tool errors are propagated."""
    client = MCPTestClient(sample_server)
    async with client.connect():
        with pytest.raises(Exception):
            await client.call_tool("divide", {"a": 1.0, "b": 0.0})


@pytest.mark.asyncio
async def test_unknown_tool_raises(sample_server: MCPServer):
    """Test that calling a nonexistent tool raises an error."""
    client = MCPTestClient(sample_server)
    async with client.connect():
        with pytest.raises(Exception):
            await client.call_tool("nonexistent_tool", {})


@pytest.mark.asyncio
async def test_not_connected_raises():
    """Test that calling methods without connecting raises RuntimeError."""
    server = MCPServer("test")
    client = MCPTestClient(server)
    with pytest.raises(RuntimeError, match="not connected"):
        await client.call_tool("test", {})
    with pytest.raises(RuntimeError, match="not connected"):
        await client.list_tools()


@pytest.mark.asyncio
async def test_empty_server_list_tools(empty_server: MCPServer):
    """Test listing tools on a server with no tools."""
    client = MCPTestClient(empty_server)
    async with client.connect():
        tools = await client.list_tools()
        assert tools == []


@pytest.mark.asyncio
async def test_get_text_content(sample_server: MCPServer):
    """Test extracting text content from a CallToolResult."""
    client = MCPTestClient(sample_server)
    async with client.connect():
        result = await client.call_tool("greet", {"name": "Test"})
        assert isinstance(result.content[0], TextContent)
        assert result.content[0].text == "Hello, Test!"


@pytest.mark.asyncio
async def test_transport_enum():
    """Test Transport enum values."""
    assert Transport.MEMORY.value == "memory"
    assert Transport.STDIO.value == "stdio"
    assert Transport.SSE.value == "sse"
    assert Transport.HTTP.value == "http"
