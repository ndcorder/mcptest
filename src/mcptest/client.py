"""Mock MCP client for testing servers."""

from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from typing import Any

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.server.fastmcp import FastMCP
from mcp.types import (
    CallToolResult,
    GetPromptResult,
    ReadResourceResult,
    TextContent,
    TextResourceContents,
)
from pydantic import AnyUrl

from mcptest.transports import Transport

try:
    from mcp.client.streamable_http import streamable_http_client
except ImportError:
    streamable_http_client = None


class MCPTestClient:
    """A test client that sends MCP requests and captures responses.

    Supports in-memory, stdio, and HTTP transports. Default is in-memory
    which directly invokes server handlers without subprocess or network overhead.
    """

    def __init__(
        self,
        server: FastMCP | str,
        transport: Transport = Transport.MEMORY,
        server_url: str = "http://localhost:8000/mcp",
    ) -> None:
        self._server = server
        self._transport = transport
        self._server_url = server_url
        self._session: ClientSession | None = None
        self._connected = False

    @asynccontextmanager
    async def connect(self):
        """Connect to the MCP server and yield self as a context manager."""
        if self._transport == Transport.MEMORY:
            if not isinstance(self._server, FastMCP):
                raise TypeError("In-memory transport requires a FastMCP server instance.")
            self._connected = True
            try:
                yield self
            finally:
                self._connected = False
        elif self._transport == Transport.STDIO:
            async with self._connect_stdio() as session:
                self._session = session
                self._connected = True
                try:
                    yield self
                finally:
                    self._session = None
                    self._connected = False
        elif self._transport == Transport.HTTP:
            async with self._connect_http() as session:
                self._session = session
                self._connected = True
                try:
                    yield self
                finally:
                    self._session = None
                    self._connected = False
        else:
            raise ValueError(f"Unknown transport: {self._transport}")

    @asynccontextmanager
    async def _connect_stdio(self):
        """Connect using stdio transport via subprocess."""
        if isinstance(self._server, str):
            command = sys.executable
            args = [self._server]
        elif isinstance(self._server, FastMCP):
            raise TypeError(
                "Stdio transport requires a server script path (str), not a FastMCP instance."
            )
        else:
            command = sys.executable
            args = [str(self._server)]

        params = StdioServerParameters(command=command, args=args)
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session

    @asynccontextmanager
    async def _connect_http(self):
        """Connect using streamable HTTP transport."""
        if streamable_http_client is None:
            raise ImportError("streamable_http_client not available in this mcp SDK version.")
        async with streamable_http_client(self._server_url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                yield session

    def _check_connected(self) -> None:
        if not self._connected:
            raise RuntimeError("Client not connected. Use `async with client.connect():`")

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> CallToolResult:
        """Call a tool on the MCP server."""
        self._check_connected()
        args = arguments or {}
        if self._session is not None:
            return await self._session.call_tool(name, args)
        # In-memory: call FastMCP directly
        server = self._server
        assert isinstance(server, FastMCP)
        content_blocks, structured = await server.call_tool(name, args)
        return CallToolResult(content=list(content_blocks), structuredContent=structured)

    async def list_tools(self) -> list[dict[str, Any]]:
        """List available tools on the server."""
        self._check_connected()
        if self._session is not None:
            result = self._session
            resp = await result.list_tools()
            tools = resp.tools
        else:
            server = self._server
            assert isinstance(server, FastMCP)
            tools = await server.list_tools()
        return [
            {"name": t.name, "description": t.description, "inputSchema": t.inputSchema}
            for t in tools
        ]

    async def list_resources(self) -> list[dict[str, Any]]:
        """List available resources on the server."""
        self._check_connected()
        if self._session is not None:
            resp = await self._session.list_resources()
            resources = resp.resources
        else:
            server = self._server
            assert isinstance(server, FastMCP)
            resources = await server.list_resources()
        return [
            {"uri": str(r.uri), "name": r.name, "description": r.description} for r in resources
        ]

    async def read_resource(self, uri: str) -> ReadResourceResult:
        """Read a resource from the server."""
        self._check_connected()
        parsed_uri = AnyUrl(uri)
        if self._session is not None:
            return await self._session.read_resource(parsed_uri)
        # In-memory: call FastMCP directly, convert to ReadResourceResult
        server = self._server
        assert isinstance(server, FastMCP)
        raw_contents = await server.read_resource(uri)
        converted = [
            TextResourceContents(
                uri=parsed_uri,
                text=c.content if hasattr(c, "content") else str(c),
                mimeType=getattr(c, "mime_type", "text/plain"),
            )
            for c in raw_contents
        ]
        return ReadResourceResult(contents=converted)

    async def list_prompts(self) -> list[dict[str, Any]]:
        """List available prompts on the server."""
        self._check_connected()
        if self._session is not None:
            resp = await self._session.list_prompts()
            prompts = resp.prompts
        else:
            server = self._server
            assert isinstance(server, FastMCP)
            prompts = await server.list_prompts()
        return [{"name": p.name, "description": p.description} for p in prompts]

    async def get_prompt(
        self, name: str, arguments: dict[str, str] | None = None
    ) -> GetPromptResult:
        """Get a prompt from the server."""
        self._check_connected()
        args = arguments or {}
        if self._session is not None:
            return await self._session.get_prompt(name, args)
        # In-memory: call FastMCP directly
        server = self._server
        assert isinstance(server, FastMCP)
        return await server.get_prompt(name, args)

    def get_text_content(self, result: CallToolResult) -> str:
        """Extract text content from a CallToolResult."""
        texts = []
        for content in result.content:
            if isinstance(content, TextContent):
                texts.append(content.text)
        return "\n".join(texts)
