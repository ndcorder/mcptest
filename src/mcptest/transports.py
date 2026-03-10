"""Transport abstraction for MCP test connections."""

from __future__ import annotations

import enum


class Transport(enum.Enum):
    """Supported MCP transport modes for testing."""

    MEMORY = "memory"
    STDIO = "stdio"
    HTTP = "http"
