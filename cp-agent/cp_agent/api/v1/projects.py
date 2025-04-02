"""Project management API endpoints."""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from loguru import logger
from pydantic import BaseModel

from cp_agent.config import settings
from cp_agent.projects import get_project_manager
from cp_agent.projects.models import Project
from cp_agent.schemas.projects import (
    GenerateSummaryRequest,
    GenerateSummaryResponse,
    ListProjectPathsResponse,
    MigrationRequest,
    MigrationResponse,
    ProjectCreateRequest,
)
from cp_agent.utils.agent_helpers import get_agent
from cp_agent.utils.project_download import create_project_zip
from cp_agent.utils.project_paths import find_project_paths
from cp_agent.utils.project_summary import generate_project_summary
from cp_agent.utils.snapshot import create_snapshot
from cp_agent.utils.supabase_utils import SupabaseUtil

router = APIRouter()


class SecretRequest(BaseModel):
    name: str
    value: str


@router.post("/", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(request: ProjectCreateRequest) -> Project:
    """Create a new project.

    Args:
        request: Project creation request containing project_id and optional name

    Returns:
        Project: The created project details

    Raises:
        HTTPException: 400 if project ID is invalid
        HTTPException: 500 if project creation fails
    """
    if not request.project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Project ID is required"
        )

    project_manager = get_project_manager()

    # Check if project already exists
    project = await project_manager.get_project(request.project_id)
    if project:
        logger.info(
            f"Project {request.project_id} already exists, returning existing project"
        )
        return project

    project_name = request.name or f"Project {request.project_id[:8]}"

    try:
        project = await project_manager.create_project(
            project_id=request.project_id, name=project_name, user_id=None
        )

        if not project:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create project",
            )

        logger.info(f"Successfully created project {request.project_id}")
        return project

    except Exception as e:
        logger.exception(e)
        logger.error(f"Error creating project {request.project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/{project_id}/integrate-supabase", status_code=status.HTTP_200_OK)
async def integrate_supabase_with_project(
    project_id: str,
) -> dict[str, str]:
    """Integrate Supabase with an existing project.

    Args:
        project_id: The ID of the project to integrate Supabase with

    Returns:
        Dict with success message

    Raises:
        HTTPException: 404 if project doesn't exist
        HTTPException: 500 if integration fails
    """
    # Check project exists
    project_manager = get_project_manager()
    project = await project_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # Derive project root from workspace path and project ID
    project_root = os.path.join(settings.WORKSPACE_PATH, project_id)
    if not os.path.exists(project_root):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project directory for {project_id} not found",
        )

    try:
        # Call the integrate_supabase function
        supabase_util = SupabaseUtil(project_root)
        await supabase_util.integrate_supabase()

        # Create git snapshot
        logger.info(f"Creating git snapshot for project {project_id}")
        commit_message = await create_snapshot(project_root)
        if commit_message:
            logger.info(f"Git snapshot created with message: {commit_message}")
        else:
            logger.info("No changes to commit in git snapshot")

        # Back up the project
        logger.info(f"Backing up project {project_id}")
        await project_manager.backup_project(project_id)
        logger.info("Project backup completed successfully")

        return {
            "message": f"Successfully integrated Supabase with project {project_id}"
        }
    except Exception as e:
        logger.exception(e)
        logger.error(f"Error integrating Supabase with project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/{project_id}/secrets", status_code=status.HTTP_200_OK)
async def set_project_secret(
    project_id: str,
    request: SecretRequest,
) -> dict[str, str]:
    """Add or update a secret in the project's Supabase instance.

    Args:
        project_id: The ID of the project
        request: Secret request containing name and value

    Returns:
        Dict with success message

    Raises:
        HTTPException: 404 if project doesn't exist
        HTTPException: 500 if setting the secret fails
    """
    # Check project exists
    project_manager = get_project_manager()
    project = await project_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    if project_manager.__class__.__name__ == "LocalProjectManager":
        if not settings.USER_SUPABASE_PAT and not settings.LINKED_SUPABASE_PROJECT_ID:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supabase integration is not configured",
            )

    # Derive project root from workspace path and project ID
    project_root = os.path.join(settings.WORKSPACE_PATH, project_id)
    if not os.path.exists(project_root):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project directory for {project_id} not found",
        )

    try:
        # Call the set_secret method
        supabase_util = SupabaseUtil(project_root)
        await supabase_util.set_secret(request.name, request.value)

        logger.info(
            f"Successfully set secret '{request.name}' for project {project_id}"
        )

        return {
            "message": f"Secret '{request.name}' successfully set for project {project_id}"
        }
    except Exception as e:
        logger.exception(e)
        logger.error(f"Error setting secret for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/{project_id}/upload", status_code=status.HTTP_200_OK)
async def upload_assets(
    project_id: str,
    files: List[UploadFile] = File(...),
) -> dict:
    """Upload multiple assets to a project's public directory.

    Args:
        project_id: The ID of the project
        files: List of files to upload

    Returns:
        Dict containing success message and uploaded file information

    Raises:
        HTTPException: If the project doesn't exist or upload fails
    """
    # Verify project exists
    project_manager = get_project_manager()
    project = await project_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # Determine project root and public directory
    project_root = Path(settings.WORKSPACE_PATH) / project_id
    if not project_root.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project directory for {project_id} not found",
        )

    # Ensure public directory exists
    public_dir = project_root / "public"
    public_dir.mkdir(exist_ok=True)

    # Process uploaded files
    uploaded_files = []
    try:
        for file in files:
            filename = file.filename
            if not filename:
                continue

            file_path = public_dir / filename

            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)

            # Create relative path from project root for client reference
            relative_path = f"/public/{filename}"

            uploaded_files.append(
                {
                    "original_name": filename,
                    "saved_name": filename,
                    "path": relative_path,
                    "size": len(content),
                    "content_type": file.content_type,
                }
            )

            logger.info(
                f"Saved file {filename} to project {project_id} (overwrote if existed)"
            )

        logger.info(f"Creating git snapshot for project {project_id}")
        commit_message = await create_snapshot(str(project_root))
        if commit_message:
            logger.info(f"Git snapshot created with message: {commit_message}")
        else:
            logger.info("No changes to commit in git snapshot")

        # Run memory compaction after upload completes
        agent = await get_agent(project_id)
        if agent.message_manager:
            await agent.message_manager.compact_memory()
            logger.info(f"Memory compaction completed for project {project_id}")

        return {
            "message": f"Successfully uploaded {len(uploaded_files)} files to project {project_id}",
            "files": uploaded_files,
        }

    except Exception as e:
        logger.exception(e)
        logger.error(f"Error uploading assets to project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload assets: {str(e)}",
        )


@router.post("/{project_id}/generate-summary", response_model=GenerateSummaryResponse)
async def generate_summary(
    project_id: str,
    request: GenerateSummaryRequest,
    background_tasks: BackgroundTasks,
) -> GenerateSummaryResponse:
    """Generate a project name and description based on the user's first message.

    Args:
        project_id: The ID of the project
        request: Contains the user's message
        background_tasks: FastAPI background tasks for background operations

    Returns:
        Generated name and description for the project

    Raises:
        HTTPException: 404 if project doesn't exist
        HTTPException: 500 if operation fails
    """
    # Check project exists
    project_manager = get_project_manager()
    project = await project_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    try:
        # Generate project name and description
        logger.info(f"Generating summary for project {project_id}")
        summary = await generate_project_summary(request.message)

        # Update index.html title in background
        project_root = os.path.join(settings.WORKSPACE_PATH, project_id)
        background_tasks.add_task(
            _update_project_title, project_root, summary.name, project_id
        )

        logger.info(f"Successfully generated summary for project {project_id}")
        return GenerateSummaryResponse(
            name=summary.name, description=summary.description
        )

    except Exception as e:
        logger.exception(e)
        logger.error(f"Error generating summary for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate project summary: {str(e)}",
        )


@router.post(
    "/{project_id}/migrations",
    response_model=MigrationResponse,
    status_code=status.HTTP_200_OK,
)
async def execute_migration(
    project_id: str,
    migration: MigrationRequest,
) -> MigrationResponse:
    """Execute a SQL migration against the project's Supabase database.

    Args:
        project_id: The ID of the project
        migration: Migration request containing SQL to execute and optional name

    Returns:
        MigrationResponse: Migration execution details including success status and results

    Raises:
        HTTPException: 404 if project doesn't exist
        HTTPException: 400 if SQL is empty or Supabase is not integrated
        HTTPException: 500 if migration execution fails
    """
    # Check project exists
    project_manager = get_project_manager()
    project = await project_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # Derive project root from workspace path and project ID
    project_root = os.path.join(settings.WORKSPACE_PATH, project_id)
    if not os.path.exists(project_root):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project directory for {project_id} not found",
        )

    try:
        # Check if Supabase is integrated with this project
        supabase_util = SupabaseUtil(project_root)
        is_integrated = await supabase_util.is_supabase_integrated()

        if not is_integrated:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supabase is not integrated with this project",
            )

        # Execute the migration
        if not migration.sql.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="SQL cannot be empty",
            )

        raw_result = await supabase_util.deploy_migration(
            migration_sql=migration.sql,
            name=migration.name,
        )

        if not raw_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Migration failed: {raw_result.get('error', 'Unknown error')}",
            )

        logger.info(f"Successfully executed migration for project {project_id}")

        # Run memory compaction after migration completes successfully
        agent = await get_agent(project_id)
        if agent.message_manager:
            await agent.message_manager.compact_memory()
            logger.info(f"Memory compaction completed for project {project_id}")

        # Parse datetime string to datetime object
        timestamp = datetime.fromisoformat(raw_result["timestamp"])

        return MigrationResponse(
            name=raw_result["name"],
            success=raw_result["success"],
            timestamp=timestamp,
            error=raw_result.get("error"),
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(e)
        logger.error(f"Error executing migration for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/{project_id}/paths", response_model=ListProjectPathsResponse)
async def list_project_paths(
    project_id: str,
) -> ListProjectPathsResponse:
    """List all pages/routes in a Vite project.

    Args:
        project_id: The ID of the project

    Returns:
        ListProjectPathsResponse: List of page paths found in the project

    Raises:
        HTTPException: 404 if project doesn't exist or directory not found
        HTTPException: 500 if operation fails
    """
    # Check project exists
    project_manager = get_project_manager()
    project = await project_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # Determine project root path
    project_root = Path(settings.WORKSPACE_PATH) / project_id
    if not project_root.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project directory for {project_id} not found",
        )

    try:
        paths = await find_project_paths(project_root)
        logger.info(f"Found {len(paths)} paths in project {project_id}")

        return ListProjectPathsResponse(paths=paths)

    except Exception as e:
        logger.exception(e)
        logger.error(f"Error listing paths for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list project paths: {str(e)}",
        )


@router.get("/{project_id}/download")
async def download_project(
    project_id: str,
    background_tasks: BackgroundTasks,
) -> FileResponse:
    """Download the source code of a project as a zip file.

    Args:
        project_id: The ID of the project
        background_tasks: FastAPI background tasks for cleanup

    Returns:
        FileResponse: A zip file containing the project source code, respecting .gitignore

    Raises:
        HTTPException: 404 if project doesn't exist or directory not found
        HTTPException: 500 if operation fails
    """
    # Check project exists
    project_manager = get_project_manager()
    project = await project_manager.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )

    # Determine project root path
    project_root = Path(settings.WORKSPACE_PATH) / project_id
    if not project_root.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project directory for {project_id} not found",
        )

    try:
        # Use the utility to create the zip file - it returns a tuple of (zip_path, zip_filename)
        zip_path, zip_filename = await create_project_zip(project_id, project_root)

        background_tasks.add_task(_cleanup_zip_file, zip_path=zip_path)

        # Create and return a FileResponse with the zip file
        return FileResponse(
            path=zip_path, filename=zip_filename, media_type="application/zip"
        )
    except Exception as e:
        logger.exception(e)
        logger.error(f"Error creating download for project {project_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project download: {str(e)}",
        )


def _cleanup_zip_file(zip_path: str) -> None:
    """Clean up the temporary zip file after it has been sent to the client.

    Args:
        zip_path: Path to the temporary zip file
    """
    try:
        if os.path.exists(zip_path):
            os.unlink(zip_path)
            logger.debug(f"Successfully removed temporary zip file: {zip_path}")
    except Exception as e:
        logger.error(f"Error cleaning up temporary zip file {zip_path}: {str(e)}")


async def _update_project_title(project_root: str, title: str, project_id: str) -> None:
    """Update the title in index.html and create a git snapshot.

    Args:
        project_root: Path to the project root
        title: New title for the webpage
        project_id: ID of the project for logging
    """
    index_html_path = os.path.join(project_root, "index.html")

    if not os.path.exists(index_html_path):
        logger.warning(
            f"index.html not found for project {project_id}, title not updated"
        )
        return

    try:
        # Read the current index.html content
        with open(index_html_path, "r") as f:
            content = f.read()

        # Replace the title using regex for more reliable matching with case insensitivity
        pattern = r"<title>(.*?)<\/title>"

        # Check if a title tag exists in the file
        if not re.search(pattern, content, re.IGNORECASE):
            logger.warning(f"No title tag found in index.html for project {project_id}")
            return

        # Replace the title tag content with case insensitivity
        updated_content = re.sub(
            pattern, f"<title>{title}</title>", content, flags=re.IGNORECASE
        )

        # Write the updated content back
        with open(index_html_path, "w") as f:
            f.write(updated_content)

        logger.info(f"Updated index.html title to '{title}' for project {project_id}")

        # Create git snapshot
        commit_message = await create_snapshot(project_root)
        if commit_message:
            logger.info(f"Git snapshot created with message: {commit_message}")
        else:
            logger.info("No changes to commit in git snapshot")

    except Exception as e:
        logger.warning(
            f"Failed to update index.html title for project {project_id}: {str(e)}"
        )
