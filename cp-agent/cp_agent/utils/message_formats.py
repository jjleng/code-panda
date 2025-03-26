"""Message handling utilities shared between agents."""

from __future__ import annotations

from base64 import b64encode
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional, TypedDict


class ImageUrl(TypedDict):
    url: str


class ImageBlock(TypedDict):
    type: str
    image_url: ImageUrl


class TextBlock(TypedDict):
    type: str
    text: str


MessagePart = TextBlock | ImageBlock
MessageContent = str | list[MessagePart]


@dataclass
class Message:
    """Message in agent conversation with multimodal support."""

    content: MessageContent
    role: str  # 'user' or 'assistant'
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Attachment:
    """Represents a file attachment in a message."""

    url: str
    type: Literal["image", "pdf", "other"]
    base64: Optional[str] = None
    filename: Optional[str] = None
    mime_type: Optional[str] = None
    size: Optional[int] = None


def create_text_block(text: str) -> TextBlock:
    """Create a text block for message content."""
    return {"type": "text", "text": text}


def create_image_block(image_url: str) -> ImageBlock:
    """Create an image block for message content."""
    return {"type": "image_url", "image_url": {"url": image_url}}


def create_message_content(text: str, attachments: list[Attachment]) -> MessageContent:
    """Convert text and attachments into MessageContent format."""
    if not attachments:
        return text

    content: list[MessagePart] = []

    if text:
        content.append(create_text_block(text))

    for attachment in attachments:
        if attachment.type == "image" or attachment.type == "pdf":
            if not attachment.base64 and not attachment.url.startswith("data:"):
                # If it's a file path, read and encode it
                with open(attachment.url, "rb") as f:
                    img_data = b64encode(f.read()).decode()
                    url = f"data:image/jpeg;base64,{img_data}"
            else:
                url = attachment.base64 or attachment.url
            content.append(create_image_block(url))
        else:
            raise ValueError(f"Unsupported attachment type: {attachment.type}")

    return content


def ensure_message_list(content: MessageContent) -> list[MessagePart]:
    """Convert message content to list format if it's a string."""
    if isinstance(content, str):
        return [create_text_block(content)]
    return content
