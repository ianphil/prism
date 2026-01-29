"""Integration tests for SocialAgent with real Ollama backend.

These tests require a running Ollama server with the mistral model available.
Run with: uv run pytest -m integration
"""

import pytest

from prism.agents.decision import AgentDecision
from prism.agents.social_agent import SocialAgent
from prism.llm.client import create_llm_client
from prism.llm.config import load_config


@pytest.mark.integration
async def test_social_agent_makes_valid_decision_with_real_ollama():
    """Integration test: SocialAgent produces valid AgentDecision with real LLM."""
    # Load config from default YAML
    config = load_config("configs/default.yaml")

    # Create real OllamaChatClient
    client = create_llm_client(config.llm)

    # Create SocialAgent with test profile
    agent = SocialAgent(
        agent_id="test_agent_001",
        name="Test User",
        interests=["technology", "artificial intelligence", "startups"],
        personality="Enthusiastic tech optimist who loves discussing new innovations",
        client=client,
        temperature=config.llm.temperature,
        max_tokens=config.llm.max_tokens,
    )

    # Sample feed post
    feed_text = """
    Just launched our new AI-powered code review tool!
    It uses LLMs to catch bugs and suggest improvements.
    Early users report 40% fewer bugs making it to production.
    #AI #DevTools #Startups
    """

    # Make a decision
    decision = await agent.decide(feed_text)

    # Verify we get a valid AgentDecision
    assert isinstance(decision, AgentDecision)
    assert decision.choice in ("LIKE", "REPLY", "RESHARE", "SCROLL")
    assert len(decision.reason) > 0

    # If REPLY or RESHARE, content should be present
    if decision.choice in ("REPLY", "RESHARE"):
        assert decision.content is not None
        assert len(decision.content) > 0


@pytest.mark.integration
async def test_social_agent_handles_unrelated_content():
    """Integration test: SocialAgent handles content outside agent's interests."""
    config = load_config("configs/default.yaml")
    client = create_llm_client(config.llm)

    # Create agent interested in cooking
    agent = SocialAgent(
        agent_id="test_agent_002",
        name="Chef Mario",
        interests=["cooking", "Italian cuisine", "restaurants"],
        personality="Passionate chef who only cares about food",
        client=client,
        temperature=config.llm.temperature,
        max_tokens=config.llm.max_tokens,
    )

    # Post about something unrelated to cooking
    feed_text = """
    New firmware update for the Mars rover just dropped!
    The team fixed the wheel actuator issue and improved solar panel efficiency.
    #Space #NASA #Engineering
    """

    decision = await agent.decide(feed_text)

    # Should still produce a valid decision
    assert isinstance(decision, AgentDecision)
    assert decision.choice in ("LIKE", "REPLY", "RESHARE", "SCROLL")
    assert len(decision.reason) > 0
