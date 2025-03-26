"""Utilities for reading file contents with optional line number formatting."""

from pathlib import Path


def read_file_content(file_path: str, add_line_numbers: bool = True) -> str:
    """
    Read and format file contents with optional line numbers.

    Args:
        file_path: Path to the file to read
        add_line_numbers: Whether to prefix lines with line numbers (default: True)

    Returns:
        File contents as a string, optionally with line numbers
    """
    try:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        if add_line_numbers:
            # Add line numbers to content
            numbered_lines = [f"{i+1} | {line}" for i, line in enumerate(lines)]
            return "".join(numbered_lines)
        else:
            # Return raw content without line numbers
            return "".join(lines)

    except UnicodeDecodeError:
        return f"Error: File {file_path} appears to be a binary file"
    except Exception as e:
        return f"Error reading file {file_path}: {str(e)}"
