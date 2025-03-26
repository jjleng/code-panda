"""Base class for agent implementations."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import AsyncGenerator, Optional

from cp_agent.context import ContextEnricher
from cp_agent.storage.list_store import ListStore
from cp_agent.types import StreamEvent
from cp_agent.utils.message_formats import MessageContent


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(
        self,
        memory: ListStore,
        cwd: str = str(Path.cwd()),
        context_enricher: Optional[ContextEnricher] = None,
    ):
        """Initialize the agent.

        Args:
            memory: Persistent storage for conversation history
            context_enricher: Optional enricher for contextual information
            cwd: Current working directory, defaults to current directory
        """
        self.memory = memory
        self.cwd = cwd
        # If context_enricher is not provided, create one with the current cwd
        if context_enricher is None:
            context_enricher = ContextEnricher(memory=memory, cwd=cwd)
        # If context_enricher is provided, ensure it has the same cwd
        else:
            context_enricher.cwd = cwd
        self.context_enricher = context_enricher

    @abstractmethod
    def run(self, message: MessageContent) -> AsyncGenerator[StreamEvent, None]:
        """Process a message and generate a response.

        Args:
            message: The input message content to process

        Returns:
            Either a string response or a stream of events
        """
        raise NotImplementedError("Agents must implement run method")
