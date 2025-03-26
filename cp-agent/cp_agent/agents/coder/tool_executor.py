"""Tool execution management for coder agent."""

from pathlib import Path
from typing import Any, Dict, Optional, Protocol, runtime_checkable

from loguru import logger

from cp_agent.agents.coder.event_bus import EventBus, EventType
from cp_agent.agents.coder.state_manager import StateManager
from cp_agent.storage.file_operation_manager import FileOperationManager
from cp_agent.utils.dependency_management import add_dependency as add_dependency_util
from cp_agent.utils.file_listing import list_files as list_files_util
from cp_agent.utils.file_reading import read_file_content
from cp_agent.utils.file_searching import format_search_results
from cp_agent.utils.file_searching import search_files as search_files_util
from cp_agent.utils.format_response import (
    invalid_tool_parameter_error,
    missing_tool_parameter_error,
)
from cp_agent.utils.merge_diff import merge_diff
from cp_agent.utils.runner_client import RunnerClient


class ToolError(Exception):
    """Exception raised by tools with standardized error information."""

    def __init__(
        self, tool_name: str, error_code: str, message: str, details: Any = None
    ):
        self.tool_name = tool_name
        self.error_code = error_code
        self.message = message
        self.details = details
        super().__init__(message)


@runtime_checkable
class Tool(Protocol):
    """Protocol defining the interface for all tools."""

    async def execute(self, *args: Any, **params: Any) -> str:
        """Execute the tool with the provided parameters."""
        ...


class ToolExecutor:
    """Manages tool registration, validation, and execution."""

    def __init__(
        self,
        cwd: str,
        state_manager: StateManager,
        file_operation_manager: FileOperationManager,
        runner: RunnerClient,
        event_bus: Optional[EventBus] = None,
    ):
        self.cwd = cwd
        self.state_manager = state_manager
        self.file_operation_manager = file_operation_manager
        self.runner = runner
        self.event_bus = event_bus
        self._tools: dict[str, Tool] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Register all default tools."""
        self.register_tool("read-file", ReadFileTool(self.cwd))
        self.register_tool(
            "write-to-file", WriteFileTool(self.cwd, self.file_operation_manager)
        )
        self.register_tool(
            "apply-diff", ApplyDiffTool(self.cwd, self.file_operation_manager)
        )
        self.register_tool(
            "delete-file", DeleteFileTool(self.cwd, self.file_operation_manager)
        )
        self.register_tool(
            "rename-file", RenameFileTool(self.cwd, self.file_operation_manager)
        )
        self.register_tool(
            "add-dependency", AddDependencyTool(self.cwd, self.file_operation_manager)
        )
        self.register_tool("search-files", SearchFilesTool(self.cwd))
        self.register_tool("list-files", ListFilesTool(self.cwd))
        self.register_tool("ask-followup-question", AskFollowupQuestionTool())

    def register_tool(self, name: str, tool: Tool) -> None:
        """Register a new tool with the given name."""
        self._tools[name] = tool

    async def validate_tool_params(
        self, tool_name: str, params: Dict[str, Any]
    ) -> None:
        """Verify tool parameters meet requirements and constraints."""
        required_params = {
            "read-file": ["path"],
            "write-to-file": ["path", "content"],
            "apply-diff": ["path", "diff"],
            "delete-file": ["path"],
            "rename-file": ["source", "destination"],
            "add-dependency": ["name"],
            "search-files": ["path", "regex"],
            "list-files": ["path"],
            "ask-followup-question": ["question"],
        }

        if tool_name not in required_params:
            raise ToolError(
                tool_name,
                "UNKNOWN_TOOL",
                invalid_tool_parameter_error(
                    tool_name, "tool_name", "Unsupported tool"
                ),
            )

        # Check required parameters and their values
        for param in required_params[tool_name]:
            if param not in params:
                raise ToolError(
                    tool_name,
                    "MISSING_PARAM",
                    missing_tool_parameter_error(param, tool_name),
                )
            if not params[param]:
                raise ToolError(
                    tool_name,
                    "INVALID_PARAM",
                    invalid_tool_parameter_error(
                        tool_name, param, "Parameter cannot be empty"
                    ),
                )

        # Path validation
        path_params = ["path", "source", "destination"]
        for param in path_params:
            if param in params:
                path = Path(params[param])
                if path.is_absolute():
                    raise ToolError(
                        tool_name,
                        "INVALID_PATH",
                        invalid_tool_parameter_error(
                            tool_name,
                            param,
                            "Path must be relative to working directory",
                        ),
                    )

    async def execute_tool(self, tool_name: str, params: Dict[str, Any]) -> str:
        """Execute a tool by name with the provided parameters."""
        if self.event_bus:
            self.event_bus.publish(
                EventType.TOOL_EXECUTING,
                {
                    "name": tool_name,
                    "params": params,
                },
            )
        try:
            await self.validate_tool_params(tool_name, params)

            if tool_name not in self._tools:
                raise ToolError(
                    tool_name,
                    "UNKNOWN_TOOL",
                    f"Tool '{tool_name}' not found",
                )

            tool = self._tools[tool_name]
            return await tool.execute(**params)

        except ToolError:
            # Re-raise ToolError directly
            raise
        except Exception as e:
            # Wrap other exceptions in ToolError
            logger.error(f"Tool execution error ({tool_name}): {e}")
            raise ToolError(tool_name, "EXECUTION_ERROR", str(e), repr(e))


class ReadFileTool:
    """Tool for reading file contents."""

    def __init__(self, cwd: str):
        self.cwd = cwd

    async def execute(self, path: str, add_line_numbers: bool = True) -> str:
        """Read and format file contents with optional line numbers."""
        try:
            file_path = Path(self.cwd) / path
            return read_file_content(str(file_path), add_line_numbers)
        except FileNotFoundError:
            raise ToolError("read-file", "FILE_NOT_FOUND", f"File not found: {path}")
        except Exception as e:
            raise ToolError("read-file", "READ_ERROR", f"Error reading file: {str(e)}")


class WriteFileTool:
    """Tool for writing content to files."""

    def __init__(self, cwd: str, file_operation_manager: FileOperationManager):
        self.cwd = cwd
        self.file_operation_manager = file_operation_manager

    async def execute(self, path: str, content: str) -> str:
        """Write content to a file."""
        file_path = Path(self.cwd) / path
        try:
            self.file_operation_manager.write_file(str(file_path), content)
            return f"Successfully wrote content to {path}"
        except Exception as e:
            raise ToolError(
                "write-to-file", "WRITE_ERROR", f"Error writing to file: {str(e)}"
            )


class ApplyDiffTool:
    """Tool for applying diffs to files."""

    def __init__(self, cwd: str, file_operation_manager: FileOperationManager):
        self.cwd = cwd
        self.file_operation_manager = file_operation_manager

    async def execute(self, path: str, diff: str) -> str:
        """Apply a diff to a file."""
        file_path = Path(self.cwd) / path
        if not file_path.exists():
            raise ToolError("apply-diff", "FILE_NOT_FOUND", f"File not found: {path}")

        try:
            # Read original file content
            with open(file_path, "r", encoding="utf-8") as f:
                original_code = f.read()

            # Apply diff using merge_diff utility
            merged_code, success = await merge_diff(original_code, diff)

            if not success:
                raise ToolError(
                    "apply-diff",
                    "MERGE_FAILED",
                    "Failed to merge diff with original code",
                )

            # Store the merged content in file store
            self.file_operation_manager.write_file(
                str(file_path), merged_code, {"type": "diff", "original": original_code}
            )

            return f"Successfully applied diff to {path}"
        except ToolError:
            raise
        except Exception as e:
            raise ToolError(
                "apply-diff", "DIFF_ERROR", f"Error applying diff: {str(e)}"
            )


class DeleteFileTool:
    """Tool for deleting files."""

    def __init__(self, cwd: str, file_operation_manager: FileOperationManager):
        self.cwd = cwd
        self.file_operation_manager = file_operation_manager

    async def execute(self, path: str) -> str:
        """Delete a file."""
        file_path = Path(self.cwd) / path
        if not file_path.exists():
            raise ToolError("delete-file", "FILE_NOT_FOUND", f"File not found: {path}")

        try:
            self.file_operation_manager.delete_file(str(file_path))
            return f"Successfully marked {path} for deletion"
        except Exception as e:
            raise ToolError(
                "delete-file", "DELETE_ERROR", f"Error deleting file: {str(e)}"
            )


class RenameFileTool:
    """Tool for renaming/moving files."""

    def __init__(self, cwd: str, file_operation_manager: FileOperationManager):
        self.cwd = cwd
        self.file_operation_manager = file_operation_manager

    async def execute(self, source: str, destination: str) -> str:
        """Rename/move a file."""
        src_path = Path(self.cwd) / source
        dst_path = Path(self.cwd) / destination

        if not src_path.exists():
            raise ToolError(
                "rename-file", "SOURCE_NOT_FOUND", f"Source file not found: {source}"
            )

        if dst_path.exists():
            raise ToolError(
                "rename-file",
                "DESTINATION_EXISTS",
                f"Destination file already exists: {destination}",
            )

        try:
            self.file_operation_manager.rename_file(str(src_path), str(dst_path))
            return f"Successfully renamed {source} to {destination}"
        except Exception as e:
            raise ToolError(
                "rename-file", "RENAME_ERROR", f"Error renaming file: {str(e)}"
            )


class AddDependencyTool:
    """Tool for adding dependencies to a project."""

    def __init__(self, cwd: str, file_operation_manager: FileOperationManager):
        self.cwd = cwd
        self.file_operation_manager = file_operation_manager

    async def execute(self, name: str) -> str:
        """Add a dependency to the project."""
        try:
            self.file_operation_manager.add_dependency(name)
            result = await add_dependency_util(self.cwd, name)
            return result
        except Exception as e:
            raise ToolError(
                "add-dependency",
                "DEPENDENCY_ERROR",
                f"Error adding dependency: {str(e)}",
            )


class SearchFilesTool:
    """Tool for searching files with regex patterns."""

    def __init__(self, cwd: str):
        self.cwd = cwd

    async def execute(
        self, path: str, regex: str, file_pattern: Optional[str] = None
    ) -> str:
        """Search for text patterns in files."""
        base_path = Path(self.cwd) / path
        try:
            matches, total_matches = await search_files_util(
                str(base_path), regex, file_pattern
            )
            return format_search_results(matches, total_matches, max_results=300)
        except FileNotFoundError:
            raise ToolError("search-files", "PATH_NOT_FOUND", f"Path not found: {path}")
        except Exception as e:
            raise ToolError(
                "search-files", "SEARCH_ERROR", f"Error searching files: {str(e)}"
            )


class ListFilesTool:
    """Tool for listing files in a directory."""

    def __init__(self, cwd: str):
        self.cwd = cwd

    async def execute(self, path: str, recursive: bool = False) -> str:
        """List files in a directory."""
        try:
            base_path = Path(self.cwd) / path
            files, reached_limit = await list_files_util(str(base_path), recursive)

            from cp_agent.utils.format_response import format_files_list

            return format_files_list(str(base_path), files, reached_limit)
        except FileNotFoundError:
            raise ToolError("list-files", "PATH_NOT_FOUND", f"Path not found: {path}")
        except Exception as e:
            raise ToolError(
                "list-files", "LIST_ERROR", f"Error listing files: {str(e)}"
            )


class AskFollowupQuestionTool:
    """Tool for asking follow-up questions to the user."""

    async def execute(self, question: str) -> str:
        """Ask a follow-up question to the user.

        The question is returned as-is and will be streamed directly to the user.
        """
        return question
