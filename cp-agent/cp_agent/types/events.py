"""Event types for streaming responses."""

from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class StreamEvent:
    """Base class for stream events."""

    pass


@dataclass
class TextEvent(StreamEvent):
    """Event for text chunks."""

    text: str


@dataclass
class ThinkingEvent(StreamEvent):
    """Event for thinking chunks."""

    text: str


@dataclass
class UsageEvent(StreamEvent):
    """Event for token usage information."""

    input_tokens: int
    output_tokens: int
    cache_write_tokens: Optional[int] = None
    cache_read_tokens: Optional[int] = None
    total_cost: Optional[float] = None


@dataclass
class ToolEvent(StreamEvent):
    """Event for tool execution results."""

    tool_name: str
    tool_id: str
    status: str
    params: Optional[dict[str, Any]]
    result: Optional[str] = None
    error: Optional[str] = None
    extra: Optional[dict[str, Any]] = None
