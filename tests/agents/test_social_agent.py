"""Tests for SocialAgent."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from prism.agents.decisions import Choice
from prism.agents.profiles import AgentProfile
from prism.agents.social_agent import SocialAgent
from prism.models.post import Post


@pytest.fixture
def mock_client() -> MagicMock:
    """Create a mock LLM client."""
    client = MagicMock()
    client.chat = AsyncMock()
    return client


@pytest.fixture
def sample_profile() -> AgentProfile:
    """Create a sample agent profile."""
    return AgentProfile(
        id="agent_001",
        name="Alice",
        interests=["technology", "startups"],
        personality="curious and enthusiastic",
    )


@pytest.fixture
def sample_feed() -> list[Post]:
    """Create a sample feed of posts."""
    return [
        Post(
            id="post_001",
            author_id="author_001",
            text="Just launched our new AI startup!",
            timestamp=datetime.now(),
            likes=50,
            reshares=10,
        ),
        Post(
            id="post_002",
            author_id="author_002",
            text="Beautiful sunset today",
            timestamp=datetime.now(),
            likes=100,
        ),
    ]


class TestSocialAgentInit:
    """Tests for SocialAgent initialization."""

    def test_initialization(
        self, sample_profile: AgentProfile, mock_client: MagicMock
    ) -> None:
        """Agent should initialize with profile and client."""
        agent = SocialAgent(profile=sample_profile, client=mock_client)
        assert agent.profile == sample_profile
        assert agent.client == mock_client

    def test_name_property(
        self, sample_profile: AgentProfile, mock_client: MagicMock
    ) -> None:
        """Agent should expose name property."""
        agent = SocialAgent(profile=sample_profile, client=mock_client)
        assert agent.name == "Alice"

    def test_interests_property(
        self, sample_profile: AgentProfile, mock_client: MagicMock
    ) -> None:
        """Agent should expose interests property."""
        agent = SocialAgent(profile=sample_profile, client=mock_client)
        assert agent.interests == ["technology", "startups"]


class TestSocialAgentDecide:
    """Tests for SocialAgent.decide() method."""

    @pytest.mark.anyio
    async def test_decide_returns_agent_decision(
        self,
        sample_profile: AgentProfile,
        mock_client: MagicMock,
        sample_feed: list[Post],
    ) -> None:
        """decide() should return an AgentDecision."""
        mock_client.chat.return_value = """{
            "choice": "LIKE",
            "reason": "Interesting startup news!",
            "content": null,
            "post_id": "post_001"
        }"""

        agent = SocialAgent(profile=sample_profile, client=mock_client)
        decision = await agent.decide(sample_feed)

        assert decision.choice == Choice.LIKE
        assert decision.reason == "Interesting startup news!"
        assert decision.content is None
        assert decision.post_id == "post_001"

    @pytest.mark.anyio
    async def test_decide_with_reply(
        self,
        sample_profile: AgentProfile,
        mock_client: MagicMock,
        sample_feed: list[Post],
    ) -> None:
        """decide() should handle REPLY with content."""
        mock_client.chat.return_value = """{
            "choice": "REPLY",
            "reason": "Want to congratulate them",
            "content": "Congrats on the launch! What problem does it solve?",
            "post_id": "post_001"
        }"""

        agent = SocialAgent(profile=sample_profile, client=mock_client)
        decision = await agent.decide(sample_feed)

        assert decision.choice == Choice.REPLY
        assert "Congrats" in decision.content

    @pytest.mark.anyio
    async def test_decide_with_reshare(
        self,
        sample_profile: AgentProfile,
        mock_client: MagicMock,
        sample_feed: list[Post],
    ) -> None:
        """decide() should handle RESHARE with content."""
        mock_client.chat.return_value = """{
            "choice": "RESHARE",
            "reason": "My followers would love this",
            "content": "Check out this exciting new startup!",
            "post_id": "post_001"
        }"""

        agent = SocialAgent(profile=sample_profile, client=mock_client)
        decision = await agent.decide(sample_feed)

        assert decision.choice == Choice.RESHARE
        assert decision.content is not None

    @pytest.mark.anyio
    async def test_decide_with_ignore(
        self,
        sample_profile: AgentProfile,
        mock_client: MagicMock,
        sample_feed: list[Post],
    ) -> None:
        """decide() should handle IGNORE."""
        mock_client.chat.return_value = """{
            "choice": "IGNORE",
            "reason": "Not relevant to my interests",
            "content": null,
            "post_id": "post_002"
        }"""

        agent = SocialAgent(profile=sample_profile, client=mock_client)
        decision = await agent.decide(sample_feed)

        assert decision.choice == Choice.IGNORE
        assert decision.content is None

    @pytest.mark.anyio
    async def test_decide_calls_client_with_messages(
        self,
        sample_profile: AgentProfile,
        mock_client: MagicMock,
        sample_feed: list[Post],
    ) -> None:
        """decide() should call client with system and user messages."""
        mock_client.chat.return_value = """{
            "choice": "IGNORE",
            "reason": "Not interested",
            "post_id": "post_001"
        }"""

        agent = SocialAgent(profile=sample_profile, client=mock_client)
        await agent.decide(sample_feed)

        # Verify client was called with messages
        mock_client.chat.assert_called_once()
        messages = mock_client.chat.call_args[0][0]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    @pytest.mark.anyio
    async def test_decide_uses_fallback_for_missing_post_id(
        self,
        sample_profile: AgentProfile,
        mock_client: MagicMock,
        sample_feed: list[Post],
    ) -> None:
        """decide() should use first post's ID as fallback."""
        mock_client.chat.return_value = """{
            "choice": "LIKE",
            "reason": "Good post"
        }"""

        agent = SocialAgent(profile=sample_profile, client=mock_client)
        decision = await agent.decide(sample_feed)

        # Should use first post's ID as fallback
        assert decision.post_id == "post_001"

    @pytest.mark.anyio
    async def test_decide_handles_missing_content_for_reply(
        self,
        sample_profile: AgentProfile,
        mock_client: MagicMock,
        sample_feed: list[Post],
    ) -> None:
        """decide() should use reason as content if REPLY missing content."""
        mock_client.chat.return_value = """{
            "choice": "REPLY",
            "reason": "I want to say something about this",
            "post_id": "post_001"
        }"""

        agent = SocialAgent(profile=sample_profile, client=mock_client)
        decision = await agent.decide(sample_feed)

        # Content should be filled from reason
        assert decision.choice == Choice.REPLY
        assert decision.content is not None
