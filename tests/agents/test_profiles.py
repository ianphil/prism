"""Tests for agent profiles."""

import pytest

from prism.agents.profiles import AgentProfile


class TestAgentProfile:
    """Tests for the AgentProfile dataclass."""

    def test_profile_creation(self) -> None:
        """Profile should be creatable with required fields."""
        profile = AgentProfile(
            id="agent_001",
            name="Alice",
            interests=["technology", "startups"],
        )
        assert profile.id == "agent_001"
        assert profile.name == "Alice"
        assert profile.interests == ["technology", "startups"]

    def test_profile_default_personality(self) -> None:
        """Profile should have default personality."""
        profile = AgentProfile(
            id="agent_001",
            name="Alice",
            interests=["tech"],
        )
        assert profile.personality == "neutral"

    def test_profile_default_stance(self) -> None:
        """Profile should have empty default stance."""
        profile = AgentProfile(
            id="agent_001",
            name="Alice",
            interests=["tech"],
        )
        assert profile.stance == {}

    def test_profile_with_all_fields(self) -> None:
        """Profile should accept all optional fields."""
        profile = AgentProfile(
            id="agent_002",
            name="Bob",
            interests=["politics", "economics"],
            personality="skeptical and analytical",
            stance={"climate": "concerned", "tech": "optimistic"},
        )
        assert profile.personality == "skeptical and analytical"
        assert profile.stance["climate"] == "concerned"

    def test_empty_id_raises(self) -> None:
        """Empty id should raise ValueError."""
        with pytest.raises(ValueError, match="id must be a non-empty string"):
            AgentProfile(
                id="",
                name="Alice",
                interests=["tech"],
            )

    def test_empty_name_raises(self) -> None:
        """Empty name should raise ValueError."""
        with pytest.raises(ValueError, match="name must be a non-empty string"):
            AgentProfile(
                id="agent_001",
                name="",
                interests=["tech"],
            )

    def test_empty_interests_raises(self) -> None:
        """Empty interests should raise ValueError."""
        with pytest.raises(ValueError, match="interests must have at least one item"):
            AgentProfile(
                id="agent_001",
                name="Alice",
                interests=[],
            )
