"""Chat API endpoint with streaming responses."""

from typing import Any, AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger

from cp_agent.projects import get_project_manager
from cp_agent.schemas.chat import ChatRequest, StreamEvent
from cp_agent.types import StreamEvent as InternalEvent
from cp_agent.types import TextEvent, ThinkingEvent, ToolEvent, UsageEvent
from cp_agent.utils.agent_helpers import get_agent

router = APIRouter()


def get_event_type(event: InternalEvent) -> str:
    """Get the event type string from an internal event.

    Args:
        event: The internal event

    Returns:
        The event type as a string
    """
    if isinstance(event, TextEvent):
        return "text"
    elif isinstance(event, ThinkingEvent):
        return "thinking"
    elif isinstance(event, ToolEvent):
        return "tool"
    elif isinstance(event, UsageEvent):
        return "usage"
    else:
        return "unknown"


@router.post("/")
async def chat(
    request: ChatRequest,
) -> StreamingResponse:
    """Process a chat message with streaming response.

    Args:
        request: The chat request containing MessageContent and project info

    Returns:
        A streaming response of SSE events
    """
    project_manager = get_project_manager()

    # Verify project exists
    project = await project_manager.get_project(request.project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    logger.info(f"Processing chat request for project: {request.project_id}")

    agent = await get_agent(request.project_id)
    agent.set_preview_path(request.context.preview_path or "/")

    async def event_generator() -> AsyncGenerator[str, Any]:
        try:
            async for event in agent.run(request.message):
                # Convert internal event types to StreamEvent for response
                if isinstance(event, (TextEvent, ThinkingEvent, ToolEvent, UsageEvent)):
                    logger.info(f"Event: {event}")
                    stream_event = StreamEvent(
                        type=get_event_type(event),
                        content=getattr(event, "text", None),
                        tool_name=getattr(event, "tool_name", None),
                        tool_id=getattr(event, "tool_id", None),
                        status=getattr(event, "status", None),
                        params=getattr(event, "params", None),
                        result=getattr(event, "result", None),
                        error=getattr(event, "error", None),
                        input_tokens=getattr(event, "input_tokens", None),
                        output_tokens=getattr(event, "output_tokens", None),
                        extra=getattr(event, "extra", None),
                    )
                    yield f"data: {stream_event.model_dump_json()}\n\n"
        except Exception as e:
            error_event = StreamEvent(type="error", error=str(e), tool_id=None)
            yield f"data: {error_event.model_dump_json()}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
