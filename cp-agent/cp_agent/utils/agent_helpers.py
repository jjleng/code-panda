"""Helper functions for agent-related operations."""

from pathlib import Path
from typing import Optional
from uuid import UUID

from cp_agent.agents.coder.agent import CoderAgent
from cp_agent.config import settings
from cp_agent.storage.list_store import FileListStore


async def get_agent(project_id: str, user_id: Optional[UUID] = None) -> CoderAgent:
    """Get a CoderAgent instance for the specified project.

    Args:
        project_id: The project ID
        user_id: Optional UUID of the current user for credit tracking

    Returns:
        A CoderAgent instance
    """
    project_root = Path(settings.WORKSPACE_PATH) / project_id
    memory_store = FileListStore(str(project_root / ".codepanda" / "memory.dat"))

    # Create a new agent for this project
    return CoderAgent(
        memory=memory_store,
        cwd=str(project_root),
        user_id=user_id,
    )
