"""Request recording and replay for MCP interactions."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mcp.types import CallToolResult, TextContent


class RecordedInteraction:
    """A single recorded MCP request/response pair."""

    def __init__(self, method: str, params: dict[str, Any], result: dict[str, Any]) -> None:
        self.method = method
        self.params = params
        self.result = result

    def to_dict(self) -> dict[str, Any]:
        return {"method": self.method, "params": self.params, "result": self.result}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RecordedInteraction:
        return cls(method=data["method"], params=data["params"], result=data["result"])


class Recorder:
    """Records MCP interactions to JSON fixture files.

    Wraps an MCPTestClient and captures every call_tool / list_tools / etc.
    interaction for later replay.
    """

    def __init__(self, fixture_dir: str | Path) -> None:
        self._fixture_dir = Path(fixture_dir)
        self._fixture_dir.mkdir(parents=True, exist_ok=True)
        self._interactions: list[RecordedInteraction] = []

    def record(self, method: str, params: dict[str, Any], result: Any) -> None:
        """Record a single interaction."""
        serialized_result = self._serialize_result(result)
        self._interactions.append(RecordedInteraction(method, params, serialized_result))

    def save(self, test_name: str) -> Path:
        """Save all recorded interactions to a JSON fixture file."""
        filepath = self._fixture_dir / f"{test_name}.json"
        data = [interaction.to_dict() for interaction in self._interactions]
        filepath.write_text(json.dumps(data, indent=2, default=str))
        return filepath

    def clear(self) -> None:
        """Clear all recorded interactions."""
        self._interactions.clear()

    @property
    def interactions(self) -> list[RecordedInteraction]:
        return list(self._interactions)

    def _serialize_result(self, result: Any) -> dict[str, Any]:
        """Serialize an MCP result to a JSON-compatible dict."""
        if isinstance(result, CallToolResult):
            content_list = []
            for c in result.content:
                if isinstance(c, TextContent):
                    content_list.append({"type": "text", "text": c.text})
                else:
                    content_list.append({"type": getattr(c, "type", "unknown")})
            return {
                "content": content_list,
                "isError": bool(
                    getattr(result, "is_error", False) or getattr(result, "isError", False)
                ),
            }
        if isinstance(result, list):
            return {"items": result}
        if isinstance(result, dict):
            return result
        if hasattr(result, "model_dump"):
            return result.model_dump(mode="json")
        return {"value": str(result)}


class Replayer:
    """Replays recorded MCP interactions from JSON fixture files.

    Loads a fixture file and serves pre-recorded responses for matching requests.
    """

    def __init__(self, fixture_dir: str | Path) -> None:
        self._fixture_dir = Path(fixture_dir)
        self._interactions: list[RecordedInteraction] = []
        self._index = 0

    def load(self, test_name: str) -> None:
        """Load interactions from a fixture file."""
        filepath = self._fixture_dir / f"{test_name}.json"
        if not filepath.exists():
            raise FileNotFoundError(f"No fixture file found: {filepath}")
        data = json.loads(filepath.read_text())
        self._interactions = [RecordedInteraction.from_dict(item) for item in data]
        self._index = 0

    def next_response(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        """Get the next recorded response for the given method.

        Raises ValueError if the recorded method doesn't match the requested one.
        """
        if self._index >= len(self._interactions):
            raise IndexError(
                f"No more recorded interactions. Expected call #{self._index + 1} "
                f"for method '{method}'."
            )
        interaction = self._interactions[self._index]
        if interaction.method != method:
            raise ValueError(
                f"Recorded interaction mismatch at index {self._index}: "
                f"expected '{interaction.method}', got '{method}'"
            )
        self._index += 1
        return interaction.result

    def replay_call_tool(self, name: str, arguments: dict[str, Any]) -> CallToolResult:
        """Replay a recorded call_tool response as a CallToolResult."""
        result_data = self.next_response("call_tool", {"name": name, "arguments": arguments})
        content = []
        for item in result_data.get("content", []):
            if item.get("type") == "text":
                content.append(TextContent(type="text", text=item["text"]))
        return CallToolResult(
            content=content,
            isError=result_data.get("isError", False),
        )

    @property
    def remaining(self) -> int:
        """Number of remaining unplayed interactions."""
        return len(self._interactions) - self._index

    @property
    def is_complete(self) -> bool:
        """Whether all recorded interactions have been replayed."""
        return self._index >= len(self._interactions)
