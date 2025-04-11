"""Tests for the ContextEnricher class."""

import pytest

from cp_agent.context import ContextEnricher
from cp_agent.storage.list_store import ListStore, MemoryListStore
from cp_agent.utils.message_formats import Message, create_text_block


@pytest.fixture
def list_store() -> ListStore:
    """Create a test list store."""
    return MemoryListStore()


@pytest.fixture
def context_enricher(list_store: ListStore) -> ContextEnricher:
    """Create a test context enricher."""
    return ContextEnricher(list_store, "/test/path")


def test_scan_messages_for_tag_string_content(
    context_enricher: ContextEnricher,
) -> None:
    """Test scanning messages with string content."""
    msg: Message = {"content": "<tag>Some content", "role": "user"}
    context_enricher.memory.rpush("messages", msg)

    assert context_enricher.scan_messages_for_tag("<tag>") is True
    assert context_enricher.scan_messages_for_tag("<other>") is False


def test_scan_messages_for_tag_list_content(context_enricher: ContextEnricher) -> None:
    """Test scanning messages with list content."""
    msg: Message = {
        "content": [
            create_text_block("<tag>First block"),
            create_text_block("Second block"),
        ],
        "role": "user",
    }
    context_enricher.memory.rpush("messages", msg)

    assert context_enricher.scan_messages_for_tag("<tag>") is True
    assert context_enricher.scan_messages_for_tag("<other>") is False


def test_scan_messages_for_tag_with_whitespace(
    context_enricher: ContextEnricher,
) -> None:
    """Test scanning messages with whitespace before tag."""
    msg: Message = {"content": "  <tag>Some content", "role": "user"}
    context_enricher.memory.rpush("messages", msg)

    assert context_enricher.scan_messages_for_tag("<tag>") is True


def test_scan_messages_for_tag_mixed_content(context_enricher: ContextEnricher) -> None:
    """Test scanning messages with mixed content types."""
    messages = [
        {"content": "Regular message", "role": "user"},
        {
            "content": [
                create_text_block("<tag>Block 1"),
                create_text_block("Block 2"),
            ],
            "role": "user",
        },
        {"content": "<other>Different tag", "role": "user"},
    ]

    for msg in messages:
        context_enricher.memory.rpush("messages", msg)

    assert context_enricher.scan_messages_for_tag("<tag>") is True
    assert context_enricher.scan_messages_for_tag("<missing>") is False


def test_delete_memory_by_tag_string_content(context_enricher: ContextEnricher) -> None:
    """Test deleting messages with string content."""
    msg1: Message = {"content": "<tag>Delete this", "role": "user"}
    msg2: Message = {"content": "Keep this", "role": "user"}

    for msg in [msg1, msg2]:
        context_enricher.memory.rpush("messages", msg)

    assert context_enricher.delete_memory_by_tag("<tag>") is True
    messages = context_enricher.memory.lrange("messages")
    assert len(messages) == 1
    assert messages[0]["content"] == "Keep this"


def test_delete_memory_by_tag_list_content(context_enricher: ContextEnricher) -> None:
    """Test deleting messages with list content."""
    msg1: Message = {
        "content": [
            create_text_block("<tag>Delete block"),
            create_text_block("Other block"),
        ],
        "role": "user",
    }
    msg2: Message = {
        "content": [
            create_text_block("Keep block 1"),
            create_text_block("Keep block 2"),
        ],
        "role": "user",
    }

    for msg in [msg1, msg2]:
        context_enricher.memory.rpush("messages", msg)

    assert context_enricher.delete_memory_by_tag("<tag>") is True
    messages = context_enricher.memory.lrange("messages")
    assert len(messages) == 1
    assert messages[0]["content"] == [
        {"type": "text", "text": "Keep block 1"},
        {"type": "text", "text": "Keep block 2"},
    ]


def test_delete_memory_by_tag_no_matches(context_enricher: ContextEnricher) -> None:
    """Test deleting messages when no matches exist."""
    msg: Message = {"content": "No tags here", "role": "user"}
    context_enricher.memory.rpush("messages", msg)

    assert context_enricher.delete_memory_by_tag("<tag>") is False
    messages = context_enricher.memory.lrange("messages")
    assert len(messages) == 1


def test_delete_memory_by_tag_multiple_matches(
    context_enricher: ContextEnricher,
) -> None:
    """Test deleting multiple messages with the same tag."""
    messages = [
        {"content": "<tag>First tagged", "role": "user"},
        {
            "content": [
                create_text_block("<tag>Second tagged"),
                create_text_block("extra"),
            ],
            "role": "user",
        },
        {"content": "Keep this", "role": "user"},
        {"content": [create_text_block("<tag>Third tagged")], "role": "user"},
    ]

    for msg in messages:
        context_enricher.memory.rpush("messages", msg)

    assert context_enricher.delete_memory_by_tag("<tag>") is True
    remaining_messages = context_enricher.memory.lrange("messages")
    assert len(remaining_messages) == 1
    assert remaining_messages[0]["content"] == "Keep this"


def test_delete_memory_by_tag_with_whitespace(
    context_enricher: ContextEnricher,
) -> None:
    """Test deleting messages with whitespace before tag."""
    msg: Message = {"content": "    <tag>Indented content", "role": "user"}
    context_enricher.memory.rpush("messages", msg)

    assert context_enricher.delete_memory_by_tag("<tag>") is True
    assert len(context_enricher.memory.lrange("messages")) == 0
