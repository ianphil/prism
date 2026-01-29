"""Tests for agent decision types."""

import pytest

from prism.agents.decisions import AgentDecision, Choice


class TestChoice:
    """Tests for the Choice enum."""

    def test_choice_has_four_values(self) -> None:
        """Choice enum should have exactly four values."""
        assert len(Choice) == 4

    def test_choice_values(self) -> None:
        """Choice enum should have IGNORE, LIKE, REPLY, RESHARE."""
        assert Choice.IGNORE.value == "IGNORE"
        assert Choice.LIKE.value == "LIKE"
        assert Choice.REPLY.value == "REPLY"
        assert Choice.RESHARE.value == "RESHARE"

    def test_choice_is_string_enum(self) -> None:
        """Choice values should be strings."""
        for choice in Choice:
            assert isinstance(choice.value, str)


class TestAgentDecision:
    """Tests for the AgentDecision dataclass."""

    def test_decision_with_ignore(self) -> None:
        """IGNORE decision should have no content."""
        decision = AgentDecision(
            choice=Choice.IGNORE,
            reason="Not interested in this topic",
            post_id="post_123",
        )
        assert decision.choice == Choice.IGNORE
        assert decision.reason == "Not interested in this topic"
        assert decision.content is None
        assert decision.post_id == "post_123"

    def test_decision_with_like(self) -> None:
        """LIKE decision should have no content."""
        decision = AgentDecision(
            choice=Choice.LIKE,
            reason="Agree with the sentiment",
            post_id="post_456",
        )
        assert decision.choice == Choice.LIKE
        assert decision.content is None

    def test_decision_with_reply(self) -> None:
        """REPLY decision requires content."""
        decision = AgentDecision(
            choice=Choice.REPLY,
            reason="Want to share my perspective",
            post_id="post_789",
            content="Great point! I also think...",
        )
        assert decision.choice == Choice.REPLY
        assert decision.content == "Great point! I also think..."

    def test_decision_with_reshare(self) -> None:
        """RESHARE decision requires content."""
        decision = AgentDecision(
            choice=Choice.RESHARE,
            reason="My followers would find this interesting",
            post_id="post_101",
            content="Check this out!",
        )
        assert decision.choice == Choice.RESHARE
        assert decision.content == "Check this out!"

    def test_decision_has_timestamp(self) -> None:
        """Decision should have a timestamp."""
        decision = AgentDecision(
            choice=Choice.IGNORE,
            reason="Not relevant",
            post_id="post_123",
        )
        assert decision.timestamp is not None

    def test_ignore_with_content_raises(self) -> None:
        """IGNORE with content should raise ValueError."""
        with pytest.raises(ValueError, match="content must be None"):
            AgentDecision(
                choice=Choice.IGNORE,
                reason="Not interested",
                post_id="post_123",
                content="This shouldn't be here",
            )

    def test_like_with_content_raises(self) -> None:
        """LIKE with content should raise ValueError."""
        with pytest.raises(ValueError, match="content must be None"):
            AgentDecision(
                choice=Choice.LIKE,
                reason="Good post",
                post_id="post_123",
                content="This shouldn't be here",
            )

    def test_reply_without_content_raises(self) -> None:
        """REPLY without content should raise ValueError."""
        with pytest.raises(ValueError, match="content is required"):
            AgentDecision(
                choice=Choice.REPLY,
                reason="Want to respond",
                post_id="post_123",
            )

    def test_reshare_without_content_raises(self) -> None:
        """RESHARE without content should raise ValueError."""
        with pytest.raises(ValueError, match="content is required"):
            AgentDecision(
                choice=Choice.RESHARE,
                reason="Want to share",
                post_id="post_123",
            )

    def test_empty_reason_raises(self) -> None:
        """Empty reason should raise ValueError."""
        with pytest.raises(ValueError, match="reason must be a non-empty string"):
            AgentDecision(
                choice=Choice.IGNORE,
                reason="",
                post_id="post_123",
            )
