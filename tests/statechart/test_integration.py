"""Integration tests for statechart system.

These tests verify that all statechart components work together correctly:
- Statechart engine with SocialAgent
- State transitions and history recording
- Timeout detection and recovery
- Reasoner invocation for ambiguous transitions (with mock LLM)
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from prism.agents.social_agent import SocialAgent
from prism.statechart import (
    AgentState,
    Statechart,
    StatechartReasoner,
    StateTransition,
    Transition,
    agents_in_state,
    state_distribution,
)


class TestStatechartIntegration:
    """Integration tests for statechart with SocialAgent."""

    def _create_social_agent_statechart(self) -> Statechart:
        """Create a statechart with typical social agent states and transitions."""
        states = {
            AgentState.IDLE,
            AgentState.SCROLLING,
            AgentState.EVALUATING,
            AgentState.COMPOSING,
            AgentState.ENGAGING_LIKE,
            AgentState.ENGAGING_REPLY,
            AgentState.ENGAGING_RESHARE,
            AgentState.RESTING,
        }

        transitions = [
            # IDLE -> SCROLLING (start browsing)
            Transition(
                trigger="start",
                source=AgentState.IDLE,
                target=AgentState.SCROLLING,
            ),
            # SCROLLING -> EVALUATING (see interesting post)
            Transition(
                trigger="see_post",
                source=AgentState.SCROLLING,
                target=AgentState.EVALUATING,
                guard=lambda agent, ctx: ctx and ctx.get("relevance", 0) > 0.3,
            ),
            # SCROLLING -> SCROLLING (skip post)
            Transition(
                trigger="see_post",
                source=AgentState.SCROLLING,
                target=AgentState.SCROLLING,
            ),
            # EVALUATING -> ENGAGING_LIKE (like post)
            Transition(
                trigger="engage",
                source=AgentState.EVALUATING,
                target=AgentState.ENGAGING_LIKE,
            ),
            # EVALUATING -> ENGAGING_REPLY (reply to post)
            Transition(
                trigger="engage",
                source=AgentState.EVALUATING,
                target=AgentState.ENGAGING_REPLY,
            ),
            # EVALUATING -> SCROLLING (pass on post)
            Transition(
                trigger="pass",
                source=AgentState.EVALUATING,
                target=AgentState.SCROLLING,
            ),
            # ENGAGING_* -> SCROLLING (continue after engagement)
            Transition(
                trigger="done",
                source=AgentState.ENGAGING_LIKE,
                target=AgentState.SCROLLING,
            ),
            Transition(
                trigger="done",
                source=AgentState.ENGAGING_REPLY,
                target=AgentState.SCROLLING,
            ),
            # SCROLLING -> RESTING (timeout recovery)
            Transition(
                trigger="timeout",
                source=AgentState.SCROLLING,
                target=AgentState.RESTING,
            ),
            # RESTING -> IDLE (return from rest)
            Transition(
                trigger="wake",
                source=AgentState.RESTING,
                target=AgentState.IDLE,
            ),
        ]

        return Statechart(
            states=states,
            transitions=transitions,
            initial=AgentState.IDLE,
        )

    def test_statechart_with_agent_transitions(self) -> None:
        """Statechart should manage state transitions for an agent."""
        mock_client = MagicMock()
        agent = SocialAgent(
            agent_id="test_agent_001",
            name="Test Agent",
            interests=["technology"],
            personality="curious",
            client=mock_client,
        )

        statechart = self._create_social_agent_statechart()

        # Initial state
        assert agent.state == AgentState.IDLE

        # Fire 'start' trigger
        new_state = statechart.fire(
            trigger="start",
            current_state=agent.state,
            agent=agent,
            context=None,
        )
        assert new_state == AgentState.SCROLLING

        # Apply the transition
        agent.transition_to(new_state, trigger="start")
        assert agent.state == AgentState.SCROLLING
        assert len(agent.state_history) == 1

    def test_guard_evaluation_with_context(self) -> None:
        """Statechart guards should evaluate with agent and context."""
        mock_client = MagicMock()
        agent = SocialAgent(
            agent_id="test_agent_002",
            name="Evaluator",
            interests=["AI"],
            personality="analytical",
            client=mock_client,
        )

        statechart = self._create_social_agent_statechart()

        # Move to SCROLLING first
        agent.transition_to(AgentState.SCROLLING, trigger="start")

        # See post with high relevance - should go to EVALUATING
        high_relevance_ctx = {"relevance": 0.8, "post_id": "123"}
        new_state = statechart.fire(
            trigger="see_post",
            current_state=agent.state,
            agent=agent,
            context=high_relevance_ctx,
        )
        assert new_state == AgentState.EVALUATING

        # Reset and try with low relevance - should stay SCROLLING
        agent.transition_to(AgentState.SCROLLING, trigger="reset")
        low_relevance_ctx = {"relevance": 0.1, "post_id": "456"}
        new_state = statechart.fire(
            trigger="see_post",
            current_state=agent.state,
            agent=agent,
            context=low_relevance_ctx,
        )
        assert new_state == AgentState.SCROLLING

    def test_state_history_recording(self) -> None:
        """Agent should record state transitions in history."""
        mock_client = MagicMock()
        agent = SocialAgent(
            agent_id="test_agent_003",
            name="Historian",
            interests=["history"],
            personality="meticulous",
            client=mock_client,
        )

        # Make several transitions
        agent.transition_to(AgentState.SCROLLING, trigger="start")
        agent.transition_to(AgentState.EVALUATING, trigger="see_post")
        agent.transition_to(AgentState.ENGAGING_LIKE, trigger="engage")
        agent.transition_to(AgentState.SCROLLING, trigger="done")

        # Check history
        assert len(agent.state_history) == 4

        # Verify first transition
        first = agent.state_history[0]
        assert isinstance(first, StateTransition)
        assert first.from_state == AgentState.IDLE
        assert first.to_state == AgentState.SCROLLING
        assert first.trigger == "start"

        # Verify last transition
        last = agent.state_history[-1]
        assert last.from_state == AgentState.ENGAGING_LIKE
        assert last.to_state == AgentState.SCROLLING
        assert last.trigger == "done"

    def test_timeout_detection_and_recovery(self) -> None:
        """Agent should detect timeout and allow recovery."""
        mock_client = MagicMock()
        agent = SocialAgent(
            agent_id="test_agent_004",
            name="Timeout Test",
            interests=["testing"],
            personality="patient",
            client=mock_client,
            timeout_threshold=3,
        )

        statechart = self._create_social_agent_statechart()

        # Move to SCROLLING
        agent.transition_to(AgentState.SCROLLING, trigger="start")
        assert agent.ticks_in_state == 0
        assert agent.is_timed_out() is False

        # Tick until timeout
        for i in range(4):
            agent.tick()

        assert agent.ticks_in_state == 4
        assert agent.is_timed_out() is True

        # Fire timeout transition to recover
        new_state = statechart.fire(
            trigger="timeout",
            current_state=agent.state,
            agent=agent,
            context=None,
        )
        assert new_state == AgentState.RESTING

        # Apply transition - should reset ticks
        agent.transition_to(new_state, trigger="timeout")
        assert agent.state == AgentState.RESTING
        assert agent.ticks_in_state == 0
        assert agent.is_timed_out() is False

    @pytest.mark.asyncio
    async def test_reasoner_for_ambiguous_transitions(self) -> None:
        """Reasoner should decide between multiple valid target states."""
        mock_llm_client = MagicMock()
        mock_llm_client.run = AsyncMock(return_value='{"next_state": "engaging_like"}')

        mock_agent_client = MagicMock()
        agent = SocialAgent(
            agent_id="test_agent_005",
            name="Decider",
            interests=["decisions"],
            personality="thoughtful",
            client=mock_agent_client,
        )

        reasoner = StatechartReasoner(client=mock_llm_client)

        # Agent is evaluating a post - multiple engagement options available
        agent.transition_to(AgentState.EVALUATING, trigger="see_post")

        # Ask reasoner to decide between LIKE and REPLY
        options = [AgentState.ENGAGING_LIKE, AgentState.ENGAGING_REPLY]
        context = {"post_id": "789", "content": "Interesting AI research"}

        result = await reasoner.decide(
            agent=agent,
            current_state=agent.state,
            trigger="engage",
            options=options,
            context=context,
        )

        # Reasoner should return one of the valid options
        assert result in options
        assert result == AgentState.ENGAGING_LIKE  # Based on mock response

    @pytest.mark.asyncio
    async def test_reasoner_fallback_on_parse_error(self) -> None:
        """Reasoner should fallback to first option on parse error."""
        mock_llm_client = MagicMock()
        mock_llm_client.run = AsyncMock(return_value="invalid json response")

        mock_agent_client = MagicMock()
        agent = SocialAgent(
            agent_id="test_agent_006",
            name="Fallback Test",
            interests=["testing"],
            personality="resilient",
            client=mock_agent_client,
        )

        reasoner = StatechartReasoner(client=mock_llm_client)

        options = [AgentState.SCROLLING, AgentState.EVALUATING]

        result = await reasoner.decide(
            agent=agent,
            current_state=AgentState.IDLE,
            trigger="test",
            options=options,
            context=None,
        )

        # Should return first option as fallback
        assert result == options[0]
        assert result == AgentState.SCROLLING


class TestQueryIntegration:
    """Integration tests for query functions with multiple agents."""

    def test_agents_in_state_with_social_agents(self) -> None:
        """agents_in_state() should work with actual SocialAgent instances."""
        mock_client = MagicMock()

        agents = [
            SocialAgent(
                agent_id=f"agent_{i}",
                name=f"Agent {i}",
                interests=["testing"],
                personality="test",
                client=mock_client,
            )
            for i in range(5)
        ]

        # Transition some agents
        agents[0].transition_to(AgentState.SCROLLING, trigger="start")
        agents[1].transition_to(AgentState.SCROLLING, trigger="start")
        agents[2].transition_to(AgentState.EVALUATING, trigger="see_post")

        # Query counts
        assert agents_in_state(AgentState.IDLE, agents) == 2
        assert agents_in_state(AgentState.SCROLLING, agents) == 2
        assert agents_in_state(AgentState.EVALUATING, agents) == 1
        assert agents_in_state(AgentState.COMPOSING, agents) == 0

    def test_state_distribution_with_social_agents(self) -> None:
        """state_distribution() should work with actual SocialAgent instances."""
        mock_client = MagicMock()

        agents = [
            SocialAgent(
                agent_id=f"agent_{i}",
                name=f"Agent {i}",
                interests=["testing"],
                personality="test",
                client=mock_client,
            )
            for i in range(10)
        ]

        # Transition agents to various states
        agents[0].transition_to(AgentState.SCROLLING, trigger="start")
        agents[1].transition_to(AgentState.SCROLLING, trigger="start")
        agents[2].transition_to(AgentState.SCROLLING, trigger="start")
        agents[3].transition_to(AgentState.EVALUATING, trigger="see_post")
        agents[4].transition_to(AgentState.ENGAGING_LIKE, trigger="engage")

        # Get distribution
        dist = state_distribution(agents)

        # Verify counts
        assert dist[AgentState.IDLE] == 5  # agents 5-9 still IDLE
        assert dist[AgentState.SCROLLING] == 3
        assert dist[AgentState.EVALUATING] == 1
        assert dist[AgentState.ENGAGING_LIKE] == 1
        assert dist[AgentState.COMPOSING] == 0
        assert dist[AgentState.RESTING] == 0

        # Total should be 10
        assert sum(dist.values()) == 10

    def test_full_workflow_integration(self) -> None:
        """Full workflow: statechart + agent + queries working together."""
        mock_client = MagicMock()

        # Create statechart
        states = {AgentState.IDLE, AgentState.SCROLLING, AgentState.RESTING}
        transitions = [
            Transition(
                trigger="start",
                source=AgentState.IDLE,
                target=AgentState.SCROLLING,
            ),
            Transition(
                trigger="rest",
                source=AgentState.SCROLLING,
                target=AgentState.RESTING,
            ),
            Transition(
                trigger="wake",
                source=AgentState.RESTING,
                target=AgentState.IDLE,
            ),
        ]
        statechart = Statechart(
            states=states, transitions=transitions, initial=AgentState.IDLE
        )

        # Create agents
        agents = [
            SocialAgent(
                agent_id=f"agent_{i}",
                name=f"Agent {i}",
                interests=["testing"],
                personality="test",
                client=mock_client,
            )
            for i in range(3)
        ]

        # All start IDLE
        dist = state_distribution(agents)
        assert dist[AgentState.IDLE] == 3

        # Fire transitions
        for agent in agents:
            new_state = statechart.fire("start", agent.state, agent, None)
            if new_state:
                agent.transition_to(new_state, trigger="start")

        # All should be SCROLLING now
        dist = state_distribution(agents)
        assert dist[AgentState.IDLE] == 0
        assert dist[AgentState.SCROLLING] == 3

        # Rest one agent
        new_state = statechart.fire("rest", agents[0].state, agents[0], None)
        if new_state:
            agents[0].transition_to(new_state, trigger="rest")

        # Check final distribution
        dist = state_distribution(agents)
        assert dist[AgentState.SCROLLING] == 2
        assert dist[AgentState.RESTING] == 1
