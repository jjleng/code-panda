"""Implementation of an AI coding agent with parallel tool execution capabilities and memory management."""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Optional, cast
from uuid import UUID
from zoneinfo import ZoneInfo

import litellm
from litellm import CustomStreamWrapper, acompletion
from loguru import logger

from cp_agent.agents.base import BaseAgent
from cp_agent.agents.coder import prompts
from cp_agent.agents.coder.event_bus import EventBus, EventType
from cp_agent.agents.coder.hooks import HookManager
from cp_agent.agents.coder.message_manager import MessageManager
from cp_agent.agents.coder.state_manager import StateManager
from cp_agent.agents.coder.stream_processor import StreamProcessor
from cp_agent.agents.coder.tool_executor import ToolError, ToolExecutor
from cp_agent.agents.searcher.agent import SearcherAgent
from cp_agent.config import settings
from cp_agent.storage.file_operation_manager import (
    FileOperationManager,
    HookContext,
    HookStatus,
)
from cp_agent.storage.list_store import BaseListStore
from cp_agent.types import StreamEvent, TextEvent, ToolEvent
from cp_agent.utils.format_response import create_text_block, too_many_mistakes
from cp_agent.utils.message_formats import MessageContent, ensure_message_list
from cp_agent.utils.runner_client import RunnerClient


class CoderAgent(BaseAgent):
    """AI coding agent that executes tasks using GPT-4 and various development tools."""

    def __init__(
        self,
        memory: BaseListStore,
        cwd: str = str(Path.cwd()),
        user_id: Optional[UUID] = None,
    ):
        super().__init__(memory=memory, cwd=cwd)
        self.preview_path = "/"
        self.user_id = user_id

        # Initialize component managers
        self.state_manager = StateManager()

        # Initialize memory management
        self.message_manager = MessageManager(
            memory=memory,
        )

        self.event_bus = EventBus()

        # Initialize clients and managers
        self.runner = RunnerClient()
        self.searcher = SearcherAgent(memory)

        # Track all the file write operations and call hooks
        self.file_operation_manager = FileOperationManager(
            cwd, event_bus=self.event_bus
        )

        # Initialize tool executor
        self.tool_executor = ToolExecutor(
            cwd=cwd,
            state_manager=self.state_manager,
            file_operation_manager=self.file_operation_manager,
            runner=self.runner,
            event_bus=self.event_bus,
        )

        # Initialize hook manager
        # Register hooks with the file operation manager
        self.hook_manager = HookManager(
            cwd, self.file_operation_manager, self.runner, self.event_bus
        )
        self.hook_manager.register_all_hooks(
            {
                "code_check": self._on_code_check_complete,
            }
        )

        # Initialize stream processor
        self.stream_processor = StreamProcessor(
            cwd=cwd,
            state_manager=self.state_manager,
            on_tool_execute=self._queue_tool_execution,
            event_bus=self.event_bus,
        )

        # Set up event listeners
        self._setup_event_listeners()

    def _setup_event_listeners(self) -> None:
        """Set up listeners for various events."""
        self.event_bus.subscribe_async(
            EventType.TOOL_COMPLETED, self._on_tool_completed
        )
        self.event_bus.subscribe_async(EventType.TOOL_FAILED, self._on_tool_failed)
        self.event_bus.subscribe_async(EventType.HOOK_FAILED, self._on_hook_failed)
        self.event_bus.subscribe(EventType.USAGE_UPDATED, self._on_usage_updated)

        # Subscribe to memory compaction requests
        self.event_bus.subscribe_async(
            EventType.MEMORY_COMPACT_REQUESTED, self._on_memory_compact_requested
        )
        self.event_bus.subscribe_async(
            EventType.MIGRATION_FAILED, self._on_migration_failed
        )

    async def _on_memory_compact_requested(self, data: Dict[str, Any]) -> None:
        """Handle memory compaction request events."""
        try:
            reason = data.get("reason", "unknown")
            logger.info(f"Memory compaction requested due to: {reason}")
            await self.message_manager.compact_memory()
            logger.info(f"Memory compaction completed successfully (reason: {reason})")
        except Exception as e:
            logger.error(f"Memory compaction failed: {str(e)}")

    async def _on_migration_failed(self, data: Dict[str, Any]) -> None:
        """Handle migration failure events and add error details to memory."""
        migration_name = data.get("migration_name", "unknown")
        error_message = data.get("error", "Unknown error")
        path = data.get("path", "unknown path")

        logger.warning(f"Migration '{migration_name}' failed: {error_message}")

        # Format the error message for the LLM's context
        formatted_error = (
            f"[Migration Failure]\n"
            f"Migration Name: {migration_name}\n"
            f"File Path: {path}\n"
            f"Error: {error_message}"
        )

        try:
            # Add the formatted error to the agent's memory
            await self.message_manager.add_memory_item(formatted_error)
            logger.info(
                f"Added migration failure details for '{migration_name}' to memory."
            )
        except Exception as e:
            logger.error(f"Failed to add migration failure details to memory: {str(e)}")

    def set_preview_path(self, preview_path: str) -> None:
        """Set the current preview path being viewed by the user."""
        self.preview_path = preview_path

    async def run(self, message: MessageContent) -> AsyncGenerator[StreamEvent, None]:
        """Process a message and generate a response stream.

        This is the standard entry point for the agent that implements the BaseAgent interface.

        Args:
            message: The message content to process

        Returns:
            A stream of events representing the agent's response
        """
        # Generate a unique task ID using timestamp
        task_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.state_manager.reset_for_new_task(task_id)

        try:
            # Gather environment information
            env_details = await self.get_environment_details(include_files=True)
            task_content = ensure_message_list(message)
            env_details_block = create_text_block(env_details)
            full_message = task_content + [env_details_block]

            # Add message to memory and prime context
            await self.message_manager.add_memory_item(full_message, role="user")
            await self.context_enricher.prime_all()
            await self.searcher.prime_search_results(message, with_llm=True)

            # Process the message recursively
            async for event in self._recursively_process_messages(full_message):
                if self.state_manager.task.status == "aborted":
                    break
                yield event

        except Exception as e:
            logger.exception(e)
            error_msg = f"Error in task {task_id}: {e}"
            logger.error(error_msg)
            await self.message_manager.add_assistant_message(error_msg)
            yield TextEvent(text=error_msg)

    async def _on_code_check_complete(
        self, ctx: HookContext[tuple[bool, list[str]]]
    ) -> None:
        """
        Handle completion of code quality checks.
        Adds check results to memory so they're available for the LLM context.
        Also tracks consecutive build/lint failures.
        """
        if ctx.status != HookStatus.SUCCESS:
            logger.error(f"Code checks failed to execute: {ctx.error}")
            self.state_manager.tool.consecutive_code_failures += 1
            logger.info(
                f"Code checks failed. Consecutive failures: {self.state_manager.tool.consecutive_code_failures}"
            )
            return

        if not ctx.result:
            logger.error("Code checks did not return a result")
            self.state_manager.tool.consecutive_code_failures += 1
            logger.info(
                f"Code checks failed. Consecutive failures: {self.state_manager.tool.consecutive_code_failures}"
            )
            return

        passed, check_results = ctx.result
        if not passed:
            # Increment consecutive failures counter on build/lint errors
            self.state_manager.tool.consecutive_code_failures += 1
            logger.info(
                f"Code checks failed. Consecutive failures: {self.state_manager.tool.consecutive_code_failures}"
            )
        else:
            logger.info("Code checks passed. Consecutive failures reset to 0")
            # Reset counter on successful build/lint
            self.state_manager.tool.consecutive_code_failures = 0

        # Store check results in memory for LLM context
        if check_results:
            env_details = await self.get_environment_details(include_files=True)
            env_details_block = create_text_block(env_details)
            check_results_block = create_text_block("\n\n".join(check_results))
            await self.message_manager.add_memory_item(
                [env_details_block, check_results_block],
            )

        logger.info(f"Code checks completed: passed={passed}, results={check_results}")

    def abort(self) -> None:
        """Abort current task execution."""
        self.state_manager.task.abort()
        logger.info(f"Task {self.state_manager.task.id} aborted")

    async def resume(self, task_id: str) -> AsyncGenerator[StreamEvent, None]:
        """Resume an existing task."""
        self.state_manager.reset_for_new_task(task_id)
        self.file_operation_manager.discard_turn()

        try:
            # Get all chat history
            chat_history = self.message_manager.get_chat_history()

            if not chat_history:
                raise ValueError("No task history found")

            last_msg = chat_history[-1]
            env_details = await self.get_environment_details(include_files=True)
            last_content = ensure_message_list(last_msg["content"])
            env_details_block = create_text_block(env_details)
            message = last_content + [env_details_block]

            # Process the message
            async for event in self._recursively_process_messages(message):
                if self.state_manager.task.status == "aborted":
                    break
                yield event

        except Exception as e:
            error_msg = f"Error resuming task {task_id}: {e}"
            logger.error(error_msg)
            yield TextEvent(text=error_msg)

    async def get_environment_details(self, include_files: bool = False) -> str:
        """Gather project context including directory, files, and system information."""
        details = []

        # Add current working directory info
        details.append(f"# Current Working Directory\n{self.cwd}")

        # Add currently viewing pages
        details.append(
            f"\n# User is currently viewing the page at: {self.preview_path}"
        )

        # Add current time with timezone using modern ZoneInfo
        local_tz = ZoneInfo("UTC")
        now = datetime.now().astimezone(local_tz)
        timezone = now.tzname()
        offset = now.utcoffset()
        if offset is not None:
            offset_hours = offset.total_seconds() / 3600
            offset_minutes = (abs(offset.total_seconds()) % 3600) / 60
            offset_str = f"{'+' if offset_hours >= 0 else '-'}{int(abs(offset_hours)):02d}:{int(offset_minutes):02d}"
        else:
            offset_str = "+00:00"
        details.append(
            f"# Current Time\n{now.strftime('%Y-%m-%d %I:%M:%S %p')} ({timezone}, UTC{offset_str})"
        )

        # Add workspace files only when include_files is True
        if include_files:
            details.append(f"\n# Files in {self.cwd}")
            try:
                files = await self.list_files(".", recursive=True)
                details.append(files if files else "(No files found)")
            except Exception as e:
                details.append(f"Error listing files: {e}")

        combined_details = "\n\n".join(details)
        return f"<environment-details>\n{combined_details}\n</environment-details>"

    async def _recursively_process_messages(
        self, user_message: MessageContent
    ) -> AsyncGenerator[StreamEvent, None]:
        """Process messages with improved state management and error handling."""
        # Check authentication and quota at the beginning of each recursive process
        self.file_operation_manager.discard_turn()
        turn_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        self.file_operation_manager.begin_turn(turn_id)

        try:
            # Check for too many consecutive mistakes
            if (
                self.state_manager.tool.consecutive_tool_failures >= 4
                or self.state_manager.tool.consecutive_code_failures >= 4
            ):
                error_msg = (
                    "Assistant has made too many consecutive mistakes. This may indicate a failure in the "
                    "thought process or inability to use tools properly. Consider providing guidance on "
                    "breaking down the task into smaller steps."
                )
                yield TextEvent(text=error_msg)

                # Get user feedback
                self.state_manager.task.fail()

                # For now, we don't try to add any remedial messages here
                # user_message = str(too_many_mistakes())
                # await self.message_manager.add_memory_item(user_message)

                # Reset mistake counters after getting feedback
                self.state_manager.tool.consecutive_tool_failures = 0
                self.state_manager.tool.consecutive_code_failures = 0
                return

            # Get system prompt
            try:
                system_prompt = await prompts.system_prompt(self.cwd)
            except Exception as e:
                logger.error(f"Failed to get context: {e}")
                raise ValueError("Failed to initialize task context") from e

            # Get all stored messages
            stored_messages = self.message_manager.get_messages()

            # Build messages for API call
            messages = [
                {"role": "system", "content": system_prompt},
                *stored_messages,
            ]

            # Initialize tool queue
            tool_queue: asyncio.Queue = asyncio.Queue()
            consumer_task = asyncio.create_task(self._tool_consumer(tool_queue))

            try:
                # Make API request with timeout
                response = await asyncio.wait_for(
                    acompletion(
                        model=settings.CODER_MODEL,
                        messages=messages,
                        api_base=settings.CODER_LLM_URL,
                        api_key=settings.CODER_API_KEY,
                        stream=True,
                        stream_options={"include_usage": True},
                        temperature=0,
                    ),
                    timeout=60,  # 1 minute timeout
                )

                # Process the streaming response
                async for event in self.stream_processor.process_stream(
                    cast(CustomStreamWrapper, response), tool_queue
                ):
                    yield event

                # Signal consumer that no more tools are coming
                await tool_queue.put(None)

                # Wait for consumer to process all tools
                await consumer_task

                # Store the assistant message
                if self.state_manager.streaming.current_message:
                    await self.message_manager.add_assistant_message(
                        self.state_manager.streaming.current_message
                    )

                # Process tool results if we have any
                if self.state_manager.tool.tool_results:
                    # First check if there's a follow-up question - handle it before anything else
                    # This ensures the LLM doesn't combine follow-up questions with other tools
                    for result in self.state_manager.tool.tool_results:
                        if (
                            result["tool"] == "ask-followup-question"
                            and result["status"] == "success"
                        ):
                            question = result["result"]
                            # Stream the follow-up question to the client
                            yield TextEvent(text=question)
                            # Mark task as complete and return immediately
                            self.state_manager.task.complete()
                            return

                    # If we get here, there's no follow-up question, so process other tools normally
                    # Format tool results as a message
                    tool_results_message = "\n\n".join(
                        [
                            f"[{result['tool']}{' for ' + result['params']['path'] if 'params' in result and 'path' in result['params'] else ''} {'Success' if result['status'] == 'success' else 'Error'}]\n"
                            f"{result['result'] if result['status'] == 'success' else result['error']}"
                            for result in self.state_manager.tool.tool_results
                        ]
                    )

                    # Add tool results to memory
                    await self.message_manager.add_memory_item(tool_results_message)

                    # Commit turn after tool execution and trigger post-edit hooks
                    try:
                        await self.file_operation_manager.commit_turn()
                    except Exception as e:
                        logger.error(f"Post-edit checks failed: {e}")

                    # Emit tool events for each completed tool
                    for result in self.state_manager.tool.tool_results:
                        yield ToolEvent(
                            tool_name=result["tool"],
                            tool_id=result["tool_id"],
                            status=(
                                "completed"
                                if result["status"] == "success"
                                else "failed"
                            ),
                            params=result.get("params"),
                            result=result.get("result"),
                            error=result.get("error"),
                            extra=result.get("extra"),
                        )

                    # Clear tool results for next iteration
                    self.state_manager.tool.clear_results()

                    # Recursively process the tool results message
                    async for recur_event in self._recursively_process_messages(
                        tool_results_message
                    ):
                        yield recur_event

                # Update state if no more tools to process
                if not self.state_manager.tool.tool_results:
                    self.state_manager.task.complete()

            except asyncio.TimeoutError:
                error_msg = "Assistant response timed out after 1 minute"
                logger.error(error_msg)
                yield TextEvent(text=error_msg)
                self.state_manager.task.timeout()

            except litellm.exceptions.BadRequestError as e:
                logger.exception(e)
                error_msg = f"Bad request error: {e.message}"
                logger.error(error_msg)
                await self.message_manager.add_assistant_message(error_msg)
                yield TextEvent(text=error_msg)
                self.state_manager.task.fail()

            except Exception as e:
                logger.error(
                    f"Task {self.state_manager.task.id} failed: {e}", exc_info=True
                )
                error_msg = f"Task failed: {str(e)}"
                await self.message_manager.add_assistant_message(error_msg)
                yield TextEvent(text=error_msg)
                self.state_manager.task.fail()

            finally:
                # Cleanup
                if not consumer_task.done():
                    consumer_task.cancel()
                    try:
                        await consumer_task
                    except asyncio.CancelledError:
                        pass

        except Exception as e:
            logger.error(
                f"Task {self.state_manager.task.id} failed: {e}", exc_info=True
            )
            error_msg = f"Task failed: {str(e)}"
            await self.message_manager.add_assistant_message(error_msg)
            yield TextEvent(text=error_msg)

    def _queue_tool_execution(
        self, tool_name: str, params: Dict[str, Any], tool_id: str
    ) -> asyncio.Task:
        """Queue a tool for execution."""
        task = asyncio.create_task(self.tool_executor.execute_tool(tool_name, params))
        return task

    def _get_old_file_content(self, params: Dict[str, Any]) -> str | None:
        """Helper method to read original file content."""
        old_content = None
        if "path" in params:
            file_path = Path(self.cwd) / str(params["path"])
            if file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        old_content = f.read()
                except Exception as e:
                    logger.error(f"Error reading original file content: {e}")
        return old_content

    async def _on_tool_completed(self, data: Dict[str, Any]) -> None:
        """Handle tool completion event."""
        tool_name = data.get("name", "")
        tool_id = data.get("id", "")
        params = data.get("params", {})
        result = data.get("result", "")

        # Collect additional context data for tool execution records
        extra = {}

        # For file modification tools, capture the before/after file contents
        # to provide complete context on what changed
        if tool_name in ["write-to-file", "apply-diff"]:
            # Get the file's original content before modification
            old_content = self._get_old_file_content(params)

            # Retrieve the new content from pending file changes
            new_content = None
            if "path" in params:
                file_path = str(Path(self.cwd) / params["path"])
                file_change = self.file_operation_manager.get_pending_file_change(
                    file_path
                )
                if file_change:
                    new_content = file_change.content

            # Store both versions for context and debugging
            extra = {"old_content": old_content, "new_content": new_content}

        # Record successful tool execution
        self.state_manager.tool.add_success(
            tool_name=tool_name,
            tool_id=tool_id,
            params=params,
            result=result,
            extra=extra,
        )

    async def _on_tool_failed(self, data: Dict[str, Any]) -> None:
        """Handle tool failure event."""
        tool_name = data.get("name", "")
        tool_id = data.get("id", "")
        params = data.get("params", {})
        error = data.get("error", "")

        # Collect additional context data for debugging failed tool executions
        extra = {}

        # For file modification tools, capture the original file content
        # to provide context on what the tool was attempting to modify
        if tool_name in ["write-to-file", "apply-diff"]:
            old_content = self._get_old_file_content(params)
            extra = {"old_content": old_content, "new_content": None}

        # Record failed tool execution
        self.state_manager.tool.add_failure(
            tool_name=tool_name,
            tool_id=tool_id,
            params=params,
            error=error,
            extra=extra,
        )

    async def _tool_consumer(self, tool_queue: asyncio.Queue) -> None:
        """Consumer that processes tools from the queue as they become available."""
        running_tools: Dict[asyncio.Task, Dict[str, Any]] = {}

        while True:
            # Check if task was aborted
            if self.state_manager.task.status == "aborted":
                # Cancel all running tools
                for task in running_tools:
                    task.cancel()
                # Clear the queue
                while not tool_queue.empty():
                    try:
                        tool_queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break
                break

            try:
                # Process any completed tools
                if running_tools:
                    done, _ = await asyncio.wait(
                        running_tools.keys(),
                        timeout=0.1,
                        return_when=asyncio.FIRST_COMPLETED,
                    )

                    for task in done:
                        tool = running_tools.pop(task)
                        await self._handle_tool_result(task, tool)

                # Check for new tools to process
                try:
                    tool = await asyncio.wait_for(tool_queue.get(), timeout=0.1)
                    if tool is None:  # Sentinel value
                        break

                    # Create and track new tool task
                    task = asyncio.create_task(
                        self.tool_executor.execute_tool(tool["name"], tool["params"])
                    )
                    running_tools[task] = tool

                except asyncio.TimeoutError:
                    continue

            except Exception as e:
                logger.exception(e)
                logger.error(f"Error in tool consumer: {e}")
                break

        # Wait for any remaining tools to complete
        if running_tools:
            done, pending = await asyncio.wait(running_tools.keys())

            # First cancel pending tasks
            for task in pending:
                task.cancel()

            # Process completed tasks
            for task in done:
                tool = running_tools[task]
                await self._handle_tool_result(task, tool)

            # Wait for cancelled tasks to finish cleanup
            if pending:
                try:
                    await asyncio.wait(pending)
                except asyncio.CancelledError:
                    pass

    async def _handle_tool_result(
        self, task: asyncio.Task, tool: Dict[str, Any]
    ) -> None:
        """Handle tool execution result consistently."""
        try:
            result = await task

            # Special handling for ask-followup-question tool
            if tool["name"] == "ask-followup-question":
                question = result

                # Add the question to the current message
                if self.state_manager.streaming.current_message:
                    self.state_manager.streaming.current_message += f"\n\n{question}"
                else:
                    self.state_manager.streaming.current_message = question

                formatted_result = question
            else:
                formatted_result = f"Result:\n{result}"

            # Update tool state through event system
            await self.event_bus.publish_async(
                EventType.TOOL_COMPLETED,
                {
                    "name": tool["name"],
                    "id": tool["tool_id"],
                    "params": tool["params"],
                    "result": formatted_result,
                },
            )

        except Exception as e:
            error_msg = str(e)
            if isinstance(e, ToolError):
                error_msg = f"{e.message} (Error code: {e.error_code})"

            # Update tool state through event system
            await self.event_bus.publish_async(
                EventType.TOOL_FAILED,
                {
                    "name": tool["name"],
                    "id": tool["tool_id"],
                    "params": tool["params"],
                    "error": error_msg,
                },
            )

    async def _on_hook_failed(self, data: Dict[str, Any]) -> None:
        """Handle hook failure events."""
        hook_name = data.get("hook_name", "unknown")
        error = data.get("error", "No details available")

        logger.warning(f"Background hook '{hook_name}' failed: {error}")

        if hook_name in ["git_snapshot", "project_backup"]:
            # We need trigger alerts for these hooks
            pass

    def get_state_dict(self) -> Dict[str, Any]:
        """Get current state as a dictionary."""
        return self.state_manager.to_dict()

    async def force_compact_memory(self) -> None:
        """Manually trigger memory compaction."""
        await self.message_manager.compact_memory()

    # Tool methods - these are forwarded to the tool executor
    async def list_files(self, path: str, recursive: bool = False) -> str:
        """Get file listing with intelligent filtering and safety checks."""
        return await self.tool_executor.execute_tool(
            "list-files", {"path": path, "recursive": recursive}
        )

    def _on_usage_updated(self, data: Dict[str, Any]) -> None:
        """Handle usage update events and deduct credits."""
        input_tokens = data.get("input_tokens", 0)
        output_tokens = data.get("output_tokens", 0)
        logger.debug(
            f"Usage updated: {input_tokens} input tokens, {output_tokens} output tokens"
        )
