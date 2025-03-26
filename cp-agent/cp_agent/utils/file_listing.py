import os
import time
from collections import deque
from concurrent.futures import TimeoutError
from pathlib import Path

import pathspec

# Create a PathSpec for directories to ignore
DIRS_TO_IGNORE_SPEC = pathspec.PathSpec.from_lines(
    "gitwildmatch",
    [
        "node_modules/**",
        "__pycache__/**",
        "env/**",
        "venv/**",
        "target/dependency/**",
        "build/dependencies/**",
        "dist/**",
        "out/**",
        "bundle/**",
        "vendor/**",
        "tmp/**",
        "temp/**",
        "deps/**",
        "pkg/**",
        "Pods/**",
        ".*/**",
    ],
)


def are_paths_equal(path1: str, path2: str) -> bool:
    """Compare two paths for equality, accounting for different path separators."""
    return os.path.normpath(path1) == os.path.normpath(path2)


def get_gitignore_spec(dir_path: str) -> pathspec.PathSpec | None:
    """Create a PathSpec from .gitignore if it exists."""
    gitignore_path = os.path.join(dir_path, ".gitignore")
    try:
        if os.path.exists(gitignore_path):
            with open(gitignore_path, "r") as f:
                return pathspec.PathSpec.from_lines("gitwildmatch", f.readlines())
    except Exception as e:
        print(f"Error reading .gitignore: {e}")
    return None


async def list_files(
    dir_path: str, recursive: bool = False, limit: int = 200
) -> tuple[list[str], bool]:
    """
    List files in a directory with gitignore support and safety checks.

    Args:
        dir_path: Directory path to list files from
        recursive: Whether to list files recursively
        limit: Maximum number of files to return

    Returns:
        Tuple of (list of file paths, boolean indicating if limit was reached)
    """
    absolute_path = str(Path(dir_path).resolve())

    # Protect against listing root directory
    root = "/" if os.name != "nt" else Path(absolute_path).drive + "\\"
    if are_paths_equal(absolute_path, root):
        return [root], False

    # Protect against listing home directory
    home_dir = str(Path.home())
    if are_paths_equal(absolute_path, home_dir):
        return [home_dir], False

    # Get gitignore spec if recursive
    gitignore_spec = get_gitignore_spec(absolute_path) if recursive else None

    try:
        if recursive:
            return await list_files_recursive(absolute_path, limit, gitignore_spec)
        else:
            return list_files_single_level(absolute_path, limit)
    except TimeoutError:
        print("Warning: File listing timed out, returning partial results")
        return [], True
    except Exception as e:
        print(f"Error listing files in {absolute_path}: {e}")
        return [], False


def list_files_single_level(dir_path: str, limit: int) -> tuple[list[str], bool]:
    """List files in a single directory level."""
    try:
        base_path = Path(dir_path)
        paths = []

        with os.scandir(dir_path) as entries:
            for entry in entries:
                path = Path(entry.path)
                relative_path = str(path.relative_to(base_path))
                if entry.is_dir():
                    paths.append(f"{relative_path}/")
                else:
                    paths.append(relative_path)

        reached_limit = len(paths) >= limit
        return paths[:limit], reached_limit
    except Exception as e:
        print(f"Error listing files in {dir_path}: {e}")
        return [], False


def should_ignore(path: str, gitignore_spec: pathspec.PathSpec | None) -> bool:
    """Check if a path should be ignored based on gitignore patterns."""
    if gitignore_spec and gitignore_spec.match_file(path):
        return True
    return DIRS_TO_IGNORE_SPEC.match_file(path)


async def list_files_recursive(
    dir_path: str, limit: int, gitignore_spec: pathspec.PathSpec | None
) -> tuple[list[str], bool]:
    """
    List files recursively using breadth-first traversal with timeout and gitignore support.
    """
    base_path = Path(dir_path)
    start_time = time.time()
    TIMEOUT = 10  # seconds
    results: list[str] = []
    queue = deque([(base_path, "")])  # (full_path, relative_path)

    while queue and len(results) < limit:
        if time.time() - start_time > TIMEOUT:
            raise TimeoutError("File listing timeout")

        # Process all directories at the current level
        level_size = len(queue)
        for _ in range(level_size):
            if len(results) >= limit:
                break

            current_path, rel_path = queue.popleft()

            try:
                entries = list(os.scandir(current_path))
                dirs = []
                files = []

                # Check if directory should be included in results
                if current_path != base_path:
                    dir_path = rel_path + "/"
                    if not should_ignore(dir_path, gitignore_spec):
                        if len(results) < limit and dir_path not in results:
                            results.append(dir_path)

                # Process entries at current directory level
                for entry in entries:
                    path = Path(entry.path)
                    relative_path = str(path.relative_to(base_path))

                    # Format path for gitignore pattern matching
                    check_path = (
                        relative_path + "/" if entry.is_dir() else relative_path
                    )
                    if should_ignore(check_path, gitignore_spec):
                        continue

                    if entry.is_dir():
                        dirs.append((path, relative_path))
                    else:
                        files.append(relative_path)

                # Ensure consistent ordering in results
                dirs.sort(key=lambda x: x[1])
                files.sort()

                # Process files before descending into subdirectories
                for file_path in files:
                    if len(results) >= limit:
                        break
                    if file_path not in results:
                        results.append(file_path)

                # Add subdirectories to processing queue
                queue.extend(dirs)

            except Exception as e:
                print(f"Error processing {current_path}: {e}")
                continue

    return sorted(results[:limit]), len(results) >= limit
