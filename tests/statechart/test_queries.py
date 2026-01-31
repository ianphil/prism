"""Tests for statechart query functions."""

from unittest.mock import MagicMock

from prism.statechart.queries import agents_in_state, state_distribution
from prism.statechart.states import AgentState

# =============================================================================
# T040: Tests for agents_in_state()
# =============================================================================


class TestAgentsInState:
    """Tests for agents_in_state() query function."""

    def test_returns_count_of_agents_in_given_state(self) -> None:
        """agents_in_state() should return count of agents in the specified state."""
        # Create mock agents with different states
        agent1 = MagicMock()
        agent1.state = AgentState.IDLE

        agent2 = MagicMock()
        agent2.state = AgentState.IDLE

        agent3 = MagicMock()
        agent3.state = AgentState.SCROLLING

        agents = [agent1, agent2, agent3]

        # Two agents are IDLE
        assert agents_in_state(AgentState.IDLE, agents) == 2
        # One agent is SCROLLING
        assert agents_in_state(AgentState.SCROLLING, agents) == 1

    def test_returns_zero_for_empty_list(self) -> None:
        """agents_in_state() should return 0 for empty agent list."""
        agents: list = []

        assert agents_in_state(AgentState.IDLE, agents) == 0

    def test_returns_zero_when_no_agents_in_state(self) -> None:
        """agents_in_state() should return 0 when no agents are in the state."""
        agent1 = MagicMock()
        agent1.state = AgentState.SCROLLING

        agent2 = MagicMock()
        agent2.state = AgentState.EVALUATING

        agents = [agent1, agent2]

        # No agents are IDLE
        assert agents_in_state(AgentState.IDLE, agents) == 0

    def test_counts_all_agent_states(self) -> None:
        """agents_in_state() should work for all AgentState values."""
        # Create agents in various states
        agent_idle = MagicMock()
        agent_idle.state = AgentState.IDLE

        agent_scrolling = MagicMock()
        agent_scrolling.state = AgentState.SCROLLING

        agent_evaluating = MagicMock()
        agent_evaluating.state = AgentState.EVALUATING

        agent_composing = MagicMock()
        agent_composing.state = AgentState.COMPOSING

        agent_like = MagicMock()
        agent_like.state = AgentState.ENGAGING_LIKE

        agent_reply = MagicMock()
        agent_reply.state = AgentState.ENGAGING_REPLY

        agent_reshare = MagicMock()
        agent_reshare.state = AgentState.ENGAGING_RESHARE

        agent_resting = MagicMock()
        agent_resting.state = AgentState.RESTING

        agents = [
            agent_idle,
            agent_scrolling,
            agent_evaluating,
            agent_composing,
            agent_like,
            agent_reply,
            agent_reshare,
            agent_resting,
        ]

        # Each state should have exactly one agent
        for state in AgentState:
            assert agents_in_state(state, agents) == 1


# =============================================================================
# T042: Tests for state_distribution()
# =============================================================================


class TestStateDistribution:
    """Tests for state_distribution() query function."""

    def test_returns_dict_mapping_state_to_count(self) -> None:
        """state_distribution() should return dict mapping AgentState to count."""
        agent1 = MagicMock()
        agent1.state = AgentState.IDLE

        agent2 = MagicMock()
        agent2.state = AgentState.SCROLLING

        agents = [agent1, agent2]

        result = state_distribution(agents)

        assert isinstance(result, dict)
        assert result[AgentState.IDLE] == 1
        assert result[AgentState.SCROLLING] == 1

    def test_all_states_present_in_result(self) -> None:
        """state_distribution() should include all AgentState values in result."""
        # Empty list should still have all states with 0 count
        agents: list = []

        result = state_distribution(agents)

        # All states should be present
        for state in AgentState:
            assert state in result
            assert result[state] == 0

    def test_correct_counts_for_mixed_states(self) -> None:
        """state_distribution() should return correct counts for mixed states."""
        # Create agents with uneven distribution
        agents = []

        # 3 IDLE agents
        for _ in range(3):
            agent = MagicMock()
            agent.state = AgentState.IDLE
            agents.append(agent)

        # 2 SCROLLING agents
        for _ in range(2):
            agent = MagicMock()
            agent.state = AgentState.SCROLLING
            agents.append(agent)

        # 1 EVALUATING agent
        agent = MagicMock()
        agent.state = AgentState.EVALUATING
        agents.append(agent)

        result = state_distribution(agents)

        assert result[AgentState.IDLE] == 3
        assert result[AgentState.SCROLLING] == 2
        assert result[AgentState.EVALUATING] == 1
        # Other states should be 0
        assert result[AgentState.COMPOSING] == 0
        assert result[AgentState.ENGAGING_LIKE] == 0
        assert result[AgentState.ENGAGING_REPLY] == 0
        assert result[AgentState.ENGAGING_RESHARE] == 0
        assert result[AgentState.RESTING] == 0

    def test_empty_list_returns_all_zeros(self) -> None:
        """state_distribution() should return all zeros for empty list."""
        agents: list = []

        result = state_distribution(agents)

        # Total should be 0
        total = sum(result.values())
        assert total == 0

        # All counts should be 0
        for state in AgentState:
            assert result[state] == 0

    def test_returns_correct_total_count(self) -> None:
        """state_distribution() counts should sum to total agents."""
        agents = []
        for i in range(10):
            agent = MagicMock()
            agent.state = list(AgentState)[i % len(AgentState)]
            agents.append(agent)

        result = state_distribution(agents)

        # Total should equal number of agents
        total = sum(result.values())
        assert total == 10
