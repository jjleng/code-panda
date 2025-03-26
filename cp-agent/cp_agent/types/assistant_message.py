"""Definitions and utilities for handling assistant messages."""

import uuid
from enum import Enum
from typing import Any, Dict, Iterator, List, Literal, Optional, TypedDict, Union

from cp_agent.types.events import TextEvent, ThinkingEvent, ToolEvent


class ToolParamName(str, Enum):
    """Parameter names available for tool usage."""

    PATH = "path"
    CONTENT = "content"
    DIFF = "diff"
    RECURSIVE = "recursive"
    REGEX = "regex"
    FILE_PATTERN = "file-pattern"
    SOURCE = "source"
    DESTINATION = "destination"
    NAME = "name"
    QUERY = "query"
    QUESTION = "question"


class ToolUseName(str, Enum):
    """Names of available tools that can be used by the assistant."""

    READ_FILE = "read-file"
    WRITE_TO_FILE = "write-to-file"
    APPLY_DIFF = "apply-diff"
    SEARCH_FILES = "search-files"
    LIST_FILES = "list-files"
    ASK_FOLLOWUP_QUESTION = "ask-followup-question"
    DELETE_FILE = "delete-file"
    RENAME_FILE = "rename-file"
    ADD_DEPENDENCY = "add-dependency"
    KB_SEARCH = "kb-search"


class TextContent(TypedDict):
    """Type definition for text content in assistant messages."""

    type: Literal["text"]
    content: str
    partial: bool


class ToolUse(TypedDict):
    """Type definition for tool usage in assistant messages."""

    type: Literal["tool_use"]
    name: str
    params: Dict[str, str]
    partial: bool


AssistantMessageContent = Union[TextContent, ToolUse]


class TextChunk(TypedDict):
    """Type definition for a chunk of text content in streaming responses."""

    type: Literal["text", "thinking"]
    content: str


def parse_assistant_message(assistant_message: str) -> List[AssistantMessageContent]:
    """Parse assistant message to extract text content and tool uses.

    Args:
        assistant_message: The message from the assistant to parse

    Returns:
        List of content blocks (text content or tool uses)
    """
    content_blocks: List[AssistantMessageContent] = []
    current_text_content: Optional[TextContent] = None
    current_text_content_start_index = 0
    current_tool_use: Optional[ToolUse] = None
    current_tool_use_start_index = 0
    current_param_name: Optional[str] = None
    current_param_value_start_index = 0
    accumulator = ""

    for i, char in enumerate(assistant_message):
        accumulator += char

        # Handle parameter value accumulation
        if current_tool_use and current_param_name:
            current_param_value = accumulator[current_param_value_start_index:]
            param_closing_tag = f"</{current_param_name}>"
            if current_param_value.endswith(param_closing_tag):
                # End of parameter value
                current_tool_use["params"][current_param_name] = current_param_value[
                    : -len(param_closing_tag)
                ].strip()
                current_param_name = None
                continue
            continue

        # Handle tool use processing
        if current_tool_use:
            current_tool_value = accumulator[current_tool_use_start_index:]
            tool_use_closing_tag = f"</{current_tool_use['name']}>"
            if current_tool_value.endswith(tool_use_closing_tag):
                # End of tool use
                current_tool_use["partial"] = False
                content_blocks.append(current_tool_use)
                current_tool_use = None
                continue
            else:
                # Check for new parameter start
                for param_name in ToolParamName:
                    param_opening_tag = f"<{param_name.value}>"
                    if accumulator.endswith(param_opening_tag):
                        current_param_name = param_name.value
                        current_param_value_start_index = len(accumulator)
                        break

                # Special case for write_to_file content parameter
                if current_tool_use[
                    "name"
                ] == ToolUseName.WRITE_TO_FILE.value and accumulator.endswith(
                    f"</{ToolParamName.CONTENT.value}>"
                ):
                    tool_content = accumulator[current_tool_use_start_index:]
                    content_start_tag = f"<{ToolParamName.CONTENT.value}>"
                    content_end_tag = f"</{ToolParamName.CONTENT.value}>"
                    content_start_index = tool_content.find(content_start_tag) + len(
                        content_start_tag
                    )
                    content_end_index = tool_content.rindex(content_end_tag)
                    if (
                        content_start_index != -1
                        and content_end_index != -1
                        and content_end_index > content_start_index
                    ):
                        current_tool_use["params"][ToolParamName.CONTENT.value] = (
                            tool_content[content_start_index:content_end_index].strip()
                        )
                continue

        # Check for new tool use start
        did_start_tool_use = False
        for tool_name in ToolUseName:
            tool_opening_tag = f"<{tool_name.value}>"
            if accumulator.endswith(tool_opening_tag):
                current_tool_use = {
                    "type": "tool_use",
                    "name": tool_name.value,
                    "params": {},
                    "partial": True,
                }
                current_tool_use_start_index = len(accumulator)
                if current_text_content:
                    current_text_content["partial"] = False
                    # Remove partially accumulated tool use tag
                    current_text_content["content"] = current_text_content["content"][
                        : -len(tool_opening_tag[:-1])
                    ].strip()
                    content_blocks.append(current_text_content)
                    current_text_content = None
                did_start_tool_use = True
                break

        if not did_start_tool_use:
            # Handle text content only if there's actual content
            if current_text_content is None:
                current_text_content_start_index = i
                current_text_content = {
                    "type": "text",
                    "content": accumulator[current_text_content_start_index:].strip(),
                    "partial": True,
                }
            else:
                current_text_content["content"] = accumulator[
                    current_text_content_start_index:
                ].strip()

    # Handle partial tool use
    if current_tool_use:
        if current_param_name:
            current_tool_use["params"][current_param_name] = accumulator[
                current_param_value_start_index:
            ].strip()
        content_blocks.append(current_tool_use)

    # Handle partial text content - always include it like TypeScript does
    elif current_text_content:
        content_blocks.append(current_text_content)

    return content_blocks


# This class is deprecated and should not be used in new code
class StreamingAssistantMessageParser:
    def __init__(self) -> None:
        """Initialize parser state."""
        self.reset_state()

    def reset_state(self) -> None:
        """Reset all internal state variables."""
        self.in_thinking_block = False
        self.in_tool_block = False
        self.partial_tag = ""
        self.thinking_content = ""
        self.tool_name = None

    def _detect_tag_start(self, content: str) -> tuple[str, str]:
        """Detect potential tag start and split content accordingly.

        Args:
            content: The content to analyze

        Returns:
            A tuple of (content_before_tag, potential_tag)
        """
        last_tag_start = content.rfind("<")
        if last_tag_start == -1:
            return content, ""

        # Check if this could be the start of a tag
        potential_tag = content[last_tag_start:]
        tag_content = potential_tag[1:].lower()

        # Check if it could be a thinking tag or tool tag
        if "thinking".startswith(tag_content) or any(
            tool_name.value.startswith(tag_content) for tool_name in ToolUseName
        ):
            return content[:last_tag_start], potential_tag

        return content, ""

    def __call__(self, chunk: Optional[str]) -> Iterator[TextChunk]:
        """Process a chunk of streaming content.

        Args:
            chunk: A chunk of text from the streaming response, or None to signal end of stream

        Yields:
            TextChunk objects containing parsed content
        """
        if chunk is None:
            # Process any remaining content using the same logic as regular chunks
            if self.partial_tag:
                # Treat remaining partial tag as regular content for final processing
                for result in self(self.partial_tag):
                    yield result
                self.partial_tag = ""

            # Yield any remaining thinking content
            if self.in_thinking_block and self.thinking_content:
                # Look for closing tag in thinking content
                if "</thinking>" in self.thinking_content:
                    idx = self.thinking_content.index("</thinking>")
                    content = self.thinking_content[:idx]
                    if content:
                        yield TextChunk(type="thinking", content=content)
                    remaining = self.thinking_content[idx + len("</thinking>") :]
                    if remaining:
                        yield TextChunk(type="text", content=remaining)
                else:
                    yield TextChunk(type="thinking", content=self.thinking_content)

            self.reset_state()
            return

        current_content = self.partial_tag + chunk
        self.partial_tag = ""

        # Split content and potential tag
        clean_content, partial = self._detect_tag_start(current_content)
        if partial:
            self.partial_tag = partial
            current_content = clean_content

        while current_content:
            # Handle tool use tags
            for tool_name in ToolUseName:
                opening_tag = f"<{tool_name.value}>"
                closing_tag = f"</{tool_name.value}>"

                if opening_tag in current_content:
                    idx = current_content.index(opening_tag)
                    # Yield text before tool use
                    text_before = current_content[:idx]
                    if text_before and not self.in_tool_block:
                        yield TextChunk(type="text", content=text_before)
                    self.in_tool_block = True
                    current_content = current_content[idx + len(opening_tag) :]
                    break

                if closing_tag in current_content and self.in_tool_block:
                    idx = current_content.index(closing_tag)
                    self.in_tool_block = False
                    current_content = current_content[idx + len(closing_tag) :]
                    break
            else:
                # Handle thinking tags
                if "<thinking>" in current_content:
                    idx = current_content.index("<thinking>")
                    text_before = current_content[:idx]
                    if text_before and not self.in_tool_block:
                        yield TextChunk(type="text", content=text_before)
                    self.in_thinking_block = True
                    current_content = current_content[idx + len("<thinking>") :]
                    continue

                if "</thinking>" in current_content and self.in_thinking_block:
                    idx = current_content.index("</thinking>")
                    thinking_content = self.thinking_content + current_content[:idx]
                    if thinking_content:
                        yield TextChunk(type="thinking", content=thinking_content)
                    self.in_thinking_block = False
                    self.thinking_content = ""
                    current_content = current_content[idx + len("</thinking>") :]
                    continue

                # If in tool block, skip the content
                if self.in_tool_block:
                    break

                # If in thinking block, accumulate content
                if self.in_thinking_block:
                    self.thinking_content += current_content
                    break

                # No more tags, yield remaining content
                if current_content and not self.in_tool_block:
                    yield TextChunk(type="text", content=current_content)
                current_content = ""


class AggressiveStreamingAssistantMessageParser:
    """Parses assistant messages aggressively, emitting events as soon as possible.

    This parser is designed to extract tools and content with minimal latency,
    which is useful for providing real-time feedback during streaming responses.
    """

    current_tool_id: Optional[str]

    def __init__(self) -> None:
        """Initialize parser state."""
        self.reset_state()

    def reset_state(self) -> None:
        """Reset all internal state variables to their default values."""
        self.in_thinking_block = False
        self.in_tool_block = False
        self.current_tool: Optional[dict[str, Any]] = None
        self.current_param_name: Optional[str] = None
        self.partial_tag = ""
        self.partial_param = ""
        self.current_params: dict[str, str] = {}
        self.current_tool_id = None
        self.thinking_buffer = ""  # Buffer for thinking content
        self.text_buffer = ""  # Buffer for regular text content
        self.accumulating_tag = False
        self.accumulated_tag = ""

    def _flush_buffers(self) -> Iterator[Union[TextEvent, ThinkingEvent]]:
        """Flush any buffered content and emit appropriate events.

        Yields:
            Events for any accumulated text or thinking content
        """
        if self.thinking_buffer and self.in_thinking_block:
            yield ThinkingEvent(text=self.thinking_buffer)
            self.thinking_buffer = ""
        elif self.text_buffer and not self.in_tool_block and not self.in_thinking_block:
            yield TextEvent(text=self.text_buffer)
            self.text_buffer = ""

    def _detect_possible_tag(
        self, tag: str
    ) -> tuple[Optional[str], Optional[str], Optional[bool]]:
        """
        Detect if accumulated tag matches a tool or parameter tag.

        Args:
            tag: The tag string to analyze

        Returns:
            A tuple of (tool_name, param_name, is_closing_tag)
        """
        tag = tag.lstrip("<").rstrip(">")
        is_closing = tag.startswith("/")
        if is_closing:
            tag = tag[1:]

        # Check tool names
        for tool in ToolUseName:
            if tool.value == tag:
                return tool.value, None, is_closing
            if tool.value.startswith(tag):
                return None, None, is_closing  # Partial tool match

        # Check parameter names
        for param in ToolParamName:
            if param.value == tag:
                return None, param.value, is_closing
            if param.value.startswith(tag):
                return None, None, is_closing  # Partial param match

        # Handle thinking tag
        if tag == "thinking":
            return "thinking", None, is_closing
        if "thinking".startswith(tag):
            return None, None, is_closing  # Partial thinking match

        # Not a recognized tag
        return None, None, None

    def __call__(
        self, chunk: Optional[str]
    ) -> Iterator[Union[TextEvent, ThinkingEvent, ToolEvent]]:
        """Process a chunk of streaming content and emit appropriate events.

        Args:
            chunk: A chunk of text from the streaming response, or None to signal end of stream

        Yields:
            Events (TextEvent, ThinkingEvent, or ToolEvent) based on the parsed content
        """
        if chunk is None:
            # Clean up state and flush buffers
            yield from self._flush_buffers()
            self.reset_state()
            return

        # Process any remaining partial tag first
        content = self.partial_tag + chunk
        self.partial_tag = ""

        while content:
            if self.accumulating_tag:
                self.accumulated_tag += content[0]
                tool_name, param_name, is_closing = self._detect_possible_tag(
                    self.accumulated_tag
                )

                if self.accumulated_tag.endswith(">"):
                    # Not a recognized tag, treat as regular text or parameter content
                    if tool_name is None and param_name is None:
                        if self.current_param_name:
                            self.partial_param += self.accumulated_tag
                        elif self.in_thinking_block:
                            self.thinking_buffer += self.accumulated_tag
                        elif not self.in_tool_block:
                            self.text_buffer += self.accumulated_tag
                        self.accumulating_tag = False
                        self.accumulated_tag = ""
                        content = content[1:]
                        continue

                    # Complete recognized tag found
                    if tool_name == "thinking":
                        if not is_closing:
                            yield from self._flush_buffers()
                            self.in_thinking_block = True
                        else:
                            yield from self._flush_buffers()
                            self.in_thinking_block = False
                    elif tool_name:
                        if not is_closing:
                            yield from self._flush_buffers()
                            self.in_tool_block = True
                            self.current_tool = {"name": tool_name, "params": {}}
                            self.current_tool_id = str(uuid.uuid4())
                            yield ToolEvent(
                                tool_name=tool_name,
                                tool_id=self.current_tool_id,
                                status="started",
                                params=None,
                            )
                        elif (
                            self.in_tool_block
                            and self.current_tool
                            and self.current_tool_id
                        ):
                            yield ToolEvent(
                                tool_name=self.current_tool["name"],
                                tool_id=self.current_tool_id,
                                status="executing",
                                params=self.current_params,
                            )
                            self.in_tool_block = False
                            self.current_tool = None
                            self.current_params = {}
                    elif param_name and self.in_tool_block:
                        if not is_closing:
                            self.current_param_name = param_name
                            self.partial_param = ""
                        elif self.current_param_name:
                            self.current_params[self.current_param_name] = (
                                self.partial_param
                            )
                            if self.current_tool and self.current_tool_id:
                                yield ToolEvent(
                                    tool_name=self.current_tool["name"],
                                    tool_id=self.current_tool_id,
                                    status="partial",
                                    params=self.current_params.copy(),
                                )
                            self.current_param_name = None

                    self.accumulating_tag = False
                    self.accumulated_tag = ""
                content = content[1:]
                continue

            if content.startswith("<"):
                self.accumulating_tag = True
                self.accumulated_tag = "<"
                content = content[1:]
                continue

            # Handle parameter content
            if self.current_param_name:
                self.partial_param += content[0]
                content = content[1:]
                continue

            # Handle regular content
            if self.in_thinking_block:
                self.thinking_buffer += content[0]
            elif not self.in_tool_block:
                self.text_buffer += content[0]
            content = content[1:]

        # Flush buffers at end of chunk
        yield from self._flush_buffers()
