"""Tests for StatechartReasoner - LLM-based agent decision making.

This module tests the Reasoner component that resolves ambiguous state
transitions using LLM inference.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from prism.statechart.states import AgentState  # noqa: F401

# =============================================================================
# T016: Tests for StatechartReasoner.__init__()
# =============================================================================


class TestStatechartReasonerInit:
    """Tests for StatechartReasoner construction."""

    def test_init_accepts_ollama_client(self) -> None:
        """StatechartReasoner accepts OllamaChatClient at construction."""
        from prism.statechart.reasoner import StatechartReasoner

        mock_client = MagicMock()
        reasoner = StatechartReasoner(client=mock_client)

        assert reasoner is not None

    def test_init_stores_client_reference(self) -> None:
        """StatechartReasoner stores client reference for later use."""
        from prism.statechart.reasoner import StatechartReasoner

        mock_client = MagicMock()
        reasoner = StatechartReasoner(client=mock_client)

        assert reasoner._client is mock_client


# =============================================================================
# T018: Tests for reasoner prompt construction
# =============================================================================


class TestBuildReasonerPrompt:
    """Tests for build_reasoner_prompt function."""

    def test_prompt_includes_agent_name(self) -> None:
        """Prompt includes agent name."""
        from prism.statechart.reasoner import build_reasoner_prompt

        prompt = build_reasoner_prompt(
            agent_name="Alice",
            agent_interests=["technology"],
            agent_personality="curious",
            current_state=AgentState.EVALUATING,
            trigger="decides",
            options=[AgentState.COMPOSING, AgentState.SCROLLING],
            context=None,
        )

        assert "Alice" in prompt

    def test_prompt_includes_agent_interests(self) -> None:
        """Prompt includes agent interests."""
        from prism.statechart.reasoner import build_reasoner_prompt

        prompt = build_reasoner_prompt(
            agent_name="Bob",
            agent_interests=["python", "machine learning"],
            agent_personality="analytical",
            current_state=AgentState.EVALUATING,
            trigger="decides",
            options=[AgentState.COMPOSING, AgentState.SCROLLING],
            context=None,
        )

        assert "python" in prompt
        assert "machine learning" in prompt

    def test_prompt_includes_current_state_and_trigger(self) -> None:
        """Prompt includes current state and trigger."""
        from prism.statechart.reasoner import build_reasoner_prompt

        prompt = build_reasoner_prompt(
            agent_name="Charlie",
            agent_interests=["art"],
            agent_personality="creative",
            current_state=AgentState.EVALUATING,
            trigger="decides",
            options=[AgentState.COMPOSING],
            context=None,
        )

        assert "evaluating" in prompt.lower()
        assert "decides" in prompt

    def test_prompt_includes_options_with_descriptions(self) -> None:
        """Prompt includes available options with descriptions."""
        from prism.statechart.reasoner import build_reasoner_prompt

        prompt = build_reasoner_prompt(
            agent_name="Diana",
            agent_interests=["music"],
            agent_personality="expressive",
            current_state=AgentState.EVALUATING,
            trigger="decides",
            options=[AgentState.ENGAGING_LIKE, AgentState.ENGAGING_REPLY],
            context=None,
        )

        # Should include state values
        assert "engaging_like" in prompt.lower()
        assert "engaging_reply" in prompt.lower()

    def test_prompt_requests_json_response_format(self) -> None:
        """Prompt requests JSON response format."""
        from prism.statechart.reasoner import build_reasoner_prompt

        prompt = build_reasoner_prompt(
            agent_name="Eve",
            agent_interests=["cooking"],
            agent_personality="enthusiastic",
            current_state=AgentState.SCROLLING,
            trigger="sees_post",
            options=[AgentState.EVALUATING, AgentState.IDLE],
            context=None,
        )

        assert "JSON" in prompt or "json" in prompt
        assert "next_state" in prompt

    def test_prompt_includes_context_when_provided(self) -> None:
        """Prompt includes context when provided."""
        from prism.statechart.reasoner import build_reasoner_prompt

        context = {"post_text": "Check out this new AI model!", "author": "tech_blog"}

        prompt = build_reasoner_prompt(
            agent_name="Frank",
            agent_interests=["AI"],
            agent_personality="tech-savvy",
            current_state=AgentState.EVALUATING,
            trigger="decides",
            options=[AgentState.COMPOSING, AgentState.SCROLLING],
            context=context,
        )

        assert "AI model" in prompt or "tech_blog" in prompt


# =============================================================================
# T020: Tests for StatechartReasoner.decide() (async)
# =============================================================================


class TestStatechartReasonerDecide:
    """Tests for StatechartReasoner.decide() method."""

    @pytest.mark.asyncio
    async def test_decide_returns_agent_state(self) -> None:
        """decide() returns an AgentState from options."""
        from prism.statechart.reasoner import StatechartReasoner

        mock_client = MagicMock()
        # Mock the run method to return valid JSON
        mock_client.run = AsyncMock(return_value='{"next_state": "composing"}')

        reasoner = StatechartReasoner(client=mock_client)
        mock_agent = MagicMock()
        mock_agent.name = "TestAgent"
        mock_agent.interests = ["tech"]
        mock_agent.personality = "curious"

        result = await reasoner.decide(
            agent=mock_agent,
            current_state=AgentState.EVALUATING,
            trigger="decides",
            options=[AgentState.COMPOSING, AgentState.SCROLLING],
            context=None,
        )

        assert result == AgentState.COMPOSING

    @pytest.mark.asyncio
    async def test_decide_calls_llm_with_prompt(self) -> None:
        """decide() calls LLM client with constructed prompt."""
        from prism.statechart.reasoner import StatechartReasoner

        mock_client = MagicMock()
        mock_client.run = AsyncMock(return_value='{"next_state": "scrolling"}')

        reasoner = StatechartReasoner(client=mock_client)
        mock_agent = MagicMock()
        mock_agent.name = "Alice"
        mock_agent.interests = ["python", "AI"]
        mock_agent.personality = "analytical"

        await reasoner.decide(
            agent=mock_agent,
            current_state=AgentState.EVALUATING,
            trigger="decides",
            options=[AgentState.COMPOSING, AgentState.SCROLLING],
            context=None,
        )

        # Verify LLM was called
        mock_client.run.assert_called_once()
        call_args = mock_client.run.call_args
        prompt = call_args[0][0] if call_args[0] else call_args[1].get("prompt", "")
        assert "Alice" in prompt

    @pytest.mark.asyncio
    async def test_decide_parses_json_response(self) -> None:
        """decide() correctly parses JSON response from LLM."""
        from prism.statechart.reasoner import StatechartReasoner

        mock_client = MagicMock()
        mock_client.run = AsyncMock(return_value='{"next_state": "engaging_like"}')

        reasoner = StatechartReasoner(client=mock_client)
        mock_agent = MagicMock()
        mock_agent.name = "Bob"
        mock_agent.interests = ["music"]
        mock_agent.personality = "enthusiastic"

        result = await reasoner.decide(
            agent=mock_agent,
            current_state=AgentState.EVALUATING,
            trigger="decides",
            options=[AgentState.ENGAGING_LIKE, AgentState.SCROLLING],
            context=None,
        )

        assert result == AgentState.ENGAGING_LIKE


# =============================================================================
# T022: Tests for reasoner parse error handling
# =============================================================================


class TestStatechartReasonerErrorHandling:
    """Tests for reasoner error handling."""

    @pytest.mark.asyncio
    async def test_json_parse_error_returns_fallback(self) -> None:
        """JSON parse error returns fallback state (first option)."""
        from prism.statechart.reasoner import StatechartReasoner

        mock_client = MagicMock()
        mock_client.run = AsyncMock(return_value="not valid json at all")

        reasoner = StatechartReasoner(client=mock_client)
        mock_agent = MagicMock()
        mock_agent.name = "Charlie"
        mock_agent.interests = ["sports"]
        mock_agent.personality = "active"

        result = await reasoner.decide(
            agent=mock_agent,
            current_state=AgentState.EVALUATING,
            trigger="decides",
            options=[AgentState.SCROLLING, AgentState.COMPOSING],
            context=None,
        )

        # Should fallback to first option
        assert result == AgentState.SCROLLING

    @pytest.mark.asyncio
    async def test_invalid_state_in_response_returns_fallback(self) -> None:
        """Invalid state value in response returns fallback."""
        from prism.statechart.reasoner import StatechartReasoner

        mock_client = MagicMock()
        mock_client.run = AsyncMock(return_value='{"next_state": "invalid_state"}')

        reasoner = StatechartReasoner(client=mock_client)
        mock_agent = MagicMock()
        mock_agent.name = "Diana"
        mock_agent.interests = ["reading"]
        mock_agent.personality = "quiet"

        result = await reasoner.decide(
            agent=mock_agent,
            current_state=AgentState.EVALUATING,
            trigger="decides",
            options=[AgentState.COMPOSING, AgentState.IDLE],
            context=None,
        )

        # Should fallback to first option
        assert result == AgentState.COMPOSING

    @pytest.mark.asyncio
    async def test_state_not_in_options_returns_fallback(self) -> None:
        """State that is valid but not in options returns fallback."""
        from prism.statechart.reasoner import StatechartReasoner

        mock_client = MagicMock()
        # Returns a valid state that isn't in options
        mock_client.run = AsyncMock(return_value='{"next_state": "resting"}')

        reasoner = StatechartReasoner(client=mock_client)
        mock_agent = MagicMock()
        mock_agent.name = "Eve"
        mock_agent.interests = ["cooking"]
        mock_agent.personality = "creative"

        result = await reasoner.decide(
            agent=mock_agent,
            current_state=AgentState.EVALUATING,
            trigger="decides",
            options=[AgentState.SCROLLING, AgentState.COMPOSING],
            context=None,
        )

        # Should fallback to first option since RESTING not in options
        assert result == AgentState.SCROLLING

    def test_empty_options_raises_value_error(self) -> None:
        """Empty options list raises ValueError."""
        from prism.statechart.reasoner import StatechartReasoner

        mock_client = MagicMock()
        reasoner = StatechartReasoner(client=mock_client)
        mock_agent = MagicMock()
        mock_agent.name = "Frank"
        mock_agent.interests = []
        mock_agent.personality = "unknown"

        with pytest.raises(ValueError, match="options"):
            # This should raise synchronously at validation
            import asyncio

            asyncio.get_event_loop().run_until_complete(
                reasoner.decide(
                    agent=mock_agent,
                    current_state=AgentState.EVALUATING,
                    trigger="decides",
                    options=[],  # Empty!
                    context=None,
                )
            )

    @pytest.mark.asyncio
    async def test_missing_next_state_key_returns_fallback(self) -> None:
        """Missing next_state key in JSON returns fallback."""
        from prism.statechart.reasoner import StatechartReasoner

        mock_client = MagicMock()
        mock_client.run = AsyncMock(return_value='{"wrong_key": "composing"}')

        reasoner = StatechartReasoner(client=mock_client)
        mock_agent = MagicMock()
        mock_agent.name = "Grace"
        mock_agent.interests = ["art"]
        mock_agent.personality = "artistic"

        result = await reasoner.decide(
            agent=mock_agent,
            current_state=AgentState.EVALUATING,
            trigger="decides",
            options=[AgentState.IDLE, AgentState.SCROLLING],
            context=None,
        )

        # Should fallback to first option
        assert result == AgentState.IDLE
