"""Utilities for project download functionality."""

import os
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Tuple

import pathspec
from loguru import logger


def should_ignore(
    rel_path: str,
    gitignore_spec: Optional[pathspec.PathSpec],
    default_ignore_spec: pathspec.PathSpec,
) -> bool:
    """Check if a file should be ignored based on gitignore patterns.

    Args:
        rel_path: Relative path from project root
        gitignore_spec: PathSpec from project's .gitignore
        default_ignore_spec: Default PathSpec with common patterns

    Returns:
        True if the file should be ignored, False otherwise
    """
    # Always check against default ignore patterns
    if default_ignore_spec.match_file(rel_path):
        return True

    # Check against project's .gitignore if available
    if gitignore_spec and gitignore_spec.match_file(rel_path):
        return True

    return False


async def create_project_zip(project_id: str, project_root: Path) -> Tuple[str, str]:
    """Create a zip file of a project respecting .gitignore.

    Args:
        project_id: The ID of the project
        project_root: Path to the project root directory

    Returns:
        Tuple containing:
            - Path to the created zip file
            - Filename for the zip file

    Raises:
        Exception: If zip creation fails
    """
    # Create a temporary directory for the zip file
    temp_dir = tempfile.mkdtemp()

    try:
        # Create zip filename
        zip_filename = f"project-{project_id}.zip"
        zip_path = os.path.join(temp_dir, zip_filename)

        # Load gitignore patterns if they exist
        gitignore_path = project_root / ".gitignore"
        gitignore_spec = None

        if gitignore_path.exists():
            with open(gitignore_path, "r") as f:
                gitignore_spec = pathspec.PathSpec.from_lines(
                    "gitwildmatch", f.readlines()
                )

        # Standard patterns to exclude from the zip file
        default_ignore_patterns = [
            "node_modules/**",
            ".git/**",
            "**/.DS_Store",
            "**/__pycache__/**",
            "**/*.pyc",
            "**/*.pyo",
            "**/env/**",
            "**/venv/**",
            "**/.env",
            "**/*.log",
            "**/dist/**",
            "**/build/**",
        ]

        default_ignore_spec = pathspec.PathSpec.from_lines(
            "gitwildmatch", default_ignore_patterns
        )

        # Create a zip file with filtered contents
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(project_root):
                # Convert absolute paths to project-relative paths
                rel_root = os.path.relpath(root, project_root)
                rel_root = "" if rel_root == "." else rel_root

                # Filter out directories that match ignore patterns
                dirs[:] = [
                    d
                    for d in dirs
                    if not should_ignore(
                        os.path.join(rel_root, d) + "/",
                        gitignore_spec,
                        default_ignore_spec,
                    )
                ]

                # Add non-ignored files to zip
                for file in files:
                    rel_path = os.path.join(rel_root, file)
                    if not should_ignore(rel_path, gitignore_spec, default_ignore_spec):
                        # Add file to zip with relative path
                        abs_path = os.path.join(root, file)
                        zip_path_in_archive = os.path.join(project_id, rel_path)
                        zipf.write(abs_path, zip_path_in_archive)

        logger.info(f"Created zip file for project {project_id} at {zip_path}")
        return zip_path, zip_filename

    except Exception as e:
        # Clean up temporary directory if an error occurs
        if os.path.exists(temp_dir):
            import shutil

            shutil.rmtree(temp_dir)

        logger.exception(e)
        logger.error(f"Error creating zip for project {project_id}: {str(e)}")
        raise
