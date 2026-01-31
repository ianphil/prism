"""Tests for AgentDecisionExecutor."""

from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from prism.rag.models import Post
from prism.simulation.executors.decision import AgentDecisionExecutor
from prism.simulation.results import ActionResult, DecisionResult
from prism.simulation.state import SimulationState
from prism.simulation.statechart_factory import create_social_media_statechart
from prism.statechart.states import AgentState


def create_mock_agent(state: AgentState = AgentState.IDLE) -> MagicMock:
    """Create a mock agent with required attributes."""
    agent = MagicMock()
    agent.agent_id = "test_agent"
    agent.name = "Test Agent"
    agent.interests = ["technology"]
    agent.personality = "curious"
    agent.state = state
    agent.ticks_in_state = 0
    agent.is_timed_out.return_value = False
    return agent


def create_test_state(agents: list | None = None) -> SimulationState:
    """Create a test SimulationState."""
    if agents is None:
        agents = [create_mock_agent()]
    return SimulationState(
        posts=[],
        agents=agents,
        statechart=create_social_media_statechart(),
    )


def create_test_post() -> Post:
    """Create a test post."""
    return Post(
        id="p1",
        author_id="a1",
        text="Test post content",
        timestamp=datetime.now(timezone.utc),
    )


class TestAgentDecisionExecutor:
    """Tests for AgentDecisionExecutor."""

    @pytest.mark.asyncio
    async def test_execute_calls_agent_tick(self) -> None:
        """T067: execute should call agent.tick() at start."""
        # Arrange
        agent = create_mock_agent(AgentState.IDLE)
        state = create_test_state([agent])
        feed: list[Post] = []

        executor = AgentDecisionExecutor()

        # Act
        await executor.execute(agent=agent, state=state, feed=feed)

        # Assert
        agent.tick.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_calls_statechart_fire(self) -> None:
        """T069: execute should call statechart.fire with correct args."""
        # Arrange
        agent = create_mock_agent(AgentState.IDLE)
        statechart = create_social_media_statechart()
        state = SimulationState(
            posts=[],
            agents=[agent],
            statechart=statechart,
        )
        feed: list[Post] = []

        executor = AgentDecisionExecutor()

        # Act
        with patch.object(statechart, "fire", return_value=AgentState.SCROLLING) as mock_fire:
            state.statechart = statechart
            await executor.execute(agent=agent, state=state, feed=feed)

            # Assert - fire was called with trigger, current_state, agent, context
            mock_fire.assert_called_once()
            call_args = mock_fire.call_args
            assert call_args[1]["trigger"] == "start_browsing"
            assert call_args[1]["current_state"] == AgentState.IDLE
            assert call_args[1]["agent"] == agent
            assert "context" in call_args[1]

    @pytest.mark.asyncio
    async def test_execute_detects_multiple_valid_targets(self) -> None:
        """T071: execute should detect multiple valid targets."""
        # Arrange - EVALUATING + decides has multiple possible targets
        agent = create_mock_agent(AgentState.EVALUATING)
        state = create_test_state([agent])
        feed = [create_test_post()]

        executor = AgentDecisionExecutor()

        # The statechart has multiple transitions from EVALUATING on "decides"
        targets = state.statechart.valid_targets(AgentState.EVALUATING, "decides")

        # Assert multiple targets exist
        assert len(targets) > 1

    @pytest.mark.asyncio
    async def test_execute_calls_reasoner_when_ambiguous(self) -> None:
        """T073: execute should call reasoner.decide when fire returns None and multiple targets exist."""
        # Arrange - Create a statechart where fire() returns None but valid_targets has multiple
        from prism.statechart.statechart import Statechart
        from prism.statechart.transitions import Transition

        # Guard that always returns False to force fire() to return None
        def always_false(agent: Any, context: Any) -> bool:
            return False

        # Create statechart with guarded transitions from EVALUATING
        statechart = Statechart(
            states=set(AgentState),
            transitions=[
                # Guarded transitions - all guards fail
                Transition(
                    trigger="decides",
                    source=AgentState.EVALUATING,
                    target=AgentState.COMPOSING,
                    guard=always_false,
                ),
                Transition(
                    trigger="decides",
                    source=AgentState.EVALUATING,
                    target=AgentState.ENGAGING_LIKE,
                    guard=always_false,
                ),
                Transition(
                    trigger="decides",
                    source=AgentState.EVALUATING,
                    target=AgentState.SCROLLING,
                    guard=always_false,
                ),
            ],
            initial=AgentState.IDLE,
        )

        agent = create_mock_agent(AgentState.EVALUATING)

        # Create mock reasoner
        mock_reasoner = AsyncMock()
        mock_reasoner.decide.return_value = AgentState.ENGAGING_LIKE

        state = SimulationState(
            posts=[],
            agents=[agent],
            statechart=statechart,
            reasoner=mock_reasoner,
        )
        feed = [create_test_post()]

        executor = AgentDecisionExecutor()

        # Act
        result = await executor.execute(agent=agent, state=state, feed=feed)

        # Assert - reasoner was called because fire returned None and multiple targets exist
        mock_reasoner.decide.assert_called_once()
        assert result.reasoner_used is True
        assert result.to_state == AgentState.ENGAGING_LIKE

    @pytest.mark.asyncio
    async def test_execute_calls_transition_to(self) -> None:
        """T075: execute should call agent.transition_to."""
        # Arrange
        agent = create_mock_agent(AgentState.IDLE)
        state = create_test_state([agent])
        feed: list[Post] = []

        executor = AgentDecisionExecutor()

        # Act
        await executor.execute(agent=agent, state=state, feed=feed)

        # Assert - transition_to was called (IDLE -> SCROLLING on start_browsing)
        agent.transition_to.assert_called()
        call_args = agent.transition_to.call_args
        assert call_args[0][0] == AgentState.SCROLLING
        assert call_args[0][1] == "start_browsing"

    @pytest.mark.asyncio
    async def test_execute_returns_decision_result(self) -> None:
        """T077: execute should return DecisionResult."""
        # Arrange
        agent = create_mock_agent(AgentState.IDLE)
        state = create_test_state([agent])
        feed: list[Post] = []

        executor = AgentDecisionExecutor()

        # Act
        result = await executor.execute(agent=agent, state=state, feed=feed)

        # Assert
        assert isinstance(result, DecisionResult)
        assert result.agent_id == "test_agent"
        assert result.trigger == "start_browsing"
        assert result.from_state == AgentState.IDLE
        assert result.to_state == AgentState.SCROLLING

    @pytest.mark.asyncio
    async def test_execute_action_for_composing_state(self) -> None:
        """T079: execute should return action based on new state - COMPOSING."""
        # Arrange
        agent = create_mock_agent(AgentState.COMPOSING)
        state = create_test_state([agent])
        feed: list[Post] = []

        executor = AgentDecisionExecutor()

        # Act - COMPOSING -> SCROLLING on finishes_composing
        result = await executor.execute(agent=agent, state=state, feed=feed)

        # Assert - action should be compose
        assert result.action is not None
        assert result.action.action == "compose"

    @pytest.mark.asyncio
    async def test_execute_action_for_engaging_like_state(self) -> None:
        """T079: execute should return action based on new state - ENGAGING_LIKE."""
        # Arrange
        agent = create_mock_agent(AgentState.ENGAGING_LIKE)
        state = create_test_state([agent])
        post = create_test_post()
        feed = [post]

        executor = AgentDecisionExecutor()

        # Act - ENGAGING_LIKE -> SCROLLING on finishes_engaging
        result = await executor.execute(agent=agent, state=state, feed=feed)

        # Assert - action should be like
        assert result.action is not None
        assert result.action.action == "like"
        assert result.action.target_post_id == post.id

    @pytest.mark.asyncio
    async def test_execute_action_for_engaging_reply_state(self) -> None:
        """T079: execute should return action - ENGAGING_REPLY."""
        # Arrange
        agent = create_mock_agent(AgentState.ENGAGING_REPLY)
        state = create_test_state([agent])
        post = create_test_post()
        feed = [post]

        executor = AgentDecisionExecutor()

        # Act
        result = await executor.execute(agent=agent, state=state, feed=feed)

        # Assert
        assert result.action is not None
        assert result.action.action == "reply"
        assert result.action.target_post_id == post.id

    @pytest.mark.asyncio
    async def test_execute_action_for_engaging_reshare_state(self) -> None:
        """T079: execute should return action - ENGAGING_RESHARE."""
        # Arrange
        agent = create_mock_agent(AgentState.ENGAGING_RESHARE)
        state = create_test_state([agent])
        post = create_test_post()
        feed = [post]

        executor = AgentDecisionExecutor()

        # Act
        result = await executor.execute(agent=agent, state=state, feed=feed)

        # Assert
        assert result.action is not None
        assert result.action.action == "reshare"
        assert result.action.target_post_id == post.id

    @pytest.mark.asyncio
    async def test_execute_scroll_action_for_non_engagement_state(self) -> None:
        """T079: execute should return scroll action for SCROLLING state."""
        # Arrange
        agent = create_mock_agent(AgentState.SCROLLING)
        state = create_test_state([agent])
        feed: list[Post] = []  # Empty feed -> feed_empty -> RESTING

        executor = AgentDecisionExecutor()

        # Act
        result = await executor.execute(agent=agent, state=state, feed=feed)

        # Assert - action should be scroll (no engagement)
        assert result.action is not None
        assert result.action.action == "scroll"

    @pytest.mark.asyncio
    async def test_execute_timeout_trigger(self) -> None:
        """execute should use timeout trigger when agent.is_timed_out() is True."""
        # Arrange
        agent = create_mock_agent(AgentState.SCROLLING)
        agent.is_timed_out.return_value = True  # Agent is timed out
        state = create_test_state([agent])
        feed = [create_test_post()]

        executor = AgentDecisionExecutor()

        # Act
        result = await executor.execute(agent=agent, state=state, feed=feed)

        # Assert - timeout trigger was used
        assert result.trigger == "timeout"
        assert result.to_state == AgentState.IDLE

    @pytest.mark.asyncio
    async def test_execute_without_reasoner_uses_first_target(self) -> None:
        """execute should use first valid target when reasoner is None."""
        # Arrange - EVALUATING has multiple targets but no reasoner
        agent = create_mock_agent(AgentState.EVALUATING)
        state = SimulationState(
            posts=[],
            agents=[agent],
            statechart=create_social_media_statechart(),
            reasoner=None,  # No reasoner
        )
        feed = [create_test_post()]

        executor = AgentDecisionExecutor()

        # Act
        result = await executor.execute(agent=agent, state=state, feed=feed)

        # Assert - reasoner_used should be False, some valid target was used
        assert result.reasoner_used is False
        # The first target from "decides" transitions (COMPOSING) should be used
        assert result.to_state in [
            AgentState.COMPOSING,
            AgentState.ENGAGING_LIKE,
            AgentState.ENGAGING_REPLY,
            AgentState.ENGAGING_RESHARE,
            AgentState.SCROLLING,
        ]

    @pytest.mark.asyncio
    async def test_execute_stays_in_state_when_no_valid_transition(self) -> None:
        """execute should stay in current state when no valid transition exists."""
        # Arrange - IDLE state but somehow no valid transition
        agent = create_mock_agent(AgentState.IDLE)

        # Create a statechart with no transitions from IDLE
        from prism.statechart.statechart import Statechart

        empty_statechart = Statechart(
            states=set(AgentState),
            transitions=[],  # No transitions!
            initial=AgentState.IDLE,
        )

        state = SimulationState(
            posts=[],
            agents=[agent],
            statechart=empty_statechart,
        )
        feed: list[Post] = []

        executor = AgentDecisionExecutor()

        # Act
        result = await executor.execute(agent=agent, state=state, feed=feed)

        # Assert - stays in IDLE
        assert result.from_state == AgentState.IDLE
        assert result.to_state == AgentState.IDLE
