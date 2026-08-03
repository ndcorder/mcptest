"""Shared test fixtures — sample MCP servers for testing the plugin."""

from __future__ import annotations

import pytest
from mcp.server import MCPServer


@pytest.fixture
def sample_server() -> MCPServer:
    """A sample MCP server with tools, resources, and prompts for testing."""
    server = MCPServer("test-server")

    @server.tool()
    def add(a: int, b: int) -> int:
        """Add two numbers together."""
        return a + b

    @server.tool()
    def greet(name: str) -> str:
        """Greet someone by name."""
        return f"Hello, {name}!"

    @server.tool()
    def divide(a: float, b: float) -> float:
        """Divide a by b."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b

    @server.resource("config://app")
    def get_config() -> str:
        """Get application configuration."""
        return '{"debug": true, "version": "1.0"}'

    @server.prompt()
    def review_code(code: str) -> str:
        """Generate a code review prompt."""
        return f"Please review this code:\n\n{code}"

    return server


@pytest.fixture
def empty_server() -> MCPServer:
    """An MCP server with no tools, resources, or prompts."""
    return MCPServer("empty-server")
