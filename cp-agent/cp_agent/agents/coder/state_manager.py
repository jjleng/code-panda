"""State management for coder agent operations."""

from datetime import datetime
from typing import Any, Dict, Optional, Set


class TaskState:
    """Manages the state of a specific task."""

    def __init__(self) -> None:
        self.id: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.status: str = "idle"  # idle, running, completed, failed, aborted, timeout

    def start(self, task_id: str) -> None:
        """Start a new task with the given ID."""
        self.id = task_id
        self.start_time = datetime.now()
        self.status = "running"

    def complete(self) -> None:
        """Mark the task as completed."""
        self.end_time = datetime.now()
        self.status = "completed"

    def fail(self) -> None:
        """Mark the task as failed."""
        self.end_time = datetime.now()
        self.status = "failed"

    def abort(self) -> None:
        """Mark the task as aborted."""
        self.end_time = datetime.now()
        self.status = "aborted"

    def timeout(self) -> None:
        """Mark the task as timed out."""
        self.end_time = datetime.now()
        self.status = "timeout"


class StreamingState:
    """Manages the state of the streaming process."""

    def __init__(self) -> None:
        self.is_active: bool = False
        self.current_message: str = ""


class ToolState:
    """Manages the state of tool executions."""

    def __init__(self) -> None:
        self.completed_tools: Set[str] = set()
        self.failed_tools: Set[str] = set()
        self.tool_results: list[Dict[str, Any]] = []
        self.consecutive_mistakes: int = 0

    def add_success(
        self,
        tool_name: str,
        tool_id: str,
        params: Dict[str, Any],
        result: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a successful tool execution."""
        self.completed_tools.add(tool_name)
        self.consecutive_mistakes = 0

        self.tool_results.append(
            {
                "tool": tool_name,
                "tool_id": tool_id,
                "status": "success",
                "result": result,
                "params": params,
                "extra": extra or {},
            }
        )

    def add_failure(
        self,
        tool_name: str,
        tool_id: str,
        params: Dict[str, Any],
        error: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a failed tool execution."""
        self.failed_tools.add(tool_name)
        self.consecutive_mistakes += 1

        self.tool_results.append(
            {
                "tool": tool_name,
                "tool_id": tool_id,
                "status": "failed",
                "error": error,
                "params": params,
                "extra": extra or {},
            }
        )

    def clear_results(self) -> None:
        """Clear the tool results list."""
        self.tool_results.clear()


class StateManager:
    """Central state manager for the coder agent."""

    def __init__(self) -> None:
        self.task = TaskState()
        self.streaming = StreamingState()
        self.tool = ToolState()

    def reset_for_new_task(self, task_id: str) -> None:
        """Reset all state for a new task."""
        self.task.start(task_id)
        self.streaming.is_active = False
        self.streaming.current_message = ""
        self.tool.completed_tools.clear()
        self.tool.failed_tools.clear()
        self.tool.tool_results.clear()
        self.tool.consecutive_mistakes = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert the current state to a dictionary."""
        return {
            "task_id": self.task.id,
            "start_time": self.task.start_time,
            "end_time": self.task.end_time,
            "status": self.task.status,
            "completed_tools": list(self.tool.completed_tools),
            "failed_tools": list(self.tool.failed_tools),
            "tool_results": self.tool.tool_results,
            "consecutive_mistakes": self.tool.consecutive_mistakes,
        }
