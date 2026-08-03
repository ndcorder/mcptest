"""MCP protocol conformance test suite."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

try:
    from mcp.server import MCPServer
except ImportError:  # MCP 1.x
    from mcp.server.fastmcp import FastMCP as MCPServer

from mcptest.client import MCPTestClient
from mcptest.transports import Transport


@dataclass
class ConformanceResult:
    """Result of a single conformance check."""

    name: str
    passed: bool
    message: str = ""


@dataclass
class ConformanceSuiteResult:
    """Aggregated results of the full conformance suite."""

    results: list[ConformanceResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def total(self) -> int:
        return len(self.results)

    @property
    def passed_count(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def failures(self) -> list[ConformanceResult]:
        return [r for r in self.results if not r.passed]

    def summary(self) -> str:
        lines = [f"Conformance: {self.passed_count}/{self.total} passed"]
        for f in self.failures:
            lines.append(f"  FAIL: {f.name} — {f.message}")
        return "\n".join(lines)


class ConformanceSuite:
    """Built-in conformance test suite for MCP servers.

    Validates that a server correctly implements the MCP protocol:
    capability negotiation, tool listing, tool calling, resource handling,
    prompt handling, and error responses.
    """

    def __init__(
        self,
        server: MCPServer,
        transport: Transport = Transport.MEMORY,
    ) -> None:
        self._server = server
        self._transport = transport

    async def run_all(self) -> ConformanceSuiteResult:
        """Run all conformance checks and return aggregated results."""
        suite_result = ConformanceSuiteResult()
        checks = [
            self.test_list_tools,
            self.test_call_tool,
            self.test_list_resources,
            self.test_list_prompts,
            self.test_unknown_tool,
            self.test_tool_schema_valid,
        ]
        for check in checks:
            result = await check()
            suite_result.results.append(result)
        return suite_result

    async def test_list_tools(self) -> ConformanceResult:
        """Verify that the server can list its tools."""
        try:
            client = MCPTestClient(self._server, transport=self._transport)
            async with client.connect():
                tools = await client.list_tools()
                if not isinstance(tools, list):
                    return ConformanceResult(
                        "list_tools", False, "list_tools did not return a list"
                    )
                return ConformanceResult("list_tools", True, f"Found {len(tools)} tools")
        except Exception as e:
            return ConformanceResult("list_tools", False, str(e))

    async def test_call_tool(self) -> ConformanceResult:
        """Verify that registered tools can be called and return valid results."""
        try:
            client = MCPTestClient(self._server, transport=self._transport)
            async with client.connect():
                tools = await client.list_tools()
                if not tools:
                    return ConformanceResult("call_tool", True, "No tools registered (skipped)")
                tool = tools[0]
                # Build minimal arguments from input schema
                args = _build_minimal_args(tool.get("inputSchema", {}))
                result = await client.call_tool(tool["name"], args)
                if result.content is None:
                    return ConformanceResult("call_tool", False, "Tool returned None content")
                return ConformanceResult("call_tool", True, f"Called '{tool['name']}' successfully")
        except Exception as e:
            return ConformanceResult("call_tool", False, str(e))

    async def test_list_resources(self) -> ConformanceResult:
        """Verify that the server can list its resources."""
        try:
            client = MCPTestClient(self._server, transport=self._transport)
            async with client.connect():
                resources = await client.list_resources()
                if not isinstance(resources, list):
                    return ConformanceResult(
                        "list_resources", False, "list_resources did not return a list"
                    )
                return ConformanceResult(
                    "list_resources", True, f"Found {len(resources)} resources"
                )
        except Exception as e:
            return ConformanceResult("list_resources", False, str(e))

    async def test_list_prompts(self) -> ConformanceResult:
        """Verify that the server can list its prompts."""
        try:
            client = MCPTestClient(self._server, transport=self._transport)
            async with client.connect():
                prompts = await client.list_prompts()
                if not isinstance(prompts, list):
                    return ConformanceResult(
                        "list_prompts", False, "list_prompts did not return a list"
                    )
                return ConformanceResult("list_prompts", True, f"Found {len(prompts)} prompts")
        except Exception as e:
            return ConformanceResult("list_prompts", False, str(e))

    async def test_unknown_tool(self) -> ConformanceResult:
        """Verify that calling a nonexistent tool raises an error or returns isError."""
        try:
            client = MCPTestClient(self._server, transport=self._transport)
            async with client.connect():
                try:
                    result = await client.call_tool("__nonexistent_tool_12345__", {})
                    if getattr(result, "is_error", False) or getattr(result, "isError", False):
                        return ConformanceResult(
                            "unknown_tool", True, "Correctly returned isError for unknown tool"
                        )
                    return ConformanceResult(
                        "unknown_tool", False, "Server did not error on unknown tool call"
                    )
                except Exception:
                    # Raising an exception is also acceptable
                    return ConformanceResult(
                        "unknown_tool", True, "Correctly raised exception for unknown tool"
                    )
        except Exception as e:
            return ConformanceResult("unknown_tool", False, f"Connection error: {e}")

    async def test_tool_schema_valid(self) -> ConformanceResult:
        """Verify that all tool input schemas are valid JSON Schema objects."""
        try:
            client = MCPTestClient(self._server, transport=self._transport)
            async with client.connect():
                tools = await client.list_tools()
                for tool in tools:
                    schema = tool.get("inputSchema", {})
                    if not isinstance(schema, dict):
                        return ConformanceResult(
                            "tool_schema_valid",
                            False,
                            f"Tool '{tool['name']}' has non-dict inputSchema",
                        )
                    if schema.get("type") != "object":
                        return ConformanceResult(
                            "tool_schema_valid",
                            False,
                            f"Tool '{tool['name']}' schema type is not 'object'",
                        )
                return ConformanceResult(
                    "tool_schema_valid", True, f"All {len(tools)} tool schemas are valid"
                )
        except Exception as e:
            return ConformanceResult("tool_schema_valid", False, str(e))


def _build_minimal_args(schema: dict[str, Any]) -> dict[str, Any]:
    """Build minimal valid arguments from a JSON Schema."""
    args: dict[str, Any] = {}
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    for name in required:
        prop = properties.get(name, {})
        prop_type = prop.get("type", "string")
        if prop_type == "string":
            args[name] = "test"
        elif prop_type == "integer":
            args[name] = 0
        elif prop_type == "number":
            args[name] = 0.0
        elif prop_type == "boolean":
            args[name] = True
        elif prop_type == "array":
            args[name] = []
        elif prop_type == "object":
            args[name] = {}
        else:
            args[name] = "test"
    return args
