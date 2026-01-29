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
