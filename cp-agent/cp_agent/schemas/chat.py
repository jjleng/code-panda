"""Chat message schema."""

from typing import Dict, Optional

from pydantic import BaseModel, Field

from cp_agent.utils.message_formats import MessageContent


class RequestContext(BaseModel):
    """Context information for chat requests."""

    preview_path: Optional[str] = Field(alias="previewPath", default="/")


class ChatRequest(BaseModel):
    """Chat request schema."""

    project_id: str = Field(description="Unique identifier for the project")
    message: MessageContent
    context: RequestContext = Field(description="Request context information")


class StreamEvent(BaseModel):
    """Base event schema for SSE responses."""

    type: str
    content: str | None = None
    error: str | None = None
    tool_name: str | None = None
    tool_id: str | None = None
    status: str | None = None
    params: Dict | None = None
    result: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    extra: Dict | None = None
