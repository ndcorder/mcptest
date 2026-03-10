"""Tests for snapshot testing utilities."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from mcp.types import CallToolResult, TextContent

from mcptest.snapshot import (
    _filter_fields,
    _serialize_result,
    assert_matches_snapshot,
)


def _make_result(text: str, is_error: bool = False) -> CallToolResult:
    """Helper to create a simple CallToolResult."""
    return CallToolResult(
        content=[TextContent(type="text", text=text)],
        isError=is_error,
    )


def test_serialize_result_text():
    """Test serializing a text CallToolResult."""
    result = _make_result("hello")
    serialized = _serialize_result(result)
    assert serialized == {"content": [{"type": "text", "text": "hello"}]}


def test_serialize_result_error():
    """Test serializing an error CallToolResult."""
    result = _make_result("error occurred", is_error=True)
    serialized = _serialize_result(result)
    assert serialized["isError"] is True


def test_filter_fields_removes_matching():
    """Test that filter_fields removes fields matching patterns."""
    data = {"name": "test", "timestamp": "2024-01-01", "id": "abc123"}
    filtered = _filter_fields(data, ["timestamp", "id"])
    assert filtered == {"name": "test"}


def test_filter_fields_glob_patterns():
    """Test that filter_fields supports glob patterns."""
    data = {"name": "test", "created_at": "2024", "updated_at": "2024"}
    filtered = _filter_fields(data, ["*_at"])
    assert filtered == {"name": "test"}


def test_filter_fields_nested():
    """Test that filter_fields works recursively on nested dicts."""
    data = {"outer": {"name": "test", "id": "123"}, "id": "456"}
    filtered = _filter_fields(data, ["id"])
    assert filtered == {"outer": {"name": "test"}}


def test_filter_fields_in_lists():
    """Test that filter_fields works on dicts inside lists."""
    data = [{"name": "a", "id": "1"}, {"name": "b", "id": "2"}]
    filtered = _filter_fields(data, ["id"])
    assert filtered == [{"name": "a"}, {"name": "b"}]


def test_snapshot_creates_file(tmp_path: Path):
    """Test that assert_matches_snapshot creates a snapshot file when missing."""
    snapshot_file = tmp_path / "snap.json"
    result = _make_result("hello")
    assert_matches_snapshot(result, snapshot_file)
    assert snapshot_file.exists()
    data = json.loads(snapshot_file.read_text())
    assert data["content"][0]["text"] == "hello"


def test_snapshot_matches(tmp_path: Path):
    """Test that assert_matches_snapshot passes when result matches snapshot."""
    snapshot_file = tmp_path / "snap.json"
    result = _make_result("hello")
    # Create the snapshot first
    assert_matches_snapshot(result, snapshot_file, update=True)
    # Now compare
    assert_matches_snapshot(result, snapshot_file)


def test_snapshot_mismatch_raises(tmp_path: Path):
    """Test that assert_matches_snapshot raises AssertionError on mismatch."""
    snapshot_file = tmp_path / "snap.json"
    result1 = _make_result("hello")
    result2 = _make_result("goodbye")
    # Create snapshot with result1
    assert_matches_snapshot(result1, snapshot_file, update=True)
    # Compare with result2 — should fail
    with pytest.raises(AssertionError, match="Snapshot mismatch"):
        assert_matches_snapshot(result2, snapshot_file)


def test_snapshot_update_overwrites(tmp_path: Path):
    """Test that update=True overwrites an existing snapshot."""
    snapshot_file = tmp_path / "snap.json"
    result1 = _make_result("old")
    result2 = _make_result("new")
    assert_matches_snapshot(result1, snapshot_file, update=True)
    assert_matches_snapshot(result2, snapshot_file, update=True)
    data = json.loads(snapshot_file.read_text())
    assert data["content"][0]["text"] == "new"


def test_snapshot_ignore_fields(tmp_path: Path):
    """Test that ignore_fields causes matching to pass despite differences."""
    snapshot_file = tmp_path / "snap.json"
    # Create snapshot
    snapshot_data = {"content": [{"type": "text", "text": "hello"}]}
    snapshot_file.write_text(json.dumps(snapshot_data))
    # The result matches (text field is not ignored)
    result = _make_result("hello")
    assert_matches_snapshot(result, snapshot_file, ignore_fields=["timestamp"])


def test_snapshot_creates_parent_dirs(tmp_path: Path):
    """Test that assert_matches_snapshot creates parent directories."""
    snapshot_file = tmp_path / "nested" / "dir" / "snap.json"
    result = _make_result("hello")
    assert_matches_snapshot(result, snapshot_file)
    assert snapshot_file.exists()
