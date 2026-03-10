"""Tests for the conformance test suite."""

from __future__ import annotations

import pytest
from mcp.server.fastmcp import FastMCP

from mcptest.conformance import ConformanceSuite, _build_minimal_args


@pytest.mark.asyncio
async def test_conformance_all_pass(sample_server: FastMCP):
    """Test that the conformance suite passes for a well-behaved server."""
    suite = ConformanceSuite(sample_server)
    result = await suite.run_all()
    assert result.passed, result.summary()
    assert result.total == 6
    assert result.failed_count == 0


@pytest.mark.asyncio
async def test_conformance_empty_server(empty_server: FastMCP):
    """Test conformance suite on a server with no tools."""
    suite = ConformanceSuite(empty_server)
    result = await suite.run_all()
    assert result.passed, result.summary()


@pytest.mark.asyncio
async def test_conformance_list_tools(sample_server: FastMCP):
    """Test the list_tools conformance check individually."""
    suite = ConformanceSuite(sample_server)
    result = await suite.test_list_tools()
    assert result.passed
    assert "3 tools" in result.message


@pytest.mark.asyncio
async def test_conformance_unknown_tool(sample_server: FastMCP):
    """Test the unknown_tool conformance check."""
    suite = ConformanceSuite(sample_server)
    result = await suite.test_unknown_tool()
    assert result.passed


@pytest.mark.asyncio
async def test_conformance_tool_schema(sample_server: FastMCP):
    """Test the tool schema validation check."""
    suite = ConformanceSuite(sample_server)
    result = await suite.test_tool_schema_valid()
    assert result.passed


@pytest.mark.asyncio
async def test_conformance_summary(sample_server: FastMCP):
    """Test that the summary output is formatted correctly."""
    suite = ConformanceSuite(sample_server)
    result = await suite.run_all()
    summary = result.summary()
    assert "6/6 passed" in summary


def test_build_minimal_args_string():
    """Test building minimal args with a required string field."""
    schema = {
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": ["name"],
    }
    args = _build_minimal_args(schema)
    assert args == {"name": "test"}


def test_build_minimal_args_integer():
    """Test building minimal args with a required integer field."""
    schema = {
        "type": "object",
        "properties": {"count": {"type": "integer"}},
        "required": ["count"],
    }
    args = _build_minimal_args(schema)
    assert args == {"count": 0}


def test_build_minimal_args_no_required():
    """Test building minimal args with no required fields."""
    schema = {
        "type": "object",
        "properties": {"optional": {"type": "string"}},
    }
    args = _build_minimal_args(schema)
    assert args == {}


def test_build_minimal_args_multiple_types():
    """Test building minimal args with multiple types."""
    schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "score": {"type": "number"},
            "active": {"type": "boolean"},
            "tags": {"type": "array"},
            "meta": {"type": "object"},
        },
        "required": ["name", "age", "score", "active", "tags", "meta"],
    }
    args = _build_minimal_args(schema)
    assert args == {
        "name": "test",
        "age": 0,
        "score": 0.0,
        "active": True,
        "tags": [],
        "meta": {},
    }
