"""
The types package contains internal type definitions used for runtime type checking.

This package should contain:
1. TypedDict definitions for internal data structures
2. Enum classes for type-safe constants
3. Custom type definitions using Python's typing module
4. Internal type hints and annotations

Do not use this package for:
- Pydantic models (use schemas/ instead)
- API request/response models (use schemas/ instead)
- Data validation logic (use schemas/ instead)

Example:
    from typing import TypedDict, Literal

    class InternalConfig(TypedDict):
        mode: Literal["dev", "prod"]
        debug: bool
"""

from cp_agent.types.assistant_message import (
    AggressiveStreamingAssistantMessageParser,
    AssistantMessageContent,
    StreamingAssistantMessageParser,
    TextChunk,
    TextContent,
    ToolParamName,
    ToolUse,
    ToolUseName,
    parse_assistant_message,
)
from cp_agent.types.events import (
    StreamEvent,
    TextEvent,
    ThinkingEvent,
    ToolEvent,
    UsageEvent,
)

__all__ = [
    "AggressiveStreamingAssistantMessageParser",
    "AssistantMessageContent",
    "parse_assistant_message",
    "StreamingAssistantMessageParser",
    "TextChunk",
    "TextContent",
    "ToolEvent",
    "ToolParamName",
    "ToolUse",
    "ToolUseName",
    "StreamEvent",
    "TextEvent",
    "UsageEvent",
    "ThinkingEvent",
]
