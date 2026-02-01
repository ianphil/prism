"""Tests for statechart factory.

This module tests the create_social_media_statechart factory function
that creates the standard social media behavior statechart.
"""

import pytest

from prism.simulation.statechart_factory import create_social_media_statechart
from prism.statechart.statechart import Statechart
from prism.statechart.states import AgentState


class TestCreateSocialMediaStatechart:
    """Tests for create_social_media_statechart factory function."""

    def test_returns_statechart_instance(self) -> None:
        """T045: Factory returns a Statechart instance."""
        result = create_social_media_statechart()

        assert isinstance(result, Statechart)

    def test_has_all_agent_states(self) -> None:
        """T047: Statechart has all AgentState values as states."""
        chart = create_social_media_statechart()

        for state in AgentState:
            assert state in chart.states, f"Missing state: {state}"

    def test_initial_state_is_idle(self) -> None:
        """T049: Statechart has initial state set to IDLE."""
        chart = create_social_media_statechart()

        assert chart.initial == AgentState.IDLE

    def test_idle_to_scrolling_on_start_browsing(self) -> None:
        """T051: Transition IDLE -> SCROLLING on 'start_browsing'."""
        chart = create_social_media_statechart()

        result = chart.fire(
            trigger="start_browsing",
            current_state=AgentState.IDLE,
            agent=None,
            context=None,
        )

        assert result == AgentState.SCROLLING

    def test_scrolling_to_evaluating_on_sees_post(self) -> None:
        """T053: Transition SCROLLING -> EVALUATING on 'sees_post'."""
        chart = create_social_media_statechart()

        result = chart.fire(
            trigger="sees_post",
            current_state=AgentState.SCROLLING,
            agent=None,
            context=None,
        )

        assert result == AgentState.EVALUATING

    def test_scrolling_to_resting_on_feed_empty(self) -> None:
        """T055: Transition SCROLLING -> RESTING on 'feed_empty'."""
        chart = create_social_media_statechart()

        result = chart.fire(
            trigger="feed_empty",
            current_state=AgentState.SCROLLING,
            agent=None,
            context=None,
        )

        assert result == AgentState.RESTING

    def test_evaluating_decides_has_multiple_targets(self) -> None:
        """T057: EVALUATING has multiple possible targets on 'decides'."""
        chart = create_social_media_statechart()

        targets = chart.valid_targets(AgentState.EVALUATING, "decides")

        # Should have multiple targets: COMPOSING, ENGAGING_*, SCROLLING
        assert len(targets) >= 5, f"Expected at least 5 targets, got {len(targets)}"
        assert AgentState.COMPOSING in targets
        assert AgentState.ENGAGING_LIKE in targets
        assert AgentState.ENGAGING_REPLY in targets
        assert AgentState.ENGAGING_RESHARE in targets
        assert AgentState.SCROLLING in targets

    def test_composing_to_scrolling_on_finishes_composing(self) -> None:
        """T059: COMPOSING -> SCROLLING on 'finishes_composing'."""
        chart = create_social_media_statechart()

        result = chart.fire(
            trigger="finishes_composing",
            current_state=AgentState.COMPOSING,
            agent=None,
            context=None,
        )

        assert result == AgentState.SCROLLING

    @pytest.mark.parametrize(
        "engaging_state",
        [
            AgentState.ENGAGING_LIKE,
            AgentState.ENGAGING_REPLY,
            AgentState.ENGAGING_RESHARE,
        ],
    )
    def test_engaging_to_scrolling_on_finishes_engaging(
        self, engaging_state: AgentState
    ) -> None:
        """T059: ENGAGING_* -> SCROLLING on 'finishes_engaging'."""
        chart = create_social_media_statechart()

        result = chart.fire(
            trigger="finishes_engaging",
            current_state=engaging_state,
            agent=None,
            context=None,
        )

        assert result == AgentState.SCROLLING

    def test_resting_to_idle_on_rested(self) -> None:
        """RESTING -> IDLE on 'rested'."""
        chart = create_social_media_statechart()

        result = chart.fire(
            trigger="rested",
            current_state=AgentState.RESTING,
            agent=None,
            context=None,
        )

        assert result == AgentState.IDLE

    @pytest.mark.parametrize(
        "state",
        [
            AgentState.SCROLLING,
            AgentState.EVALUATING,
            AgentState.COMPOSING,
            AgentState.ENGAGING_LIKE,
            AgentState.ENGAGING_REPLY,
            AgentState.ENGAGING_RESHARE,
            AgentState.RESTING,
        ],
    )
    def test_timeout_returns_to_idle(self, state: AgentState) -> None:
        """T061: All states can transition to IDLE on 'timeout'."""
        chart = create_social_media_statechart()

        result = chart.fire(
            trigger="timeout",
            current_state=state,
            agent=None,
            context=None,
        )

        assert result == AgentState.IDLE
