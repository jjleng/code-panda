"""Stream processing capabilities for handling LLM responses."""

import asyncio
from typing import Any, AsyncGenerator, Callable, Dict, Optional

from litellm import CustomStreamWrapper, Usage
from litellm.types.utils import ModelResponseStream, StreamingChoices
from loguru import logger

from cp_agent.agents.coder.event_bus import EventBus, EventType
from cp_agent.agents.coder.state_manager import StateManager
from cp_agent.types import (
    AggressiveStreamingAssistantMessageParser,
    StreamEvent,
    TextEvent,
    ToolEvent,
    UsageEvent,
)


class StreamProcessor:
    """Processes streaming responses from LLM into structured events."""

    def __init__(
        self,
        cwd: str,
        state_manager: StateManager,
        on_tool_execute: Callable[[str, Dict[str, Any], str], asyncio.Task],
        event_bus: Optional[EventBus] = None,
    ):
        self.cwd = cwd
        self.state_manager = state_manager
        self.on_tool_execute = on_tool_execute
        self.parser = AggressiveStreamingAssistantMessageParser()
        self.event_bus = event_bus

    async def process_stream(
        self, response: CustomStreamWrapper, tool_queue: asyncio.Queue
    ) -> AsyncGenerator[StreamEvent, None]:
        """Process a streaming LLM response into structured events.

        Args:
            response: Streaming LLM response
            tool_queue: Queue for tool execution requests

        Yields:
            StreamEvents for UI rendering
        """
        try:
            self.state_manager.streaming.is_active = True
            self.state_manager.streaming.current_message = ""

            # Publish stream started event
            if self.event_bus:
                self.event_bus.publish(EventType.STREAM_STARTED, {})

            async for chunk in response:
                # Check if processing should stop
                if self.state_manager.task.status == "aborted":
                    break

                if isinstance(chunk, ModelResponseStream) and chunk.choices:
                    choice = chunk.choices[0]
                    if isinstance(choice, StreamingChoices) and choice.delta.content:
                        content = choice.delta.content
                        self.state_manager.streaming.current_message += content

                        # Process events from parser
                        for event in self.parser(content):
                            yield event

                            # Handle tool events
                            if (
                                isinstance(event, ToolEvent)
                                and event.status == "executing"
                            ):
                                # Publish tool requested event
                                if self.event_bus:
                                    self.event_bus.publish(
                                        EventType.TOOL_REQUESTED,
                                        {
                                            "name": event.tool_name,
                                            "id": event.tool_id,
                                            "params": event.params,
                                        },
                                    )

                                # Queue tool for execution
                                await tool_queue.put(
                                    {
                                        "name": event.tool_name,
                                        "params": event.params or {},
                                        "tool_id": event.tool_id,
                                    }
                                )

                    # Yield usage information if available
                    if "usage" in chunk:
                        usage: Usage = chunk["usage"]
                        usage_event = UsageEvent(
                            input_tokens=usage.prompt_tokens,
                            output_tokens=usage.completion_tokens,
                        )
                        yield usage_event

                        if self.event_bus:
                            self.event_bus.publish(
                                EventType.USAGE_UPDATED,
                                {
                                    "input_tokens": usage.prompt_tokens,
                                    "output_tokens": usage.completion_tokens,
                                },
                            )

            # Process any remaining content
            for event in self.parser(None):
                yield event

            # Publish stream ended event
            if self.event_bus:
                self.event_bus.publish(EventType.STREAM_ENDED, {})

        except asyncio.CancelledError:
            logger.info("Stream processing cancelled")
            raise

        except Exception as e:
            logger.error(f"Error processing stream: {e}", exc_info=True)
            yield TextEvent(text=f"Error processing assistant response: {e}")

        finally:
            self.state_manager.streaming.is_active = False
