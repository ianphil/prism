"""Tests for trigger determination logic.

This module tests the determine_trigger function that maps agent state
and context to appropriate trigger names for statechart transitions.
"""

from unittest.mock import MagicMock

import pytest

from prism.simulation.triggers import determine_trigger
from prism.statechart.states import AgentState


class TestDetermineTrigger:
    """Tests for determine_trigger function."""

    def test_determine_trigger_returns_string(self) -> None:
        """T029: determine_trigger returns a string trigger name."""
        agent = MagicMock()
        agent.state = AgentState.IDLE
        agent.is_timed_out.return_value = False

        result = determine_trigger(agent=agent, feed=[], state=None)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_idle_returns_start_browsing(self) -> None:
        """T031: IDLE state returns 'start_browsing' trigger."""
        agent = MagicMock()
        agent.state = AgentState.IDLE
        agent.is_timed_out.return_value = False

        result = determine_trigger(agent=agent, feed=[], state=None)

        assert result == "start_browsing"

    def test_scrolling_with_feed_returns_sees_post(self) -> None:
        """T033: SCROLLING state with non-empty feed returns 'sees_post' trigger."""
        agent = MagicMock()
        agent.state = AgentState.SCROLLING
        agent.is_timed_out.return_value = False

        # Create a mock post
        post = MagicMock()
        feed = [post]

        result = determine_trigger(agent=agent, feed=feed, state=None)

        assert result == "sees_post"

    def test_scrolling_with_empty_feed_returns_feed_empty(self) -> None:
        """T035: SCROLLING state with empty feed returns 'feed_empty' trigger."""
        agent = MagicMock()
        agent.state = AgentState.SCROLLING
        agent.is_timed_out.return_value = False

        result = determine_trigger(agent=agent, feed=[], state=None)

        assert result == "feed_empty"

    def test_evaluating_returns_decides(self) -> None:
        """T037: EVALUATING state returns 'decides' trigger."""
        agent = MagicMock()
        agent.state = AgentState.EVALUATING
        agent.is_timed_out.return_value = False

        result = determine_trigger(agent=agent, feed=[], state=None)

        assert result == "decides"

    def test_composing_returns_finishes_composing(self) -> None:
        """T039: COMPOSING state returns 'finishes_composing' trigger."""
        agent = MagicMock()
        agent.state = AgentState.COMPOSING
        agent.is_timed_out.return_value = False

        result = determine_trigger(agent=agent, feed=[], state=None)

        assert result == "finishes_composing"

    @pytest.mark.parametrize(
        "engaging_state",
        [
            AgentState.ENGAGING_LIKE,
            AgentState.ENGAGING_REPLY,
            AgentState.ENGAGING_RESHARE,
        ],
    )
    def test_engaging_states_return_finishes_engaging(
        self, engaging_state: AgentState
    ) -> None:
        """T041: ENGAGING_* states return 'finishes_engaging' trigger."""
        agent = MagicMock()
        agent.state = engaging_state
        agent.is_timed_out.return_value = False

        result = determine_trigger(agent=agent, feed=[], state=None)

        assert result == "finishes_engaging"

    def test_resting_returns_rested(self) -> None:
        """T043: RESTING state returns 'rested' trigger."""
        agent = MagicMock()
        agent.state = AgentState.RESTING
        agent.is_timed_out.return_value = False

        result = determine_trigger(agent=agent, feed=[], state=None)

        assert result == "rested"
