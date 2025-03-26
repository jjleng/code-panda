"""Module for searching text patterns in files with context."""

import os
import re
from pathlib import Path
from typing import Optional, TypedDict, Union


class MatchContext(TypedDict):
    """Type for representing a search match with its context."""

    line_num: int
    before: str
    match: str
    after: str


async def search_files(
    base_path: Union[str, Path],
    regex: str,
    file_pattern: Optional[str] = None,
    max_results: int = 300,
) -> tuple[dict[str, list[MatchContext]], int]:
    """Find text patterns in files with context lines and optional file type filtering.

    Args:
        base_path: Base directory path to search in
        regex: Regular expression pattern to search for
        file_pattern: Optional glob pattern to filter files (e.g. "*.py")
        max_results: Maximum number of matches to return

    Returns:
        Tuple of (matches grouped by file, total match count)
    """
    path = Path(base_path)
    if not path.exists():
        raise FileNotFoundError(f"Path not found: {path}")

    pattern = re.compile(regex)
    matches: dict[str, list[MatchContext]] = {}
    total_matches = 0

    def glob_to_regex(glob_pattern: str) -> str:
        """Convert glob pattern to regex pattern."""
        # Escape all special regex characters first
        pattern = re.escape(glob_pattern)
        # Convert glob * to regex .*
        pattern = pattern.replace("\\*", ".*")
        # Convert glob ? to regex .
        pattern = pattern.replace("\\?", ".")
        # Ensure pattern matches entire string
        return f"^{pattern}$"

    file_regex = re.compile(glob_to_regex(file_pattern)) if file_pattern else None

    for root, _, files in os.walk(path):
        if total_matches >= max_results:
            break

        for file in files:
            if file_regex and not file_regex.match(file):
                continue

            try:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(base_path)

                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines):
                        if pattern.search(line):
                            # Get context lines (1 line before and after)
                            before_ctx = lines[i - 1] if i > 0 else ""
                            after_ctx = lines[i + 1] if i < len(lines) - 1 else ""

                            if str(rel_path) not in matches:
                                matches[str(rel_path)] = []

                            matches[str(rel_path)].append(
                                {
                                    "line_num": i + 1,
                                    "before": before_ctx.rstrip(),
                                    "match": line.rstrip(),
                                    "after": after_ctx.rstrip(),
                                }
                            )
                            total_matches += 1

                            if total_matches >= max_results:
                                break
            except (UnicodeDecodeError, IOError):
                continue  # Skip binary or unreadable files

    return matches, total_matches


def format_search_results(
    matches: dict[str, list[MatchContext]], total_matches: int, max_results: int
) -> str:
    """Format search results into a readable string with file paths and context.

    Args:
        matches: Dictionary of matches grouped by file
        total_matches: Total number of matches found
        max_results: Maximum number of results allowed

    Returns:
        Formatted string representation of search results
    """
    output = []

    if total_matches >= max_results:
        output.append(
            f"Showing first {max_results} of {max_results}+ results. Use a more specific search if necessary.\n"
        )
    else:
        result_str = "1 result" if total_matches == 1 else f"{total_matches} results"
        output.append(f"Found {result_str}.\n")

    for file_path, file_matches in matches.items():
        output.append(f"{file_path}")
        output.append("│----")

        for match in file_matches:
            if match["before"]:
                output.append(f"│{match['before']}")
            output.append(f"│{match['match']}")
            if match["after"]:
                output.append(f"│{match['after']}")
            output.append("│----")

        output.append("")

    return "\n".join(output).strip()
