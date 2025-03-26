"""Searcher agent implementation."""

import re
from typing import AsyncGenerator, List, cast

from litellm import Choices, acompletion
from litellm.types.utils import ModelResponse
from loguru import logger

from cp_agent.agents.base import BaseAgent
from cp_agent.agents.searcher import prompts
from cp_agent.config import settings
from cp_agent.kb.kb_manager import Document, KnowledgeBaseManager
from cp_agent.storage.list_store import ListStore
from cp_agent.types import StreamEvent, ToolUseName, parse_assistant_message
from cp_agent.utils.message_formats import (
    MessageContent,
    TextBlock,
    ensure_message_list,
)


class SearcherAgent(BaseAgent):
    """Agent for handling search-related queries using GPT-4o-mini."""

    def __init__(self, memory: ListStore):
        """Initialize the searcher agent."""
        super().__init__(memory)
        self.kb_manager = KnowledgeBaseManager()

    def _filter_by_score(self, results: List[tuple[Document, float]]) -> List[str]:
        """Filter search results by relevance score threshold.

        Args:
            results: List of (document, score) tuples from search

        Returns:
            List of document contents that meet the configured minimum relevance score threshold
        """
        return [
            doc.content
            for doc, score in results
            if score >= settings.KB_MIN_RELEVANCE_SCORE
        ]

    async def kb_search(self, query: str) -> List[str]:
        """Perform knowledge base search.

        Args:
            query: The search query text

        Returns:
            List of relevant document contents that meet score threshold
        """
        results = self.kb_manager.search_similar(query=query, top_k=3)

        if not results:
            return []

        return self._filter_by_score(results)

    async def llm_search(self, message: MessageContent) -> List[str]:
        """Process a message using GPT-4o-mini.

        Args:
            message: The message content to process

        Returns:
            List of search results
        """
        try:
            system_prompt = await prompts.system_prompt()

            stored_messages = self.memory.lrange("messages")

            current_message = {"role": "user", "content": message}

            messages = [
                {"role": "system", "content": system_prompt},
                *stored_messages,
                current_message,
            ]

            response = cast(
                ModelResponse,
                await acompletion(
                    model=settings.DEFAULT_MODEL,
                    messages=messages,
                    api_base=settings.DEFAULT_LLM_URL,
                    api_key=settings.DEFAULT_MODEL_API_KEY,
                ),
            )

            assistant_message = cast(List[Choices], response.choices)[0].message.content
            content_blocks = parse_assistant_message(assistant_message or "")

            response_parts = []
            for block in content_blocks:
                if (
                    block["type"] == "tool_use"
                    and block["name"] == ToolUseName.KB_SEARCH
                    and not block["partial"]
                ):
                    query = block["params"].get("query", "")
                    kb_results = await self.kb_search(query)
                    if kb_results:
                        response_parts.append(kb_results[0])

            return response_parts

        except Exception as e:
            logger.exception(e)
            logger.error(f"Error processing message: {e}")
            return []

    async def llm_search_simple(self, message: MessageContent) -> List[str]:
        """Process a message using GPT-4o-mini with simplified query generation.

        Args:
            message: The message content to process

        Returns:
            List of search results
        """
        try:
            system_prompt = await prompts.system_prompt_simple()

            stored_messages = self.memory.lrange("messages")

            current_message = {"role": "user", "content": message}

            messages = [
                {"role": "system", "content": system_prompt},
                *stored_messages,
                current_message,
            ]

            response = cast(
                ModelResponse,
                await acompletion(
                    model=settings.DEFAULT_MODEL,
                    messages=messages,
                    api_base=settings.DEFAULT_LLM_URL,
                    api_key=settings.DEFAULT_MODEL_API_KEY,
                    max_tokens=200,  # cut off the response at 200 tokens.
                ),
            )

            # Get the raw query text without parsing XML tags
            query = cast(List[Choices], response.choices)[0].message.content

            # Ensure query is a string and strip any whitespace
            if query:
                query = query.strip()
                logger.info(f"Generated search query: {query}")

                # Execute the search with the generated query
                kb_results = await self.kb_search(query)
                return kb_results

            return []

        except Exception as e:
            logger.exception(e)
            logger.error(f"Error processing message with simple search: {e}")
            return []

    def _check_tag_exists(self, tag: str) -> bool:
        """Check if a specific knowledge tag exists in memory.

        Args:
            tag: Tag to search for (e.g. 'relevant-knowledge-supabase-login')

        Returns:
            bool: True if tag exists in memory
        """
        stored_messages = self.memory.lrange("messages")
        return any(
            isinstance(msg.get("content"), str) and f"<{tag}>" in msg["content"]
            for msg in stored_messages
        )

    async def prime_search_results(
        self,
        message: MessageContent,
        with_llm: bool = False,
        skip_if_exists: bool = True,
    ) -> None:
        """Cache search results preserving their original knowledge tags.

        Args:
            message: The message content to process
            with_llm: If True, use LLM for search
            skip_if_exists: If True, skip if any tagged knowledge already exists
        """
        if not with_llm:
            search_results = await self.search_from_message(message)
        else:
            search_results = await self.llm_search_simple(message)

        for result in search_results:
            # Extract tag from result (matches format <tag-name>content</tag-name>)
            tag_match = re.match(r"<([\w-]+)>", result)
            if tag_match and tag_match.group(1):
                tag = tag_match.group(1)
                if skip_if_exists and self._check_tag_exists(tag):
                    continue
                msg = {"role": "user", "content": result}
                self.memory.rpush("messages", msg)

    async def search_from_message(self, message: MessageContent) -> list[str]:
        """Process a message by directly extracting text and searching without LLM.

        Args:
            message: The message content to process

        Returns:
            List of search results
        """
        # Convert message to list format if it's a string
        message_parts = ensure_message_list(message)

        # Extract and concatenate all text content
        text_parts: list[str] = []
        for part in message_parts:
            if part["type"] == "text":
                text_block = cast(TextBlock, part)
                text_parts.append(text_block["text"])

        text_content = "\n".join(text_parts)

        # Return empty list if no text content found
        if not text_content.strip():
            return []

        # Perform knowledge base search directly
        return await self.kb_search(text_content)

    def run(self, message: MessageContent) -> AsyncGenerator[StreamEvent, None]:
        raise NotImplementedError("Agents must implement run method")
