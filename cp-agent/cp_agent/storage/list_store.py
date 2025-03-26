import pickle
import threading
import time
from abc import ABC, abstractmethod
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Protocol, Tuple

from litellm import token_counter
from loguru import logger


class ListStore(Protocol):
    """Protocol defining the interface for list storage implementations"""

    def lpush(self, key: str, *values: Any) -> int:
        """Push items to the left of the list"""
        ...

    def rpush(self, key: str, *values: Any) -> int:
        """Push items to the right of the list"""
        ...

    def lpop(self, key: str) -> Optional[Any]:
        """Remove and return the leftmost item"""
        ...

    def rpop(self, key: str) -> Optional[Any]:
        """Remove and return the rightmost item"""
        ...

    def lrange(self, key: str, start: int = 0, end: int = -1) -> list[Any]:
        """Get a range of items from the list"""
        ...

    def delete(self, key: str) -> bool:
        """Delete a key from the store"""
        ...

    def ltrim(self, key: str, start: int, end: int) -> bool:
        """Trim a list to the specified range of elements"""
        ...

    def lrem(self, key: str, value: Any, count: int = 0) -> int:
        """Remove elements equal to value.
        If count > 0: remove count elements from head to tail
        If count < 0: remove count elements from tail to head
        If count = 0: remove all elements equal to value"""
        ...

    def lclear(self, key: str) -> bool:
        """Empty a list without deleting the key"""
        ...


class BaseListStore(ABC):
    """Abstract base class with common functionality for list stores"""

    def __init__(self) -> None:
        self.data: dict[str, list] = {}
        self._lock = threading.Lock()

    @contextmanager
    def _safe_operation(self) -> Generator[Any, Any, Any]:
        """Context manager for thread-safe operations"""
        with self._lock:
            try:
                yield
            finally:
                self._persist()

    @abstractmethod
    def _persist(self) -> None:
        """Persist data if needed - override in concrete implementations"""
        pass

    def lpush(self, key: str, *values: Any) -> int:
        with self._safe_operation():
            if key not in self.data:
                self.data[key] = list(reversed(values))
            else:
                # Add elements in reverse order at the head
                for value in values:
                    self.data[key].insert(0, value)
            return len(self.data[key])

    def rpush(self, key: str, *values: Any) -> int:
        with self._safe_operation():
            if key not in self.data:
                self.data[key] = []
            self.data[key].extend(values)
            return len(self.data[key])

    def lpop(self, key: str) -> Optional[Any]:
        with self._safe_operation():
            if key not in self.data or not self.data[key]:
                return None
            return self.data[key].pop(0)

    def rpop(self, key: str) -> Optional[Any]:
        with self._safe_operation():
            if key not in self.data or not self.data[key]:
                return None
            return self.data[key].pop()

    def lrange(self, key: str, start: int = 0, end: int = -1) -> list[Any]:
        # Read operations don't need persistence but still need thread safety
        with self._lock:
            if key not in self.data:
                return []
            # Handle negative indices like Redis
            if start < 0:
                start = max(len(self.data[key]) + start, 0)
            if end < 0:
                end = len(self.data[key]) + end + 1
            else:
                end = end + 1  # Make end inclusive like Redis
            return self.data[key][start:end]

    def delete(self, key: str) -> bool:
        """Delete a key from the store"""
        with self._safe_operation():
            if key not in self.data:
                return False
            del self.data[key]
            return True

    def ltrim(self, key: str, start: int, end: int) -> bool:
        """Trim a list to the specified range of elements"""
        with self._safe_operation():
            if key not in self.data:
                return False
            try:
                # Handle negative indices like Python/Redis
                if start < 0:
                    start = max(len(self.data[key]) + start, 0)
                if end < 0:
                    end = len(self.data[key]) + end + 1
                else:
                    end = end + 1  # Make end inclusive like Redis
                self.data[key] = self.data[key][start:end]
                return True
            except IndexError:
                return False

    def lrem(self, key: str, value: Any, count: int = 0) -> int:
        """Remove elements equal to value"""
        with self._safe_operation():
            if key not in self.data:
                return 0

            if count == 0:
                # Remove all occurrences
                original_length = len(self.data[key])
                self.data[key] = [x for x in self.data[key] if x != value]
                return original_length - len(self.data[key])

            removed = 0
            if count > 0:
                # Remove from head to tail
                i = 0
                while i < len(self.data[key]) and removed < count:
                    if self.data[key][i] == value:
                        self.data[key].pop(i)
                        removed += 1
                    else:
                        i += 1
            else:
                # Remove from tail to head
                i = len(self.data[key]) - 1
                count = abs(count)
                while i >= 0 and removed < count:
                    if self.data[key][i] == value:
                        self.data[key].pop(i)
                        removed += 1
                    i -= 1

            return removed

    def lclear(self, key: str) -> bool:
        """Empty a list without deleting the key"""
        with self._safe_operation():
            if key not in self.data:
                return False
            self.data[key] = []
            return True


class MemoryListStore(BaseListStore):
    """In-memory implementation of ListStore"""

    def _persist(self) -> None:
        # No persistence needed for memory-only store
        pass


class FileListStore(BaseListStore):
    """File-based implementation of ListStore with pickle serialization"""

    def __init__(self, filename: str = "liststore.dat") -> None:
        super().__init__()
        self.filename = filename
        self._load()

    def _load(self) -> None:
        """Load data from file if exists"""
        path = Path(self.filename)
        if path.exists():
            try:
                with open(self.filename, "rb") as f:
                    self.data = pickle.load(f)
            except (pickle.PickleError, EOFError, Exception) as e:
                # Reset to empty dictionary if file is corrupted or can't be loaded
                self.data = {}

    def _persist(self) -> None:
        """Persist data to file"""
        # Ensure directory exists
        Path(self.filename).parent.mkdir(parents=True, exist_ok=True)

        # Write to temporary file first then rename for better atomicity
        temp_file = f"{self.filename}.tmp"
        try:
            with open(temp_file, "wb") as f:
                pickle.dump(self.data, f)
            Path(temp_file).replace(self.filename)
        except Exception as e:
            # Clean up temp file if something went wrong
            try:
                Path(temp_file).unlink()
            except:
                pass
            raise e


class TokenBasedCompactingListStore(BaseListStore):
    """ListStore with token-based memory compaction

    This implementation compacts memory based on token usage rather than message count,
    and removes context that can be reprimed by the context enricher when needed.
    """

    def __init__(
        self,
        backend: BaseListStore,
        compact_threshold_tokens: int = 40000,  # When to trigger compaction
        compact_target_ratio: float = 0.5,  # Target to reduce tokens by this ratio
        compaction_lock_timeout: float = 1.0,  # Timeout for compaction lock in seconds
    ) -> None:
        """Initialize with a backend store and token-based compaction settings

        Args:
            backend: The underlying storage implementation
            compact_threshold_tokens: Number of tokens that triggers compaction
            compact_target_ratio: Target ratio to reduce tokens (e.g. 0.5 = halve the tokens)
            compaction_lock_timeout: How long to wait for compaction lock (seconds)
        """
        # Skip BaseListStore initialization since we're delegating to backend
        self.backend = backend
        self.compact_threshold_tokens = compact_threshold_tokens
        self.compact_target_ratio = compact_target_ratio
        self.compaction_lock_timeout = compaction_lock_timeout
        self.last_compaction_check: Dict[str, float] = (
            {}
        )  # Track last check time per key
        self.token_counts: Dict[str, int] = {}  # Track token counts per key

        # Tags for content that can be reprimed by the context enricher
        self.primable_tags = {
            "<project-info>",
            "<supabase-report>",
            "<supabase-general-instructions>",
            "<supabase-integration-instructions>",
            "<environment-details>",
        }

        self._compaction_lock = threading.Lock()
        logger.info(
            "TokenBasedCompactingListStore initialized with threshold={}",
            compact_threshold_tokens,
        )

    def _persist(self) -> None:
        """Delegate persistence to backend"""
        self.backend._persist()

    def _extract_message_text(self, message: Any) -> str:
        """Extract all text content from a message for token counting"""
        if not isinstance(message, dict):
            return str(message)

        content = message.get("content", "")
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            # Handle multi-part content
            result = []
            for item in content:
                if isinstance(item, str):
                    result.append(item)
                elif isinstance(item, dict) and "text" in item:
                    result.append(item["text"])
            return " ".join(result)
        return str(content)

    def _count_message_tokens(self, message: Any) -> int:
        """Count tokens for a single message"""
        # Create a single-item list with the message for token counting
        message_list = (
            [message]
            if isinstance(message, dict)
            else [{"role": "user", "content": str(message)}]
        )
        return self._get_token_count(message_list)

    def _get_token_count(self, messages: List[Any]) -> int:
        """Get total token count for a list of messages"""
        # We use gpt-4o as a reference model for token counting
        return token_counter(model="gpt-4o", messages=messages)

    def _message_contains_tag(self, message: Any, tag: str) -> bool:
        """Check if a message contains a specific tag"""
        text = self._extract_message_text(message)
        return tag in text

    def _should_compact(self, key: str) -> bool:
        """Check if compaction should be performed based on token count"""
        # Add throttling to avoid checking too frequently
        current_time = time.time()
        if key in self.last_compaction_check:
            # Only check once per second per key
            if current_time - self.last_compaction_check[key] < 1.0:
                return False

        self.last_compaction_check[key] = current_time

        messages = self.backend.lrange(key)
        if not messages:
            return False
        token_count = self._get_token_count(messages)
        self.token_counts[key] = token_count  # Store the token count for logging

        logger.debug(
            "Current token count for key '{}': {}/{}",
            key,
            token_count,
            self.compact_threshold_tokens,
        )

        return token_count >= self.compact_threshold_tokens

    def _remove_primable_messages(self, messages: List[Any]) -> List[Any]:
        """Remove messages containing tags that can be reprimed by ContextEnricher"""
        return [
            msg
            for msg in messages
            if not any(
                self._message_contains_tag(msg, tag) for tag in self.primable_tags
            )
        ]

    def perform_compaction(self, key: str) -> Tuple[int, int, int]:
        """Perform compaction on messages in the specified key

        Returns:
            Tuple of (original_token_count, new_token_count, removed_messages)
        """
        if not self._compaction_lock.acquire(timeout=self.compaction_lock_timeout):
            logger.warning(
                "Could not acquire compaction lock - another compaction is running"
            )
            return (0, 0, 0)  # Another compaction is already running

        try:
            # Perform all operations within a single backend lock acquisition if possible
            logger.info("Starting compaction for key '{}'", key)
            return self._perform_standard_compaction(key)

        finally:
            self._compaction_lock.release()

    def _perform_standard_compaction(self, key: str) -> Tuple[int, int, int]:
        """Standard compaction implementation"""
        messages = self.backend.lrange(key)
        if not messages:
            logger.debug("No messages found for key '{}', skipping compaction", key)
            return (0, 0, 0)

        # Count initial tokens
        original_token_count = self._get_token_count(messages)
        if original_token_count < self.compact_threshold_tokens:
            logger.debug(
                "Token count {} is below threshold {}, skipping compaction",
                original_token_count,
                self.compact_threshold_tokens,
            )
            return (original_token_count, original_token_count, 0)

        # First remove all primable messages
        original_message_count = len(messages)
        messages = self._remove_primable_messages(messages)
        primable_removed = original_message_count - len(messages)

        if primable_removed > 0:
            logger.info(
                "Removed {} primable messages from key '{}'", primable_removed, key
            )

        # Calculate target token count
        token_count = self._get_token_count(messages)
        target_token_count = int(original_token_count * self.compact_target_ratio)

        # If removing primable content was enough, we're done
        if token_count <= target_token_count:
            logger.info(
                "Compaction completed by primable removal only: {} → {} tokens ({} messages removed)",
                original_token_count,
                token_count,
                primable_removed,
            )

            # Replace messages in storage - backend is already thread-safe
            self.backend.delete(key)
            if messages:
                self.backend.rpush(key, *messages)

            self.token_counts[key] = token_count  # Update stored count
            return (original_token_count, token_count, primable_removed)

        # Keep the first system message if it exists
        start_index = 0
        if (
            messages
            and isinstance(messages[0], dict)
            and messages[0].get("role") == "system"
        ):
            start_index = 1
            logger.debug("Preserving system message during compaction")

        # Remove oldest messages until we get under target
        i = start_index
        removed_count = primable_removed
        while i < len(messages) and token_count > target_token_count:
            msg_tokens = self._count_message_tokens(messages[i])
            messages.pop(i)  # Remove the message
            token_count -= msg_tokens
            removed_count += 1
            # i is not incremented because we're removing items and the next item shifts down

        logger.info(
            "Compaction completed: {} → {} tokens ({} total messages removed)",
            original_token_count,
            token_count,
            removed_count,
        )

        self.backend.delete(key)
        if messages:
            self.backend.rpush(key, *messages)

        self.token_counts[key] = token_count  # Update stored count
        return (original_token_count, token_count, removed_count)

    # Override only the methods that need custom behavior

    def rpush(self, key: str, *values: Any) -> int:
        result = self.backend.rpush(key, *values)

        if self._should_compact(key):
            logger.info("Compaction triggered by rpush for key '{}'", key)
            self.perform_compaction(key)

        return result

    def lpush(self, key: str, *values: Any) -> int:
        result = self.backend.lpush(key, *values)

        if self._should_compact(key):
            logger.info("Compaction triggered by lpush for key '{}'", key)
            self.perform_compaction(key)

        return result

    # Use __getattr__ to delegate all other methods to the backend
    def __getattr__(self, name: str) -> Any:
        """Delegate all other methods to the backend store"""
        backend_attr = getattr(self.backend, name)

        return backend_attr


# Example Redis implementation (stub)
"""
class RedisListStore(BaseListStore):
    def __init__(self, redis_url: str):
        super().__init__()
        self.redis = Redis.from_url(redis_url)

    def lpush(self, key: str, *values: Any) -> int:
        # Would use redis.lpush directly
        pass
"""
