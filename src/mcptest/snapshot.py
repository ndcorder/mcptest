"""Snapshot testing utilities for MCP tool responses."""

from __future__ import annotations

import fnmatch
import json
from pathlib import Path
from typing import Any

from mcp.types import CallToolResult, TextContent


def _serialize_result(result: CallToolResult) -> dict[str, Any]:
    """Convert a CallToolResult to a JSON-serializable dict."""
    content = []
    for c in result.content:
        if isinstance(c, TextContent):
            content.append({"type": "text", "text": c.text})
        elif hasattr(c, "model_dump"):
            content.append(c.model_dump(mode="json"))
        else:
            content.append({"type": getattr(c, "type", "unknown")})
    data: dict[str, Any] = {"content": content}
    if result.isError:
        data["isError"] = True
    if result.structuredContent is not None:
        data["structuredContent"] = result.structuredContent
    return data


def _filter_fields(data: Any, ignore_patterns: list[str]) -> Any:
    """Recursively remove fields matching ignore patterns from a dict."""
    if isinstance(data, dict):
        return {
            k: _filter_fields(v, ignore_patterns)
            for k, v in data.items()
            if not any(fnmatch.fnmatch(k, pat) for pat in ignore_patterns)
        }
    if isinstance(data, list):
        return [_filter_fields(item, ignore_patterns) for item in data]
    return data


def assert_matches_snapshot(
    result: CallToolResult,
    snapshot_path: str | Path,
    *,
    ignore_fields: list[str] | None = None,
    update: bool = False,
) -> None:
    """Assert that a tool result matches a stored snapshot.

    Args:
        result: The CallToolResult to compare.
        snapshot_path: Path to the snapshot JSON file.
        ignore_fields: Glob patterns for field names to ignore (e.g., ["*timestamp*", "id"]).
        update: If True, overwrite the snapshot with the current result.
    """
    path = Path(snapshot_path)
    ignore = ignore_fields or []
    actual = _filter_fields(_serialize_result(result), ignore)

    if update or not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(actual, indent=2, default=str) + "\n")
        return

    expected = _filter_fields(json.loads(path.read_text()), ignore)

    if actual != expected:
        actual_str = json.dumps(actual, indent=2, sort_keys=True, default=str)
        expected_str = json.dumps(expected, indent=2, sort_keys=True, default=str)
        raise AssertionError(
            f"Snapshot mismatch.\n\n"
            f"Expected:\n{expected_str}\n\n"
            f"Actual:\n{actual_str}\n\n"
            f"To update the snapshot, pass update=True or run with --snapshot-update."
        )
