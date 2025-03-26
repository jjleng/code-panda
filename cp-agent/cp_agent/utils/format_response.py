"""Response formatting utilities for agent tools and messages."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from cp_agent.utils.message_formats import (
    MessageContent,
    MessagePart,
    create_image_block,
    create_text_block,
)


@dataclass
class ToolResponse:
    """Container for tool operation results with role and content."""

    role: str = "user"
    content: MessageContent = ""

    @staticmethod
    def create_text_message(text: str, role: str = "user") -> ToolResponse:
        """Create a text-only message."""
        return ToolResponse(role=role, content=text)

    @staticmethod
    def create_multimodal_message(
        text: str, images: list[str], role: str = "user"
    ) -> ToolResponse:
        """Create a message with both text and images.

        Args:
            text: The text content
            images: List of image paths or base64 strings
            role: Message role (default: "user")
        """
        message_parts: list[MessagePart] = []
        message_parts.append(create_text_block(text))

        for img in images:
            message_parts.append(create_image_block(img))

        return ToolResponse(role=role, content=message_parts)


def tool_error(error: str, tool_name: str = "", path: str = "") -> str:
    """Format response for a failed tool operation.

    Error messages should be concise and actionable. When tools fail, the agent should
    understand what went wrong and how to fix it in subsequent attempts.
    """
    prefix = "Error"
    if tool_name:
        if path:
            prefix = f"Error executing {tool_name} for '{path}'"
        else:
            prefix = f"Error executing {tool_name}"

    return f"{prefix}:\n<error-details>\n{error}\n</error-details>"


def missing_tool_parameter_error(param_name: str, tool_name: str) -> str:
    """Format error for missing required tool parameter."""
    return (
        f"Error executing {tool_name}:\n<error-details>\n"
        f"Missing required parameter '{param_name}'. Provide the parameter and retry.\n"
        f"</error-details>"
    )


def invalid_tool_parameter_error(tool_name: str, param_name: str, message: str) -> str:
    """Format error for invalid tool parameter."""
    return (
        f"Error executing {tool_name}:\n<error-details>\n"
        f"Invalid value for '{param_name}': {message}\n"
        f"</error-details>"
    )


def tool_result(text: str, images: Optional[list[str]] = None) -> ToolResponse:
    """Format successful tool execution result with optional images.

    Args:
        text: The text content of the message
        images: Optional list of image paths or base64 strings

    Returns:
        ToolResponse object with formatted content
    """
    if images:
        return ToolResponse.create_multimodal_message(text, images)
    return ToolResponse.create_text_message(text)


def format_files_list(base_path: str, files: list[str], hit_limit: bool = False) -> str:
    """Format directory listing with optional truncation notice.

    Args:
        base_path: The absolute path that all files are relative to
        files: List of absolute file paths
        hit_limit: Whether the file list was truncated

    Returns:
        A formatted string of relative file paths, sorted with directories first
    """
    if not files or (len(files) == 1 and not files[0]):
        return "No files found."

    # Convert absolute paths to relative and ensure forward slashes
    relative_paths = [
        path.replace("\\", "/")  # Convert Windows backslashes if any
        for path in [
            path[len(base_path) :].lstrip("/") if path.startswith(base_path) else path
            for path in files
        ]
    ]

    # Sort files so directories are listed before their contents
    sorted_paths = sorted(
        relative_paths,
        key=lambda p: (
            # Split path into components
            tuple(
                # For each component, create a tuple of:
                # (is_file_at_this_level, normalized_component_name)
                # is_file_at_this_level helps sort directories before files
                (i + 1 == len(p.split("/")), component.lower())
                for i, component in enumerate(p.split("/"))
            )
        ),
    )

    file_list = "\n".join(sorted_paths)

    if hit_limit:
        return (
            f"{file_list}\n\n"
            "(File list truncated. Use list_files on specific subdirectories if you need to explore further.)"
        )
    return file_list


def too_many_mistakes() -> str:
    """Format response when agent makes too many consecutive mistakes."""
    return (
        "[ERROR] Multiple tool execution failures detected.\n\n"
        "Review the tool usage strategy and retry:\n\n"
        f"{tool_use_instructions_reminder()}"
    )


def tool_use_instructions_reminder() -> str:
    """Instructions for efficient tool usage with parallel execution."""
    return (
        "# Tool Usage Strategy\n\n"
        "1. Read Operations - Always Batch\n"
        "- Gather ALL needed information in one turn\n"
        "- Group ALL reads, searches, listings together\n"
        "- Process results before any writes\n\n"
        "2. Write Operations - Based on Confidence\n"
        "A. Batch Together When:\n"
        "- You understand all required changes\n"
        "- You can write all changes correctly in one turn\n"
        "- Changes form a logically complete unit\n\n"
        "B. Execute Sequentially When:\n"
        "- Changes depend on user feedback\n"
        "- You need to verify intermediate state\n"
        "- You're uncertain about combined effects\n\n"
        "Tool uses should follow this pattern:\n\n"
        "<thinking>\n"
        "First gathering all required information...\n"
        "</thinking>\n"
        "[Group read operations]\n"
        "[Tool Response]\n\n"
        "<thinking>\n"
        "Making all logically related changes...\n"
        "</thinking>\n"
        "[Write operations based on confidence]\n"
        "[Tool Response]"
    )
