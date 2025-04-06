"""Event publishing and subscription system for coder agent components."""

from enum import Enum, auto
from typing import Any, Awaitable, Callable, Dict, Optional, Set, TypeVar

from loguru import logger

T = TypeVar("T")
EventCallback = Callable[[Dict[str, Any]], None]
AsyncEventCallback = Callable[[Dict[str, Any]], Awaitable[Any]]


class EventType(Enum):
    """Standard event types for the coder agent."""

    TASK_STARTED = auto()
    TASK_COMPLETED = auto()
    TASK_FAILED = auto()
    TASK_ABORTED = auto()
    TASK_TIMEOUT = auto()

    TOOL_REQUESTED = auto()
    TOOL_EXECUTING = auto()
    TOOL_COMPLETED = auto()
    TOOL_FAILED = auto()

    TURN_STARTED = auto()
    TURN_COMPLETED = auto()
    TURN_DISCARDED = auto()

    FILE_READ = auto()
    FILE_WRITTEN = auto()
    FILE_DELETED = auto()
    FILE_RENAMED = auto()
    FILE_DIFF_APPLIED = auto()

    DEPENDENCY_ADDED = auto()

    STREAM_STARTED = auto()
    STREAM_ENDED = auto()
    THINKING_STARTED = auto()
    THINKING_ENDED = auto()

    MEMORY_COMPACT_REQUESTED = auto()

    HOOK_FAILED = auto()
    USAGE_UPDATED = auto()
    MIGRATION_FAILED = auto()


class EventBus:
    """Event bus for publishing and subscribing to events."""

    def __init__(self) -> None:
        self._sync_subscribers: Dict[EventType, Set[EventCallback]] = {}
        self._async_subscribers: Dict[EventType, Set[AsyncEventCallback]] = {}
        logger.debug("EventBus initialized")

    def subscribe(self, event_type: EventType, callback: EventCallback) -> None:
        """Subscribe to an event type with a synchronous callback."""
        if event_type not in self._sync_subscribers:
            self._sync_subscribers[event_type] = set()
        self._sync_subscribers[event_type].add(callback)
        logger.debug(f"Sync subscriber added for {event_type.name}")

    def subscribe_async(
        self, event_type: EventType, callback: AsyncEventCallback
    ) -> None:
        """Subscribe to an event type with an asynchronous callback."""
        if event_type not in self._async_subscribers:
            self._async_subscribers[event_type] = set()
        self._async_subscribers[event_type].add(callback)
        logger.debug(f"Async subscriber added for {event_type.name}")

    def unsubscribe(self, event_type: EventType, callback: EventCallback) -> None:
        """Unsubscribe a synchronous callback from an event type."""
        if event_type in self._sync_subscribers:
            self._sync_subscribers[event_type].discard(callback)
            logger.debug(f"Sync subscriber removed from {event_type.name}")

    def unsubscribe_async(
        self, event_type: EventType, callback: AsyncEventCallback
    ) -> None:
        """Unsubscribe an asynchronous callback from an event type."""
        if event_type in self._async_subscribers:
            self._async_subscribers[event_type].discard(callback)
            logger.debug(f"Async subscriber removed from {event_type.name}")

    def publish(
        self, event_type: EventType, data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Publish an event synchronously to all subscribers."""
        data = data or {}
        logger.debug(f"Publishing sync event: {event_type.name}, data: {data}")

        if event_type in self._sync_subscribers:
            for callback in self._sync_subscribers[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in event handler for {event_type.name}: {e}")

    async def publish_async(
        self, event_type: EventType, data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Publish an event asynchronously to all subscribers."""
        data = data or {}
        logger.debug(f"Publishing async event: {event_type.name}, data: {data}")

        # Execute synchronous subscribers
        self.publish(event_type, data)

        # Execute asynchronous subscribers
        if event_type in self._async_subscribers:
            for callback in self._async_subscribers[event_type]:
                try:
                    await callback(data)
                except Exception as e:
                    logger.error(
                        f"Error in async event handler for {event_type.name}: {e}"
                    )
