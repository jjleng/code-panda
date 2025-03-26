"""Tests for searcher agent."""

from unittest.mock import MagicMock, patch

import pytest

from cp_agent.agents.searcher.agent import SearcherAgent
from cp_agent.kb.kb_manager import Document
from cp_agent.storage.list_store import ListStore


@pytest.mark.asyncio
async def test_integration_search() -> None:
    """Test the full search pipeline with real LLM calls."""
    mock_memory = MagicMock(spec=ListStore)
    mock_memory.lrange.return_value = []  # No conversation history
    agent = SearcherAgent(memory=mock_memory)

    # Only mock the KB part since we can't include real docs in tests
    with patch.object(
        agent.kb_manager,
        "search_similar",
        return_value=[
            (
                Document(
                    content="Guide: How to implement authentication with Supabase",
                    metadata={},
                ),
                0.9,
            ),
            (Document(content="Setting up a new Supabase project", metadata={}), 0.85),
            (Document(content="Unrelated document", metadata={}), 0.3),
        ],
    ):
        results = await agent.llm_search(
            "How do I implement authentication with supabase?"
        )

        # Verify we got relevant results
        assert len(results) > 0
        # Check that results contain authentication-related content
        assert any("authentication" in result.lower() for result in results)
        # Check that low-relevance results were filtered
        assert "Unrelated document" not in results


@pytest.mark.asyncio
async def test_integration_empty_results() -> None:
    """Test the search pipeline with no matching KB documents."""
    mock_memory = MagicMock(spec=ListStore)
    mock_memory.lrange.return_value = []  # No conversation history
    agent = SearcherAgent(memory=mock_memory)

    # Mock empty KB results
    with patch.object(agent.kb_manager, "search_similar", return_value=[]):
        results = await agent.llm_search("Tell me about a completely nonexistent topic")
        assert len(results) == 0
