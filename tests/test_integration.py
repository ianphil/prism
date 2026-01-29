"""Integration tests for PRISM foundation."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from prism import (
    AgentDecision,
    AgentProfile,
    Choice,
    Config,
    OllamaChatClient,
    Post,
    SocialAgent,
    load_config,
)


class TestPackageImports:
    """Test that all package exports are accessible."""

    def test_version_available(self) -> None:
        """Package version should be accessible."""
        from prism import __version__

        assert __version__ == "0.1.0"

    def test_agent_imports(self) -> None:
        """Agent classes should be importable from prism."""
        assert AgentDecision is not None
        assert AgentProfile is not None
        assert Choice is not None
        assert SocialAgent is not None

    def test_llm_imports(self) -> None:
        """LLM client should be importable from prism."""
        assert OllamaChatClient is not None

    def test_config_imports(self) -> None:
        """Config classes should be importable from prism."""
        assert Config is not None
        assert load_config is not None

    def test_model_imports(self) -> None:
        """Data models should be importable from prism."""
        assert Post is not None


class TestEndToEndWorkflow:
    """Integration test for complete agent workflow."""

    @pytest.mark.anyio
    async def test_agent_makes_decision_on_feed(self) -> None:
        """Agent should make a complete decision on a feed of posts."""
        # Setup: Create profile and mock client
        profile = AgentProfile(
            id="integration_test_agent",
            name="IntegrationBot",
            interests=["AI", "machine learning", "technology"],
            personality="enthusiastic tech advocate",
        )

        mock_client = MagicMock(spec=OllamaChatClient)
        mock_client.chat = AsyncMock(return_value="""{
            "choice": "REPLY",
            "reason": "This is relevant to my AI interests",
            "content": "Congrats on the deployment! What model are you using?",
            "post_id": "post_001"
        }""")

        # Create feed
        feed = [
            Post(
                id="post_001",
                author_id="author_001",
                text="Just deployed our new AI model!",
                timestamp=datetime.now(),
                likes=50,
            ),
            Post(
                id="post_002",
                author_id="author_002",
                text="Beautiful sunset today",
                timestamp=datetime.now(),
            ),
        ]

        # Execute: Agent makes decision
        agent = SocialAgent(profile=profile, client=mock_client)
        decision = await agent.decide(feed)

        # Verify: Decision is properly formed
        assert isinstance(decision, AgentDecision)
        assert decision.choice == Choice.REPLY
        assert decision.post_id == "post_001"
        assert decision.reason is not None
        assert decision.content is not None
        assert "Congrats" in decision.content

    @pytest.mark.anyio
    async def test_agent_ignores_irrelevant_posts(self) -> None:
        """Agent should ignore posts outside its interests."""
        profile = AgentProfile(
            id="finance_agent",
            name="FinanceBot",
            interests=["stocks", "investing", "economics"],
            personality="analytical and cautious",
        )

        mock_client = MagicMock(spec=OllamaChatClient)
        mock_client.chat = AsyncMock(return_value="""{
            "choice": "IGNORE",
            "reason": "Not relevant to my financial interests",
            "content": null,
            "post_id": "post_001"
        }""")

        feed = [
            Post(
                id="post_001",
                author_id="author_001",
                text="My cat learned a new trick!",
                timestamp=datetime.now(),
            ),
        ]

        agent = SocialAgent(profile=profile, client=mock_client)
        decision = await agent.decide(feed)

        assert decision.choice == Choice.IGNORE
        assert decision.content is None


class TestConfigIntegration:
    """Integration tests for configuration system."""

    def test_config_creates_valid_client_params(self) -> None:
        """Config values should be usable for client initialization."""
        config = load_config()

        # Should be able to create client from config values
        client = OllamaChatClient(
            endpoint=config.llm.endpoint,
            model=config.llm.model,
            timeout=config.llm.timeout,
        )

        assert client.endpoint == config.llm.endpoint
        assert client.model == config.llm.model
        assert client.timeout == config.llm.timeout

    def test_default_config_is_valid(self) -> None:
        """Default configuration should pass validation."""
        config = load_config()

        assert config.llm.endpoint.startswith("http")
        assert config.llm.model is not None
        assert config.llm.timeout > 0
        assert config.llm.reasoning_effort in ["low", "medium", "high"]


class TestDataModelIntegration:
    """Integration tests for data models working together."""

    def test_post_formats_for_agent_prompt(self) -> None:
        """Post should format correctly for agent prompts."""
        post = Post(
            id="test_post",
            author_id="author",
            text="Test content",
            timestamp=datetime.now(),
            has_media=True,
            media_type="image",
            media_description="A test image",
            likes=10,
            reshares=5,
            replies=2,
        )

        formatted = post.format_for_prompt()

        assert "Test content" in formatted
        assert "IMAGE" in formatted
        assert "test image" in formatted
        assert "10" in formatted  # likes

    def test_decision_validates_content_for_choice(self) -> None:
        """AgentDecision should validate content matches choice."""
        # Valid LIKE (no content)
        decision = AgentDecision(
            choice=Choice.LIKE,
            reason="Good post",
            post_id="post_001",
        )
        assert decision.content is None

        # Valid REPLY (with content)
        decision = AgentDecision(
            choice=Choice.REPLY,
            reason="Want to respond",
            content="Great point!",
            post_id="post_001",
        )
        assert decision.content == "Great point!"

        # Invalid: REPLY without content should raise
        with pytest.raises(ValueError):
            AgentDecision(
                choice=Choice.REPLY,
                reason="Want to respond",
                post_id="post_001",
            )
