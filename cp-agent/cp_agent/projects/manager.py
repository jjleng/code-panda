import os
import shutil
import subprocess
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Optional

from loguru import logger

from cp_agent.config import settings
from cp_agent.projects.models import Project


class BaseProjectManager(ABC):
    """
    Abstract base class for project management implementations.
    Open source projects can implement this with file-based storage,
    while hosted version can use Supabase.
    """

    def __init__(self) -> None:
        os.makedirs(settings.WORKSPACE_PATH, exist_ok=True)

    async def _clone_starter_project(self, project_id: str) -> str:
        """Clone starter project from GitHub."""
        project_path = os.path.join(settings.WORKSPACE_PATH, project_id)
        if os.path.exists(project_path):
            shutil.rmtree(project_path)
        os.makedirs(project_path, exist_ok=True)

        try:
            result = subprocess.run(
                ["git", "clone", settings.STARTER_PROJECT_REPO, project_path],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise Exception(f"Git clone failed: {result.stderr}")
            return project_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Error cloning repository: {e.stderr}")
            raise
        except Exception as e:
            logger.error(f"Error cloning repository: {e}")
            raise

    async def get_project(self, project_id: str) -> Optional[Project]:
        """Get project information by ID."""
        project_path = os.path.join(settings.WORKSPACE_PATH, project_id)
        if not os.path.exists(project_path):
            return None

        # If project exists in workspace, return a proper project object
        project: Project = {
            "id": project_id,
        }
        return project

    @abstractmethod
    async def create_project(
        self,
        project_id: str,
        name: str,
        description: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[Project]:
        """Create a new project entry."""
        pass

    @abstractmethod
    async def backup_project(self, project_id: str) -> bool:
        """Backup a project. Returns True if successful, False otherwise."""
        pass


class LocalProjectManager(BaseProjectManager):
    """Local implementation using in-memory storage."""

    def __init__(self) -> None:
        super().__init__()

    async def create_project(
        self,
        project_id: str,
        name: str,
        description: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[Project]:
        """Create project in local storage and clone starter project."""
        try:
            # Use existing project if it exists locally, otherwise clone from git
            project_path = os.path.join(settings.WORKSPACE_PATH, project_id)
            if not os.path.exists(project_path):
                await self._clone_starter_project(project_id)

            # Create project entry
            now = datetime.now(timezone.utc)
            project: Project = {
                "id": project_id,
                "name": name,
                "description": description,
                "user_id": user_id,
                "created_at": now,
                "updated_at": now,
            }
            return project
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return None

    async def backup_project(self, project_id: str) -> bool:
        """Local implementation does nothing."""
        return True


def get_project_manager() -> BaseProjectManager:
    """Get appropriate project manager implementation."""
    return LocalProjectManager()
