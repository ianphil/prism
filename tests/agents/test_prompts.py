"""Tests for prompt template functions."""

from prism.agents.prompts import build_feed_prompt, build_system_prompt


class TestBuildSystemPrompt:
    """Tests for build_system_prompt function."""

    def test_includes_agent_name(self):
        """System prompt should include the agent's name."""
        prompt = build_system_prompt(
            name="Alice",
            interests=["technology", "AI"],
            personality="curious and analytical",
        )
        assert "Alice" in prompt

    def test_includes_interests(self):
        """System prompt should include the agent's interests."""
        prompt = build_system_prompt(
            name="Bob",
            interests=["cryptocurrency", "finance", "tech news"],
            personality="enthusiastic investor",
        )
        assert "cryptocurrency" in prompt
        assert "finance" in prompt
        assert "tech news" in prompt

    def test_includes_personality(self):
        """System prompt should include the agent's personality."""
        prompt = build_system_prompt(
            name="Charlie",
            interests=["sports"],
            personality="competitive and outspoken",
        )
        assert "competitive and outspoken" in prompt

    def test_mentions_valid_choices(self):
        """System prompt should mention all valid decision choices."""
        prompt = build_system_prompt(
            name="Dana",
            interests=["music"],
            personality="creative",
        )
        assert "LIKE" in prompt
        assert "REPLY" in prompt
        assert "RESHARE" in prompt
        assert "SCROLL" in prompt

    def test_instructs_json_output(self):
        """System prompt should instruct agent to return JSON."""
        prompt = build_system_prompt(
            name="Eve",
            interests=["cooking"],
            personality="helpful",
        )
        # Should mention JSON format for structured output
        assert "JSON" in prompt or "json" in prompt


class TestBuildFeedPrompt:
    """Tests for build_feed_prompt function."""

    def test_formats_feed_text(self):
        """Feed prompt should include the provided feed text."""
        feed_text = "Check out this new AI model!"
        prompt = build_feed_prompt(feed_text)
        assert "Check out this new AI model!" in prompt

    def test_returns_string(self):
        """Feed prompt should return a string."""
        prompt = build_feed_prompt("Some post content")
        assert isinstance(prompt, str)

    def test_handles_multiline_feed(self):
        """Feed prompt should handle multiline feed text."""
        feed_text = """Post 1: Hello world!
Post 2: Great news today.
Post 3: Check this out."""
        prompt = build_feed_prompt(feed_text)
        assert "Hello world!" in prompt
        assert "Great news today" in prompt
        assert "Check this out" in prompt
