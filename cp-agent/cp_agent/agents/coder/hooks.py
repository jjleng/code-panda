"""Hook management for the AI coding agent."""

import asyncio
import copy
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Optional, TypeVar

from loguru import logger

from cp_agent.agents.coder.event_bus import EventBus, EventType
from cp_agent.projects.manager import get_project_manager
from cp_agent.storage.file_operation_manager import (
    ChangeType,
    FileOperationManager,
    HookContext,
    HookStatus,
    WriteTurn,
)
from cp_agent.utils.code_checks import perform_code_checks
from cp_agent.utils.runner_client import RunnerClient
from cp_agent.utils.snapshot import create_snapshot
from cp_agent.utils.supabase_utils import SupabaseUtil

T = TypeVar("T")
HookFunc = Callable[[WriteTurn], Any]
CompletionFunc = Callable[[HookContext[Any]], Awaitable[Any]]


class HookManager:
    """Manages hooks for file operations in the coding agent."""

    def __init__(
        self,
        cwd: str,
        file_store: FileOperationManager,
        runner: RunnerClient,
        event_bus: EventBus,
    ):
        """Initialize the HookManager.

        Args:
            cwd: The current working directory
            file_store: The FileOperationManager to register hooks with
            runner: The RunnerClient for running code checks
            event_bus: Event bus for publishing events
        """
        self.cwd = cwd
        self.file_store = file_store
        self.runner = runner
        self.event_bus = event_bus

    def register_all_hooks(
        self,
        callbacks: Optional[Dict[str, CompletionFunc]] = None,
    ) -> None:
        """Register all hooks with the file store in the correct order.

        Args:
            callbacks: Dictionary mapping hook names to their completion callbacks
        """
        callbacks = callbacks or {}

        # IMPORTANT: Register code_check hook FIRST to ensure it runs before other post-commit hooks
        self.file_store.add_post_commit_hook(
            "code_check", self._code_check_hook, callbacks.get("code_check")
        )

        # Then register other post-commit hooks that depend on code check results
        self.file_store.add_post_commit_hook(
            "git_snapshot",
            self._git_snapshot_hook,
            callbacks.get("git_snapshot") or self._on_git_snapshot_complete,
            blocking=False,
        )

        self.file_store.add_post_commit_hook(
            "project_backup",
            self._project_backup_hook,
            callbacks.get("project_backup")
            or self._on_project_backup_complete,  # Add default callback
            blocking=False,
        )

        # Register write hooks - these run before commit
        self.file_store.add_write_hook(
            "deploy_edge_function",
            self._deploy_edge_function_hook,
            callbacks.get("deploy_edge_function")
            or self._on_deploy_edge_function_complete,
        )

        # Register the new migration deployment hook
        self.file_store.add_write_hook(
            "deploy_migrations",
            self._deploy_migrations_hook,
            callbacks.get("deploy_migrations") or self._on_deploy_migrations_complete,
        )

    async def _code_check_hook(self, turn: WriteTurn) -> tuple[bool, list[str]]:
        """
        Post-commit hook that runs code quality checks.

        Args:
            turn: The current write turn with changes

        Returns:
            Tuple of (passed: bool, check_results: list[str])
            passed is True if no errors were found
            check_results contains any linting or error messages
        """
        logger.info("Running code quality checks")
        project_id = Path(turn.cwd).name
        has_errors, check_results = await perform_code_checks(project_id, self.runner)
        return not has_errors, check_results

    async def _git_snapshot_hook(self, turn: WriteTurn) -> Optional[str]:
        """
        Post-commit hook that creates a git snapshot.
        Only runs if code checks passed and changes were made.

        This hook is designed to run asynchronously, so it makes a copy
        of any hook results it depends on to prevent race conditions.

        Args:
            turn: The current write turn with changes

        Returns:
            The commit message if snapshot was created, None if skipped
        """
        logger.info("Creating git snapshot")
        if not turn.changes:
            logger.info("No changes to commit")
            return None

        # Get a copy of the code_check results to prevent race conditions
        code_check_ctx = copy.deepcopy(turn.get_hook_result("code_check"))

        if not code_check_ctx or code_check_ctx.status != HookStatus.SUCCESS:
            logger.info(
                "Skipping git snapshot - code checks did not complete successfully"
            )
            return None

        if not code_check_ctx.result:
            logger.info("Skipping git snapshot - code checks did not return a result")
            return None

        passed, _ = code_check_ctx.result
        if not passed:
            logger.info("Skipping git snapshot - code checks found errors")
            return None

        # Let create_snapshot generate an appropriate commit message
        commit_message = await create_snapshot(turn.cwd)
        return commit_message

    async def _on_git_snapshot_complete(self, ctx: HookContext[Optional[str]]) -> None:
        """
        Handle completion of git snapshot creation.
        """
        if ctx.status != HookStatus.SUCCESS:
            logger.error(f"Git snapshot failed to execute: {ctx.error}")
            # Publish event about git snapshot failure
            try:
                await self.event_bus.publish_async(
                    EventType.HOOK_FAILED,
                    {
                        "hook_name": "git_snapshot",
                        "error": str(ctx.error),
                    },
                )
            except Exception as e:
                logger.error(f"Failed to publish git snapshot failure event: {e}")
            return

        if ctx.result:
            # Snapshot was created successfully
            logger.info(f"Created git snapshot: {ctx.result}")
        else:
            # Snapshot was skipped (no changes or failed checks)
            logger.info("Git snapshot was skipped")

    async def _project_backup_hook(self, turn: WriteTurn) -> None:
        """
        Post-commit hook that performs project backup.
        Only runs if code checks passed.

        This hook is designed to run asynchronously, so it makes a copy
        of any hook results it depends on to prevent race conditions.
        """
        logger.info("Running project backup")

        # Get a copy of the code_check results to prevent race conditions
        code_check_ctx = copy.deepcopy(turn.get_hook_result("code_check"))

        if not code_check_ctx or code_check_ctx.status != HookStatus.SUCCESS:
            logger.info(
                "Skipping project backup - code checks did not complete successfully"
            )
            return

        if not code_check_ctx.result:
            logger.info("Skipping project backup - code checks did not return a result")
            return

        passed, _ = code_check_ctx.result
        if not passed:
            logger.info("Skipping project backup - code checks found errors")
            return

        # Proceed with backup
        project_id = Path(turn.cwd).name
        project_manager = get_project_manager()
        await project_manager.backup_project(project_id)
        logger.info("Project backup completed successfully")

    async def _on_project_backup_complete(self, ctx: HookContext[None]) -> None:
        """
        Handle completion of project backup.
        """
        if ctx.status != HookStatus.SUCCESS:
            logger.error(f"Project backup failed to execute: {ctx.error}")
            # Publish event about project backup failure
            try:
                await self.event_bus.publish_async(
                    EventType.HOOK_FAILED,
                    {
                        "hook_name": "project_backup",
                        "error": str(ctx.error),
                    },
                )
            except Exception as e:
                logger.error(f"Failed to publish project backup failure event: {e}")
            return

        logger.info("Project backup completed successfully")

    async def _deploy_edge_function_hook(self, turn: WriteTurn) -> list[dict[str, Any]]:
        """
        Write hook that deploys edge functions if a file is in the supabase/functions directory.
        This hook runs before files are committed to disk, so it uses the content from the change.
        It deploys multiple edge functions in parallel to save time.
        It also deletes edge functions when the corresponding file is deleted.

        Args:
            turn: The current write turn with changes

        Returns:
            List of deployment results (empty list if none were deployed)
        """

        edge_functions_to_deploy = []
        edge_functions_to_delete = []

        # First, collect all the edge functions that need to be deployed or deleted
        for change in turn.changes:
            # Convert the path to a pathlib.Path object for easier manipulation
            path = Path(change.path) if change.path else None
            if not path:
                continue

            # Try to make path relative to cwd if it's absolute
            if path.is_absolute():
                try:
                    rel_path = path.relative_to(Path(self.cwd))
                except ValueError:
                    # Not a subpath of cwd
                    continue
            else:
                rel_path = path

            # Check if this matches the edge function pattern
            parts = list(rel_path.parts)
            if len(parts) >= 3 and parts[0] == "supabase" and parts[1] == "functions":
                function_name = None

                # Handle both patterns:
                # 1. supabase/functions/function-name.ts
                # 2. supabase/functions/function-name/index.ts
                if len(parts) == 3 and rel_path.suffix.lower() == ".ts":
                    # Pattern 1: Standard function file
                    function_name = rel_path.stem
                elif len(parts) >= 4 and parts[-1].lower() == "index.ts":
                    # Pattern 2: Function in its own directory with index.ts
                    function_name = parts[2]  # Directory name is function name

                # Only proceed if we identified a function name using either pattern
                if function_name:
                    if change.change_type == ChangeType.WRITE and change.content:
                        # Add to deploy list
                        edge_functions_to_deploy.append(
                            {
                                "function_name": function_name,
                                "source_code": change.content,
                            }
                        )
                    elif change.change_type == ChangeType.DELETE:
                        # Add to delete list
                        edge_functions_to_delete.append(
                            {"function_name": function_name}
                        )

        supabase_util = SupabaseUtil(self.cwd)
        results = []

        # Process edge function deployments in parallel
        if edge_functions_to_deploy:

            async def deploy_function(func_data: dict) -> dict:
                try:
                    result = await supabase_util.deploy_edge_function(
                        func_data["function_name"], func_data["source_code"]
                    )
                    logger.info(f"Deployed edge function: {func_data['function_name']}")
                    return {
                        "function_name": func_data["function_name"],
                        "operation": "deploy",
                        "success": True,
                        "result": result,
                    }
                except Exception as e:
                    logger.error(
                        f"Failed to deploy edge function {func_data['function_name']}: {e}"
                    )
                    return {
                        "function_name": func_data["function_name"],
                        "operation": "deploy",
                        "success": False,
                        "error": str(e),
                    }

            # Create tasks for concurrent deployment
            deployment_tasks = [
                deploy_function(func_data) for func_data in edge_functions_to_deploy
            ]

            if deployment_tasks:
                # Run all deployments concurrently
                deploy_results = await asyncio.gather(*deployment_tasks)
                results.extend(deploy_results)

        # Process edge function deletions in parallel
        if edge_functions_to_delete:

            async def delete_function(func_data: dict) -> dict:
                try:
                    success = await supabase_util.delete_edge_function(
                        func_data["function_name"]
                    )
                    if success:
                        logger.info(
                            f"Deleted edge function: {func_data['function_name']}"
                        )
                        return {
                            "function_name": func_data["function_name"],
                            "operation": "delete",
                            "success": True,
                        }
                    else:
                        logger.error(
                            f"Failed to delete edge function {func_data['function_name']}"
                        )
                        return {
                            "function_name": func_data["function_name"],
                            "operation": "delete",
                            "success": False,
                            "error": "Deletion failed or verification failed",
                        }
                except Exception as e:
                    logger.error(
                        f"Error deleting edge function {func_data['function_name']}: {e}"
                    )
                    return {
                        "function_name": func_data["function_name"],
                        "operation": "delete",
                        "success": False,
                        "error": str(e),
                    }

            # Use asyncio.gather to delete all functions in parallel
            deletion_tasks = [
                delete_function(func_data) for func_data in edge_functions_to_delete
            ]

            if deletion_tasks:
                # Execute all deletion tasks concurrently and collect results
                delete_results = await asyncio.gather(*deletion_tasks)
                results.extend(delete_results)

        return results

    async def _on_deploy_edge_function_complete(
        self, ctx: HookContext[list[dict[str, Any]]]
    ) -> None:
        """
        Handle completion of edge function deployment or deletion.

        Args:
            ctx: The hook context containing the result
        """
        if ctx.status != HookStatus.SUCCESS:
            logger.error(f"Edge function operations failed: {ctx.error}")
            return

        if not ctx.result:
            # No functions were deployed or deleted
            return

        # Log successful and failed deployments/deletions
        successful_deploys = [
            r["function_name"]
            for r in ctx.result
            if r.get("success") and r.get("operation") == "deploy"
        ]
        failed_deploys = [
            r["function_name"]
            for r in ctx.result
            if not r.get("success") and r.get("operation") == "deploy"
        ]
        successful_deletes = [
            r["function_name"]
            for r in ctx.result
            if r.get("success") and r.get("operation") == "delete"
        ]
        failed_deletes = [
            r["function_name"]
            for r in ctx.result
            if not r.get("success") and r.get("operation") == "delete"
        ]

        if successful_deploys:
            logger.info(
                f"Successfully deployed edge functions: {', '.join(successful_deploys)}"
            )

        if failed_deploys:
            logger.warning(
                f"Failed to deploy edge functions: {', '.join(failed_deploys)}"
            )

        if successful_deletes:
            logger.info(
                f"Successfully deleted edge functions: {', '.join(successful_deletes)}"
            )

        if failed_deletes:
            logger.warning(
                f"Failed to delete edge functions: {', '.join(failed_deletes)}"
            )

        # Request memory compaction via event bus after successful edge function operations
        if successful_deploys or successful_deletes:
            try:
                # Publish event to request memory compaction
                await self.event_bus.publish_async(
                    EventType.MEMORY_COMPACT_REQUESTED,
                    {
                        "reason": "edge_function_operations",
                        "functions_deployed": len(successful_deploys),
                        "functions_deleted": len(successful_deletes),
                    },
                )
                logger.info(
                    "Memory compaction requested after edge function operations"
                )
            except Exception as e:
                logger.error(f"Error requesting memory compaction: {str(e)}")

    async def _deploy_migrations_hook(self, turn: WriteTurn) -> list[dict[str, Any]]:
        """
        Write hook that deploys SQL migrations if a file is in the supabase/migrations directory.
        This hook runs before files are committed to disk, so it uses the content from the change.
        It sorts migrations by filename to ensure chronological order of application.

        Args:
            turn: The current write turn with changes

        Returns:
            List of migration results (empty list if none were deployed)
        """
        migrations_to_deploy = []

        # First, collect all the migrations that need to be deployed
        for change in turn.changes:
            # Convert the path to a pathlib.Path object for easier manipulation
            path = Path(change.path) if change.path else None
            if not path:
                continue

            # Try to make path relative to cwd if it's absolute
            if path.is_absolute():
                try:
                    rel_path = path.relative_to(Path(self.cwd))
                except ValueError:
                    # Not a subpath of cwd
                    continue
            else:
                rel_path = path

            # Check if this matches the migrations pattern
            parts = list(rel_path.parts)
            if len(parts) >= 3 and parts[0] == "supabase" and parts[1] == "migrations":
                # Only process SQL files
                if not rel_path.suffix.lower() == ".sql":
                    continue

                if change.change_type == ChangeType.WRITE and change.content:
                    # Extract the migration name from the filename
                    migration_name = rel_path.stem

                    # Add to deploy list with the path as sorting key
                    migrations_to_deploy.append(
                        {
                            "name": migration_name,
                            "content": change.content,
                            "path": str(rel_path),  # Use full path for sorting
                        }
                    )

        # Sort migrations to ensure they're applied in chronological order
        # This assumes filenames start with timestamps or have a natural sort order
        migrations_to_deploy.sort(key=lambda m: m["path"])

        supabase_util = SupabaseUtil(self.cwd)
        results = []

        # Deploy migrations sequentially in the sorted order
        for migration in migrations_to_deploy:
            try:
                result = await supabase_util.deploy_migration(
                    migration_sql=migration["content"],
                    name=migration["name"],
                )
                logger.info(f"Deployed migration: {migration['name']}")
                results.append(
                    {
                        "migration_name": migration["name"],
                        "path": migration["path"],
                        "success": result["success"],
                        "timestamp": result["timestamp"],
                        "error": result.get("error"),
                    }
                )

                # If a migration fails, stop processing further migrations
                if not result["success"]:
                    logger.error(
                        f"Migration {migration['name']} failed: {result.get('error')}"
                    )
                    break

            except Exception as e:
                logger.error(f"Error deploying migration {migration['name']}: {str(e)}")
                results.append(
                    {
                        "migration_name": migration["name"],
                        "path": migration["path"],
                        "success": False,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                break  # Stop on first failure

        return results

    async def _on_deploy_migrations_complete(
        self, ctx: HookContext[list[dict[str, Any]]]
    ) -> None:
        """
        Handle completion of SQL migration deployment.

        Args:
            ctx: The hook context containing the result
        """
        if ctx.status != HookStatus.SUCCESS:
            logger.error(f"Migration operations failed: {ctx.error}")
            return

        if not ctx.result:
            # No migrations were deployed
            return

        # Log successful and failed migrations
        successful_migrations = [
            r["migration_name"] for r in ctx.result if r.get("success")
        ]
        failed_migrations = [
            r["migration_name"] for r in ctx.result if not r.get("success")
        ]

        if successful_migrations:
            logger.info(
                f"Successfully deployed migrations: {', '.join(successful_migrations)}"
            )

        if failed_migrations:
            logger.warning(
                f"Failed to deploy migrations: {', '.join(failed_migrations)}"
            )

        # Request memory compaction via event bus after successful migration operations
        if successful_migrations:
            try:
                # Publish event to request memory compaction
                await self.event_bus.publish_async(
                    EventType.MEMORY_COMPACT_REQUESTED,
                    {
                        "reason": "migration_operations",
                        "migrations_deployed": len(successful_migrations),
                    },
                )
                logger.info("Memory compaction requested after migration operations")
            except Exception as e:
                logger.error(f"Error requesting memory compaction: {str(e)}")

    # Methods that might be called by the agent after getting hook results
    async def process_code_check_results(
        self,
        ctx: HookContext[tuple[bool, list[str]]],
        add_memory_callback: Callable[[str], Awaitable[None]],
    ) -> None:
        """Process code check results and add them to memory if needed.

        Args:
            ctx: The code check hook context with results
            add_memory_callback: A callback to add results to agent memory
        """
        if ctx.status != HookStatus.SUCCESS:
            return

        if not ctx.result:
            return

        passed, check_results = ctx.result
        # Only add to memory if there are results to report
        if check_results:
            await add_memory_callback("\n\n".join(check_results))
