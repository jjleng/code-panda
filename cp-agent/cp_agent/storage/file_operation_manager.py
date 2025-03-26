"""
FileOperationManager manages file operations in memory and coordinates turn-based actions.

This module provides a virtual layer for file operations, allowing batched processing
of file writes, renames, deletions, dependency additions and coordinated execution
of operation-triggered actions.
"""

import asyncio
import copy
import os
import shutil
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Generic, List, Optional, Set, TypeVar

from loguru import logger

from cp_agent.agents.coder.event_bus import EventBus, EventType

# Constants for protected directories/paths
PROTECTED_PATHS = {".codepanda"}


class HookStatus(Enum):
    """Status of a hook execution."""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    ABORTED = "aborted"


T = TypeVar("T")  # Type of hook result


class ChangeType(Enum):
    """Type of file change operation."""

    WRITE = "write"
    DELETE = "delete"
    RENAME = "rename"
    ADD_DEPENDENCY = "add_dependency"


@dataclass
class FileChange:
    """Represents a single file operation."""

    path: str
    change_type: ChangeType
    content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HookContext(Generic[T]):
    """Execution context for hooks."""

    hook_name: str
    status: HookStatus = HookStatus.PENDING
    result: Optional[T] = None
    error: Optional[str] = None


@dataclass
class WriteTurn:
    """Represents a group of file changes in a single turn."""

    turn_id: str
    cwd: str
    changes: List[FileChange] = field(default_factory=list)
    hook_results: Dict[str, HookContext] = field(default_factory=dict)

    def get_hook_result(self, hook_name: str) -> Optional[HookContext]:
        """Get result of a specific hook."""
        return self.hook_results.get(hook_name)

    def set_hook_result(
        self,
        hook_name: str,
        status: HookStatus,
        result: Any = None,
        error: Optional[str] = None,
    ) -> None:
        """Record result of a hook execution."""
        self.hook_results[hook_name] = HookContext(
            hook_name=hook_name, status=status, result=result, error=error
        )


@dataclass
class Hook(Generic[T]):
    """Represents a hook with its execution function and optional callback."""

    name: str
    func: Callable[[WriteTurn], Awaitable[T]]
    callback: Optional[Callable[[HookContext[T]], Awaitable[Any]]] = None
    blocking: bool = True


class FileOperationManager:
    """
    A virtual layer for managing file operations and coordinating turn-based actions.

    This manager collects file operations during each turn and provides mechanisms for committing
    changes and running associated hooks. Operations include writes, deletions, renames,
    and dependency additions.
    """

    def __init__(self, cwd: str, event_bus: Optional[EventBus] = None):
        """Initialize manager with working directory.

        Args:
            cwd: Current working directory for operations
            event_bus: Optional event bus for publishing file events
        """
        self._cwd = cwd
        self._current_turn: Optional[WriteTurn] = None
        self._write_hooks: List[Hook] = []
        self._post_commit_hooks: List[Hook] = []
        self._event_bus = event_bus

    def resolve_path(self, path: str) -> str:
        """Resolve a potentially relative path to an absolute path using the cwd.

        Args:
            path: The path to resolve

        Returns:
            Absolute path resolved against the cwd
        """
        if os.path.isabs(path):
            return path
        return os.path.normpath(os.path.join(self._cwd, path))

    def begin_turn(self, turn_id: str) -> None:
        """Start a new turn for collecting file changes."""
        if self._current_turn is not None:
            raise RuntimeError(f"Turn {self._current_turn.turn_id} is still active")
        self._current_turn = WriteTurn(turn_id=turn_id, cwd=self._cwd)

    def write_file(
        self, path: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record a file write operation for the current turn.

        Args:
            path: The file path to write to
            content: The content to write
            metadata: Optional metadata about the write operation
        """
        if self._current_turn is None:
            raise RuntimeError("No active turn")

        # Resolve path to absolute path
        abs_path = self.resolve_path(path)

        self._current_turn.changes.append(
            FileChange(
                path=abs_path,
                change_type=ChangeType.WRITE,
                content=content,
                metadata=metadata or {},
            )
        )

    def _is_protected_path(self, path: str) -> bool:
        """
        Check if a path is protected from deletion.

        Args:
            path: The absolute path to check

        Returns:
            True if the path is protected, False otherwise
        """
        # Normalize the path to handle different path formats
        norm_path = os.path.normpath(path)

        # Check if path is in any protected directory
        path_parts = norm_path.split(os.sep)

        # Look for protected paths in the path parts
        for i in range(len(path_parts)):
            if path_parts[i] in PROTECTED_PATHS:
                # This is either a protected directory or a file/dir under it
                return True

        return False

    def delete_file(self, path: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Record a file deletion operation for the current turn.

        Args:
            path: The file path to delete
            metadata: Optional metadata about the deletion operation

        Raises:
            RuntimeError: If no active turn or attempting to delete a protected file
            FileNotFoundError: If the file doesn't exist
        """
        if self._current_turn is None:
            raise RuntimeError("No active turn")

        # Resolve path to absolute path
        abs_path = self.resolve_path(path)

        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"File not found: {abs_path}")

        # Check if the file is in a protected directory
        if self._is_protected_path(abs_path):
            raise RuntimeError(f"Cannot delete protected file: {abs_path}")

        self._current_turn.changes.append(
            FileChange(
                path=abs_path,
                change_type=ChangeType.DELETE,
                metadata=metadata or {},
            )
        )

    def rename_file(
        self,
        source_path: str,
        destination_path: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Record a file rename operation for the current turn.

        Args:
            source_path: The path of the file to rename
            destination_path: The destination path for the renamed file
            metadata: Optional metadata about the rename operation
        """
        if self._current_turn is None:
            raise RuntimeError("No active turn")

        # Resolve paths to absolute paths
        abs_source_path = self.resolve_path(source_path)
        abs_destination_path = self.resolve_path(destination_path)

        if not os.path.exists(abs_source_path):
            raise FileNotFoundError(f"Source file not found: {abs_source_path}")

        if os.path.exists(abs_destination_path):
            raise FileExistsError(
                f"Destination file already exists: {abs_destination_path}"
            )

        self._current_turn.changes.append(
            FileChange(
                path=abs_source_path,
                change_type=ChangeType.RENAME,
                content=abs_destination_path,  # Store destination path in content field
                metadata=metadata or {"destination": abs_destination_path},
            )
        )

    def add_dependency(
        self, name: str, metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record a dependency addition operation for the current turn.

        Args:
            name: The name of the dependency to add
            metadata: Optional metadata about the dependency operation
        """
        if self._current_turn is None:
            raise RuntimeError("No active turn")

        self._current_turn.changes.append(
            FileChange(
                path="",  # Path is empty as this is a project-level operation
                change_type=ChangeType.ADD_DEPENDENCY,
                content=name,  # Store dependency name in content field
                metadata=metadata or {"dependency_name": name},
            )
        )

    def apply_diff(
        self, path: str, content: str, start_line: int, end_line: int
    ) -> None:
        """
        Record a diff application operation for the current turn.

        Args:
            path: The file path to apply the diff to
            content: The new content
            start_line: Starting line of the change
            end_line: Ending line of the change
        """
        metadata = {"type": "diff", "start_line": start_line, "end_line": end_line}
        self.write_file(path, content, metadata)

    def add_write_hook(
        self,
        name: str,
        hook: Callable[[WriteTurn], Awaitable[T]],
        callback: Optional[Callable[[HookContext[T]], Awaitable[Any]]] = None,
    ) -> None:
        """
        Add a hook that runs before changes are committed to disk.

        Args:
            name: Unique name for the hook
            hook: Async callback that receives the WriteTurn
            callback: Optional callback to run with hook result
        """
        self._write_hooks.append(Hook(name=name, func=hook, callback=callback))

    def add_post_commit_hook(
        self,
        name: str,
        hook: Callable[[WriteTurn], Awaitable[T]],
        callback: Optional[Callable[[HookContext[T]], Awaitable[Any]]] = None,
        blocking: bool = True,
    ) -> None:
        """
        Add a hook that runs after changes are committed to disk.

        Args:
            name: Unique name for the hook
            hook: Async callback that receives the WriteTurn
            callback: Optional callback to run with hook result
            blocking: Whether to block execution until this hook completes
        """
        self._post_commit_hooks.append(
            Hook(name=name, func=hook, callback=callback, blocking=blocking)
        )

    def _ensure_parent_dirs(self, path: str) -> None:
        """Ensure parent directories exist for a given path."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    def _write_and_flush_file(self, path: str, content: str) -> None:
        """
        Write content to file and ensure it's properly flushed to disk.

        This is important for ensuring the Vite server detects changes
        and post-commit hooks have access to the latest file content.
        """
        self._ensure_parent_dirs(path)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            # Force OS-level file flush to ensure data is written to disk
            os.fsync(f.fileno())

    async def commit_turn(self) -> None:
        """
        Commit all changes from the current turn to disk and run associated hooks.

        This:
        1. Runs pre-commit hooks
        2. Writes all files to disk
        3. Runs post-commit hooks (only if there were changes)
        4. Clears the current turn
        """
        if self._current_turn is None:
            return
        logger.info(f"Committing turn {self._current_turn.turn_id}")

        try:
            # Run pre-commit hooks
            for hook in self._write_hooks:
                try:
                    result: Any = await hook.func(self._current_turn)
                    ctx: HookContext[Any] = HookContext(
                        hook_name=hook.name, status=HookStatus.SUCCESS, result=result
                    )
                    self._current_turn.set_hook_result(
                        hook.name, HookStatus.SUCCESS, result
                    )
                    if hook.callback:
                        await hook.callback(ctx)
                except Exception as e:
                    logger.error(f"Write hook {hook.name} failed: {e}")
                    ctx = HookContext(
                        hook_name=hook.name, status=HookStatus.FAILED, error=str(e)
                    )
                    self._current_turn.set_hook_result(
                        hook.name, HookStatus.FAILED, error=str(e)
                    )
                    if hook.callback:
                        await hook.callback(ctx)

            # Check if there are any changes to commit
            has_changes = len(self._current_turn.changes) > 0

            # Apply changes to disk (only if there are changes)
            if has_changes:
                for change in self._current_turn.changes:
                    if change.change_type == ChangeType.WRITE:
                        if (
                            change.content is not None
                        ):  # Write operations must have content
                            self._write_and_flush_file(change.path, change.content)
                            # Publish file written event
                            if self._event_bus:
                                self._event_bus.publish(
                                    EventType.FILE_WRITTEN,
                                    {
                                        "path": change.path,
                                        "metadata": change.metadata,
                                    },
                                )
                        else:
                            logger.error(
                                f"Write operation missing content for {change.path}"
                            )
                    elif change.change_type == ChangeType.DELETE:
                        try:
                            if os.path.exists(change.path):
                                os.remove(change.path)
                                # Publish file deleted event
                                if self._event_bus:
                                    self._event_bus.publish(
                                        EventType.FILE_DELETED,
                                        {
                                            "path": change.path,
                                            "metadata": change.metadata,
                                        },
                                    )
                            else:
                                logger.warning(
                                    f"File to delete not found: {change.path}"
                                )
                        except Exception as e:
                            logger.error(f"Failed to delete file {change.path}: {e}")
                            raise
                    elif change.change_type == ChangeType.RENAME:
                        try:
                            source_path = change.path
                            destination_path = change.content
                            if not destination_path:
                                raise ValueError(
                                    "Destination path is required for rename"
                                )
                            if os.path.exists(source_path):
                                self._ensure_parent_dirs(destination_path)
                                shutil.move(source_path, destination_path)
                                # Publish file renamed event
                                if self._event_bus:
                                    self._event_bus.publish(
                                        EventType.FILE_RENAMED,
                                        {
                                            "source_path": source_path,
                                            "destination_path": destination_path,
                                            "metadata": change.metadata,
                                        },
                                    )
                            else:
                                logger.warning(
                                    f"File to rename not found: {source_path}"
                                )
                        except Exception as e:
                            logger.error(f"Failed to rename file {change.path}: {e}")
                            raise
                    elif change.change_type == ChangeType.ADD_DEPENDENCY:
                        # For add_dependency, we don't actually perform the action here
                        # This is just for tracking the change in the turn
                        logger.info(f"Recorded dependency addition: {change.content}")
                        # Publish dependency added event
                        if self._event_bus:
                            self._event_bus.publish(
                                EventType.DEPENDENCY_ADDED,
                                {
                                    "dependency": change.content,
                                    "metadata": change.metadata,
                                },
                            )

            # Run post-commit hooks only if there were changes
            if has_changes:
                # First process blocking hooks
                for hook in self._post_commit_hooks:
                    if hook.blocking:  # Only execute blocking hooks in the main flow
                        try:
                            result = await hook.func(self._current_turn)
                            ctx = HookContext(
                                hook_name=hook.name,
                                status=HookStatus.SUCCESS,
                                result=result,
                            )
                            self._current_turn.set_hook_result(
                                hook.name, HookStatus.SUCCESS, result
                            )
                            if hook.callback:
                                await hook.callback(ctx)
                        except Exception as e:
                            logger.error(f"Post-commit hook {hook.name} failed: {e}")
                            ctx = HookContext(
                                hook_name=hook.name,
                                status=HookStatus.FAILED,
                                error=str(e),
                            )
                            self._current_turn.set_hook_result(
                                hook.name, HookStatus.FAILED, error=str(e)
                            )
                            if hook.callback:
                                await hook.callback(ctx)

                non_blocking_hooks = [
                    hook for hook in self._post_commit_hooks if not hook.blocking
                ]
                if non_blocking_hooks:
                    # Create copies of the turn for each non-blocking hook
                    turn_copies = {
                        hook.name: copy.deepcopy(self._current_turn)
                        for hook in non_blocking_hooks
                    }

                    async def run_hook(hook_obj: Hook) -> None:
                        hook_name = hook_obj.name
                        turn_copy = turn_copies[hook_name]
                        logger.info(
                            f"Running non-blocking hook {hook_name} concurrently"
                        )
                        try:
                            result = await hook_obj.func(turn_copy)
                            ctx: HookContext[Any] = HookContext(
                                hook_name=hook_name,
                                status=HookStatus.SUCCESS,
                                result=result,
                            )
                            # Don't update the original turn as it might be gone by the time this completes
                            if hook_obj.callback:
                                await hook_obj.callback(ctx)
                            logger.info(
                                f"Successfully completed concurrent hook {hook_name}"
                            )
                        except Exception as e:
                            logger.error(f"Concurrent hook {hook_name} failed: {e}")
                            ctx = HookContext(
                                hook_name=hook_name,
                                status=HookStatus.FAILED,
                                error=str(e),
                            )
                            if hook_obj.callback:
                                try:
                                    await hook_obj.callback(ctx)
                                except Exception as callback_err:
                                    logger.error(
                                        f"Error in callback for hook {hook_name}: {callback_err}"
                                    )

                    # Run all non-blocking hooks concurrently and wait for all to complete
                    logger.info(
                        f"Running {len(non_blocking_hooks)} non-blocking hooks concurrently"
                    )
                    await asyncio.gather(
                        *(run_hook(hook) for hook in non_blocking_hooks)
                    )
                    logger.info("All concurrent hooks completed")
            else:
                logger.info("No changes to commit, skipping post-commit hooks")

        finally:
            # Always clear the current turn
            self._current_turn = None

    def discard_turn(self) -> None:
        """Discard all changes in the current turn without committing them."""
        self._current_turn = None

    def get_pending_changes(self) -> List[FileChange]:
        """Get all pending changes in the current turn."""
        if self._current_turn is None:
            return []
        return self._current_turn.changes.copy()

    def get_pending_file_change(self, path: str) -> Optional[FileChange]:
        """Get a specific pending file change by path.

        Args:
            path: The file path to look for

        Returns:
            The FileChange object if found, None otherwise
        """
        if self._current_turn is None:
            return None

        for change in self._current_turn.changes:
            if change.path == path:
                return change

        return None
