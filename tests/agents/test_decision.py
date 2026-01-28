"""Tests for AgentDecision Pydantic model."""

import pytest
from pydantic import ValidationError

from prism.agents.decision import AgentDecision


class TestAgentDecisionValid:
    def test_like_with_no_content(self):
        decision = AgentDecision(
            choice="LIKE",
            reason="This aligns with my interests.",
        )
        assert decision.choice == "LIKE"
        assert decision.reason == "This aligns with my interests."
        assert decision.content is None

    def test_scroll_with_no_content(self):
        decision = AgentDecision(
            choice="SCROLL",
            reason="Not relevant to me.",
        )
        assert decision.choice == "SCROLL"
        assert decision.content is None

    def test_reply_with_content(self):
        decision = AgentDecision(
            choice="REPLY",
            reason="I want to share my perspective.",
            content="Great point! I agree completely.",
        )
        assert decision.choice == "REPLY"
        assert decision.content == "Great point! I agree completely."

    def test_reshare_with_content(self):
        decision = AgentDecision(
            choice="RESHARE",
            reason="My followers should see this.",
            content="Important news about AI safety.",
        )
        assert decision.choice == "RESHARE"
        assert decision.content == "Important news about AI safety."

    def test_all_fields_populated(self):
        decision = AgentDecision(
            choice="LIKE",
            reason="Interesting take.",
            content="Optional content for a like.",
        )
        assert decision.choice == "LIKE"
        assert decision.content == "Optional content for a like."


class TestAgentDecisionInvalid:
    def test_invalid_choice_raises_error(self):
        with pytest.raises(ValidationError):
            AgentDecision(
                choice="BLOCK",
                reason="Not a valid choice.",
            )

    def test_reply_without_content_raises_error(self):
        with pytest.raises(ValidationError):
            AgentDecision(
                choice="REPLY",
                reason="I want to reply.",
                content=None,
            )

    def test_reshare_without_content_raises_error(self):
        with pytest.raises(ValidationError):
            AgentDecision(
                choice="RESHARE",
                reason="Worth resharing.",
                content=None,
            )

    def test_reply_with_empty_content_raises_error(self):
        with pytest.raises(ValidationError):
            AgentDecision(
                choice="REPLY",
                reason="I want to reply.",
                content="",
            )

    def test_reshare_with_empty_content_raises_error(self):
        with pytest.raises(ValidationError):
            AgentDecision(
                choice="RESHARE",
                reason="Worth resharing.",
                content="",
            )

    def test_empty_reason_raises_error(self):
        with pytest.raises(ValidationError):
            AgentDecision(
                choice="LIKE",
                reason="",
            )

    def test_missing_reason_raises_error(self):
        with pytest.raises(ValidationError):
            AgentDecision(choice="LIKE")
