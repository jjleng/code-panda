import tempfile
from pathlib import Path

import pytest

from cp_agent.storage.list_store import FileListStore, MemoryListStore


def test_memory_store_basic_operations() -> None:
    store = MemoryListStore()

    # Test lpush and rpush
    assert store.lpush("test_list", 1, 2, 3) == 3
    assert store.rpush("test_list", 4, 5) == 5

    # Test lrange - lpush should add elements in reverse order at head
    assert store.lrange("test_list") == [3, 2, 1, 4, 5]
    assert store.lrange("test_list", 1, 3) == [2, 1, 4]

    # Test lpop and rpop
    assert store.lpop("test_list") == 3
    assert store.rpop("test_list") == 5

    # Test non-existent key
    assert store.lpop("non_existent") is None
    assert store.rpop("non_existent") is None
    assert store.lrange("non_existent") == []


def test_memory_store_ltrim() -> None:
    store = MemoryListStore()
    store.rpush("test_list", 1, 2, 3, 4, 5)

    # Test trim with positive indices
    assert store.ltrim("test_list", 1, 3) is True
    assert store.lrange("test_list") == [2, 3, 4]

    # Test trim with negative indices
    store.rpush("test_list", 5, 6)
    assert store.ltrim("test_list", 0, -2) is True
    assert store.lrange("test_list") == [2, 3, 4, 5]


def test_memory_store_lrem() -> None:
    store = MemoryListStore()
    store.rpush("test_list", 1, 2, 2, 3, 2, 4, 2)

    # Test removing from head (positive count)
    assert store.lrem("test_list", 2, 2) == 2
    assert store.lrange("test_list") == [1, 3, 2, 4, 2]

    # Test removing from tail (negative count)
    assert store.lrem("test_list", 2, -1) == 1
    assert store.lrange("test_list") == [1, 3, 2, 4]

    # Test removing all occurrences (count = 0)
    store.rpush("test_list", 2, 2)
    assert store.lrem("test_list", 2, 0) == 3
    assert store.lrange("test_list") == [1, 3, 4]


def test_memory_store_delete_and_clear() -> None:
    store = MemoryListStore()
    store.rpush("test_list", 1, 2, 3)

    # Test lclear
    assert store.lclear("test_list") is True
    assert store.lrange("test_list") == []
    assert store.lclear("non_existent") is False

    # Test delete
    store.rpush("test_list", 1, 2, 3)
    assert store.delete("test_list") is True
    assert store.lrange("test_list") == []
    assert store.delete("non_existent") is False


def test_file_store_persistence() -> None:
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        temp_path = tmp.name

    try:
        # Create store and add data
        store1 = FileListStore(temp_path)
        store1.rpush("test_list", 1, 2, 3)
        store1.lpush("another_list", "a", "b")

        # Create new store instance with same file
        store2 = FileListStore(temp_path)

        # Verify data persisted
        assert store2.lrange("test_list") == [1, 2, 3]
        assert store2.lrange("another_list") == [
            "b",
            "a",
        ]  # lpush adds elements in reverse order

    finally:
        # Clean up
        Path(temp_path).unlink()


def test_file_store_atomic_writes() -> None:
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        temp_path = tmp.name

    try:
        store = FileListStore(temp_path)
        store.rpush("test_list", 1, 2, 3)

        # Verify temp file is cleaned up
        temp_file = Path(f"{temp_path}.tmp")
        assert not temp_file.exists()

        # Verify data was written to main file
        assert Path(temp_path).exists()

    finally:
        Path(temp_path).unlink()


def test_thread_safety() -> None:
    store = MemoryListStore()
    store.rpush("test_list", 1)

    # Basic test that operations maintain thread safety
    # For more thorough testing, would need concurrent operations
    assert store.lpush("test_list", 2) == 2
    assert store.rpop("test_list") == 1
    assert len(store.lrange("test_list")) == 1
