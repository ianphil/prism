"""Tests for StateUpdateExecutor."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from prism.rag.models import Post
from prism.simulation.executors.state_update import StateUpdateExecutor
from prism.simulation.results import ActionResult, DecisionResult
from prism.simulation.state import SimulationState
from prism.simulation.statechart_factory import create_social_media_statechart
from prism.statechart.states import AgentState


def create_test_post(id: str = "p1") -> Post:
    """Create a test post."""
    return Post(
        id=id,
        author_id="a1",
        text="Test post content",
        timestamp=datetime.now(timezone.utc),
        likes=0,
        reshares=0,
        replies=0,
    )


def create_mock_agent() -> MagicMock:
    """Create a mock agent."""
    agent = MagicMock()
    agent.agent_id = "test_agent"
    agent.state = AgentState.IDLE
    return agent


def create_test_state(posts: list[Post] | None = None) -> SimulationState:
    """Create a test SimulationState."""
    if posts is None:
        posts = [create_test_post()]
    return SimulationState(
        posts=posts,
        agents=[create_mock_agent()],
        statechart=create_social_media_statechart(),
    )


class TestStateUpdateExecutor:
    """Tests for StateUpdateExecutor."""

    @pytest.mark.asyncio
    async def test_handles_like_action(self) -> None:
        """T081: executor should handle like action - increment post.likes and metrics."""
        # Arrange
        post = create_test_post("p1")
        state = create_test_state([post])
        mock_retriever = MagicMock()

        decision = DecisionResult(
            agent_id="test_agent",
            trigger="finishes_engaging",
            from_state=AgentState.ENGAGING_LIKE,
            to_state=AgentState.SCROLLING,
            action=ActionResult(action="like", target_post_id="p1"),
        )

        executor = StateUpdateExecutor(retriever=mock_retriever)

        # Act
        await executor.execute(agent=MagicMock(), state=state, decision=decision)

        # Assert
        assert post.likes == 1
        assert state.metrics.total_likes == 1

    @pytest.mark.asyncio
    async def test_handles_reply_action(self) -> None:
        """T083: executor should handle reply action - increment replies + add post."""
        # Arrange
        post = create_test_post("p1")
        state = create_test_state([post])
        mock_retriever = MagicMock()

        reply_post = Post(
            id="p2",
            author_id="test_agent",
            text="Reply content",
            timestamp=datetime.now(timezone.utc),
        )

        decision = DecisionResult(
            agent_id="test_agent",
            trigger="finishes_engaging",
            from_state=AgentState.ENGAGING_REPLY,
            to_state=AgentState.SCROLLING,
            action=ActionResult(
                action="reply",
                target_post_id="p1",
                content="Reply content",
            ),
        )

        executor = StateUpdateExecutor(retriever=mock_retriever)

        # Act
        await executor.execute(
            agent=MagicMock(), state=state, decision=decision, new_post=reply_post
        )

        # Assert
        assert post.replies == 1
        assert state.metrics.total_replies == 1
        assert len(state.posts) == 2
        assert state.posts[1].id == "p2"
        mock_retriever.add_post.assert_called_once_with(reply_post)

    @pytest.mark.asyncio
    async def test_handles_reshare_action(self) -> None:
        """T085: executor should handle reshare action."""
        # Arrange
        post = create_test_post("p1")
        state = create_test_state([post])
        mock_retriever = MagicMock()

        reshare_post = Post(
            id="p3",
            author_id="test_agent",
            text="RT: Test post content",
            timestamp=datetime.now(timezone.utc),
        )

        decision = DecisionResult(
            agent_id="test_agent",
            trigger="finishes_engaging",
            from_state=AgentState.ENGAGING_RESHARE,
            to_state=AgentState.SCROLLING,
            action=ActionResult(action="reshare", target_post_id="p1"),
        )

        executor = StateUpdateExecutor(retriever=mock_retriever)

        # Act
        await executor.execute(
            agent=MagicMock(), state=state, decision=decision, new_post=reshare_post
        )

        # Assert
        assert post.reshares == 1
        assert state.metrics.total_reshares == 1
        assert len(state.posts) == 2
        mock_retriever.add_post.assert_called_once_with(reshare_post)

    @pytest.mark.asyncio
    async def test_handles_compose_action(self) -> None:
        """T087: executor should handle compose action - add new post."""
        # Arrange
        state = create_test_state([])
        mock_retriever = MagicMock()

        new_post = Post(
            id="p4",
            author_id="test_agent",
            text="New original content",
            timestamp=datetime.now(timezone.utc),
        )

        decision = DecisionResult(
            agent_id="test_agent",
            trigger="finishes_composing",
            from_state=AgentState.COMPOSING,
            to_state=AgentState.SCROLLING,
            action=ActionResult(action="compose", target_post_id=None),
        )

        executor = StateUpdateExecutor(retriever=mock_retriever)

        # Act
        await executor.execute(
            agent=MagicMock(), state=state, decision=decision, new_post=new_post
        )

        # Assert
        assert len(state.posts) == 1
        assert state.posts[0].id == "p4"
        assert state.metrics.posts_created == 1
        mock_retriever.add_post.assert_called_once_with(new_post)

    @pytest.mark.asyncio
    async def test_handles_scroll_action_no_changes(self) -> None:
        """T089: executor should handle scroll action - no changes."""
        # Arrange
        post = create_test_post("p1")
        state = create_test_state([post])
        mock_retriever = MagicMock()

        decision = DecisionResult(
            agent_id="test_agent",
            trigger="sees_post",
            from_state=AgentState.SCROLLING,
            to_state=AgentState.EVALUATING,
            action=ActionResult(action="scroll", target_post_id=None),
        )

        executor = StateUpdateExecutor(retriever=mock_retriever)

        # Act
        await executor.execute(agent=MagicMock(), state=state, decision=decision)

        # Assert - no changes
        assert post.likes == 0
        assert post.reshares == 0
        assert post.replies == 0
        assert state.metrics.total_likes == 0
        assert len(state.posts) == 1
        mock_retriever.add_post.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_none_action(self) -> None:
        """executor should handle None action gracefully."""
        # Arrange
        state = create_test_state([])
        mock_retriever = MagicMock()

        decision = DecisionResult(
            agent_id="test_agent",
            trigger="start_browsing",
            from_state=AgentState.IDLE,
            to_state=AgentState.SCROLLING,
            action=None,
        )

        executor = StateUpdateExecutor(retriever=mock_retriever)

        # Act - should not raise
        await executor.execute(agent=MagicMock(), state=state, decision=decision)

        # Assert - no errors
        mock_retriever.add_post.assert_not_called()

    @pytest.mark.asyncio
    async def test_like_nonexistent_post_is_noop(self) -> None:
        """executor should handle like on non-existent post gracefully."""
        # Arrange
        state = create_test_state([])  # No posts
        mock_retriever = MagicMock()

        decision = DecisionResult(
            agent_id="test_agent",
            trigger="finishes_engaging",
            from_state=AgentState.ENGAGING_LIKE,
            to_state=AgentState.SCROLLING,
            action=ActionResult(action="like", target_post_id="nonexistent"),
        )

        executor = StateUpdateExecutor(retriever=mock_retriever)

        # Act - should not raise
        await executor.execute(agent=MagicMock(), state=state, decision=decision)

        # Assert - no metrics changed
        assert state.metrics.total_likes == 0
