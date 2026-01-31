"""Tests for simulation state models (T007-T020)."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError


class TestEngagementMetricsDefaults:
    """T007: Test EngagementMetrics with default zero values."""

    def test_metrics_has_total_likes_default_zero(self):
        """EngagementMetrics should have total_likes defaulting to 0."""
        from prism.simulation.state import EngagementMetrics

        metrics = EngagementMetrics()
        assert metrics.total_likes == 0

    def test_metrics_has_total_reshares_default_zero(self):
        """EngagementMetrics should have total_reshares defaulting to 0."""
        from prism.simulation.state import EngagementMetrics

        metrics = EngagementMetrics()
        assert metrics.total_reshares == 0

    def test_metrics_has_total_replies_default_zero(self):
        """EngagementMetrics should have total_replies defaulting to 0."""
        from prism.simulation.state import EngagementMetrics

        metrics = EngagementMetrics()
        assert metrics.total_replies == 0

    def test_metrics_has_posts_created_default_zero(self):
        """EngagementMetrics should have posts_created defaulting to 0."""
        from prism.simulation.state import EngagementMetrics

        metrics = EngagementMetrics()
        assert metrics.posts_created == 0

    def test_metrics_negative_total_likes_raises_error(self):
        """total_likes < 0 should raise ValidationError."""
        from prism.simulation.state import EngagementMetrics

        with pytest.raises(ValidationError) as exc_info:
            EngagementMetrics(total_likes=-1)

        assert "total_likes" in str(exc_info.value)

    def test_metrics_negative_total_reshares_raises_error(self):
        """total_reshares < 0 should raise ValidationError."""
        from prism.simulation.state import EngagementMetrics

        with pytest.raises(ValidationError) as exc_info:
            EngagementMetrics(total_reshares=-1)

        assert "total_reshares" in str(exc_info.value)

    def test_metrics_negative_total_replies_raises_error(self):
        """total_replies < 0 should raise ValidationError."""
        from prism.simulation.state import EngagementMetrics

        with pytest.raises(ValidationError) as exc_info:
            EngagementMetrics(total_replies=-1)

        assert "total_replies" in str(exc_info.value)

    def test_metrics_negative_posts_created_raises_error(self):
        """posts_created < 0 should raise ValidationError."""
        from prism.simulation.state import EngagementMetrics

        with pytest.raises(ValidationError) as exc_info:
            EngagementMetrics(posts_created=-1)

        assert "posts_created" in str(exc_info.value)


class TestEngagementMetricsIncrements:
    """T009: Test EngagementMetrics increment methods."""

    def test_increment_like_increases_total_likes(self):
        """increment_like should increase total_likes by 1."""
        from prism.simulation.state import EngagementMetrics

        metrics = EngagementMetrics()
        metrics.increment_like()
        assert metrics.total_likes == 1

    def test_increment_like_multiple_times(self):
        """increment_like should accumulate."""
        from prism.simulation.state import EngagementMetrics

        metrics = EngagementMetrics()
        metrics.increment_like()
        metrics.increment_like()
        metrics.increment_like()
        assert metrics.total_likes == 3

    def test_increment_reshare_increases_total_reshares(self):
        """increment_reshare should increase total_reshares by 1."""
        from prism.simulation.state import EngagementMetrics

        metrics = EngagementMetrics()
        metrics.increment_reshare()
        assert metrics.total_reshares == 1

    def test_increment_reply_increases_total_replies(self):
        """increment_reply should increase total_replies by 1."""
        from prism.simulation.state import EngagementMetrics

        metrics = EngagementMetrics()
        metrics.increment_reply()
        assert metrics.total_replies == 1

    def test_increment_post_created_increases_posts_created(self):
        """increment_post_created should increase posts_created by 1."""
        from prism.simulation.state import EngagementMetrics

        metrics = EngagementMetrics()
        metrics.increment_post_created()
        assert metrics.posts_created == 1


class TestSimulationStateRequiredFields:
    """T011: Test SimulationState with required fields."""

    def test_state_has_posts_field(self):
        """SimulationState should have posts field of type list[Post]."""
        from prism.simulation.state import SimulationState
        from prism.statechart.statechart import Statechart
        from prism.statechart.states import AgentState

        # Create minimal statechart
        statechart = Statechart(
            states={AgentState.IDLE, AgentState.SCROLLING},
            transitions=[],
            initial=AgentState.IDLE,
        )
        # Create mock agent
        agent = MagicMock()
        agent.state = AgentState.IDLE

        state = SimulationState(
            posts=[],
            agents=[agent],
            statechart=statechart,
        )
        assert state.posts == []
        assert isinstance(state.posts, list)

    def test_state_has_agents_field(self):
        """SimulationState should have agents field."""
        from prism.simulation.state import SimulationState
        from prism.statechart.statechart import Statechart
        from prism.statechart.states import AgentState

        statechart = Statechart(
            states={AgentState.IDLE, AgentState.SCROLLING},
            transitions=[],
            initial=AgentState.IDLE,
        )
        agent = MagicMock()
        agent.state = AgentState.IDLE

        state = SimulationState(
            posts=[],
            agents=[agent],
            statechart=statechart,
        )
        assert state.agents == [agent]

    def test_state_has_round_number_field(self):
        """SimulationState should have round_number field defaulting to 0."""
        from prism.simulation.state import SimulationState
        from prism.statechart.statechart import Statechart
        from prism.statechart.states import AgentState

        statechart = Statechart(
            states={AgentState.IDLE},
            transitions=[],
            initial=AgentState.IDLE,
        )
        agent = MagicMock()
        agent.state = AgentState.IDLE

        state = SimulationState(
            posts=[],
            agents=[agent],
            statechart=statechart,
        )
        assert state.round_number == 0

    def test_state_has_metrics_field(self):
        """SimulationState should have metrics field of type EngagementMetrics."""
        from prism.simulation.state import EngagementMetrics, SimulationState
        from prism.statechart.statechart import Statechart
        from prism.statechart.states import AgentState

        statechart = Statechart(
            states={AgentState.IDLE},
            transitions=[],
            initial=AgentState.IDLE,
        )
        agent = MagicMock()
        agent.state = AgentState.IDLE

        state = SimulationState(
            posts=[],
            agents=[agent],
            statechart=statechart,
        )
        assert isinstance(state.metrics, EngagementMetrics)

    def test_state_has_statechart_field(self):
        """SimulationState should have statechart field."""
        from prism.simulation.state import SimulationState
        from prism.statechart.statechart import Statechart
        from prism.statechart.states import AgentState

        statechart = Statechart(
            states={AgentState.IDLE},
            transitions=[],
            initial=AgentState.IDLE,
        )
        agent = MagicMock()
        agent.state = AgentState.IDLE

        state = SimulationState(
            posts=[],
            agents=[agent],
            statechart=statechart,
        )
        assert state.statechart is statechart


class TestSimulationStateValidation:
    """T013: Test SimulationState validates non-empty agents."""

    def test_empty_agents_raises_error(self):
        """Empty agents list should raise ValueError."""
        from prism.simulation.state import SimulationState
        from prism.statechart.statechart import Statechart
        from prism.statechart.states import AgentState

        statechart = Statechart(
            states={AgentState.IDLE},
            transitions=[],
            initial=AgentState.IDLE,
        )

        with pytest.raises(ValueError) as exc_info:
            SimulationState(
                posts=[],
                agents=[],  # Empty!
                statechart=statechart,
            )

        assert "agents" in str(exc_info.value).lower()


class TestSimulationStateDistribution:
    """T015: Test get_state_distribution returns dict."""

    def test_get_state_distribution_returns_dict(self):
        """get_state_distribution should return dict[AgentState, int]."""
        from prism.simulation.state import SimulationState
        from prism.statechart.statechart import Statechart
        from prism.statechart.states import AgentState

        statechart = Statechart(
            states={AgentState.IDLE, AgentState.SCROLLING},
            transitions=[],
            initial=AgentState.IDLE,
        )
        agent1 = MagicMock()
        agent1.state = AgentState.IDLE
        agent2 = MagicMock()
        agent2.state = AgentState.SCROLLING

        state = SimulationState(
            posts=[],
            agents=[agent1, agent2],
            statechart=statechart,
        )

        distribution = state.get_state_distribution()

        assert isinstance(distribution, dict)
        assert distribution[AgentState.IDLE] == 1
        assert distribution[AgentState.SCROLLING] == 1


class TestSimulationStateAddPost:
    """T017: Test add_post adds to posts and increments metrics."""

    def test_add_post_appends_to_posts_list(self):
        """add_post should append post to posts list."""
        from prism.rag.models import Post
        from prism.simulation.state import SimulationState
        from prism.statechart.statechart import Statechart
        from prism.statechart.states import AgentState

        statechart = Statechart(
            states={AgentState.IDLE},
            transitions=[],
            initial=AgentState.IDLE,
        )
        agent = MagicMock()
        agent.state = AgentState.IDLE

        state = SimulationState(
            posts=[],
            agents=[agent],
            statechart=statechart,
        )

        post = Post(
            id="post_001",
            author_id="agent_1",
            text="Test post",
            timestamp=datetime.now(),
        )
        state.add_post(post)

        assert len(state.posts) == 1
        assert state.posts[0] == post

    def test_add_post_increments_posts_created(self):
        """add_post should increment metrics.posts_created."""
        from prism.rag.models import Post
        from prism.simulation.state import SimulationState
        from prism.statechart.statechart import Statechart
        from prism.statechart.states import AgentState

        statechart = Statechart(
            states={AgentState.IDLE},
            transitions=[],
            initial=AgentState.IDLE,
        )
        agent = MagicMock()
        agent.state = AgentState.IDLE

        state = SimulationState(
            posts=[],
            agents=[agent],
            statechart=statechart,
        )

        post = Post(
            id="post_001",
            author_id="agent_1",
            text="Test post",
            timestamp=datetime.now(),
        )
        state.add_post(post)

        assert state.metrics.posts_created == 1


class TestSimulationStateAdvanceRound:
    """T019: Test advance_round increments round_number."""

    def test_advance_round_increments_round_number(self):
        """advance_round should increment round_number by 1."""
        from prism.simulation.state import SimulationState
        from prism.statechart.statechart import Statechart
        from prism.statechart.states import AgentState

        statechart = Statechart(
            states={AgentState.IDLE},
            transitions=[],
            initial=AgentState.IDLE,
        )
        agent = MagicMock()
        agent.state = AgentState.IDLE

        state = SimulationState(
            posts=[],
            agents=[agent],
            statechart=statechart,
        )

        assert state.round_number == 0
        state.advance_round()
        assert state.round_number == 1
        state.advance_round()
        assert state.round_number == 2
