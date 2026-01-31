"""Tests for FeedRetrievalExecutor."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from prism.rag.models import Post
from prism.simulation.executors.feed import FeedRetrievalExecutor


class TestFeedRetrievalExecutor:
    """Tests for FeedRetrievalExecutor."""

    def test_execute_returns_list_of_posts(self) -> None:
        """T063: execute should return list[Post]."""
        # Arrange
        mock_retriever = MagicMock()
        posts = [
            Post(
                id="p1",
                author_id="a1",
                text="Hello world",
                timestamp=datetime.now(timezone.utc),
            ),
            Post(
                id="p2",
                author_id="a2",
                text="Another post",
                timestamp=datetime.now(timezone.utc),
            ),
        ]
        mock_retriever.get_feed.return_value = posts

        mock_agent = MagicMock()
        mock_agent.interests = ["technology", "science"]

        mock_state = MagicMock()

        executor = FeedRetrievalExecutor(retriever=mock_retriever)

        # Act
        result = executor.execute(agent=mock_agent, state=mock_state)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(p, Post) for p in result)
        assert result[0].id == "p1"
        assert result[1].id == "p2"

    def test_execute_uses_agent_interests(self) -> None:
        """T065: execute should use agent.interests for retrieval."""
        # Arrange
        mock_retriever = MagicMock()
        mock_retriever.get_feed.return_value = []

        mock_agent = MagicMock()
        mock_agent.interests = ["crypto", "blockchain"]

        mock_state = MagicMock()

        executor = FeedRetrievalExecutor(retriever=mock_retriever)

        # Act
        executor.execute(agent=mock_agent, state=mock_state)

        # Assert
        mock_retriever.get_feed.assert_called_once_with(
            interests=["crypto", "blockchain"]
        )

    def test_execute_returns_empty_list_when_no_posts(self) -> None:
        """execute should return empty list when retriever returns empty."""
        # Arrange
        mock_retriever = MagicMock()
        mock_retriever.get_feed.return_value = []

        mock_agent = MagicMock()
        mock_agent.interests = ["music"]

        mock_state = MagicMock()

        executor = FeedRetrievalExecutor(retriever=mock_retriever)

        # Act
        result = executor.execute(agent=mock_agent, state=mock_state)

        # Assert
        assert result == []


@pytest.mark.asyncio
class TestFeedRetrievalExecutorAsync:
    """Async tests for FeedRetrievalExecutor."""

    async def test_execute_async_returns_list_of_posts(self) -> None:
        """execute_async should return list[Post]."""
        # Arrange
        mock_retriever = MagicMock()
        posts = [
            Post(
                id="p1",
                author_id="a1",
                text="Hello world",
                timestamp=datetime.now(timezone.utc),
            ),
        ]
        mock_retriever.get_feed.return_value = posts

        mock_agent = MagicMock()
        mock_agent.interests = ["technology"]

        mock_state = MagicMock()

        executor = FeedRetrievalExecutor(retriever=mock_retriever)

        # Act
        result = await executor.execute_async(agent=mock_agent, state=mock_state)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].id == "p1"
