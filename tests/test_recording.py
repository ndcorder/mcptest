"""Tests for recording and replay functionality."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from mcp.types import CallToolResult, TextContent

from mcptest.recording import Recorder, Replayer


def test_recorder_records_interaction(tmp_path: Path):
    """Test that a recorder captures interactions."""
    recorder = Recorder(tmp_path / "fixtures")
    result = CallToolResult(
        content=[TextContent(type="text", text="42")],
    )
    recorder.record("call_tool", {"name": "add", "arguments": {"a": 1, "b": 2}}, result)
    assert len(recorder.interactions) == 1
    assert recorder.interactions[0].method == "call_tool"


def test_recorder_saves_to_file(tmp_path: Path):
    """Test that interactions are saved to a JSON file."""
    recorder = Recorder(tmp_path / "fixtures")
    result = CallToolResult(
        content=[TextContent(type="text", text="hello")],
    )
    recorder.record("call_tool", {"name": "greet", "arguments": {"name": "test"}}, result)
    filepath = recorder.save("test_greet")
    assert filepath.exists()
    data = json.loads(filepath.read_text())
    assert len(data) == 1
    assert data[0]["method"] == "call_tool"
    assert data[0]["result"]["content"][0]["text"] == "hello"


def test_recorder_clear(tmp_path: Path):
    """Test clearing recorded interactions."""
    recorder = Recorder(tmp_path / "fixtures")
    recorder.record("call_tool", {}, {"value": "test"})
    assert len(recorder.interactions) == 1
    recorder.clear()
    assert len(recorder.interactions) == 0


def test_replayer_loads_fixture(tmp_path: Path):
    """Test that a replayer can load a fixture file."""
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    data = [
        {
            "method": "call_tool",
            "params": {"name": "add", "arguments": {"a": 1, "b": 2}},
            "result": {"content": [{"type": "text", "text": "3"}], "isError": False},
        }
    ]
    (fixture_dir / "test_add.json").write_text(json.dumps(data))

    replayer = Replayer(fixture_dir)
    replayer.load("test_add")
    assert replayer.remaining == 1
    assert not replayer.is_complete


def test_replayer_next_response(tmp_path: Path):
    """Test getting the next response from a replayer."""
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    data = [
        {
            "method": "call_tool",
            "params": {"name": "add", "arguments": {}},
            "result": {"content": [{"type": "text", "text": "3"}]},
        }
    ]
    (fixture_dir / "test.json").write_text(json.dumps(data))

    replayer = Replayer(fixture_dir)
    replayer.load("test")
    response = replayer.next_response("call_tool", {})
    assert response["content"][0]["text"] == "3"
    assert replayer.is_complete


def test_replayer_method_mismatch(tmp_path: Path):
    """Test that replayer raises ValueError on method mismatch."""
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    data = [
        {
            "method": "call_tool",
            "params": {},
            "result": {"content": []},
        }
    ]
    (fixture_dir / "test.json").write_text(json.dumps(data))

    replayer = Replayer(fixture_dir)
    replayer.load("test")
    with pytest.raises(ValueError, match="mismatch"):
        replayer.next_response("list_tools", {})


def test_replayer_exhausted(tmp_path: Path):
    """Test that replayer raises IndexError when all interactions are consumed."""
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    data = [
        {"method": "call_tool", "params": {}, "result": {"content": []}},
    ]
    (fixture_dir / "test.json").write_text(json.dumps(data))

    replayer = Replayer(fixture_dir)
    replayer.load("test")
    replayer.next_response("call_tool", {})
    with pytest.raises(IndexError):
        replayer.next_response("call_tool", {})


def test_replayer_missing_fixture(tmp_path: Path):
    """Test that replayer raises FileNotFoundError for missing fixtures."""
    replayer = Replayer(tmp_path)
    with pytest.raises(FileNotFoundError):
        replayer.load("nonexistent")


def test_replayer_replay_call_tool(tmp_path: Path):
    """Test replaying a call_tool response as CallToolResult."""
    fixture_dir = tmp_path / "fixtures"
    fixture_dir.mkdir()
    data = [
        {
            "method": "call_tool",
            "params": {"name": "greet", "arguments": {"name": "Test"}},
            "result": {
                "content": [{"type": "text", "text": "Hello, Test!"}],
                "isError": False,
            },
        }
    ]
    (fixture_dir / "test.json").write_text(json.dumps(data))

    replayer = Replayer(fixture_dir)
    replayer.load("test")
    result = replayer.replay_call_tool("greet", {"name": "Test"})
    assert isinstance(result, CallToolResult)
    assert len(result.content) == 1
    assert isinstance(result.content[0], TextContent)
    assert result.content[0].text == "Hello, Test!"


def test_recorder_serializes_list(tmp_path: Path):
    """Test that recorder can serialize list results."""
    recorder = Recorder(tmp_path / "fixtures")
    recorder.record("list_tools", {}, [{"name": "add"}, {"name": "greet"}])
    assert recorder.interactions[0].result == {"items": [{"name": "add"}, {"name": "greet"}]}


def test_recorder_serializes_dict(tmp_path: Path):
    """Test that recorder can serialize dict results."""
    recorder = Recorder(tmp_path / "fixtures")
    recorder.record("custom", {}, {"key": "value"})
    assert recorder.interactions[0].result == {"key": "value"}
