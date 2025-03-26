"""Message handling and storage capabilities for the coder agent."""

from typing import Any, Optional

from loguru import logger

from cp_agent.config import settings
from cp_agent.storage.list_store import BaseListStore, TokenBasedCompactingListStore
from cp_agent.utils.message_formats import (
    Attachment,
    Message,
    MessageContent,
    create_message_content,
)


class MessageManager:
    """Handles message storage, retrieval, and formatting for the coder agent."""

    def __init__(
        self,
        memory: BaseListStore,
        compact_threshold_tokens: int = settings.COMPACT_THRESHOLD_TOKENS,
        compact_target_ratio: float = settings.COMPACT_TARGET_RATIO,
        enable_prompt_cache: bool = settings.ENABLE_PROMPT_CACHE,
    ):
        """Initialize the message manager with token-based memory management.

        Args:
            memory: The underlying ListStore implementation to use
            compact_threshold_tokens: Number of tokens that triggers compaction
            compact_target_ratio: Target ratio to reduce tokens (e.g., 0.5 = halve the tokens)
            enable_prompt_cache: Whether to optimize memory for prompt caching
        """
        # Create a compacting store wrapper if not already using one
        if not isinstance(memory, TokenBasedCompactingListStore):
            self.memory = TokenBasedCompactingListStore(
                backend=memory,
                compact_threshold_tokens=compact_threshold_tokens,
                compact_target_ratio=compact_target_ratio,
            )
        else:
            self.memory = memory

        self.chat_history: list[dict[str, Any]] = []
        self.enable_prompt_cache = enable_prompt_cache

    async def compact_memory(self) -> None:
        """Manually trigger memory compaction."""
        if hasattr(self.memory, "perform_compaction"):
            original_tokens, new_tokens, removed_msgs = self.memory.perform_compaction(
                "messages"
            )

            if removed_msgs > 0:
                logger.info(
                    f"Memory compacted: {original_tokens} → {new_tokens} tokens "
                    f"({(new_tokens/original_tokens):.1%}), removed {removed_msgs} messages"
                )

    async def add_user_message(
        self, text: str, attachments: Optional[list[Attachment]] = None
    ) -> None:
        """Add user message with optional attachments to both API memory and chat history."""
        attachments = attachments or []
        content = create_message_content(text, attachments)

        msg = Message(content=content, role="user")
        self.memory.rpush("messages", {"role": "user", "content": content})

        self.chat_history.append(
            {
                "role": "user",
                "content": text,
                "timestamp": msg.timestamp,
                "attachments": [
                    {
                        "url": att.url,
                        "type": att.type,
                        "filename": att.filename,
                        "mime_type": att.mime_type,
                        "size": att.size,
                    }
                    for att in attachments
                ],
            }
        )

    async def add_assistant_message(self, content: str) -> None:
        """Add assistant message to both API memory and chat history."""
        msg = Message(content=content, role="assistant")
        self.memory.rpush("messages", {"role": "assistant", "content": content})

        self.chat_history.append(
            {
                "role": "assistant",
                "content": content,
                "timestamp": msg.timestamp,
            }
        )

    async def add_memory_item(
        self, content: MessageContent, role: str = "user"
    ) -> None:
        """Add a message to API memory only (not visible in chat history)."""
        # When not caching prompts, remove existing environment details before adding new ones
        if not self.enable_prompt_cache and role == "user":
            content_str = str(content) if isinstance(content, (str, list)) else ""
            if "<environment-details>" in content_str:
                # Filter out outdated environment details from memory
                messages = self.memory.lrange("messages")
                filtered_messages = []

                for msg in messages:
                    if isinstance(msg, dict) and isinstance(msg.get("content"), list):
                        # Process messages with list-type content which may contain environment details
                        msg_content = msg.get("content", [])

                        filtered_items = []
                        for item in msg_content:
                            # Exclude items containing environment details
                            if not (
                                isinstance(item, dict)
                                and "text" in item
                                and "<environment-details>" in item["text"]
                            ):
                                filtered_items.append(item)

                        # Preserve messages that still have content after filtering
                        if filtered_items:
                            filtered_msg = msg.copy()
                            filtered_msg["content"] = filtered_items
                            filtered_messages.append(filtered_msg)
                    else:
                        # Preserve non-list content messages (which can't contain environment details)
                        filtered_messages.append(msg)

                # Clear existing messages and re-add all filtered ones in a single operation
                self.memory.delete("messages")
                if filtered_messages:
                    self.memory.rpush("messages", *filtered_messages)

        # Store the new message in memory
        self.memory.rpush("messages", {"role": role, "content": content})

    def get_messages(self) -> list[dict[str, Any]]:
        """Retrieve all stored messages."""
        return self.memory.lrange("messages")

    def get_chat_history(self) -> list[dict[str, Any]]:
        """Retrieve UI-friendly chat history."""
        return self.chat_history
