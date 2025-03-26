"""Tests for the FileOperationManager module."""

import os
from typing import List, Optional
from unittest.mock import AsyncMock, patch

import pytest

from cp_agent.storage.file_operation_manager import (
    FileOperationManager,
    HookContext,
    HookStatus,
    WriteTurn,
)


@pytest.fixture
def store(tmp_path: str) -> FileOperationManager:
    """Create a FileOperationManager instance for testing."""
    return FileOperationManager(str(tmp_path))


@pytest.mark.asyncio
async def test_basic_write_operations(tmp_path: str) -> None:
    """Test basic write operations in the store."""
    store = FileOperationManager(str(tmp_path))

    # Start a turn
    store.begin_turn("turn-1")

    # Record some writes
    test_content = "hello world"
    test_file = os.path.join(tmp_path, "test.txt")
    store.write_file(test_file, test_content)

    # Verify pending changes
    changes = store.get_pending_changes()
    assert len(changes) == 1
    assert changes[0].path == test_file
    assert changes[0].content == test_content

    # Commit and verify file was written
    await store.commit_turn()
    assert os.path.exists(test_file)
    with open(test_file) as f:
        assert f.read() == test_content


def test_turn_management() -> None:
    """Test turn management logic."""
    store = FileOperationManager("/tmp")

    # Cannot write without active turn
    with pytest.raises(RuntimeError):
        store.write_file("test.txt", "content")

    # Cannot start turn while one is active
    store.begin_turn("turn-1")
    with pytest.raises(RuntimeError):
        store.begin_turn("turn-2")

    # Can discard turn
    store.discard_turn()
    assert store.get_pending_changes() == []

    # Can start new turn after discarding
    store.begin_turn("turn-2")
    assert True  # No exception raised


@pytest.mark.asyncio
async def test_hooks(tmp_path: str) -> None:
    """Test that hooks are called appropriately."""
    store = FileOperationManager(str(tmp_path))

    write_hooks_called: List[str] = []
    post_commit_hooks_called: List[str] = []

    async def write_hook(turn: WriteTurn) -> None:
        write_hooks_called.append(turn.turn_id)

    async def post_commit_hook(turn: WriteTurn) -> None:
        post_commit_hooks_called.append(turn.turn_id)

    store.add_write_hook("write_hook", write_hook)
    store.add_post_commit_hook("post_commit_hook", post_commit_hook)

    # Start turn and make changes
    store.begin_turn("turn-1")
    test_file = os.path.join(tmp_path, "test.txt")
    store.write_file(test_file, "content")

    # Commit and verify hooks were called
    await store.commit_turn()
    assert write_hooks_called == ["turn-1"]
    assert post_commit_hooks_called == ["turn-1"]


@pytest.mark.asyncio
async def test_git_snapshot_hook(tmp_path: str) -> None:
    """Test git snapshot hook functionality."""
    store = FileOperationManager(str(tmp_path))
    test_file = os.path.join(tmp_path, "test.txt")

    with patch(
        "cp_agent.utils.snapshot.create_snapshot", new_callable=AsyncMock
    ) as mock_create_snapshot:
        # Add snapshot hook
        async def create_snapshot_hook(turn: WriteTurn) -> Optional[str]:
            # Mock implementation of the snapshot hook
            if not turn.changes:
                return None

            # Build message from changes
            messages = []
            for change in turn.changes:
                if change.metadata.get("type") == "diff":
                    messages.append(
                        f"Modified {change.path} "
                        f"(lines {change.metadata['start_line']}-{change.metadata['end_line']})"
                    )
                else:
                    messages.append(f"Updated {change.path}")

            commit_message = "\n".join(messages)
            # Call the mocked function instead of real implementation
            await mock_create_snapshot(turn.cwd, commit_message=commit_message)
            return commit_message

        store.add_post_commit_hook("git_snapshot", create_snapshot_hook)

        # Make some changes
        store.begin_turn("turn-1")
        store.write_file(test_file, "content")
        await store.commit_turn()

        # Verify snapshot was created with correct message
        mock_create_snapshot.assert_called_once()
        commit_message = mock_create_snapshot.call_args[1]["commit_message"]
        assert "Updated" in commit_message
        assert test_file in commit_message


@pytest.mark.asyncio
async def test_hook_error_handling(tmp_path: str) -> None:
    """Test error handling during hook execution."""
    store = FileOperationManager(str(tmp_path))
    test_file = os.path.join(tmp_path, "test.txt")

    async def failing_hook(turn: WriteTurn) -> None:
        raise Exception("Hook error")

    store.add_post_commit_hook("failing_hook", failing_hook)

    # File writes should succeed even if hook fails
    store.begin_turn("turn-1")
    store.write_file(test_file, "content")
    await store.commit_turn()

    # Verify file was written despite hook error
    assert os.path.exists(test_file)
    with open(test_file) as f:
        assert f.read() == "content"


@pytest.mark.asyncio
async def test_diff_metadata_in_snapshot(tmp_path: str) -> None:
    """Test that diff metadata appears correctly in git snapshot messages."""
    store = FileOperationManager(str(tmp_path))
    test_file = os.path.join(tmp_path, "test.txt")

    with patch(
        "cp_agent.utils.snapshot.create_snapshot", new_callable=AsyncMock
    ) as mock_create_snapshot:

        async def create_snapshot_hook(turn: WriteTurn) -> Optional[str]:
            # Mock implementation of the snapshot hook
            if not turn.changes:
                return None

            # Build message from changes
            messages = []
            for change in turn.changes:
                if change.metadata.get("type") == "diff":
                    messages.append(
                        f"Modified {change.path} "
                        f"(lines {change.metadata['start_line']}-{change.metadata['end_line']})"
                    )
                else:
                    messages.append(f"Updated {change.path}")

            commit_message = "\n".join(messages)
            # Call the mocked function instead of real implementation
            await mock_create_snapshot(turn.cwd, commit_message=commit_message)
            return commit_message

        store.add_post_commit_hook("git_snapshot", create_snapshot_hook)

        # Apply a diff change
        store.begin_turn("turn-1")
        store.apply_diff(test_file, "new content", 1, 5)
        await store.commit_turn()

        # Verify commit message includes diff information
        mock_create_snapshot.assert_called_once()
        commit_message = mock_create_snapshot.call_args[1]["commit_message"]
        assert "Modified" in commit_message
        assert "lines 1-5" in commit_message


@pytest.mark.asyncio
async def test_multiple_changes_in_turn(tmp_path: str) -> None:
    """Test handling multiple file changes in a single turn."""
    store = FileOperationManager(str(tmp_path))
    file1 = os.path.join(tmp_path, "file1.txt")
    file2 = os.path.join(tmp_path, "file2.txt")

    store.begin_turn("turn-1")
    store.write_file(file1, "content 1")
    store.write_file(file2, "content 2")
    await store.commit_turn()

    # Verify both files were written
    assert os.path.exists(file1)
    assert os.path.exists(file2)
    with open(file1) as f:
        assert f.read() == "content 1"
    with open(file2) as f:
        assert f.read() == "content 2"


@pytest.mark.asyncio
async def test_turn_state_after_abort(tmp_path: str) -> None:
    """Test that turn state is properly reset after discard/abort."""
    store = FileOperationManager(str(tmp_path))
    file_path = os.path.join(tmp_path, "test.txt")

    # Begin turn and add some changes
    store.begin_turn("turn-1")
    store.write_file(file_path, "test content")

    # Get pending changes
    changes = store.get_pending_changes()
    assert len(changes) == 1

    # Abort/discard the turn
    store.discard_turn()

    # Verify pending changes are cleared
    assert store.get_pending_changes() == []

    # Verify file was not written
    assert not os.path.exists(file_path)

    # Verify we can start a new turn
    store.begin_turn("turn-2")
    assert True


@pytest.mark.asyncio
async def test_hook_execution_order(tmp_path: str) -> None:
    """Test that hooks execute in the correct order."""
    store = FileOperationManager(str(tmp_path))
    execution_order = []

    async def write_hook1(turn: WriteTurn) -> str:
        execution_order.append("write_hook1")
        return "write_hook1 result"

    async def write_hook2(turn: WriteTurn) -> str:
        execution_order.append("write_hook2")
        return "write_hook2 result"

    async def post_hook1(turn: WriteTurn) -> str:
        execution_order.append("post_hook1")
        return "post_hook1 result"

    async def post_hook2(turn: WriteTurn) -> str:
        execution_order.append("post_hook2")
        return "post_hook2 result"

    # Add hooks in specific order
    store.add_write_hook("write_hook1", write_hook1)
    store.add_write_hook("write_hook2", write_hook2)
    store.add_post_commit_hook("post_hook1", post_hook1)
    store.add_post_commit_hook("post_hook2", post_hook2)

    # Execute turn
    store.begin_turn("turn-1")
    store.write_file(os.path.join(tmp_path, "test.txt"), "content")
    await store.commit_turn()

    # Verify hooks executed in correct order
    assert execution_order == ["write_hook1", "write_hook2", "post_hook1", "post_hook2"]


@pytest.mark.asyncio
async def test_hook_context_passing(tmp_path: str) -> None:
    """Test that hook context is correctly passed between hooks."""
    store = FileOperationManager(str(tmp_path))

    code_check_called = False
    git_snapshot_called = False

    async def code_check_hook(turn: WriteTurn) -> tuple[bool, list[str]]:
        nonlocal code_check_called
        code_check_called = True
        return True, ["No issues found"]

    async def git_snapshot_hook(turn: WriteTurn) -> Optional[str]:
        nonlocal git_snapshot_called
        git_snapshot_called = True

        # Check if code_check hook ran and was successful
        code_check_ctx = turn.get_hook_result("code_check")
        assert code_check_ctx is not None
        assert code_check_ctx.status == HookStatus.SUCCESS
        assert code_check_ctx.result is not None
        assert code_check_ctx.result[0] is True  # Passed

        # Return a commit message
        return "Snapshot created"

    async def on_code_check_complete(ctx: HookContext[tuple[bool, list[str]]]) -> None:
        assert ctx.hook_name == "code_check"
        assert ctx.status == HookStatus.SUCCESS
        assert ctx.result is not None and ctx.result[0] is True

    # Add hooks with explicit type parameters
    store.add_post_commit_hook("code_check", code_check_hook, on_code_check_complete)
    store.add_post_commit_hook("git_snapshot", git_snapshot_hook)

    # Execute turn
    store.begin_turn("turn-1")
    store.write_file(os.path.join(tmp_path, "test.txt"), "content")
    await store.commit_turn()

    # Verify hooks were called
    assert code_check_called
    assert git_snapshot_called


@pytest.mark.asyncio
async def test_file_write_failure(tmp_path: str) -> None:
    """Test handling of file write failures."""
    store = FileOperationManager(str(tmp_path))
    test_file = os.path.join(tmp_path, "test.txt")

    # Create a directory with the same name to cause write failure
    os.mkdir(test_file)

    # Start turn and attempt write
    store.begin_turn("turn-1")
    store.write_file(test_file, "content")

    # Verify write failure is handled correctly
    with pytest.raises(Exception):
        await store.commit_turn()

    # No writes should have succeeded since the first one failed
    assert not os.path.isfile(os.path.join(tmp_path, "other.txt"))


@pytest.mark.asyncio
async def test_partial_success_scenario(tmp_path: str) -> None:
    """Test scenario where some hooks succeed and others fail."""
    store = FileOperationManager(str(tmp_path))
    hooks_called = []

    async def successful_hook(turn: WriteTurn) -> str:
        hooks_called.append("successful_hook")
        return "Success"

    async def failing_hook(turn: WriteTurn) -> None:
        hooks_called.append("failing_hook")
        raise Exception("Hook failure")

    async def depends_on_previous(turn: WriteTurn) -> str:
        hooks_called.append("depends_on_previous")
        # This hook should still run even if previous hook failed
        return "Still ran"

    store.add_post_commit_hook("successful_hook", successful_hook)
    store.add_post_commit_hook("failing_hook", failing_hook)
    store.add_post_commit_hook("depends_on_previous", depends_on_previous)

    # Execute turn
    store.begin_turn("turn-1")
    test_file = os.path.join(tmp_path, "test.txt")
    store.write_file(test_file, "content")
    await store.commit_turn()

    # All hooks should have been attempted
    assert hooks_called == ["successful_hook", "failing_hook", "depends_on_previous"]

    # The file write should have completed despite hook failures
    assert os.path.exists(test_file)
    with open(test_file) as f:
        assert f.read() == "content"


@pytest.mark.asyncio
async def test_skip_post_commit_hooks_when_no_changes(tmp_path: str) -> None:
    """Test that post-commit hooks are skipped when no changes were made."""
    store = FileOperationManager(str(tmp_path))
    post_commit_hooks_called = []

    async def post_commit_hook(turn: WriteTurn) -> str:
        post_commit_hooks_called.append(turn.turn_id)
        return "This should not be called when no changes"

    store.add_post_commit_hook("post_commit_hook", post_commit_hook)

    # Start turn but don't make any changes
    store.begin_turn("turn-with-no-changes")

    # Commit with no changes
    await store.commit_turn()

    # Verify post-commit hooks were not called
    assert len(post_commit_hooks_called) == 0

    # Now make a turn with changes to verify hooks work normally
    store.begin_turn("turn-with-changes")
    test_file = os.path.join(tmp_path, "test.txt")
    store.write_file(test_file, "content")
    await store.commit_turn()

    # Verify hook was called this time
    assert post_commit_hooks_called == ["turn-with-changes"]


@pytest.mark.asyncio
async def test_file_deletion_operations(tmp_path: str) -> None:
    """Test file deletion operations in the store."""
    store = FileOperationManager(str(tmp_path))

    # Create a test file first
    test_file = os.path.join(tmp_path, "test.txt")
    with open(test_file, "w") as f:
        f.write("test content")

    # Start a turn
    store.begin_turn("turn-1")

    # Record deletion
    store.delete_file(test_file)

    # Verify pending changes
    changes = store.get_pending_changes()
    assert len(changes) == 1
    assert changes[0].path == test_file
    assert changes[0].change_type.value == "delete"
    assert changes[0].content is None

    # Commit and verify file was deleted
    await store.commit_turn()
    assert not os.path.exists(test_file)


@pytest.mark.asyncio
async def test_file_deletion_hooks(tmp_path: str) -> None:
    """Test that hooks are called for deletion operations."""
    store = FileOperationManager(str(tmp_path))
    test_file = os.path.join(tmp_path, "test.txt")

    # Create test file
    with open(test_file, "w") as f:
        f.write("test content")

    write_hooks_called: List[str] = []
    post_commit_hooks_called: List[str] = []
    deletion_metadata: List[dict] = []

    async def write_hook(turn: WriteTurn) -> None:
        write_hooks_called.append(turn.turn_id)
        # Record any deletion operations
        for change in turn.changes:
            if change.change_type.value == "delete":
                deletion_metadata.append({"path": change.path})

    async def post_commit_hook(turn: WriteTurn) -> None:
        post_commit_hooks_called.append(turn.turn_id)

    store.add_write_hook("write_hook", write_hook)
    store.add_post_commit_hook("post_commit_hook", post_commit_hook)

    # Start turn and delete file
    store.begin_turn("turn-1")
    store.delete_file(test_file)

    # Commit and verify hooks were called
    await store.commit_turn()
    assert write_hooks_called == ["turn-1"]
    assert post_commit_hooks_called == ["turn-1"]
    assert len(deletion_metadata) == 1
    assert deletion_metadata[0]["path"] == test_file


@pytest.mark.asyncio
async def test_file_deletion_error_handling(tmp_path: str) -> None:
    """Test error handling for file deletion operations."""
    store = FileOperationManager(str(tmp_path))
    test_file = os.path.join(tmp_path, "nonexistent.txt")

    # Attempt to delete non-existent file
    store.begin_turn("turn-1")
    with pytest.raises(FileNotFoundError):
        store.delete_file(test_file)

    # Verify no pending changes
    changes = store.get_pending_changes()
    assert len(changes) == 0


@pytest.mark.asyncio
async def test_mixed_operations_in_turn(tmp_path: str) -> None:
    """Test handling mixed write and delete operations in a single turn."""
    store = FileOperationManager(str(tmp_path))
    file1 = os.path.join(tmp_path, "file1.txt")
    file2 = os.path.join(tmp_path, "file2.txt")

    # Create initial files
    with open(file1, "w") as f:
        f.write("file 1 content")
    with open(file2, "w") as f:
        f.write("file 2 content")

    # Start turn with mixed operations
    store.begin_turn("turn-1")
    store.delete_file(file1)  # Delete first file
    store.write_file(file2, "updated content")  # Update second file
    store.write_file(
        os.path.join(tmp_path, "file3.txt"), "new content"
    )  # Create new file

    # Verify pending changes
    changes = store.get_pending_changes()
    assert len(changes) == 3

    # Commit and verify results
    await store.commit_turn()

    # First file should be deleted
    assert not os.path.exists(file1)

    # Second file should be updated
    assert os.path.exists(file2)
    with open(file2) as f:
        assert f.read() == "updated content"

    # Third file should be created
    file3 = os.path.join(tmp_path, "file3.txt")
    assert os.path.exists(file3)
    with open(file3) as f:
        assert f.read() == "new content"
