"""Tests for SocialAgent class."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from prism.agents.decision import AgentDecision
from prism.agents.social_agent import SocialAgent


class TestSocialAgentConstruction:
    """Tests for SocialAgent construction."""

    def test_construction_with_profile_data(self):
        """SocialAgent should accept profile data at construction."""
        mock_client = MagicMock()

        agent = SocialAgent(
            agent_id="agent_001",
            name="Alice",
            interests=["technology", "AI"],
            personality="curious and analytical",
            client=mock_client,
        )

        assert agent.agent_id == "agent_001"
        assert agent.name == "Alice"
        assert agent.interests == ["technology", "AI"]
        assert agent.personality == "curious and analytical"

    def test_stores_client_reference(self):
        """SocialAgent should store the client reference."""
        mock_client = MagicMock()

        agent = SocialAgent(
            agent_id="agent_002",
            name="Bob",
            interests=["sports"],
            personality="enthusiastic",
            client=mock_client,
        )

        assert agent._client is mock_client

    def test_raises_value_error_for_empty_interests(self):
        """SocialAgent should raise ValueError if interests is empty."""
        mock_client = MagicMock()

        with pytest.raises(ValueError, match="interests must be a non-empty list"):
            SocialAgent(
                agent_id="agent_invalid",
                name="Nobody",
                interests=[],
                personality="undefined",
                client=mock_client,
            )


class TestSocialAgentDecide:
    """Tests for SocialAgent.decide() method."""

    @pytest.mark.asyncio
    async def test_decide_returns_agent_decision(self):
        """decide() should return an AgentDecision instance."""
        # Mock the client and agent
        mock_agent = MagicMock()
        mock_response = MagicMock()
        mock_response.value = None
        mock_response.text = json.dumps(
            {
                "choice": "LIKE",
                "reason": "This aligns with my interests.",
                "content": None,
            }
        )
        mock_agent.run = AsyncMock(return_value=mock_response)

        mock_client = MagicMock()
        mock_client.as_agent.return_value = mock_agent

        agent = SocialAgent(
            agent_id="agent_003",
            name="Charlie",
            interests=["tech"],
            personality="analytical",
            client=mock_client,
        )

        decision = await agent.decide("Check out this new tech gadget!")

        assert isinstance(decision, AgentDecision)
        assert decision.choice == "LIKE"

    @pytest.mark.asyncio
    async def test_decide_parses_json_from_text(self):
        """decide() should parse JSON from response.text when value is None."""
        mock_agent = MagicMock()
        mock_response = MagicMock()
        mock_response.value = None  # Ollama doesn't populate .value
        mock_response.text = json.dumps(
            {
                "choice": "REPLY",
                "reason": "I want to share my thoughts on this.",
                "content": "Great point! I agree completely.",
            }
        )
        mock_agent.run = AsyncMock(return_value=mock_response)

        mock_client = MagicMock()
        mock_client.as_agent.return_value = mock_agent

        agent = SocialAgent(
            agent_id="agent_004",
            name="Dana",
            interests=["discussion"],
            personality="talkative",
            client=mock_client,
        )

        decision = await agent.decide("What do you think about AI?")

        assert decision.choice == "REPLY"
        assert decision.content == "Great point! I agree completely."

    @pytest.mark.asyncio
    async def test_decide_fallback_scroll_on_parse_failure(self):
        """decide() should return SCROLL on JSON parse failure."""
        mock_agent = MagicMock()
        mock_response = MagicMock()
        mock_response.value = None
        mock_response.text = "This is not valid JSON at all!"
        mock_agent.run = AsyncMock(return_value=mock_response)

        mock_client = MagicMock()
        mock_client.as_agent.return_value = mock_agent

        agent = SocialAgent(
            agent_id="agent_005",
            name="Eve",
            interests=["anything"],
            personality="easygoing",
            client=mock_client,
        )

        decision = await agent.decide("Some post content")

        assert decision.choice == "SCROLL"
        assert "parse" in decision.reason.lower() or "error" in decision.reason.lower()

    @pytest.mark.asyncio
    async def test_decide_fallback_scroll_on_validation_failure(self):
        """decide() should return SCROLL when JSON is valid but validation fails."""
        mock_agent = MagicMock()
        mock_response = MagicMock()
        mock_response.value = None
        # Valid JSON but missing required content for REPLY
        mock_response.text = json.dumps(
            {
                "choice": "REPLY",
                "reason": "I want to reply",
                "content": None,  # Invalid: REPLY requires content
            }
        )
        mock_agent.run = AsyncMock(return_value=mock_response)

        mock_client = MagicMock()
        mock_client.as_agent.return_value = mock_agent

        agent = SocialAgent(
            agent_id="agent_006",
            name="Frank",
            interests=["tech"],
            personality="brief",
            client=mock_client,
        )

        decision = await agent.decide("Some post")

        assert decision.choice == "SCROLL"
        assert decision.reason  # Should have an error reason

    @pytest.mark.asyncio
    async def test_decide_uses_structured_output_when_available(self):
        """decide() should use response.value when populated."""
        mock_agent = MagicMock()
        mock_response = MagicMock()
        # Simulate structured output being populated
        mock_response.value = AgentDecision(
            choice="RESHARE",
            reason="This is important news.",
            content="Everyone should see this!",
        )
        mock_response.text = "some text"
        mock_agent.run = AsyncMock(return_value=mock_response)

        mock_client = MagicMock()
        mock_client.as_agent.return_value = mock_agent

        agent = SocialAgent(
            agent_id="agent_007",
            name="Grace",
            interests=["news"],
            personality="informative",
            client=mock_client,
        )

        decision = await agent.decide("Breaking news!")

        assert decision.choice == "RESHARE"
        assert decision.content == "Everyone should see this!"


class TestSocialAgentOptions:
    """Tests for SocialAgent configuration options."""

    @pytest.mark.asyncio
    async def test_passes_temperature_to_agent_run(self):
        """decide() should pass temperature option to agent.run()."""
        mock_agent = MagicMock()
        mock_response = MagicMock()
        mock_response.value = None
        mock_response.text = json.dumps(
            {
                "choice": "SCROLL",
                "reason": "Not interested.",
                "content": None,
            }
        )
        mock_agent.run = AsyncMock(return_value=mock_response)

        mock_client = MagicMock()
        mock_client.as_agent.return_value = mock_agent

        agent = SocialAgent(
            agent_id="agent_008",
            name="Henry",
            interests=["misc"],
            personality="neutral",
            client=mock_client,
            temperature=0.5,
            max_tokens=256,
        )

        await agent.decide("Some post")

        # Verify run was called with options
        mock_agent.run.assert_called_once()
        call_kwargs = mock_agent.run.call_args
        assert "options" in call_kwargs.kwargs or len(call_kwargs.args) > 1


# =============================================================================
# Phase 4: Timeout Transitions (T024-T029)
# =============================================================================


class TestSocialAgentTick:
    """Tests for SocialAgent.tick() method (T024)."""

    def test_tick_increments_ticks_in_state(self) -> None:
        """tick() should increment ticks_in_state by 1."""
        mock_client = MagicMock()
        agent = SocialAgent(
            agent_id="agent_tick_001",
            name="Ticker",
            interests=["time"],
            personality="punctual",
            client=mock_client,
        )

        initial_ticks = agent.ticks_in_state
        agent.tick()

        assert agent.ticks_in_state == initial_ticks + 1

    def test_tick_starts_at_zero(self) -> None:
        """New agents should start with ticks_in_state = 0."""
        mock_client = MagicMock()
        agent = SocialAgent(
            agent_id="agent_tick_002",
            name="Fresh",
            interests=["new"],
            personality="fresh",
            client=mock_client,
        )

        assert agent.ticks_in_state == 0

    def test_multiple_ticks_accumulate(self) -> None:
        """Multiple tick() calls should accumulate."""
        mock_client = MagicMock()
        agent = SocialAgent(
            agent_id="agent_tick_003",
            name="Counter",
            interests=["counting"],
            personality="precise",
            client=mock_client,
        )

        for _ in range(5):
            agent.tick()

        assert agent.ticks_in_state == 5


class TestSocialAgentIsTimedOut:
    """Tests for SocialAgent.is_timed_out() method (T026)."""

    def test_is_timed_out_false_when_under_threshold(self) -> None:
        """is_timed_out() should return False when ticks < threshold."""
        mock_client = MagicMock()
        agent = SocialAgent(
            agent_id="agent_timeout_001",
            name="Patient",
            interests=["waiting"],
            personality="patient",
            client=mock_client,
            timeout_threshold=5,
        )

        # Tick 3 times (under threshold of 5)
        for _ in range(3):
            agent.tick()

        assert agent.is_timed_out() is False

    def test_is_timed_out_false_at_exact_threshold(self) -> None:
        """is_timed_out() should return False when ticks == threshold."""
        mock_client = MagicMock()
        agent = SocialAgent(
            agent_id="agent_timeout_002",
            name="Edge",
            interests=["boundaries"],
            personality="precise",
            client=mock_client,
            timeout_threshold=5,
        )

        # Tick exactly 5 times
        for _ in range(5):
            agent.tick()

        assert agent.is_timed_out() is False

    def test_is_timed_out_true_when_over_threshold(self) -> None:
        """is_timed_out() should return True when ticks > threshold."""
        mock_client = MagicMock()
        agent = SocialAgent(
            agent_id="agent_timeout_003",
            name="Overdue",
            interests=["delays"],
            personality="slow",
            client=mock_client,
            timeout_threshold=5,
        )

        # Tick 6 times (over threshold of 5)
        for _ in range(6):
            agent.tick()

        assert agent.is_timed_out() is True


class TestSocialAgentTimeoutThreshold:
    """Tests for SocialAgent timeout_threshold parameter (T028)."""

    def test_timeout_threshold_default_is_five(self) -> None:
        """Default timeout_threshold should be 5."""
        mock_client = MagicMock()
        agent = SocialAgent(
            agent_id="agent_default_001",
            name="Default",
            interests=["defaults"],
            personality="standard",
            client=mock_client,
        )

        assert agent.timeout_threshold == 5

    def test_timeout_threshold_can_be_set_at_construction(self) -> None:
        """timeout_threshold should be settable at construction."""
        mock_client = MagicMock()
        agent = SocialAgent(
            agent_id="agent_custom_001",
            name="Custom",
            interests=["customization"],
            personality="unique",
            client=mock_client,
            timeout_threshold=10,
        )

        assert agent.timeout_threshold == 10

    def test_timeout_threshold_must_be_positive(self) -> None:
        """timeout_threshold must be > 0."""
        mock_client = MagicMock()

        with pytest.raises(ValueError, match="timeout_threshold"):
            SocialAgent(
                agent_id="agent_invalid_001",
                name="Invalid",
                interests=["errors"],
                personality="problematic",
                client=mock_client,
                timeout_threshold=0,
            )

    def test_timeout_threshold_negative_raises_error(self) -> None:
        """Negative timeout_threshold should raise ValueError."""
        mock_client = MagicMock()

        with pytest.raises(ValueError, match="timeout_threshold"):
            SocialAgent(
                agent_id="agent_invalid_002",
                name="Negative",
                interests=["errors"],
                personality="problematic",
                client=mock_client,
                timeout_threshold=-1,
            )


# =============================================================================
# Phase 5: SocialAgent Integration (T030-T039)
# =============================================================================


class TestSocialAgentStateField:
    """Tests for SocialAgent.state field (T030)."""

    def test_state_default_is_idle(self) -> None:
        """Default state should be AgentState.IDLE."""
        from prism.statechart.states import AgentState

        mock_client = MagicMock()
        agent = SocialAgent(
            agent_id="agent_state_001",
            name="Default",
            interests=["defaults"],
            personality="standard",
            client=mock_client,
        )

        assert agent.state == AgentState.IDLE

    def test_state_can_be_set_to_any_valid_state(self) -> None:
        """state should be assignable to any valid AgentState."""
        from prism.statechart.states import AgentState

        mock_client = MagicMock()
        agent = SocialAgent(
            agent_id="agent_state_002",
            name="Flexible",
            interests=["states"],
            personality="adaptable",
            client=mock_client,
        )

        # Assign to a different state
        agent.state = AgentState.SCROLLING
        assert agent.state == AgentState.SCROLLING

        agent.state = AgentState.EVALUATING
        assert agent.state == AgentState.EVALUATING

        agent.state = AgentState.COMPOSING
        assert agent.state == AgentState.COMPOSING


class TestSocialAgentStateHistory:
    """Tests for SocialAgent.state_history field (T032)."""

    def test_state_history_initialized_as_empty_list(self) -> None:
        """state_history should be initialized as empty list."""
        mock_client = MagicMock()
        agent = SocialAgent(
            agent_id="agent_history_001",
            name="Historian",
            interests=["history"],
            personality="meticulous",
            client=mock_client,
        )

        assert agent.state_history == []
        assert isinstance(agent.state_history, list)

    def test_state_history_is_list_of_state_transitions(self) -> None:
        """state_history should be typed as list[StateTransition]."""
        mock_client = MagicMock()
        agent = SocialAgent(
            agent_id="agent_history_002",
            name="Tracker",
            interests=["tracking"],
            personality="detailed",
            client=mock_client,
        )

        # Verify we can access it and it's empty
        assert len(agent.state_history) == 0


class TestSocialAgentTransitionTo:
    """Tests for SocialAgent.transition_to() method (T034)."""

    def test_transition_to_updates_state(self) -> None:
        """transition_to() should update state to new value."""
        from prism.statechart.states import AgentState

        mock_client = MagicMock()
        agent = SocialAgent(
            agent_id="agent_trans_001",
            name="Transitioner",
            interests=["transitions"],
            personality="dynamic",
            client=mock_client,
        )

        agent.transition_to(AgentState.SCROLLING, trigger="start")

        assert agent.state == AgentState.SCROLLING

    def test_transition_to_appends_to_history(self) -> None:
        """transition_to() should append StateTransition to history."""
        from prism.statechart.states import AgentState
        from prism.statechart.transitions import StateTransition

        mock_client = MagicMock()
        agent = SocialAgent(
            agent_id="agent_trans_002",
            name="Recorder",
            interests=["recording"],
            personality="thorough",
            client=mock_client,
        )

        agent.transition_to(AgentState.SCROLLING, trigger="start")

        assert len(agent.state_history) == 1
        assert isinstance(agent.state_history[0], StateTransition)
        assert agent.state_history[0].from_state == AgentState.IDLE
        assert agent.state_history[0].to_state == AgentState.SCROLLING
        assert agent.state_history[0].trigger == "start"

    def test_transition_to_resets_ticks_in_state(self) -> None:
        """transition_to() should reset ticks_in_state to 0."""
        from prism.statechart.states import AgentState

        mock_client = MagicMock()
        agent = SocialAgent(
            agent_id="agent_trans_003",
            name="Resetter",
            interests=["resetting"],
            personality="fresh",
            client=mock_client,
        )

        # Accumulate some ticks
        for _ in range(3):
            agent.tick()
        assert agent.ticks_in_state == 3

        agent.transition_to(AgentState.SCROLLING, trigger="start")

        assert agent.ticks_in_state == 0

    def test_transition_to_noop_for_same_state(self) -> None:
        """transition_to() should be no-op for self-transitions."""
        from prism.statechart.states import AgentState

        mock_client = MagicMock()
        agent = SocialAgent(
            agent_id="agent_trans_004",
            name="Static",
            interests=["staying"],
            personality="steady",
            client=mock_client,
        )

        # Transition to same state (IDLE -> IDLE)
        agent.transition_to(AgentState.IDLE, trigger="noop")

        # History should be empty (no transition recorded)
        assert len(agent.state_history) == 0
        assert agent.state == AgentState.IDLE

    def test_transition_to_accepts_optional_context(self) -> None:
        """transition_to() should accept optional context dict."""
        from prism.statechart.states import AgentState

        mock_client = MagicMock()
        agent = SocialAgent(
            agent_id="agent_trans_005",
            name="Contextual",
            interests=["context"],
            personality="detailed",
            client=mock_client,
        )

        context = {"post_id": "123", "relevance": 0.9}
        agent.transition_to(AgentState.EVALUATING, trigger="see_post", context=context)

        assert agent.state_history[0].context == context


class TestSocialAgentHistoryPruning:
    """Tests for history pruning in transition_to() (T036)."""

    def test_history_respects_max_depth(self) -> None:
        """History should not exceed max_history_depth."""
        from prism.statechart.states import AgentState

        mock_client = MagicMock()
        agent = SocialAgent(
            agent_id="agent_prune_001",
            name="Pruner",
            interests=["pruning"],
            personality="tidy",
            client=mock_client,
            max_history_depth=3,
        )

        # Make 5 transitions
        states = [
            AgentState.SCROLLING,
            AgentState.EVALUATING,
            AgentState.COMPOSING,
            AgentState.ENGAGING_LIKE,
            AgentState.RESTING,
        ]
        for i, state in enumerate(states):
            agent.transition_to(state, trigger=f"trigger_{i}")

        # History should only have 3 entries
        assert len(agent.state_history) == 3

    def test_oldest_entries_removed_first(self) -> None:
        """Oldest entries should be removed first (FIFO)."""
        from prism.statechart.states import AgentState

        mock_client = MagicMock()
        agent = SocialAgent(
            agent_id="agent_prune_002",
            name="FIFO",
            interests=["ordering"],
            personality="orderly",
            client=mock_client,
            max_history_depth=2,
        )

        # Make 3 transitions
        agent.transition_to(AgentState.SCROLLING, trigger="first")
        agent.transition_to(AgentState.EVALUATING, trigger="second")
        agent.transition_to(AgentState.COMPOSING, trigger="third")

        # Only last 2 transitions should remain
        assert len(agent.state_history) == 2
        assert agent.state_history[0].trigger == "second"
        assert agent.state_history[1].trigger == "third"

    def test_max_history_depth_default_is_100(self) -> None:
        """Default max_history_depth should be 100."""
        mock_client = MagicMock()
        agent = SocialAgent(
            agent_id="agent_prune_003",
            name="Default",
            interests=["defaults"],
            personality="standard",
            client=mock_client,
        )

        assert agent.max_history_depth == 100

    def test_max_history_depth_can_be_set_at_construction(self) -> None:
        """max_history_depth should be settable at construction."""
        mock_client = MagicMock()
        agent = SocialAgent(
            agent_id="agent_prune_004",
            name="Custom",
            interests=["customization"],
            personality="unique",
            client=mock_client,
            max_history_depth=50,
        )

        assert agent.max_history_depth == 50


class TestSocialAgentEngagementThreshold:
    """Tests for engagement_threshold parameter and should_engage() (T038)."""

    def test_engagement_threshold_default_is_half(self) -> None:
        """Default engagement_threshold should be 0.5."""
        mock_client = MagicMock()
        agent = SocialAgent(
            agent_id="agent_engage_001",
            name="Default",
            interests=["defaults"],
            personality="standard",
            client=mock_client,
        )

        assert agent.engagement_threshold == 0.5

    def test_engagement_threshold_can_be_set_at_construction(self) -> None:
        """engagement_threshold should be settable at construction."""
        mock_client = MagicMock()
        agent = SocialAgent(
            agent_id="agent_engage_002",
            name="Custom",
            interests=["customization"],
            personality="unique",
            client=mock_client,
            engagement_threshold=0.7,
        )

        assert agent.engagement_threshold == 0.7

    def test_should_engage_returns_true_above_threshold(self) -> None:
        """should_engage() should return True when relevance > threshold."""
        mock_client = MagicMock()
        agent = SocialAgent(
            agent_id="agent_engage_003",
            name="Engager",
            interests=["engagement"],
            personality="active",
            client=mock_client,
            engagement_threshold=0.5,
        )

        assert agent.should_engage(0.6) is True
        assert agent.should_engage(0.9) is True
        assert agent.should_engage(1.0) is True

    def test_should_engage_returns_false_below_threshold(self) -> None:
        """should_engage() should return False when relevance < threshold."""
        mock_client = MagicMock()
        agent = SocialAgent(
            agent_id="agent_engage_004",
            name="Selector",
            interests=["selection"],
            personality="picky",
            client=mock_client,
            engagement_threshold=0.5,
        )

        assert agent.should_engage(0.4) is False
        assert agent.should_engage(0.1) is False
        assert agent.should_engage(0.0) is False

    def test_should_engage_returns_true_at_exact_threshold(self) -> None:
        """should_engage() should return True when relevance == threshold."""
        mock_client = MagicMock()
        agent = SocialAgent(
            agent_id="agent_engage_005",
            name="Exact",
            interests=["precision"],
            personality="precise",
            client=mock_client,
            engagement_threshold=0.5,
        )

        assert agent.should_engage(0.5) is True

    def test_should_engage_with_different_thresholds(self) -> None:
        """should_engage() should respect different threshold values."""
        mock_client = MagicMock()

        # Low threshold agent
        low_agent = SocialAgent(
            agent_id="agent_engage_006",
            name="Easy",
            interests=["anything"],
            personality="easygoing",
            client=mock_client,
            engagement_threshold=0.2,
        )
        assert low_agent.should_engage(0.3) is True

        # High threshold agent
        high_agent = SocialAgent(
            agent_id="agent_engage_007",
            name="Picky",
            interests=["quality"],
            personality="selective",
            client=mock_client,
            engagement_threshold=0.9,
        )
        assert high_agent.should_engage(0.8) is False
        assert high_agent.should_engage(0.95) is True
