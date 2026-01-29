"""Tests for prompt building utilities."""

from datetime import datetime, timedelta

import pytest

from prism.agents.profiles import AgentProfile
from prism.agents.prompts import (
    build_system_prompt,
    build_user_prompt,
    parse_decision_response,
)
from prism.models.post import Post


class TestBuildSystemPrompt:
    """Tests for build_system_prompt function."""

    def test_includes_agent_name(self) -> None:
        """System prompt should include agent name."""
        profile = AgentProfile(
            id="agent_001",
            name="Alice",
            interests=["technology"],
        )
        prompt = build_system_prompt(profile)
        assert "Alice" in prompt

    def test_includes_interests(self) -> None:
        """System prompt should include interests."""
        profile = AgentProfile(
            id="agent_001",
            name="Alice",
            interests=["technology", "startups", "AI"],
        )
        prompt = build_system_prompt(profile)
        assert "technology" in prompt
        assert "startups" in prompt
        assert "AI" in prompt

    def test_includes_personality(self) -> None:
        """System prompt should include personality."""
        profile = AgentProfile(
            id="agent_001",
            name="Bob",
            interests=["finance"],
            personality="skeptical and analytical",
        )
        prompt = build_system_prompt(profile)
        assert "skeptical and analytical" in prompt

    def test_includes_decision_options(self) -> None:
        """System prompt should list all decision options."""
        profile = AgentProfile(
            id="agent_001",
            name="Alice",
            interests=["tech"],
        )
        prompt = build_system_prompt(profile)
        assert "IGNORE" in prompt
        assert "LIKE" in prompt
        assert "REPLY" in prompt
        assert "RESHARE" in prompt

    def test_includes_json_format(self) -> None:
        """System prompt should specify JSON format."""
        profile = AgentProfile(
            id="agent_001",
            name="Alice",
            interests=["tech"],
        )
        prompt = build_system_prompt(profile)
        assert '"choice"' in prompt
        assert '"reason"' in prompt
        assert '"content"' in prompt
        assert '"post_id"' in prompt

    def test_includes_stance_if_present(self) -> None:
        """System prompt should include stance positions if present."""
        profile = AgentProfile(
            id="agent_001",
            name="Bob",
            interests=["politics"],
            stance={"climate": "concerned", "economy": "cautious"},
        )
        prompt = build_system_prompt(profile)
        assert "climate" in prompt
        assert "concerned" in prompt
        assert "economy" in prompt


class TestBuildUserPrompt:
    """Tests for build_user_prompt function."""

    def test_empty_feed(self) -> None:
        """Empty feed should return empty message."""
        profile = AgentProfile(
            id="agent_001",
            name="Alice",
            interests=["tech"],
        )
        prompt = build_user_prompt([], profile)
        assert "empty" in prompt.lower()

    def test_includes_post_content(self) -> None:
        """User prompt should include post text."""
        profile = AgentProfile(
            id="agent_001",
            name="Alice",
            interests=["tech"],
        )
        posts = [
            Post(
                id="post_001",
                author_id="author_001",
                text="Check out this cool new feature!",
                timestamp=datetime.now() - timedelta(hours=1),
            )
        ]
        prompt = build_user_prompt(posts, profile)
        assert "Check out this cool new feature!" in prompt

    def test_includes_post_ids(self) -> None:
        """User prompt should include post IDs."""
        profile = AgentProfile(
            id="agent_001",
            name="Alice",
            interests=["tech"],
        )
        posts = [
            Post(
                id="post_123",
                author_id="author_001",
                text="Test post",
                timestamp=datetime.now(),
            )
        ]
        prompt = build_user_prompt(posts, profile)
        assert "post_123" in prompt

    def test_includes_agent_name(self) -> None:
        """User prompt should address agent by name."""
        profile = AgentProfile(
            id="agent_001",
            name="Bob",
            interests=["tech"],
        )
        posts = [
            Post(
                id="post_001",
                author_id="author_001",
                text="Test",
                timestamp=datetime.now(),
            )
        ]
        prompt = build_user_prompt(posts, profile)
        assert "Bob" in prompt

    def test_multiple_posts_numbered(self) -> None:
        """Multiple posts should be numbered."""
        profile = AgentProfile(
            id="agent_001",
            name="Alice",
            interests=["tech"],
        )
        posts = [
            Post(
                id=f"post_{i}",
                author_id="author_001",
                text=f"Post {i}",
                timestamp=datetime.now(),
            )
            for i in range(3)
        ]
        prompt = build_user_prompt(posts, profile)
        assert "Post #1" in prompt
        assert "Post #2" in prompt
        assert "Post #3" in prompt


class TestParseDecisionResponse:
    """Tests for parse_decision_response function."""

    def test_parse_valid_json(self) -> None:
        """Should parse valid JSON response."""
        response = """{
            "choice": "LIKE",
            "reason": "I agree with this",
            "content": null,
            "post_id": "post_123"
        }"""
        result = parse_decision_response(response)
        assert result["choice"] == "LIKE"
        assert result["reason"] == "I agree with this"
        assert result["content"] is None
        assert result["post_id"] == "post_123"

    def test_parse_json_with_surrounding_text(self) -> None:
        """Should extract JSON from response with extra text."""
        response = """Here's my decision:
        {
            "choice": "REPLY",
            "reason": "I want to respond",
            "content": "Great point!",
            "post_id": "post_456"
        }
        That's my answer."""
        result = parse_decision_response(response)
        assert result["choice"] == "REPLY"
        assert result["content"] == "Great point!"

    def test_parse_lowercase_choice(self) -> None:
        """Should handle lowercase choice values."""
        response = '{"choice": "like", "reason": "good", "post_id": "p1"}'
        result = parse_decision_response(response)
        assert result["choice"] == "LIKE"

    def test_parse_missing_reason_uses_default(self) -> None:
        """Should provide default reason if missing."""
        response = '{"choice": "IGNORE", "post_id": "p1"}'
        result = parse_decision_response(response)
        assert result["reason"] == "No reason provided"

    def test_parse_missing_post_id_uses_fallback(self) -> None:
        """Should use fallback post_id if missing."""
        response = '{"choice": "LIKE", "reason": "good"}'
        result = parse_decision_response(response, fallback_post_id="fallback_123")
        assert result["post_id"] == "fallback_123"

    def test_parse_missing_post_id_no_fallback_raises(self) -> None:
        """Should raise if post_id missing and no fallback."""
        response = '{"choice": "LIKE", "reason": "good"}'
        with pytest.raises(ValueError, match="post_id"):
            parse_decision_response(response)

    def test_parse_fallback_from_text(self) -> None:
        """Should extract choice from unstructured text."""
        response = "I think I'll LIKE this post because it's interesting."
        result = parse_decision_response(response, fallback_post_id="p1")
        assert result["choice"] == "LIKE"

    def test_parse_invalid_response_raises(self) -> None:
        """Should raise for completely unparseable response."""
        response = "I don't know what to do."
        with pytest.raises(ValueError, match="Could not parse"):
            parse_decision_response(response)

    def test_parse_invalid_json_raises(self) -> None:
        """Should raise for malformed JSON."""
        response = '{"choice": "LIKE", reason: missing quotes}'
        with pytest.raises(ValueError, match="Invalid JSON"):
            parse_decision_response(response)
