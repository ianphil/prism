"""Tests for AgentRoundExecutor."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from prism.rag.models import Post
from prism.simulation.executors.round import AgentRoundExecutor
from prism.simulation.results import ActionResult, DecisionResult
from prism.simulation.state import SimulationState
from prism.simulation.statechart_factory import create_social_media_statechart
from prism.statechart.states import AgentState


def create_mock_agent() -> MagicMock:
    """Create a mock agent."""
    agent = MagicMock()
    agent.agent_id = "test_agent"
    agent.state = AgentState.IDLE
    agent.interests = ["technology"]
    return agent


def create_test_state() -> SimulationState:
    """Create a test SimulationState."""
    return SimulationState(
        posts=[],
        agents=[create_mock_agent()],
        statechart=create_social_media_statechart(),
        round_number=0,
    )


def create_test_post() -> Post:
    """Create a test post."""
    return Post(
        id="p1",
        author_id="a1",
        text="Test content",
        timestamp=datetime.now(timezone.utc),
    )


class TestAgentRoundExecutor:
    """Tests for AgentRoundExecutor."""

    @pytest.mark.asyncio
    async def test_execute_coordinates_pipeline(self) -> None:
        """T097: executor should coordinate feed, decision, state, logging pipeline."""
        # Arrange
        agent = create_mock_agent()
        state = create_test_state()
        posts = [create_test_post()]

        # Create mock executors
        mock_feed_exec = AsyncMock()
        mock_feed_exec.execute_async.return_value = posts

        mock_decision_exec = AsyncMock()
        mock_decision_exec.execute.return_value = DecisionResult(
            agent_id="test_agent",
            trigger="start_browsing",
            from_state=AgentState.IDLE,
            to_state=AgentState.SCROLLING,
            action=ActionResult(action="scroll", target_post_id=None),
        )

        mock_state_exec = AsyncMock()
        mock_logging_exec = AsyncMock()

        executor = AgentRoundExecutor(
            feed_executor=mock_feed_exec,
            decision_executor=mock_decision_exec,
            state_executor=mock_state_exec,
            logging_executor=mock_logging_exec,
        )

        # Act
        await executor.execute(agent=agent, state=state)

        # Assert - all executors were called in order
        mock_feed_exec.execute_async.assert_called_once_with(agent=agent, state=state)
        mock_decision_exec.execute.assert_called_once()
        mock_state_exec.execute.assert_called_once()
        mock_logging_exec.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_returns_decision_result(self) -> None:
        """T099: executor should return DecisionResult from decision executor."""
        # Arrange
        agent = create_mock_agent()
        state = create_test_state()

        expected_result = DecisionResult(
            agent_id="test_agent",
            trigger="start_browsing",
            from_state=AgentState.IDLE,
            to_state=AgentState.SCROLLING,
            action=ActionResult(action="scroll", target_post_id=None),
        )

        mock_feed_exec = AsyncMock()
        mock_feed_exec.execute_async.return_value = []

        mock_decision_exec = AsyncMock()
        mock_decision_exec.execute.return_value = expected_result

        mock_state_exec = AsyncMock()
        mock_logging_exec = AsyncMock()

        executor = AgentRoundExecutor(
            feed_executor=mock_feed_exec,
            decision_executor=mock_decision_exec,
            state_executor=mock_state_exec,
            logging_executor=mock_logging_exec,
        )

        # Act
        result = await executor.execute(agent=agent, state=state)

        # Assert
        assert result == expected_result
        assert isinstance(result, DecisionResult)
        assert result.agent_id == "test_agent"
        assert result.from_state == AgentState.IDLE
        assert result.to_state == AgentState.SCROLLING

    @pytest.mark.asyncio
    async def test_passes_feed_to_decision_executor(self) -> None:
        """decision executor should receive feed from feed executor."""
        # Arrange
        agent = create_mock_agent()
        state = create_test_state()
        posts = [create_test_post(), create_test_post()]

        mock_feed_exec = AsyncMock()
        mock_feed_exec.execute_async.return_value = posts

        mock_decision_exec = AsyncMock()
        mock_decision_exec.execute.return_value = DecisionResult(
            agent_id="test_agent",
            trigger="start_browsing",
            from_state=AgentState.IDLE,
            to_state=AgentState.SCROLLING,
            action=ActionResult(action="scroll", target_post_id=None),
        )

        mock_state_exec = AsyncMock()
        mock_logging_exec = AsyncMock()

        executor = AgentRoundExecutor(
            feed_executor=mock_feed_exec,
            decision_executor=mock_decision_exec,
            state_executor=mock_state_exec,
            logging_executor=mock_logging_exec,
        )

        # Act
        await executor.execute(agent=agent, state=state)

        # Assert - decision executor received the feed
        call_kwargs = mock_decision_exec.execute.call_args[1]
        assert "feed" in call_kwargs
        assert call_kwargs["feed"] == posts

    @pytest.mark.asyncio
    async def test_passes_decision_to_state_executor(self) -> None:
        """state executor should receive decision from decision executor."""
        # Arrange
        agent = create_mock_agent()
        state = create_test_state()

        decision = DecisionResult(
            agent_id="test_agent",
            trigger="start_browsing",
            from_state=AgentState.IDLE,
            to_state=AgentState.SCROLLING,
            action=ActionResult(action="scroll", target_post_id=None),
        )

        mock_feed_exec = AsyncMock()
        mock_feed_exec.execute_async.return_value = []

        mock_decision_exec = AsyncMock()
        mock_decision_exec.execute.return_value = decision

        mock_state_exec = AsyncMock()
        mock_logging_exec = AsyncMock()

        executor = AgentRoundExecutor(
            feed_executor=mock_feed_exec,
            decision_executor=mock_decision_exec,
            state_executor=mock_state_exec,
            logging_executor=mock_logging_exec,
        )

        # Act
        await executor.execute(agent=agent, state=state)

        # Assert - state executor received the decision
        call_kwargs = mock_state_exec.execute.call_args[1]
        assert "decision" in call_kwargs
        assert call_kwargs["decision"] == decision
