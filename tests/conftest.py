"""Shared test fixtures and configuration."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from prism.agents import AgentProfile
from prism.models import Post


@pytest.fixture
def sample_profile() -> AgentProfile:
    """Create a sample agent profile for testing."""
    return AgentProfile(
        id="test_agent_001",
        name="TestAlice",
        interests=["technology", "AI", "startups"],
        personality="curious and analytical tech enthusiast",
    )


@pytest.fixture
def sample_posts() -> list[Post]:
    """Create sample posts for testing."""
    return [
        Post(
            id="post_001",
            author_id="author_001",
            text="Just deployed our new AI model to production!",
            timestamp=datetime.now(),
            likes=42,
            reshares=12,
            replies=5,
        ),
        Post(
            id="post_002",
            author_id="author_002",
            text="Beautiful weather for a hike today.",
            timestamp=datetime.now(),
            likes=89,
            reshares=3,
        ),
        Post(
            id="post_003",
            author_id="author_003",
            text="Thoughts on the latest startup funding trends?",
            timestamp=datetime.now(),
            has_media=True,
            media_type="image",
            media_description="Chart showing VC funding by sector",
            likes=156,
            reshares=45,
            replies=23,
        ),
    ]


@pytest.fixture
def mock_llm_client() -> MagicMock:
    """Create a mock LLM client for testing."""
    client = MagicMock()
    client.chat = AsyncMock()
    return client
