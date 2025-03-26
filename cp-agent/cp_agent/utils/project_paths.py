"""Utility functions for finding project paths and routes."""

import re
from pathlib import Path
from typing import List

from loguru import logger


async def find_project_paths(project_root: Path) -> List[str]:
    """Find all valid page/routes paths in a project.

    This function uses router configuration files parsing to identify paths,
    while filtering out parameterized routes.

    Args:
        project_root: Root directory of the project

    Returns:
        List of valid, non-parameterized paths in the project
    """
    # Check if project root exists
    if not project_root.exists() or not project_root.is_dir():
        logger.warning(
            f"Project root {project_root} does not exist or is not a directory"
        )
        return ["/"]

    # Find valid paths from router files
    paths = _find_router_based_paths(project_root)

    # Add root path if not already present
    if "/" not in paths:
        paths.append("/")

    # Remove duplicates and sort for consistent output
    paths = sorted(list(set(paths)))

    return paths


def _find_router_based_paths(project_root: Path) -> List[str]:
    """Find non-parameterized paths from router configuration files.

    Args:
        project_root: Root directory of the project

    Returns:
        List of valid, non-parameterized paths in the project
    """
    non_parameterized_paths = []

    # Common extensions for web pages
    page_extensions = [".js", ".jsx", ".ts", ".tsx", ".vue", ".svelte"]

    # Router file patterns to search for
    file_patterns = ["App", "app", "main", "index", "router", "routes"]

    # Find all potential router definition files
    router_files: List[Path] = []

    def find_files_with_pattern(pattern: str, ext: str) -> List[Path]:
        """Helper function to find files matching pattern with extension, excluding node_modules."""
        return [
            p
            for p in project_root.rglob(f"{pattern}{ext}")
            if "node_modules" not in p.parts
        ]

    # Collect all router files
    for pattern in file_patterns:
        for ext in page_extensions:
            router_files.extend(find_files_with_pattern(pattern, ext))

    # Process router files to extract non-parameterized routes
    for file_path in router_files:
        try:
            if file_path.exists():
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    logger.debug(f"Processing router file: {file_path}")

                    # Find Route components in the file
                    route_elements = re.findall(r"<Route\s+([^>]*?)(?:/>|>)", content)

                    for route_attrs in route_elements:
                        # Extract the path attribute value
                        path_match = re.search(r'path=(["\'])(.*?)\1', route_attrs)

                        if not path_match:
                            continue

                        path = path_match.group(2).strip()

                        # Only add non-parameterized routes
                        if not any(
                            param_marker in path for param_marker in [":", "*", "{"]
                        ):
                            if path:
                                # Normalize path to start with / and not end with / (except root)
                                if not path.startswith("/"):
                                    path = "/" + path

                                if len(path) > 1:
                                    path = path.rstrip("/")

                                if path and path not in non_parameterized_paths:
                                    non_parameterized_paths.append(path)

        except Exception as e:
            logger.warning(f"Error processing router file {file_path}: {str(e)}")

    return non_parameterized_paths
